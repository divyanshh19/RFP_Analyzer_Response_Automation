import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { 
    Play, CheckCircle2, Clock, AlertCircle, RefreshCw, 
    FileText, Search, ShieldAlert, Cpu, Sparkles, CheckCheck, 
    Download, ArrowRight, CornerDownRight, MessageSquare 
} from 'lucide-react';

const WORKFLOW_STAGES = [
    { id: 'DOCUMENT_INGESTION', label: '1. Document Ingestion', icon: FileText, desc: 'Digital & OCR text extraction' },
    { id: 'REQUIREMENT_ANALYSIS', label: '2. Requirement Analysis', icon: Search, desc: 'Criteria, deadlines & deliverables' },
    { id: 'KNOWLEDGE_RETRIEVAL', label: '3. Knowledge Retrieval', icon: Cpu, desc: 'Vector search across company documents' },
    { id: 'COMPLIANCE_ANALYSIS', label: '4. Compliance Analysis', icon: ShieldAlert, desc: 'Evidence-based matrix & score' },
    { id: 'GAP_ANALYSIS', label: '5. Gap Analysis', icon: RefreshCw, desc: 'Iterative re-retrieval & missing items' },
    { id: 'PROPOSAL_GENERATION', label: '6. Proposal Generation', icon: Sparkles, desc: 'Grounded narrative section drafting' },
    { id: 'PROPOSAL_VALIDATION', label: '7. Proposal Validation', icon: CheckCircle2, desc: 'Automated claim & coverage audit' },
    { id: 'HUMAN_REVIEW', label: '8. Human Review', icon: CheckCheck, desc: 'Human-in-the-loop interrupt checkpoint' },
    { id: 'EXPORT', label: '9. Final Export', icon: Download, desc: 'Branded Microsoft Word DOCX compilation' }
];

