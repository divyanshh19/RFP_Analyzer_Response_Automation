import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProjectDetail from './pages/ProjectDetail';

const PrivateRoute = ({ children }) => {
    return localStorage.getItem('token') ? children : <Navigate to="/login" />;
};

export default function App() {
    return (
        <Router>
            <div className="min-h-screen font-sans text-gray-900">
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
                    <Route path="/project/:id" element={<PrivateRoute><ProjectDetail /></PrivateRoute>} />
                </Routes>
            </div>
        </Router>
    );
}
