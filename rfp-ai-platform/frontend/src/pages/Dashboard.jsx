import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { 
    Plus, Folder, LogOut, BrainCircuit, Sparkles, CheckCircle2, 
    FileText, ShieldCheck, ArrowRight, Activity 
} from 'lucide-react';
import AICopilotWidget from '../components/AICopilotWidget';

export default function Dashboard() {
    const [projects, setProjects] = useState([]);
    const [isCreating, setIsCreating] = useState(false);
    const [name, setName] = useState('');
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => { fetchProjects(); }, []);

    const fetchProjects = async () => {
        try {
            setLoading(true);
            const res = await api.get('/projects');
            setProjects(res.data);
        } catch (e) {
            if (e.response?.status === 401) {
                localStorage.removeItem('token');
                navigate('/login');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await api.post('/projects', { name, description: '' });
            setIsCreating(false);
            navigate(`/project/${res.data.id}`);
        } catch (err) {
            alert('Failed to create workspace: ' + (err.response?.data?.detail || err.message));
        }
    };

    const completedCount = projects.filter(p => p.status === 'COMPLETED').length;
    const activeCount = projects.length - completedCount;

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
            {/* Top Navigation */}
            <nav className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-xs">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-600 rounded-xl shadow-xs">
                        <BrainCircuit className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-lg text-slate-900 tracking-tight">RFP Intelligence Platform</span>
                            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full">
                                LangGraph + MCP
                            </span>
                        </div>
                        <p className="text-xs text-slate-400">Autonomous Tender Analysis & Proposal Automation</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => { localStorage.removeItem('token'); navigate('/login'); }} 
                        className="flex items-center text-xs font-semibold text-slate-600 hover:text-rose-600 px-3 py-1.5 rounded-lg hover:bg-rose-50 transition"
                    >
                        <LogOut className="w-4 h-4 mr-1.5" /> Logout
                    </button>
                </div>
            </nav>

            <div className="max-w-6xl mx-auto p-8 w-full">
                {/* Executive Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total RFP Workspaces</p>
                            <h3 className="text-2xl font-bold text-slate-900 mt-1">{projects.length}</h3>
                        </div>
                        <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                            <Folder className="w-5 h-5" />
                        </div>
                    </div>

                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Analysis</p>
                            <h3 className="text-2xl font-bold text-amber-600 mt-1">{activeCount}</h3>
                        </div>
                        <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>

                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Completed Proposals</p>
                            <h3 className="text-2xl font-bold text-emerald-600 mt-1">{completedCount}</h3>
                        </div>
                        <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                            <CheckCircle2 className="w-5 h-5" />
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white p-5 rounded-2xl shadow-sm flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold text-indigo-200 uppercase tracking-wider">Agent Engine</p>
                            <div className="flex items-center gap-1.5 mt-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                                <span className="text-sm font-bold text-white">9-Agent Graph</span>
                            </div>
                            <p className="text-[11px] text-indigo-300 mt-0.5">FastMCP + Hybrid Tools</p>
                        </div>
                        <div className="p-3 bg-white/10 text-indigo-300 rounded-xl">
                            <Sparkles className="w-5 h-5" />
                        </div>
                    </div>
                </div>

                {/* Section Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">RFP Workspaces</h2>
                        <p className="text-xs text-slate-500 mt-0.5">Select a project to review intelligence, compliance matrices, and agent workflows.</p>
                    </div>
                    <button 
                        onClick={() => setIsCreating(true)}
                        className="flex items-center gap-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
                    >
                        <Plus className="w-4 h-4" /> New RFP Workspace
                    </button>
                </div>

                {/* Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {/* Create New Card */}
                    <div 
                        onClick={() => setIsCreating(true)}
                        className="border-2 border-dashed border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/30 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition group min-h-[200px]"
                    >
                        <div className="bg-indigo-50 p-3.5 rounded-2xl mb-3 group-hover:bg-indigo-100 text-indigo-600 transition">
                            <Plus className="w-6 h-6" />
                        </div>
                        <span className="font-semibold text-slate-700 text-sm">Create New Workspace</span>
                        <span className="text-xs text-slate-400 mt-1 text-center">Analyze a new RFP or tender document</span>
                    </div>

                    {/* Project Cards */}
                    {projects.map(p => (
                        <div key={p.id} 
                            onClick={() => navigate(`/project/${p.id}`)}
                            className="bg-white rounded-2xl border border-slate-200 p-5 flex flex-col cursor-pointer hover:shadow-md hover:border-indigo-300 transition min-h-[200px] justify-between group"
                        >
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <div className="p-2 bg-slate-100 rounded-xl text-indigo-600 group-hover:bg-indigo-50 transition">
                                        <Folder className="w-5 h-5" />
                                    </div>
                                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-wider ${
                                        p.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                                    }`}>
                                        {p.status || 'ACTIVE'}
                                    </span>
                                </div>
                                <h3 className="font-semibold text-base text-slate-900 line-clamp-2 leading-snug group-hover:text-indigo-600 transition">
                                    {p.name}
                                </h3>
                                <p className="text-xs text-slate-400 mt-1 font-mono">{p.id.slice(0, 16)}...</p>
                            </div>
                            <div className="pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-400 mt-4">
                                <span>{new Date(p.created_at || Date.now()).toLocaleDateString()}</span>
                                <span className="flex items-center gap-1 text-indigo-600 font-semibold group-hover:translate-x-0.5 transition">
                                    Open Workspace <ArrowRight className="w-3.5 h-3.5" />
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {isCreating && (
                    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
                        <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-md border border-slate-200">
                            <h2 className="text-lg font-bold text-slate-900 mb-1">Create New Workspace</h2>
                            <p className="text-xs text-slate-500 mb-5">Provide a title for this procurement or RFP opportunity.</p>
                            <form onSubmit={handleCreate}>
                                <input 
                                    autoFocus 
                                    required 
                                    type="text" 
                                    placeholder="e.g. Smart City IoT Infrastructure RFP 2026" 
                                    className="w-full border border-slate-200 p-3 rounded-xl mb-6 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                                    value={name} 
                                    onChange={e => setName(e.target.value)} 
                                />
                                <div className="flex justify-end gap-2.5">
                                    <button 
                                        type="button" 
                                        onClick={() => setIsCreating(false)} 
                                        className="px-4 py-2 font-medium text-xs text-slate-600 hover:bg-slate-100 rounded-xl transition"
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        type="submit" 
                                        className="px-4 py-2 font-semibold text-xs bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition shadow-xs"
                                    >
                                        Create Workspace
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>

            {/* Global AI Copilot */}
            <AICopilotWidget />
        </div>
    );
}
