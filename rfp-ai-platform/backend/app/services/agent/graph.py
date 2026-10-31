"""
LangGraph StateGraph Workflow Orchestrator for the 9-Agent RFP Automation Lifecycle.
Features state checkpointing, tool-calling loops, cyclical self-correction, and human approval interrupts.
"""

from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.agent.state import RFPWorkflowState, make_initial_state
from app.services.agent.routing import (
    should_proceed_after_ingestion,
    should_proceed_after_requirements,
    should_proceed_after_compliance,
    should_retry_retrieval,
    should_revise_proposal,
    should_export_or_terminate
)
from app.services.agent.nodes.ingestion_node import document_ingestion_node
from app.services.agent.nodes.requirements_node import requirement_analysis_node
from app.services.agent.nodes.retrieval_node import knowledge_retrieval_node
from app.services.agent.nodes.compliance_node import compliance_analysis_node
from app.services.agent.nodes.gap_analysis_node import gap_analysis_node
from app.services.agent.nodes.proposal_node import proposal_generation_node
from app.services.agent.nodes.validation_node import proposal_validation_node
from app.services.agent.nodes.human_review_node import human_review_node
from app.services.agent.nodes.export_node import export_node


def build_rfp_workflow():
    """Builds and compiles the 9-agent LangGraph workflow."""
    workflow = StateGraph(RFPWorkflowState)

    # 1. Register Nodes
    workflow.add_node("document_ingestion", document_ingestion_node)
    workflow.add_node("requirement_analysis", requirement_analysis_node)
    workflow.add_node("knowledge_retrieval", knowledge_retrieval_node)
    workflow.add_node("compliance_analysis", compliance_analysis_node)
    workflow.add_node("gap_analysis", gap_analysis_node)
    workflow.add_node("proposal_generation", proposal_generation_node)
    workflow.add_node("proposal_validation", proposal_validation_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("export", export_node)

    # 2. Sequential & Guarded Conditional Edges
    workflow.add_edge(START, "document_ingestion")
    
    # Conditional Edge: Ingestion -> Requirements OR Halt (on ingestion failure)
    workflow.add_conditional_edges(
        "document_ingestion",
        should_proceed_after_ingestion,
        {
            "proceed_to_requirements": "requirement_analysis",
            "halt": END
        }
    )
    
    # Conditional Edge: Requirements -> Retrieval OR Halt (on extraction failure / quota block)
    workflow.add_conditional_edges(
        "requirement_analysis",
        should_proceed_after_requirements,
        {
            "proceed_to_retrieval": "knowledge_retrieval",
            "halt": END
        }
    )
    
    workflow.add_edge("knowledge_retrieval", "compliance_analysis")
    
    # Conditional Edge: Compliance -> Gap Analysis OR Halt (on assessment failure / quota block)
    workflow.add_conditional_edges(
        "compliance_analysis",
        should_proceed_after_compliance,
        {
            "proceed_to_gaps": "gap_analysis",
            "halt": END
        }
    )

    # 3. Conditional Edge: Gap Analysis -> Re-retrieval Loop OR Proposal Generation
    workflow.add_conditional_edges(
        "gap_analysis",
        should_retry_retrieval,
        {
            "retry_retrieval": "knowledge_retrieval",
            "proceed_to_proposal": "proposal_generation"
        }
    )

    # 4. Sequential Edge: Proposal Generation -> Validation
    workflow.add_edge("proposal_generation", "proposal_validation")

    # 5. Conditional Edge: Validation -> Revision Loop OR Human Review
    workflow.add_conditional_edges(
        "proposal_validation",
        should_revise_proposal,
        {
            "revise_proposal": "proposal_generation",
            "request_human_review": "human_review"
        }
    )

    # 6. Conditional Edge: Human Review Checkpoint -> Export, Revise, or End
    workflow.add_conditional_edges(
        "human_review",
        should_export_or_terminate,
        {
            "proceed_to_export": "export",
            "revise_proposal": "proposal_generation",
            "terminate": END
        }
    )

    workflow.add_edge("export", END)

    # Compile with memory checkpointer and interrupt before human review
    checkpointer = MemorySaver()
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"]
    )
    return app


# Singleton compiled graph instance
rfp_workflow_app = build_rfp_workflow()
