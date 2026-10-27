import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { Plus, Folder, LogOut, BrainCircuit } from 'lucide-react';

export default function Dashboard() {
    const [projects, setProjects] = useState([]);
    const [isCreating, setIsCreating] = useState(false);
    const [name, setName] = useState('');
    const navigate = useNavigate();

    useEffect(() => { fetchProjects(); }, []);

    const fetchProjects = async () => {
        try {
            const res = await api.get('/projects');
            setProjects(res.data);
        } catch (e) {
            if (e.response?.status === 401) {
                localStorage.removeItem('token');
                navigate('/login');
            }
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        const res = await api.post('/projects', { name, description: '' });
        setIsCreating(false);
        navigate(`/project/${res.data.id}`);
    };

    return (
        <div>
            {/* Navbar */}
            <nav className="bg-white border-b px-8 py-4 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-blue-600 rounded-md">
                        <BrainCircuit className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-xl text-gray-800">RFP Analyzer</span>
                </div>
                <button onClick={() => { localStorage.removeItem('token'); navigate('/login'); }} 
                    className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-900">
                    <LogOut className="w-4 h-4 mr-2" /> Logout
                </button>
            </nav>

            <div className="max-w-6xl mx-auto p-8 mt-4">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">My Workspaces</h1>

                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {/* Create New Card */}
                    <div 
                        onClick={() => setIsCreating(true)}
                        className="border-2 border-dashed border-gray-300 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition group min-h-[200px]"
                    >
                        <div className="bg-blue-100 p-3 rounded-full mb-3 group-hover:bg-blue-200 transition">
                            <Plus className="w-6 h-6 text-blue-600" />
                        </div>
                        <span className="font-semibold text-gray-700">New RFP Project</span>
                    </div>

                    {/* Project Cards */}
                    {projects.map(p => (
                        <div key={p.id} 
                            onClick={() => navigate(`/project/${p.id}`)}
                            className="bg-white rounded-xl shadow-sm border p-6 flex flex-col cursor-pointer hover:shadow-md hover:border-blue-300 transition min-h-[200px]"
                        >
                            <div className="mb-auto">
                                <Folder className="w-8 h-8 text-blue-500 mb-4" />
                                <h3 className="font-semibold text-lg line-clamp-2">{p.name}</h3>
                            </div>
                            <div className="mt-4 pt-4 border-t flex justify-between items-center text-sm">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${p.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                    {p.status}
                                </span>
                                <span className="text-gray-400 text-xs">
                                    {new Date(p.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {isCreating && (
                    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50">
                        <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md">
                            <h2 className="text-xl font-bold mb-4">Create New Workspace</h2>
                            <form onSubmit={handleCreate}>
                                <input autoFocus required type="text" placeholder="e.g. Acme Corp Bid 2026" 
                                    className="w-full border p-2.5 rounded-lg mb-6 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                    value={name} onChange={e => setName(e.target.value)} />
                                <div className="flex justify-end gap-3">
                                    <button type="button" onClick={() => setIsCreating(false)} className="px-4 py-2 font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition">Cancel</button>
                                    <button type="submit" className="px-4 py-2 font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">Create</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
