import React, { useState, useEffect, useRef } from 'react';
import api from '../api/axios';
import { 
    Bot, X, Send, Sparkles, Trash2, ChevronRight, 
    FileText, CheckCircle2, Loader2, ArrowUpRight 
} from 'lucide-react';

const SUGGESTED_QUERIES = [
    "What are the mandatory tender requirements?",
    "What is the submission deadline?",
    "Why are certain requirements non-compliant?",
    "What certifications does our company hold?",
    "What is the current workflow execution stage?"
];

export default function AICopilotWidget({ projectId }) {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => {
        if (isOpen && projectId) {
            fetchHistory();
        }
    }, [isOpen, projectId]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const fetchHistory = async () => {
        try {
            const res = await api.get(`/assistant/${projectId}/history`);
            if (res.data?.history) {
                setMessages(res.data.history);
            }
        } catch (e) {
            // New conversation
        }
    };

    const handleSend = async (textToSend) => {
        const query = (textToSend || input).trim();
        if (!query || loading) return;

        setInput('');
        const userMsg = { role: 'user', content: query, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);

        try {
            const res = await api.post('/assistant/chat', {
                project_id: projectId,
                message: query
            });

            const botMsg = {
                role: 'assistant',
                content: res.data.answer,
                citations: res.data.citations || [],
                tools_used: res.data.tools_used || [],
                suggested_followups: res.data.suggested_followups || [],
                timestamp: res.data.timestamp || new Date().toISOString()
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (e) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Failed to contact AI Copilot service: ' + (e.response?.data?.detail || e.message),
                timestamp: new Date().toISOString()
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleClear = async () => {
        try {
            await api.delete(`/assistant/${projectId}/history`);
            setMessages([]);
        } catch (e) {
            setMessages([]);
        }
    };

    return (
        <>
            {/* Floating Trigger Button */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-indigo-600 to-indigo-800 text-white p-4 rounded-full shadow-2xl hover:scale-105 hover:shadow-indigo-500/25 transition-all flex items-center gap-2.5 font-bold text-xs"
                >
                    <div className="relative">
                        <Bot className="w-5 h-5" />
                        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white animate-pulse" />
                    </div>
                    <span>Ask RFP Copilot</span>
                </button>
            )}

            {/* Chat Drawer / Popout */}
            {isOpen && (
                <div className="fixed bottom-6 right-6 z-50 w-[420px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[85vh] bg-white rounded-3xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
                    
                    {/* Header */}
                    <div className="px-5 py-4 bg-slate-900 text-white flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-600 rounded-xl">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-bold text-sm flex items-center gap-1.5">
                                    RFP AI Copilot
                                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                                </h3>
                                <p className="text-[11px] text-slate-400 font-mono truncate max-w-[200px]">
                                    Project: {projectId}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-1">
                            <button
                                onClick={handleClear}
                                title="Clear conversation history"
                                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Messages Body */}
                    <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50">
                        {messages.length === 0 && (
                            <div className="text-center py-8 px-4">
                                <Bot className="w-10 h-10 text-indigo-500 mx-auto mb-3 opacity-80" />
                                <h4 className="font-bold text-sm text-slate-800 mb-1">How can I assist your bid?</h4>
                                <p className="text-xs text-slate-500 mb-4 leading-relaxed">
                                    I analyze tender requirements, evaluate knowledge-base compliance, check deadlines, and assist with proposal writing.
                                </p>
                                
                                <div className="space-y-1.5 text-left">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-1">Suggested Inquiries</span>
                                    {SUGGESTED_QUERIES.map((q, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => handleSend(q)}
                                            className="w-full text-left text-xs p-2.5 bg-white hover:bg-indigo-50/70 border border-slate-200/80 rounded-xl text-slate-700 transition flex items-center justify-between group"
                                        >
                                            <span className="truncate">{q}</span>
                                            <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 transition" />
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`max-w-[88%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                                    msg.role === 'user'
                                        ? 'bg-indigo-600 text-white rounded-tr-sm shadow-sm'
                                        : 'bg-white text-slate-800 rounded-tl-sm border border-slate-200/80 shadow-sm'
                                }`}>
                                    {msg.content}
                                </div>

                                {/* Tool execution indicator */}
                                {msg.tools_used && msg.tools_used.length > 0 && (
                                    <div className="flex gap-1.5 mt-1">
                                        {msg.tools_used.map((t, tIdx) => (
                                            <span key={tIdx} className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono">
                                                Tool: {t}
                                            </span>
                                        ))}
                                    </div>
                                )}

                                {/* Citations */}
                                {msg.citations && msg.citations.length > 0 && (
                                    <div className="mt-1 space-y-1 max-w-[88%]">
                                        {msg.citations.map((c, cIdx) => (
                                            <div key={cIdx} className="text-[10px] text-slate-500 bg-slate-100 p-1.5 rounded-md flex items-center gap-1">
                                                <FileText className="w-3 h-3 text-slate-400" />
                                                <span>Source: <strong>{c.source}</strong> (Page {c.page || 1})</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Followup chips */}
                                {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-2 max-w-[88%]">
                                        {msg.suggested_followups.map((f, fIdx) => (
                                            <button
                                                key={fIdx}
                                                onClick={() => handleSend(f)}
                                                className="text-[10px] px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition font-medium border border-indigo-200/60"
                                            >
                                                {f}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}

                        {loading && (
                            <div className="flex items-center gap-2 p-3 bg-white rounded-2xl border border-slate-200/80 text-xs text-slate-500 w-fit">
                                <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                                <span>Copilot is analyzing context & tools...</span>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    {/* Input Bar */}
                    <div className="p-3 bg-white border-t border-slate-100">
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                handleSend();
                            }}
                            className="flex items-center gap-2"
                        >
                            <input
                                type="text"
                                placeholder="Ask about deadlines, compliance, or proposal wording..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                className="flex-1 text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || loading}
                                className="p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition disabled:opacity-40"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
}
