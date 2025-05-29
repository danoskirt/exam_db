// src/components/ExamPage.js
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function ExamPage({ participantData }) {
    const navigate = useNavigate();
    const [questions, setQuestions] = useState([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [timer, setTimer] = useState(0); // in seconds
    const [sessionStartTime, setSessionStartTime] = useState(null); // When the exam session was started
    const [questionStartTime, setQuestionStartTime] = useState(null); // When current question was displayed
    const [behavioralData, setBehavioralData] = useState([]); // To track time spent per question, etc.

    // Effect to redirect if participantData is missing
    useEffect(() => {
        if (!participantData || !participantData.participantId) {
            navigate('/login');
            return;
        }
        if (participantData.submittedAt) {
            navigate(`/results/${participantData.participantId}`);
            return;
        }

        // Initialize session start time from participantData if available
        if (participantData.startedAt) {
            const start = new Date(participantData.startedAt);
            setSessionStartTime(start);
            setQuestionStartTime(new Date()); // Start timer for first question immediately
            // Calculate elapsed time if resuming
            const now = new Date();
            const elapsed = Math.floor((now.getTime() - start.getTime()) / 1000);
            setTimer(participantData.examDetails.duration_minutes * 60 - elapsed);
        } else {
            // This case should ideally not happen if ExamDashboard handles starting the session
            setError("Exam session not properly started. Please go back to dashboard.");
            navigate('/exam-dashboard');
        }

        const fetchQuestions = async () => {
            try {
                // MODIFIED: Removed scratchCardPin
                const response = await api.getExamQuestions(participantData.participantId);
                if (response.error) {
                    setError(response.error);
                } else {
                    setQuestions(response.questions);
                }
            } catch (err) {
                console.error('Error fetching questions:', err);
                setError('Failed to load questions.');
            }
        };

        fetchQuestions();

    }, [participantData, navigate]);

    // Timer countdown effect
    useEffect(() => {
        if (sessionStartTime && timer > 0 && !participantData.submittedAt) {
            const interval = setInterval(() => {
                setTimer(prevTimer => {
                    if (prevTimer <= 1) {
                        clearInterval(interval);
                        handleSubmitExam(); // Auto-submit when timer runs out
                        return 0;
                    }
                    return prevTimer - 1;
                });
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [timer, sessionStartTime, participantData.submittedAt]);


    const handleAnswerChange = useCallback((questionId, value) => {
        setAnswers(prevAnswers => ({
            ...prevAnswers,
            [questionId]: value,
        }));
    }, []);

    const recordQuestionTime = useCallback(() => {
        if (questionStartTime && questions.length > 0) {
            const timeTaken = Math.floor((new Date().getTime() - questionStartTime.getTime()) / 1000);
            const currentQuestionId = questions[currentQuestionIndex]?.id;

            if (currentQuestionId) {
                setBehavioralData(prevData => [
                    ...prevData,
                    { question_id: currentQuestionId, time_taken_seconds: timeTaken }
                ]);
            }
        }
    }, [questionStartTime, questions, currentQuestionIndex]);

    const handleNextQuestion = () => {
        recordQuestionTime(); // Record time for the current question
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(prevIndex => prevIndex + 1);
            setQuestionStartTime(new Date()); // Reset timer for next question
        }
    };

    const handlePreviousQuestion = () => {
        recordQuestionTime(); // Record time for the current question
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(prevIndex => prevIndex - 1);
            setQuestionStartTime(new Date()); // Reset timer for previous question
        }
    };

    const handleSubmitExam = async () => {
        recordQuestionTime(); // Record time for the last question

        if (!participantData || !participantData.participantId) {
            setError('Participant data missing. Please log in again.');
            navigate('/login');
            return;
        }

        setMessage('Submitting exam...');
        setError('');

        const formattedAnswers = questions.map(q => ({
            question_id: q.id,
            answer: answers[q.id] || null, // Ensure answer is recorded, even if empty
            time_taken_seconds: behavioralData.find(d => d.question_id === q.id)?.time_taken_seconds || 0 // Retrieve recorded time
        }));

        try {
            // MODIFIED: Removed scratchCardPin
            const response = await api.submitExam(participantData.participantId, formattedAnswers, {
                total_time_spent: participantData.examDetails.duration_minutes * 60 - timer,
                // Add any other behavioral data you collect
                question_times: behavioralData
            });

            if (response.error) {
                setError(response.error);
                setMessage('');
            } else {
                setMessage(response.message);
                setParticipantData(prevData => ({ ...prevData, submittedAt: response.submitted_at }));
                navigate(`/results/${participantData.participantId}`);
            }
        } catch (err) {
            console.error('Exam submission failed:', err);
            setError('Failed to submit exam. Please try again or contact support.');
            setMessage('');
        }
    };

    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    };


    if (!questions.length) {
        return <div className="container">Loading questions...</div>;
    }

    const currentQuestion = questions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    const isFirstQuestion = currentQuestionIndex === 0;

    return (
        <div className="container exam-page">
            <h2>Exam: {participantData.examDetails?.name}</h2>
            <div className="timer">Time Left: {formatTime(timer)}</div>

            {message && <p className="success-message">{message}</p>}
            {error && <p className="error-message">{error}</p>}

            <div className="question-navigation">
                Question {currentQuestionIndex + 1} of {questions.length}
            </div>

            <div className="question-card">
                <p><strong>{currentQuestion.question_text}</strong></p>
                {currentQuestion.question_type === 'mcq' && currentQuestion.options && (
                    <div className="options">
                        {Object.entries(currentQuestion.options).map(([key, value]) => (
                            <label key={key}>
                                <input
                                    type="radio"
                                    name={`question-${currentQuestion.id}`}
                                    value={key}
                                    checked={answers[currentQuestion.id] === key}
                                    onChange={() => handleAnswerChange(currentQuestion.id, key)}
                                />
                                {key}) {value}
                            </label>
                        ))}
                    </div>
                )}
                {currentQuestion.question_type === 'short_answer' && (
                    <textarea
                        value={answers[currentQuestion.id] || ''}
                        onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                        placeholder="Type your answer here..."
                        rows="4"
                    ></textarea>
                )}
                {currentQuestion.question_type === 'true_false' && (
                    <div className="options">
                        <label>
                            <input
                                type="radio"
                                name={`question-${currentQuestion.id}`}
                                value="True"
                                checked={answers[currentQuestion.id] === 'True'}
                                onChange={() => handleAnswerChange(currentQuestion.id, 'True')}
                            /> True
                        </label>
                        <label>
                            <input
                                type="radio"
                                name={`question-${currentQuestion.id}`}
                                value="False"
                                checked={answers[currentQuestion.id] === 'False'}
                                onChange={() => handleAnswerChange(currentQuestion.id, 'False')}
                            /> False
                        </label>
                    </div>
                )}
            </div>

            <div className="navigation-buttons">
                <button onClick={handlePreviousQuestion} disabled={isFirstQuestion}>
                    Previous
                </button>
                {!isLastQuestion && (
                    <button onClick={handleNextQuestion}>Next</button>
                )}
                {isLastQuestion && (
                    <button onClick={handleSubmitExam} className="submit-button">
                        Submit Exam
                    </button>
                )}
            </div>
        </div>
    );
}

export default ExamPage;