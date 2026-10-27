import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { Play, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

export default function RequirementReview({ projectId }) {
    const [requirements, setRequirements] = useState([]);
    const [loadingId, setLoadingId] = useState(null);
    const [responses, setResponses] = useState({});

    useEffect(() => { fetchRequirements(); }, [projectId]);

    const fetchRequirements = async () => {
        const res = await api.get(`/rfp/${projectId}/requirements`);
        setRequirements(res.data);
    };

    const generateResponse = async (reqId) => {
        setLoadingId(reqId);
        try {
            const res = await api.post(`/generation/${reqId}/draft`);
            setResponses(prev => ({...prev, [reqId]: res.data.response_text}));
            fetchRequirements(); // refresh statuses (e.g. NEEDS_INFORMATION)
        } catch (e) {
            alert('Failed to generate response: ' + (e.response?.data?.detail || e.message));
        }
        setLoadingId(null);
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <table className="w-full text-left border-collapse">
                <thead className="bg-gray-50 border-b">
                    <tr>
                        <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Req ID</th>
                        <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider w-1/3">Requirement Text</th>
                        <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Gap Analysis</th>
                        <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider w-1/3">AI Grounded Response</th>
                        <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {requirements.map(req => (
                        <tr key={req.id} className="hover:bg-blue-50/50 transition-colors">
                            <td className="p-4 text-xs font-mono text-gray-600 align-top whitespace-nowrap">{req.requirement_id}</td>
                            <td className="p-4 text-sm text-gray-800 align-top">
                                <div className="mb-2">{req.description}</div>
                                <div className="flex gap-2 text-xs">
                                    <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-600 border">{req.category}</span>
                                    <span className={`px-2 py-0.5 rounded border ${req.priority === 'HIGH' ? 'bg-red-50 text-red-600 border-red-200' : 'bg-gray-100 text-gray-600 border-gray-200'}`}>{req.priority}</span>
                                </div>
                            </td>
                            <td className="p-4 align-top">
                                {req.status === 'PENDING' && <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Pending</span>}
                                {req.status === 'SUPPORTED' && <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200"><CheckCircle2 className="w-3 h-3 mr-1"/> Supported</span>}
                                {req.status === 'NEEDS_INFORMATION' && <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200"><AlertCircle className="w-3 h-3 mr-1"/> Missing Context</span>}
                            </td>
                            <td className="p-4 text-sm text-gray-700 align-top bg-gray-50/50">
                                {responses[req.id] ? (
                                    <div className="prose prose-sm max-w-none">{responses[req.id]}</div>
                                ) : (
                                    <span className="text-gray-400 italic">No response drafted yet.</span>
                                )}
                            </td>
                            <td className="p-4 align-top text-right">
                                <button onClick={() => generateResponse(req.id)} disabled={loadingId === req.id}
                                    className="inline-flex items-center px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                                    {loadingId === req.id ? "Drafting..." : <><Play className="w-4 h-4 mr-1.5" /> Auto-Answer</>}
                                </button>
                            </td>
                        </tr>
                    ))}
                    {requirements.length === 0 && (
                        <tr>
                            <td colSpan="5" className="p-12 text-center text-gray-500">
                                <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                                No requirements extracted yet. Please upload a document first.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
