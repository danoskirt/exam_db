// src/components/ExamDashboard.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function ExamDashboard({ participantData, setParticipantData }) {
    const navigate = useNavigate();
    const [examQuestions, setExamQuestions] = useState([]);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [examStarted, setExamStarted] = useState(false);

    useEffect(() => {
        if (!participantData || !participantData.participantId) {
            navigate('/login'); // Redirect to login if no participant data
            return;
        }

        // Check if exam is already submitted
        if (participantData.submittedAt) { // Assuming submittedAt is part of participantData from login response
            navigate(`/results/${participantData.participantId}`);
            return;
        }

        const fetchExamDetailsAndStartSession = async () => {
            try {
                // 1. Start Exam Session (no scratch card pin needed here)
                const startResponse = await api.startExamSession(participantData.participantId);
                if (startResponse.error) {
                    setError(startResponse.error);
                    return;
                }
                setMessage(startResponse.message);
                setExamStarted(true);
                // Update participantData with started_at if it was just set
                setParticipantData(prevData => ({ ...prevData, startedAt: startResponse.started_at }));

                // 2. Fetch Questions (no scratch card pin needed here)
                const questionsResponse = await api.getExamQuestions(participantData.participantId);
                if (questionsResponse.error) {
                    setError(questionsResponse.error);
                    return;
                }
                setExamQuestions(questionsResponse.questions);

            } catch (err) {
                console.error('Error fetching exam details or starting session:', err);
                setError('Failed to load exam. Please try logging in again.');
                // Potentially clear participant data and redirect to login
                setParticipantData(null);
                navigate('/login');
            }
        };

        if (!examStarted) { // Only try to start if not already marked as started
            fetchExamDetailsAndStartSession();
        }
    }, [participantData, navigate, examStarted, setParticipantData]);


    const handleStartExam = () => {
        // This button might not be strictly necessary if auto-starting on dashboard load
        // But if you want a manual "Start Exam" button, you could trigger fetchExamDetailsAndStartSession here
        // For now, it's just for display/navigation
        if (examStarted && examQuestions.length > 0) {
            navigate('/exam');
        } else {
            setError("Exam not ready yet or failed to load. Please try again.");
        }
    };

    if (!participantData) {
        return <div className="container">Loading participant data...</div>;
    }

    const { examDetails, examCode, registrationId } = participantData;

    return (
        <div className="container">
            <h2>Welcome, {participantData.name || participantData.email}!</h2>
            <h3>Exam Dashboard</h3>
            {message && <p className="success-message">{message}</p>}
            {error && <p className="error-message">{error}</p>}

            {examDetails ? (
                <div>
                    <p><strong>Exam Name:</strong> {examDetails.name}</p>
                    <p><strong>Exam Code:</strong> {examCode}</p>
                    <p><strong>Your Registration ID:</strong> {registrationId}</p>
                    <p><strong>Duration:</strong> {examDetails.duration_minutes} minutes</p>
                    <p><strong>Pass Percentage:</strong> {examDetails.pass_percentage}%</p>

                    {examStarted && examQuestions.length > 0 ? (
                        <div>
                            <p className="success-message">Exam is ready!</p>
                            <button className="button-primary" onClick={handleStartExam}>
                                Go to Exam
                            </button>
                        </div>
                    ) : (
                        <p>Loading exam questions...</p>
                    )}
                </div>
            ) : (
                <p>No exam details available or still loading...</p>
            )}
        </div>
    );
}

export default ExamDashboard;