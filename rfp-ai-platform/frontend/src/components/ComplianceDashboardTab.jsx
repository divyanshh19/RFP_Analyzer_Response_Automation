import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { 
    ShieldCheck, AlertTriangle, XCircle, HelpCircle, CheckCircle2, 
    Search, Filter, ExternalLink, Loader2, RefreshCw, Clock 
} from 'lucide-react';
import EvidenceInspectorModal from './EvidenceInspectorModal';

export default function ComplianceDashboardTab({ projectId }) {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedItem, setSelectedItem] = useState(null);
    const [retrying, setRetrying] = useState(false);

    useEffect(() => {
        fetchCompliance();
    }, [projectId]);

    const fetchCompliance = async () => {
        try {
            setLoading(true);
            const res = await api.get(`/workflow/${projectId}/compliance`);
            setReport(res.data);
        } catch (e) {
            setReport(null);
        } finally {
            setLoading(false);
        }
    };

    const handleRetry = async () => {
        try {
            setRetrying(true);
            await api.post(`/workflow/${projectId}/retry`);
            await fetchCompliance();
        } catch (e) {
            alert('Retry attempt failed: ' + (e.response?.data?.detail || e.message));
        } finally {
            setRetrying(false);
        }
    };

    if (loading) {
        return (
            <div className="bg-white rounded-2xl p-16 text-center border border-slate-200">
                <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
                <p className="text-sm text-slate-500 font-medium">Loading compliance intelligence...</p>
            </div>
        );
    }

    const metrics = report?.metrics || {};
    const rawMatrix = report?.compliance_matrix || [];
    // Strictly isolate actual RFP requirements. Filter out any synthetic error records.
    const matrix = rawMatrix.filter(item => 
        item && !String(item.requirement_id || '').startsWith('ERR-') && !String(item.requirement_id || '').toLowerCase().includes('error')
    );
    const isBlocked = report?.execution_state === 'Blocked' || Boolean(report?.blocked_reason && report.blocked_reason.includes('429'));
    const isFailed = report?.execution_state === 'Failed';

    const filteredItems = matrix.filter(item => {
        const matchesStatus = filterStatus === 'ALL' || item.status === filterStatus;
        const matchesQuery = !searchQuery || 
            item.requirement_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (item.category && item.category.toLowerCase().includes(searchQuery.toLowerCase()));
        return matchesStatus && matchesQuery;
    });

    const getStatusBadge = (status) => {
        const s = (status || '').toLowerCase();
        if (s.includes('partially')) {
            return (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                    <AlertTriangle className="w-3 h-3 mr-1" /> Partially Compliant
                </span>
            );
        } else if (s.includes('non') || s.includes('not')) {
            return (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    <XCircle className="w-3 h-3 mr-1" /> Non-Compliant
                </span>
            );
        } else if (s.includes('clarif')) {
            return (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                    <HelpCircle className="w-3 h-3 mr-1" /> Needs Clarification
                </span>
            );
        }
        return (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Compliant
            </span>
        );
    };

    // Calculate display score (N/A if unassessed or blocked)
    const overallScoreDisplay = (metrics.overall_score !== null && metrics.overall_score !== undefined) 
        ? `${metrics.overall_score}%` 
        : 'N/A';

    const mandatoryScoreDisplay = (metrics.mandatory_compliance_score !== null && metrics.mandatory_compliance_score !== undefined) 
        ? `${metrics.mandatory_compliance_score}%` 
        : 'N/A';

    return (
        <div className="space-y-6">
            {/* Top Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {/* Overall Score */}
                <div className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-2xl p-5 shadow-lg flex flex-col justify-between col-span-1 md:col-span-2 lg:col-span-1">
                    <div>
                        <span className="text-xs font-medium text-indigo-300 uppercase tracking-wider">Overall Score</span>
                        <div className="text-4xl font-extrabold mt-2 tracking-tight text-white">
                            {overallScoreDisplay}
                        </div>
                    </div>
                    <div className="text-[11px] text-indigo-200/80 mt-4 pt-3 border-t border-indigo-800/60">
                        Mandatory Score: <strong className="text-white">{mandatoryScoreDisplay}</strong>
                    </div>
                </div>

                {/* Compliant */}
                <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Compliant</span>
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div className="text-3xl font-bold text-slate-800 mt-2">
                        {metrics.compliant_count || 0}
                    </div>
                    <span className="text-[11px] text-emerald-600 font-semibold mt-2">Supported by direct evidence</span>
                </div>

                {/* Partially Compliant */}
                <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Partial</span>
                        <AlertTriangle className="w-5 h-5 text-amber-500" />
                    </div>
                    <div className="text-3xl font-bold text-slate-800 mt-2">
                        {metrics.partially_compliant_count || 0}
                    </div>
                    <span className="text-[11px] text-amber-600 font-semibold mt-2">Partial evidence found</span>
                </div>

                {/* Non-Compliant */}
                <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Non-Compliant</span>
                        <XCircle className="w-5 h-5 text-rose-500" />
                    </div>
                    <div className="text-3xl font-bold text-slate-800 mt-2">
                        {metrics.non_compliant_count || 0}
                    </div>
                    <span className="text-[11px] text-rose-600 font-semibold mt-2">Missing critical evidence</span>
                </div>

                {/* Clarification Required */}
                <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Clarification</span>
                        <HelpCircle className="w-5 h-5 text-purple-500" />
                    </div>
                    <div className="text-3xl font-bold text-slate-800 mt-2">
                        {metrics.clarification_count || 0}
                    </div>
                    <span className="text-[11px] text-purple-600 font-semibold mt-2">Requires buyer inquiry</span>
                </div>
            </div>

            {/* Error / Quota Blocked Panel */}
            {(isBlocked || isFailed || report?.blocked_reason) && (
                <div className={`p-5 rounded-2xl border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    isBlocked ? 'bg-amber-50 border-amber-200' : 'bg-rose-50 border-rose-200'
                }`}>
                    <div className="flex items-start gap-3.5">
                        <div className={`p-2.5 rounded-xl mt-0.5 ${
                            isBlocked ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700'
                        }`}>
                            {isBlocked ? <Clock className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h4 className="text-sm font-bold text-slate-900">
                                    {isBlocked 
                                        ? 'Intelligence Engine Blocked: Google Gemini API Quota Exhausted' 
                                        : 'Assessment Pipeline Halted on Infrastructure Error'}
                                </h4>
                                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                                    isBlocked ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-rose-100 text-rose-800 border-rose-300'
                                }`}>
                                    State: {report?.execution_state || 'Blocked'}
                                </span>
                            </div>
                            <p className="text-xs text-slate-700 mt-1 max-w-2xl leading-relaxed">
                                {report?.blocked_reason || 'An external API limitation interrupted the analysis pipeline.'}
                            </p>
                            <p className="text-[11px] text-slate-500 mt-1.5 italic">
                                *Integrity Guarantee: Infrastructure exceptions, rate limits, and LLM quota errors are strictly isolated and never converted into RFP requirements or counted toward compliance scores.*
                            </p>
                        </div>
                    </div>

                    <button
                        onClick={handleRetry}
                        disabled={retrying}
                        className={`px-5 py-2.5 rounded-xl text-xs font-bold transition shadow-sm flex items-center gap-2 whitespace-nowrap self-start md:self-auto disabled:opacity-50 text-white ${
                            isBlocked ? 'bg-amber-600 hover:bg-amber-700' : 'bg-rose-600 hover:bg-rose-700'
                        }`}
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${retrying ? 'animate-spin' : ''}`} />
                        {retrying ? 'Retrying Stage...' : 'Retry Assessment Now'}
                    </button>
                </div>
            )}

            {/* Filter and Search Bar */}
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="relative w-full md:w-96">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                        type="text"
                        placeholder="Search requirement text, ID, or category..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                    />
                </div>

                <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                    <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
                    {['ALL', 'Compliant', 'Partially compliant', 'Non-compliant', 'Requires clarification'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setFilterStatus(status)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                                filterStatus === status
                                    ? 'bg-slate-900 text-white shadow-sm'
                                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                        >
                            {status === 'ALL' ? 'All Requirements' : status}
                        </button>
                    ))}
                </div>
            </div>

            {/* Compliance Matrix Table */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-100">
                        <tr>
                            <th className="p-4 text-[11px] font-bold text-slate-400 uppercase tracking-wider">Req ID</th>
                            <th className="p-4 text-[11px] font-bold text-slate-400 uppercase tracking-wider w-2/5">Requirement Description</th>
                            <th className="p-4 text-[11px] font-bold text-slate-400 uppercase tracking-wider">Category</th>
                            <th className="p-4 text-[11px] font-bold text-slate-400 uppercase tracking-wider">Compliance Status</th>
                            <th className="p-4 text-[11px] font-bold text-slate-400 uppercase tracking-wider">Score</th>
                            <th className="p-4 text-[11px] font-bold text-slate-400 uppercase tracking-wider text-right">Evidence Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-xs">
                        {filteredItems.map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                                <td className="p-4 font-mono font-bold text-slate-800 align-top whitespace-nowrap">
                                    {item.requirement_id}
                                </td>
                                <td className="p-4 text-slate-700 align-top leading-relaxed">
                                    <div className="font-medium text-slate-900 mb-1">{item.description}</div>
                                    <div className="text-[11px] text-slate-500 italic line-clamp-2">
                                        Rationale: {item.rationale}
                                    </div>
                                </td>
                                <td className="p-4 align-top whitespace-nowrap">
                                    <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-medium text-[11px]">
                                        {item.category || 'General'}
                                    </span>
                                </td>
                                <td className="p-4 align-top whitespace-nowrap">
                                    {getStatusBadge(item.status)}
                                </td>
                                <td className="p-4 align-top font-bold text-slate-700">
                                    {Math.round((item.compliance_score || 0) * 100)}%
                                </td>
                                <td className="p-4 align-top text-right whitespace-nowrap">
                                    <button
                                        onClick={() => setSelectedItem(item)}
                                        className="inline-flex items-center px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-700 font-semibold hover:bg-indigo-100 transition"
                                    >
                                        <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                                        Inspect Evidence
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {filteredItems.length === 0 && (
                            <tr>
                                <td colSpan="6" className="p-12 text-center text-slate-400">
                                    {matrix.length === 0 
                                        ? 'No genuine requirements currently available in the compliance matrix.' 
                                        : 'No requirements match the selected filter.'}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Evidence Modal */}
            <EvidenceInspectorModal
                item={selectedItem}
                onClose={() => setSelectedItem(null)}
            />
        </div>
    );
}
