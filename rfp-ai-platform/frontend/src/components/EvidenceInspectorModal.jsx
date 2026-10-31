import React from 'react';
import { X, CheckCircle2, AlertTriangle, XCircle, HelpCircle, FileText, Bookmark } from 'lucide-react';

export default function EvidenceInspectorModal({ item, onClose }) {
    if (!item) return null;

    const getStatusBadge = (status) => {
        const s = (status || '').toLowerCase();
        if (s.includes('partially')) {
            return (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                    <AlertTriangle className="w-3.5 h-3.5 mr-1.5" /> Partially Compliant
                </span>
            );
        } else if (s.includes('non') || s.includes('not')) {
            return (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    <XCircle className="w-3.5 h-3.5 mr-1.5" /> Non-Compliant
                </span>
            );
        } else if (s.includes('clarif')) {
            return (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                    <HelpCircle className="w-3.5 h-3.5 mr-1.5" /> Needs Clarification
                </span>
            );
        }
        return (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> Fully Compliant
            </span>
        );
    };

    const evidenceList = item.evidence_citations || [];

    return (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
                
                {/* Header */}
                <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
                    <div className="flex items-center gap-3">
                        <div className="px-2.5 py-1 bg-slate-800 text-white font-mono text-xs font-bold rounded-md">
                            {item.requirement_id}
                        </div>
                        <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-700">
                            {item.category || 'General'}
                        </span>
                        {item.mandatory && (
                            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 border border-rose-200">
                                Mandatory
                            </span>
                        )}
                    </div>
                    <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 overflow-y-auto space-y-6">
                    {/* Requirement Description */}
                    <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Requirement Statement</h4>
                        <p className="text-base text-slate-800 font-medium leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
                            {item.description}
                        </p>
                    </div>

                    {/* Status & Compliance Determination */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Compliance Status</h4>
                            <div className="flex items-center gap-3">
                                {getStatusBadge(item.status)}
                                <span className="text-sm font-semibold text-slate-700">
                                    Score: {Math.round((item.compliance_score || 0) * 100)}%
                                </span>
                            </div>
                        </div>

                        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Audit Rationale</h4>
                            <p className="text-xs text-slate-600 leading-relaxed">
                                {item.rationale || 'Evaluated strictly against verified knowledge base documents.'}
                            </p>
                        </div>
                    </div>

                    {/* Missing Information / Gap Alert */}
                    {item.missing_information && (
                        <div className="p-4 bg-amber-50/70 rounded-xl border border-amber-200">
                            <div className="flex items-center gap-2 text-amber-800 text-xs font-bold uppercase tracking-wider mb-1">
                                <AlertTriangle className="w-4 h-4 text-amber-600" />
                                Missing Information / Gap Identified
                            </div>
                            <p className="text-xs text-amber-900 leading-relaxed font-medium">
                                {item.missing_information}
                            </p>
                        </div>
                    )}

                    {/* Verified Evidence Chunks */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                                Supporting Evidence Citations ({evidenceList.length})
                            </h4>
                            <span className="text-xs text-slate-400">Zero Hallucination Grounding</span>
                        </div>

                        {evidenceList.length > 0 ? (
                            <div className="space-y-3">
                                {evidenceList.map((chunk, idx) => (
                                    <div key={idx} className="p-4 bg-slate-50/60 rounded-xl border border-slate-200 text-xs space-y-2">
                                        <div className="flex items-center justify-between text-slate-500 font-mono text-[11px]">
                                            <span className="flex items-center gap-1.5 font-semibold text-indigo-700">
                                                <FileText className="w-3.5 h-3.5" />
                                                {chunk.document_type || 'KNOWLEDGE_BASE'} (Page {chunk.page_number || '1'})
                                            </span>
                                            {chunk.similarity_score && (
                                                <span className="px-2 py-0.5 rounded bg-slate-200/80 text-slate-700">
                                                    Similarity: {Math.round(chunk.similarity_score * 100)}%
                                                </span>
                                            )}
                                        </div>
                                        {chunk.section_name && chunk.section_name !== 'N/A' && (
                                            <div className="text-slate-600 font-medium flex items-center gap-1">
                                                <Bookmark className="w-3 h-3 text-slate-400" /> Section: {chunk.section_name}
                                            </div>
                                        )}
                                        <p className="text-slate-700 leading-relaxed italic bg-white p-3 rounded-lg border border-slate-200/70">
                                            "{chunk.text}"
                                        </p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                                No evidence chunks were found in the uploaded knowledge base for this requirement.
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex justify-end">
                    <button onClick={onClose} className="px-5 py-2 bg-slate-800 text-white rounded-xl text-xs font-semibold hover:bg-slate-900 transition">
                        Close Inspector
                    </button>
                </div>
            </div>
        </div>
    );
}
