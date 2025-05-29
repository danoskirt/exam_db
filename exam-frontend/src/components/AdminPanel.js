// src/components/AdminPanel.js
import React from 'react';
import { useNavigate } from 'react-router-dom';

function AdminPanel() {
    const navigate = useNavigate();
    return (
        <div className="container">
            <h2>Admin Panel (Placeholder)</h2>
            <p>This section would contain features for:</p>
            <ul>
                <li>Creating/Managing Exams</li>
                <li>Uploading PDFs and generating questions</li>
                <li>Generating Scratch Cards</li>
                <li>Viewing Participant Results (all participants for an exam)</li>
                <li>Analyzing Exam Difficulty</li>
            </ul>
            <p>For now, please manage admin tasks via the Flask backend directly or tools like Postman/Insomnia.</p>
            <button onClick={() => navigate('/')}>Go to Home</button>
        </div>
    );
}

export default AdminPanel;