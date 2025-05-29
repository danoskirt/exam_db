// src/components/ExamResults.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';

function ExamResults() {
    const { participantId } = useParams();
    const navigate = useNavigate();
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchResults = async () => {
            setLoading(true);
            setError('');
            try {
                const response = await api.getParticipantResults(participantId);
                if (response.error) {
                    setError(response.error);
                } else {
                    setResults(response);
                }
            } catch (err) {
                console.error('Error fetching results:', err);
                setError('Failed to load exam results. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        if (participantId) {
            fetchResults();
        } else {
            setError('Participant ID is missing.');
            setLoading(false);
        }
    }, [participantId]);

    if (loading) {
        return <div className="container">Loading results...</div>;
    }

    if (error) {
        return (
            <div className="container">
                <p className="error-message">{error}</p>
                <button onClick={() => navigate('/')}>Go to Home</button>
            </div>
        );
    }

    if (!results) {
        return (
            <div className="container">
                <p>No results found for this participant.</p>
                <button onClick={() => navigate('/')}>Go to Home</button>
            </div>
        );
    }

    const {
        name,
        exam_name,
        final_score,
        max_possible_score,
        total_questions_answered,
        total_correct_answers_count,
        percentage_correct_by_count,
        overall_percentage_by_score,
        passed_exam,
        is_suspicious,
        answers_detail
    } = results;

    const resultsSummaryClass = passed_exam ? 'results-summary passed' : 'results-summary failed';

    return (
        <div className="container">
            <h2>Exam Results for {name} ({results.registration_id})</h2>
            <h3>Exam: {exam_name}</h3>

            <div className={resultsSummaryClass}>
                <p><strong>Overall Score:</strong> {final_score} / {max_possible_score}</p>
                <p><strong>Percentage by Score:</strong> {overall_percentage_by_score}%</p>
                <p><strong>Questions Answered Correctly:</strong> {total_correct_answers_count} / {total_questions_answered}</p>
                <p><strong>Percentage Correct (by count):</strong> {percentage_correct_by_count}%</p>
                <p><strong>Status:</strong> {passed_exam ? 'PASSED' : 'FAILED'}</p>
                {is_suspicious && <p className="error-message"><strong>Suspicious Activity Detected!</strong> (e.g., unusual submission time)</p>}
            </div>

            <div className="result-detail">
                <h3>Detailed Answers:</h3>
                {answers_detail.length === 0 ? (
                    <p>No answers submitted for detailed review.</p>
                ) : (
                    answers_detail.map((ans) => (
                        <div key={ans.question_id} className={`result-question ${ans.is_correct ? 'correct' : 'incorrect'}`}>
                            <h4>Q: {ans.question_text}</h4>
                            {ans.question_type === 'mcq' && ans.options && (
                                <p>Options: {Object.entries(ans.options).map(([key, value]) => `${key}) ${value}`).join(', ')}</p>
                            )}
                            <p><strong>Your Answer:</strong> {ans.submitted_answer || "No answer"}</p>
                            <p><strong>Correct Answer:</strong> {ans.correct_answer_reference || "N/A"}</p>
                            <p><strong>Status:</strong> {ans.is_correct ? 'Correct' : 'Incorrect'}</p>
                            <p><strong>Score Earned:</strong> {ans.score_earned} / {ans.max_score}</p>
                            <p><em>Time Taken: {ans.time_taken_seconds} seconds</em></p>
                        </div>
                    ))
                )}
            </div>
            <button onClick={() => navigate('/')}>Go to Home</button>
        </div>
    );
}

export default ExamResults;