export default function AgenticWorkflowTab({ projectId, onRefreshNeeded }) {
    const [statusData, setStatusData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [executing, setExecuting] = useState(false);
    const [reviewAction, setReviewAction] = useState('APPROVED');
    const [reviewFeedback, setReviewFeedback] = useState('');
    const [submittingReview, setSubmittingReview] = useState(false);

    useEffect(() => {
        pollStatus();
    }, [projectId]);

    const pollStatus = async () => {
        try {
            setLoading(true);
            const res = await api.get(`/workflow/${projectId}/status`);
            setStatusData(res.data);
        } catch (e) {
            setStatusData(null);
        } finally {
            setLoading(false);
        }
    };

    const handleStartWorkflow = async () => {
        setExecuting(true);
        try {
            await api.post(`/workflow/${projectId}/start`, {});
            await pollStatus();
            if (onRefreshNeeded) onRefreshNeeded();
        } catch (e) {
            alert('Failed to start workflow: ' + (e.response?.data?.detail || e.message));
        } finally {
            setExecuting(false);
        }
    };

    const handleResumeReview = async () => {
        setSubmittingReview(true);
        try {
            await api.post(`/workflow/${projectId}/review`, {
                action: reviewAction,
                feedback: reviewFeedback
            });
            await pollStatus();
            if (onRefreshNeeded) onRefreshNeeded();
        } catch (e) {
            alert('Failed to submit human review decision: ' + (e.response?.data?.detail || e.message));
        } finally {
            setSubmittingReview(false);
        }
    };

    const handleDownloadExport = async () => {
        try {
            const res = await api.get(`/export/${projectId}/docx`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', statusData?.export_file_name || 'RFP_Final_Proposal.docx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) {
            alert('Export download failed. Ensure proposal has been approved and compiled.');
        }
    };

    const stageHistory = statusData?.stage_history || [];
    const currentStatus = statusData?.workflow_status || 'NOT_STARTED';
    const executionState = statusData?.execution_state || (currentStatus === 'NOT_STARTED' ? 'Pending' : 'Running');
    const isBlocked = executionState === 'Blocked' || Boolean(statusData?.blocked_reason && statusData.blocked_reason.includes('429'));
    const isFailed = executionState === 'Failed';

    const handleRetryWorkflow = async () => {
        setExecuting(true);
        try {
            await api.post(`/workflow/${projectId}/retry`);
            await pollStatus();
            if (onRefreshNeeded) onRefreshNeeded();
        } catch (e) {
            alert('Retry failed: ' + (e.response?.data?.detail || e.message));
        } finally {
            setExecuting(false);
        }
    };

    const getStageState = (stageId) => {
        // Find in history
        const match = stageHistory.slice().reverse().find(s => s.stage && s.stage.startsWith(stageId));
        if (match) {
            return {
                status: match.status,
                summary: match.summary,
                started_at: match.started_at,
                completed_at: match.completed_at
            };
        }
        if (currentStatus === 'AWAITING_HUMAN_APPROVAL' && stageId === 'HUMAN_REVIEW') {
            return { status: 'WAITING_INPUT', summary: 'Workflow paused at human approval checkpoint.' };
        }
        return { status: 'PENDING', summary: 'Awaiting execution' };
    };

    return (
        <div className="space-y-8">
            {/* Action Header Banner */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase bg-indigo-50 text-indigo-700 border border-indigo-200">
                            LangGraph Multi-Agent Orchestrator
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase ${
                            executionState === 'Completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                            executionState === 'Blocked' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                            executionState === 'Failed' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                            executionState === 'Running' ? 'bg-blue-50 text-blue-700 border border-blue-200 animate-pulse' :
                            'bg-slate-100 text-slate-700'
                        }`}>
                            Execution State: {executionState}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400">
                            Stage: {statusData?.current_stage || currentStatus}
                        </span>
                    </div>
                    <h2 className="text-xl font-bold text-slate-900">Autonomous 9-Stage RFP Pipeline</h2>
                    <p className="text-xs text-slate-500 mt-1 max-w-xl">
                        Orchestrates specialized MCP tools through LangGraph with iterative gap remediation, claim validation, and human review checkpoints.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={pollStatus}
                        disabled={loading || executing}
                        className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition flex items-center"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
                        Refresh State
                    </button>

                    <button
                        onClick={handleStartWorkflow}
                        disabled={executing || currentStatus === 'AWAITING_HUMAN_APPROVAL'}
                        className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 shadow-md transition disabled:opacity-50 flex items-center"
                    >
                        {executing ? (
                            <>
                                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                Agents Executing...
                            </>
                        ) : (
                            <>
                                <Play className="w-4 h-4 mr-2" />
                                {currentStatus === 'NOT_STARTED' ? 'Launch Full Agentic Workflow' : 'Re-Run Pipeline'}
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Error / Quota Blocked Panel */}
            {(isBlocked || isFailed || statusData?.blocked_reason) && (
                <div className={`p-5 rounded-2xl border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    isBlocked ? 'bg-amber-50 border-amber-200' : 'bg-rose-50 border-rose-200'
                }`}>
                    <div className="flex items-start gap-3.5">
                        <div className={`p-2.5 rounded-xl mt-0.5 ${
                            isBlocked ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700'
                        }`}>
                            <AlertCircle className="w-5 h-5" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h4 className="text-sm font-bold text-slate-900">
                                    {isBlocked 
                                        ? 'Workflow Paused: Google Gemini API Quota Exhausted' 
                                        : 'Agent Pipeline Execution Halted'}
                                </h4>
                                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                                    isBlocked ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-rose-100 text-rose-800 border-rose-300'
                                }`}>
                                    State: {executionState}
                                </span>
                            </div>
                            <p className="text-xs text-slate-700 mt-1 max-w-2xl leading-relaxed">
                                {statusData?.blocked_reason || 'An external dependency error interrupted agent execution.'}
                            </p>
                            <p className="text-[11px] text-slate-500 mt-1.5 italic">
                                *Anti-Hallucination Guarantee: Infrastructure exceptions and quota limits are strictly halted and never converted into compliance requirements or scores.*
                            </p>
                        </div>
                    </div>

                    <button
                        onClick={handleRetryWorkflow}
                        disabled={executing}
                        className={`px-5 py-2.5 rounded-xl text-xs font-bold transition shadow-sm flex items-center gap-2 whitespace-nowrap self-start md:self-auto disabled:opacity-50 text-white ${
                            isBlocked ? 'bg-amber-600 hover:bg-amber-700' : 'bg-rose-600 hover:bg-rose-700'
                        }`}
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${executing ? 'animate-spin' : ''}`} />
                        {executing ? 'Retrying Stage...' : 'Retry Workflow Stage'}
                    </button>
                </div>
            )}

            {/* Human-in-the-Loop Interrupt Checkpoint Box (Only active when paused) */}
            {currentStatus === 'AWAITING_HUMAN_APPROVAL' && (
                <div className="bg-amber-50/70 rounded-2xl border-2 border-amber-300 p-6 shadow-md animate-in fade-in duration-200">
                    <div className="flex items-center gap-2 text-amber-900 font-bold text-base mb-1">
                        <AlertCircle className="w-5 h-5 text-amber-600" />
                        Human Review Checkpoint — Action Required
                    </div>
                    <p className="text-xs text-amber-800 mb-4 max-w-2xl leading-relaxed">
                        The LangGraph workflow has completed Proposal Generation and automated QA Validation. Execution is currently paused awaiting your explicit human sign-off before compiling the final client document.
                    </p>

                    <div className="bg-white p-4 rounded-xl border border-amber-200 space-y-4 max-w-2xl">
                        <div>
                            <label className="text-xs font-bold text-slate-700 block mb-2">Review Decision</label>
                            <div className="flex gap-3">
                                <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="review_action"
                                        value="APPROVED"
                                        checked={reviewAction === 'APPROVED'}
                                        onChange={(e) => setReviewAction(e.target.value)}
                                        className="text-indigo-600"
                                    />
                                    Approve & Proceed to Final Word Export
                                </label>
                                <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="review_action"
                                        value="REVISE"
                                        checked={reviewAction === 'REVISE'}
                                        onChange={(e) => setReviewAction(e.target.value)}
                                        className="text-indigo-600"
                                    />
                                    Request AI Revision
                                </label>
                            </div>
                        </div>

                        {reviewAction === 'REVISE' && (
                            <div>
                                <label className="text-xs font-bold text-slate-700 block mb-1">
                                    Revision Instructions for AI Generator
                                </label>
                                <textarea
                                    rows="3"
                                    placeholder="e.g. Please expand the SLA response regarding our disaster recovery timeline and emphasize our SOC 2 compliance..."
                                    value={reviewFeedback}
                                    onChange={(e) => setReviewFeedback(e.target.value)}
                                    className="w-full text-xs p-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                                />
                            </div>
                        )}

                        <div className="flex justify-end gap-3 pt-2">
                            <button
                                onClick={handleResumeReview}
                                disabled={submittingReview}
                                className="px-6 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition shadow-sm disabled:opacity-50 flex items-center"
                            >
                                {submittingReview ? (
                                    <>
                                        <RefreshCw className="w-3.5 h-3.5 mr-2 animate-spin" />
                                        Resuming Workflow...
                                    </>
                                ) : (
                                    <>
                                        Resume Workflow past Checkpoint
                                        <ArrowRight className="w-3.5 h-3.5 ml-2" />
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Completed Export Banner */}
            {currentStatus === 'COMPLETED' && (
                <div className="bg-emerald-50/70 rounded-2xl border border-emerald-200 p-6 shadow-sm flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2 text-emerald-800 font-bold text-base mb-1">
                            <CheckCheck className="w-5 h-5 text-emerald-600" />
                            Proposal Package Ready
                        </div>
                        <p className="text-xs text-emerald-700">
                            Word DOCX document compiled successfully with full compliance matrix and evidence citations.
                        </p>
                    </div>

                    <button
                        onClick={handleDownloadExport}
                        className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition shadow-md flex items-center"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Download DOCX Package
                    </button>
                </div>
            )}

            {/* 9-Stage Stepper Cards */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-6">
                    Agent Execution Lifecycle
                </h3>

                <div className="space-y-4">
                    {WORKFLOW_STAGES.map((stage, idx) => {
                        const Icon = stage.icon;
                        const stateInfo = getStageState(stage.id);

                        const isDone = stateInfo.status === 'COMPLETED';
                        const isWaiting = stateInfo.status === 'WAITING_INPUT';
                        const isFailed = stateInfo.status === 'FAILED';

                        return (
                            <div
                                key={stage.id}
                                className={`p-4 rounded-xl border transition flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                                    isDone ? 'bg-slate-50/50 border-slate-200' :
                                    isWaiting ? 'bg-amber-50/50 border-amber-300' :
                                    isFailed ? 'bg-rose-50/50 border-rose-200' :
                                    'bg-white border-slate-100 opacity-70'
                                }`}
                            >
                                <div className="flex items-start gap-4">
                                    <div className={`p-2.5 rounded-xl ${
                                        isDone ? 'bg-emerald-100 text-emerald-700' :
                                        isWaiting ? 'bg-amber-100 text-amber-700 animate-pulse' :
                                        isFailed ? 'bg-rose-100 text-rose-700' :
                                        'bg-slate-100 text-slate-400'
                                    }`}>
                                        <Icon className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h4 className="text-sm font-bold text-slate-900">{stage.label}</h4>
                                            {isDone && (
                                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                                                    Done
                                                </span>
                                            )}
                                            {isWaiting && (
                                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                                                    Checkpoint
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-xs text-slate-500 mt-0.5">{stage.desc}</p>
                                        {stateInfo.summary && (
                                            <p className="text-xs text-indigo-900 font-medium mt-2 bg-indigo-50/70 p-2 rounded-lg border border-indigo-100/70">
                                                {stateInfo.summary}
                                            </p>
                                        )}
                                    </div>
                                </div>

                                <div className="text-right text-xs text-slate-400 font-mono shrink-0">
                                    {stateInfo.completed_at ? (
                                        <span>{new Date(stateInfo.completed_at).toLocaleTimeString()}</span>
                                    ) : stateInfo.status}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
