import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { Lock, Mail, BrainCircuit } from 'lucide-react';

export default function Login() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (isLogin) {
                const formData = new URLSearchParams();
                formData.append('username', email); // OAuth2 expects username
                formData.append('password', password);
                
                const res = await api.post('/auth/login', formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                });
                localStorage.setItem('token', res.data.access_token);
                navigate('/');
            } else {
                // Backend requires a 'name' field, so we default it to the email prefix
                const defaultName = email.split('@')[0];
                await api.post('/auth/register', { name: defaultName, email, password });
                setIsLogin(true);
                alert("Registered successfully! Please log in.");
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Authentication failed");
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="w-full max-w-md p-10 bg-white rounded-xl shadow-xl">
                <div className="flex justify-center mb-6">
                    <div className="p-3 bg-blue-600 rounded-lg">
                        <BrainCircuit className="w-8 h-8 text-white" />
                    </div>
                </div>
                <h2 className="mb-8 text-2xl font-bold text-center text-gray-800">
                    {isLogin ? 'Sign in to RFP AI' : 'Create an Account'}
                </h2>
                
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Email Address</label>
                        <div className="relative mt-1">
                            <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
                                className="w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Password</label>
                        <div className="relative mt-1">
                            <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
                                className="w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                        </div>
                    </div>
                    <button type="submit" className="w-full py-2.5 text-white bg-blue-600 rounded-lg hover:bg-blue-700 font-medium transition-colors">
                        {isLogin ? 'Sign In' : 'Sign Up'}
                    </button>
                </form>
                
                <p className="mt-6 text-sm text-center text-gray-600">
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <button onClick={() => setIsLogin(!isLogin)} className="font-medium text-blue-600 hover:text-blue-500">
                        {isLogin ? 'Sign up' : 'Log in'}
                    </button>
                </p>
            </div>
        </div>
    );
}
