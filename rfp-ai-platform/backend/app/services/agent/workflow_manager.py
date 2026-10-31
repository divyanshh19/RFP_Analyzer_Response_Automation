"""
Workflow Execution Manager.
Provides thread-safe state access, workflow initiation, state querying, and checkpoint resumption.
"""

import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.agent.graph import rfp_workflow_app
from app.services.agent.state import make_initial_state, RFPWorkflowState, WorkflowExecutionState

# In-memory execution tracking store
_active_state_cache: Dict[str, RFPWorkflowState] = {}
_workflow_locks: Dict[str, threading.Lock] = {}


class WorkflowManager:
    """Manages LangGraph execution lifecycles by project_id."""
    
    @staticmethod
    def _get_lock(project_id: str) -> threading.Lock:
        if project_id not in _workflow_locks:
            _workflow_locks[project_id] = threading.Lock()
        return _workflow_locks[project_id]
        
    @classmethod
    def start_workflow(
        cls,
        project_id: str,
        document_id: str,
        file_path: str,
        file_type: str = "pdf"
    ) -> Dict[str, Any]:
        """Initializes and executes the workflow until the human review interrupt or early halt."""
        pid = str(project_id)
        config = {"configurable": {"thread_id": pid}}
        
        init_state = make_initial_state(
            project_id=pid,
            document_id=str(document_id),
            file_path=file_path,
            file_type=file_type
        )
        init_state["execution_state"] = WorkflowExecutionState.RUNNING.value
        _active_state_cache[pid] = init_state
        
        lock = cls._get_lock(pid)
        with lock:
            try:
                # Runs from START until interrupt_before=["human_review"] or early halt
                result = rfp_workflow_app.invoke(init_state, config=config)
                _active_state_cache[pid] = result
                
                # Check if paused at human review interrupt
                snapshot = None
                try:
                    snapshot = rfp_workflow_app.get_state(config)
                except Exception:
                    pass
                is_interrupted = bool(snapshot and snapshot.next and "human_review" in snapshot.next)
                
                execution_state = result.get("execution_state")
                if not execution_state:
                    execution_state = WorkflowExecutionState.RUNNING.value if is_interrupted else WorkflowExecutionState.COMPLETED.value
                    
                overall_score = result.get("compliance_score_metrics", {}).get("overall_score")
                
                return {
                    "project_id": pid,
                    "execution_state": execution_state,
                    "status": result.get("workflow_status", "AWAITING_HUMAN_APPROVAL" if is_interrupted else execution_state),
                    "current_stage": "HUMAN_REVIEW" if is_interrupted else result.get("current_stage", "COMPLETED"),
                    "blocked_reason": result.get("blocked_reason"),
                    "retry_stage": result.get("retry_stage"),
                    "compliance_score": overall_score,
                    "is_interrupted": is_interrupted,
                    "total_requirements": len(result.get("requirements", [])),
                    "errors": result.get("errors", [])
                }
            except Exception as e:
                import traceback
                traceback.print_exc()
                init_state["execution_state"] = WorkflowExecutionState.FAILED.value
                init_state["workflow_status"] = "FAILED"
                init_state["errors"].append(str(e))
                _active_state_cache[pid] = init_state
                return {
                    "project_id": pid,
                    "execution_state": WorkflowExecutionState.FAILED.value,
                    "status": "FAILED",
                    "error": str(e)
                }

    @classmethod
    def retry_workflow(cls, project_id: str, stage: Optional[str] = None) -> Dict[str, Any]:
        """
        Retries a failed or blocked workflow stage once API quota resets or issue is resolved.
        Clears the blocked state and resumes from the failed node checkpoint without restarting the pipeline.
        """
        pid = str(project_id)
        config = {"configurable": {"thread_id": pid}}
        lock = cls._get_lock(pid)
        
        NODE_PRECEDING_MAP = {
            "DOCUMENT_INGESTION": None,
            "REQUIREMENT_ANALYSIS": "document_ingestion",
            "KNOWLEDGE_RETRIEVAL": "requirement_analysis",
            "COMPLIANCE_ANALYSIS": "knowledge_retrieval",
            "GAP_ANALYSIS": "compliance_analysis",
            "PROPOSAL_GENERATION": "gap_analysis",
            "PROPOSAL_VALIDATION": "proposal_generation",
            "HUMAN_REVIEW": "proposal_validation",
            "EXPORT": "human_review"
        }
        
        with lock:
            state = cls.get_workflow_state(pid)
            if not state:
                return {
                    "project_id": pid,
                    "execution_state": WorkflowExecutionState.FAILED.value,
                    "status": "FAILED",
                    "error": "No cached workflow state found to retry."
                }
                
            raw_stage = stage or state.get("retry_stage") or state.get("current_stage") or "COMPLIANCE_ANALYSIS"
            target_stage = str(raw_stage).strip().upper()
            preceding_node = NODE_PRECEDING_MAP.get(target_stage)
            
            # Clear error/blocked indicators
            updates = {
                "execution_state": WorkflowExecutionState.RUNNING.value,
                "blocked_reason": None,
                "errors": []
            }
            
            try:
                if preceding_node:
                    # Update state in checkpointer as preceding node, setting next to target_stage
                    rfp_workflow_app.update_state(config, updates, as_node=preceding_node)
                    result = rfp_workflow_app.invoke(None, config=config)
                else:
                    state.update(updates)
                    result = rfp_workflow_app.invoke(state, config=config)
                    
                _active_state_cache[pid] = result
                
                snapshot = None
                try:
                    snapshot = rfp_workflow_app.get_state(config)
                except Exception:
                    pass
                is_interrupted = bool(snapshot and snapshot.next and "human_review" in snapshot.next)
                execution_state = result.get("execution_state", WorkflowExecutionState.RUNNING.value if is_interrupted else WorkflowExecutionState.COMPLETED.value)
                overall_score = result.get("compliance_score_metrics", {}).get("overall_score")
                
                return {
                    "project_id": pid,
                    "execution_state": execution_state,
                    "status": result.get("workflow_status"),
                    "current_stage": "HUMAN_REVIEW" if is_interrupted else result.get("current_stage", "COMPLETED"),
                    "blocked_reason": result.get("blocked_reason"),
                    "retry_stage": result.get("retry_stage"),
                    "compliance_score": overall_score,
                    "is_interrupted": is_interrupted,
                    "total_requirements": len(result.get("requirements", [])),
                    "errors": result.get("errors", [])
                }
            except Exception as e:
                import traceback
                traceback.print_exc()
                state["execution_state"] = WorkflowExecutionState.FAILED.value
                state["errors"].append(str(e))
                _active_state_cache[pid] = state
                return {
                    "project_id": pid,
                    "execution_state": WorkflowExecutionState.FAILED.value,
                    "status": "FAILED",
                    "error": str(e)
                }
                
    @classmethod
    def get_workflow_state(cls, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves snapshot of the current state of a workflow thread."""
        pid = str(project_id)
        config = {"configurable": {"thread_id": pid}}
        
        # Check LangGraph checkpointer snapshot
        try:
            snapshot = rfp_workflow_app.get_state(config)
            if snapshot and snapshot.values:
                state_data = dict(snapshot.values)
                # Next node if interrupted
                state_data["next_node"] = list(snapshot.next) if snapshot.next else None
                return state_data
        except Exception:
            pass
            
        return _active_state_cache.get(pid)
        
    @classmethod
    def resume_human_review(
        cls,
        project_id: str,
        action: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resumes the workflow past the human review checkpoint.
        Action must be 'APPROVED', 'REVISE', or 'REJECTED'.
        """
        pid = str(project_id)
        config = {"configurable": {"thread_id": pid}}
        lock = cls._get_lock(pid)
        
        action_clean = action.strip().upper()
        if action_clean not in ["APPROVED", "REVISE", "REJECTED"]:
            action_clean = "REVISE" if "rev" in action_clean else "APPROVED"
            
        with lock:
            try:
                # Update state at checkpoint
                rfp_workflow_app.update_state(
                    config,
                    {
                        "human_review_status": action_clean,
                        "human_feedback": feedback,
                        "reviewed_at": datetime.now(timezone.utc).isoformat()
                    },
                    as_node="human_review"
                )
                
                # Resume execution past checkpoint
                result = rfp_workflow_app.invoke(None, config=config)
                _active_state_cache[pid] = result
                return {
                    "project_id": pid,
                    "status": result.get("workflow_status", "COMPLETED"),
                    "export_file_path": result.get("export_file_path"),
                    "export_file_name": result.get("export_file_name")
                }
            except Exception as e:
                return {
                    "project_id": pid,
                    "status": "FAILED",
                    "error": str(e)
                }


workflow_manager = WorkflowManager()
