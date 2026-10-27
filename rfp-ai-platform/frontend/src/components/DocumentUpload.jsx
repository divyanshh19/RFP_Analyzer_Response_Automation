import React, { useState } from 'react';
import api from '../api/axios';
import { UploadCloud, CheckCircle, Loader } from 'lucide-react';

export default function DocumentUpload({ projectId, onComplete }) {
    const [file, setFile] = useState(null);
    const [docType, setDocType] = useState('RFP');
    const [status, setStatus] = useState(''); // '', 'uploading', 'processing', 'extracting', 'done'

    const handleUpload = async () => {
        if (!file) return;
        try {
            setStatus('uploading');
            const formData = new FormData();
            formData.append('file', file);
            formData.append('rfp_project_id', projectId); // Must match backend parameter name
            formData.append('document_type', docType); // Pass selected document type
            
            // Phase 4: Upload
            const uploadRes = await api.post('/documents/upload', formData);
            const docId = uploadRes.data.id;
            
            // Phase 5, 6, 7, 8: Extract, OCR, Chunk, Embed
            setStatus('processing');
            await api.post(`/documents/${docId}/process`);
            
            // Phase 10: Extract Requirements using Gemini (ONLY for RFPs)
            if (docType === 'RFP') {
                setStatus('extracting');
                await api.post(`/rfp/${docId}/extract-requirements`);
            }
            
            setStatus('done');
            if(onComplete && docType === 'RFP') onComplete();
        } catch (e) {
            const errorDetail = e.response?.data?.detail;
            const errorMsg = typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail || e.message);
            alert('Pipeline Error: ' + errorMsg);
            setStatus('');
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-16 border-2 border-dashed border-gray-300 rounded-xl bg-white hover:border-blue-500 transition-colors">
            <UploadCloud className="w-16 h-16 text-blue-500 mb-6" />
            <h3 className="text-2xl font-bold text-gray-800 mb-2">Upload Document</h3>
            <p className="text-gray-500 mb-6 max-w-sm text-center">
                Upload your client's RFP to extract requirements, or upload your Company Profile to the Knowledge Base to generate answers.
            </p>
            
            <div className="flex flex-col items-center gap-4 mb-6 w-full max-w-xs">
                <select 
                    value={docType}
                    onChange={e => setDocType(e.target.value)}
                    className="w-full border-gray-300 rounded-lg shadow-sm text-gray-700 bg-gray-50 p-2 border"
                >
                    <option value="RFP">RFP Document (Extract Requirements)</option>
                    <option value="KNOWLEDGE_BASE">Company Profile (Knowledge Base)</option>
                </select>
                <input type="file" onChange={e => setFile(e.target.files[0])} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" accept=".pdf,.docx" />
            </div>
            
            <button onClick={handleUpload} disabled={!file || status !== ''} className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center font-medium shadow-md transition-all">
                {status === '' && "Start Full Ingestion Pipeline"}
                {status === 'uploading' && <><Loader className="w-5 h-5 mr-3 animate-spin" /> Uploading to Server...</>}
                {status === 'processing' && <><Loader className="w-5 h-5 mr-3 animate-spin" /> Chunking & Vectorizing...</>}
                {status === 'extracting' && <><Loader className="w-5 h-5 mr-3 animate-spin" /> AI Extracting Requirements...</>}
                {status === 'done' && <><CheckCircle className="w-5 h-5 mr-3" /> Ingestion Complete</>}
            </button>
        </div>
    );
}
