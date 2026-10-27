import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, ListChecks, Download, BookOpen } from 'lucide-react';
import DocumentUpload from '../components/DocumentUpload';
import RequirementReview from '../components/RequirementReview';
import api from '../api/axios';

export default function ProjectDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('upload');

    const handleExport = async () => {
        try {
            const res = await api.get(`/export/${id}/docx`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'RFP_Response.docx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) {
            alert('Export failed. Ensure you have generated responses first.');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b px-8 py-5">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button onClick={() => navigate('/')} className="p-2 bg-gray-50 hover:bg-gray-100 rounded-full border transition-colors">
                            <ArrowLeft className="w-5 h-5 text-gray-600" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Project Workspace</h1>
                            <p className="text-sm font-mono text-gray-500 mt-1">{id}</p>
                        </div>
                    </div>
                    
                    <button className="flex items-center px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 text-sm font-medium transition">
                        <BookOpen className="w-4 h-4 mr-2" />
                        Manage Knowledge Base
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="bg-white border-b shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-8 flex gap-8">
                    <button onClick={() => setActiveTab('upload')} 
                        className={`py-4 px-2 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === 'upload' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
                        <Upload className="w-4 h-4" /> 1. Upload & Ingest
                    </button>
                    <button onClick={() => setActiveTab('review')} 
                        className={`py-4 px-2 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === 'review' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
                        <ListChecks className="w-4 h-4" /> 2. Generate & Review Responses
                    </button>
                    <button onClick={() => setActiveTab('export')} 
                        className={`py-4 px-2 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === 'export' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
                        <Download className="w-4 h-4" /> 3. Final Export
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 max-w-7xl mx-auto w-full p-8 pb-24">
                {activeTab === 'upload' && <DocumentUpload projectId={id} onComplete={() => setActiveTab('review')} />}
                {activeTab === 'review' && <RequirementReview projectId={id} />}
                {activeTab === 'export' && (
                    <div className="bg-white rounded-xl shadow-sm border p-16 text-center flex flex-col items-center max-w-3xl mx-auto mt-8">
                        <div className="p-4 bg-green-50 rounded-full mb-6">
                            <Download className="w-12 h-12 text-green-600" />
                        </div>
                        <h2 className="text-3xl font-bold mb-4 text-gray-800">Export Complete Response</h2>
                        <p className="text-gray-600 mb-10 max-w-md text-lg leading-relaxed">
                            Compile all finalized AI responses and requirement tables into a perfectly formatted Microsoft Word document ready for client submission.
                        </p>
                        <button onClick={handleExport} className="px-10 py-4 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 transition shadow-lg hover:shadow-xl hover:-translate-y-0.5 flex items-center text-lg">
                            Download DOCX Package
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
