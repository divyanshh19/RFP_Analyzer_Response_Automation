import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    ArrowLeft, Upload, GitBranch, ShieldCheck, FileSpreadsheet, 
    Download, BookOpen, ListChecks, Sparkles 
} from 'lucide-react';
import DocumentUpload from '../components/DocumentUpload';
import RequirementReview from '../components/RequirementReview';
import AgenticWorkflowTab from '../components/AgenticWorkflowTab';
import ComplianceDashboardTab from '../components/ComplianceDashboardTab';
import ProposalReviewTab from '../components/ProposalReviewTab';
import AICopilotWidget from '../components/AICopilotWidget';
import api from '../api/axios';

export default function ProjectDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('workflow');

    const handleExport = async () => {
        try {
            const res = await api.get(`/workflow/${id}/export/docx`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `RFP_Agentic_Proposal_${id.slice(0, 8)}.docx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) {
            // Fallback to legacy export if agentic export has not completed yet
            try {
                const res = await api.get(`/export/${id}/docx`, { responseType: 'blob' });
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `RFP_Response_${id.slice(0, 8)}.docx`);
                document.body.appendChild(link);
                link.click();
                link.remove();
            } catch (err) {
                alert('Export failed. Please run the Agentic Workflow or generate responses first.');
            }
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col relative font-sans text-slate-800">
            {/* Header */}
            <div className="bg-white border-b border-slate-200 px-8 py-4 shadow-xs">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button 
                            onClick={() => navigate('/')} 
                            className="p-2 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200 transition-colors text-slate-600"
                            title="Back to Workspaces"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <div className="flex items-center gap-2">
                                <h1 className="text-xl font-bold text-slate-900 tracking-tight">RFP Intelligence Workspace</h1>
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                                    <Sparkles className="w-3 h-3 text-indigo-600" /> LangGraph Agentic Engine
                                </span>
                            </div>
                            <p className="text-xs font-mono text-slate-400 mt-0.5">Workspace ID: {id}</p>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                        <button 
                            onClick={() => setActiveTab('upload')}
                            className="flex items-center px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                        >
                            <BookOpen className="w-4 h-4 mr-1.5 text-slate-500" />
                            Knowledge Base & Docs
                        </button>
                        <button 
                            onClick={handleExport}
                            className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition shadow-sm"
                        >
                            <Download className="w-4 h-4 mr-1.5" />
                            Quick Export DOCX
                        </button>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-xs">
                <div className="max-w-7xl mx-auto px-8 flex gap-2 overflow-x-auto">
                    <button 
                        onClick={() => setActiveTab('workflow')} 
                        className={`py-3.5 px-4 border-b-2 font-semibold text-xs tracking-wide flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'workflow' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/40' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}
                    >
                        <GitBranch className="w-4 h-4" /> 1. Agentic Workflow
                    </button>
                    <button 
                        onClick={() => setActiveTab('upload')} 
                        className={`py-3.5 px-4 border-b-2 font-semibold text-xs tracking-wide flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'upload' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/40' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}
                    >
                        <Upload className="w-4 h-4" /> 2. Upload & Ingest
                    </button>
                    <button 
                        onClick={() => setActiveTab('compliance')} 
                        className={`py-3.5 px-4 border-b-2 font-semibold text-xs tracking-wide flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'compliance' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/40' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}
                    >
                        <ShieldCheck className="w-4 h-4" /> 3. Compliance Matrix
                    </button>
                    <button 
                        onClick={() => setActiveTab('proposal')} 
                        className={`py-3.5 px-4 border-b-2 font-semibold text-xs tracking-wide flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'proposal' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/40' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}
                    >
                        <FileSpreadsheet className="w-4 h-4" /> 4. Proposal Sections
                    </button>
                    <button 
                        onClick={() => setActiveTab('requirements')} 
                        className={`py-3.5 px-4 border-b-2 font-semibold text-xs tracking-wide flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'requirements' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/40' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}
                    >
                        <ListChecks className="w-4 h-4" /> 5. Requirement QA
                    </button>
                    <button 
                        onClick={() => setActiveTab('export')} 
                        className={`py-3.5 px-4 border-b-2 font-semibold text-xs tracking-wide flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'export' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/40' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}
                    >
                        <Download className="w-4 h-4" /> 6. Export Package
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 max-w-7xl mx-auto w-full p-8 pb-32">
                {activeTab === 'workflow' && (
                    <AgenticWorkflowTab 
                        projectId={id} 
                        onRefreshNeeded={() => {}} 
                    />
                )}
                {activeTab === 'upload' && (
                    <DocumentUpload 
                        projectId={id} 
                        onComplete={() => setActiveTab('workflow')} 
                    />
                )}
                {activeTab === 'compliance' && (
                    <ComplianceDashboardTab 
                        projectId={id} 
                    />
                )}
                {activeTab === 'proposal' && (
                    <ProposalReviewTab 
                        projectId={id} 
                    />
                )}
                {activeTab === 'requirements' && (
                    <RequirementReview 
                        projectId={id} 
                    />
                )}
                {activeTab === 'export' && (
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-16 text-center flex flex-col items-center max-w-2xl mx-auto mt-6">
                        <div className="p-4 bg-emerald-50 text-emerald-600 rounded-2xl mb-5 border border-emerald-100">
                            <Download className="w-10 h-10" />
                        </div>
                        <h2 className="text-2xl font-bold mb-2 text-slate-900 tracking-tight">Export Proposal Package</h2>
                        <p className="text-slate-500 mb-8 max-w-md text-sm leading-relaxed">
                            Generate and download the compiled, branded Microsoft Word (.docx) document including executive summary, technical approach, compliance matrix, and team qualifications.
                        </p>
                        <button 
                            onClick={handleExport} 
                            className="px-8 py-3.5 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 transition shadow-md hover:shadow-lg flex items-center gap-2 text-sm"
                        >
                            <Download className="w-4 h-4" /> Download DOCX Package
                        </button>
                    </div>
                )}
            </div>

            {/* AI Copilot Persistent Drawer */}
            <AICopilotWidget projectId={id} />
        </div>
    );
}
