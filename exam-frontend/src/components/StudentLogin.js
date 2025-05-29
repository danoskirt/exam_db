// src/components/StudentLogin.js
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../api';

function StudentLogin({ setParticipantData }) {
    const [emailOrRegId, setEmailOrRegId] = useState('');
    const [scratchCardPin, setScratchCardPin] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const location = useLocation();

    // Pre-fill fields if redirected from registration
    useEffect(() => {
        if (location.state) {
            if (location.state.email) setEmailOrRegId(location.state.email);
            if (location.state.registrationId) setEmailOrRegId(location.state.registrationId); // Prefer reg ID for login
            if (location.state.scratchCardPin) setScratchCardPin(location.state.scratchCardPin);
            if (location.state.message) setMessage(location.state.message);
        }
    }, [location.state]);

    const handleLogin = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');

        if (!emailOrRegId || !scratchCardPin) {
            setError('Please enter your email/registration ID and scratch card PIN.');
            return;
        }

        let credentials = { scratch_card_pin: scratchCardPin };
        // Determine if input is email or registration_id
        if (emailOrRegId.includes('@')) {
            credentials.email = emailOrRegId;
        } else {
            credentials.registration_id = emailOrRegId;
        }

        try {
            const response = await api.studentLogin(credentials);
            if (response.error) {
                setError(response.error);
            } else {
                setMessage(response.message);
                // Store all relevant data in App's state
                setParticipantData({
                    participantId: response.participant_id,
                    registrationId: response.registration_id,
                    examId: response.exam_id,
                    scratchCardPin: scratchCardPin,
                    examDetails: { // Pass exam details like duration and pass percentage
                        name: response.exam_name,
                        duration_minutes: response.duration_minutes,
                        pass_percentage: response.pass_percentage
                    },
                    startedAt: response.started_at // If already started, this will be populated
                });

                // Navigate to dashboard or results based on submitted_at status
                if (response.submitted_at) {
                    navigate(`/results/${response.participant_id}`);
                } else {
                    navigate('/exam-dashboard');
                }
            }
        } catch (err) {
            console.error('Login failed:', err);
            setError('Failed to log in. Please check your credentials or server status.');
        }
    };

    return (
        <div className="container">
            <h2>Student Login</h2>
            <form onSubmit={handleLogin}>
                <div className="form-group">
                    <label htmlFor="emailOrRegId">Email or Registration ID:</label>
                    <input
                        type="text"
                        id="emailOrRegId"
                        value={emailOrRegId}
                        onChange={(e) => setEmailOrRegId(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="loginScratchCardPin">Scratch Card PIN:</label>
                    {/* Corrected: All attributes must be within the opening tag */}
                    <input
                        type="password" /* Use password type for PIN */
                        id="loginScratchCardPin"
                        value={scratchCardPin}
                        onChange={(e) => setScratchCardPin(e.target.value)}
                        required
                        maxLength="20"
                    />
                </div>
                <button type="submit">Login</button>
            </form>
            {message && <p className="success-message">{message}</p>}
            {error && <p className="error-message">{error}</p>}
            <p>Not registered yet? <button onClick={() => navigate('/register')}>Register Here</button></p>
        </div>
    );
}

export default StudentLogin;