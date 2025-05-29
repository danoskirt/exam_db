// src/api.js
const API_BASE_URL = 'http://localhost:5000/api';

const api = {
    // --- Student API Calls ---
    registerForExam: async (name, email, scratchCardPin) => { // Removed examCode from params
        const response = await fetch(`${API_BASE_URL}/register_for_exam`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, scratch_card_pin: scratchCardPin }), // Removed exam_code from body
        });
        return response.json();
    },

    studentLogin: async (credentials) => { // credentials now MUST include exam_code
        const response = await fetch(`${API_BASE_URL}/student_login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials), // {email: '...', scratch_card_pin: '...', exam_code: '...'} OR {registration_id: '...', scratch_card_pin: '...', exam_code: '...'}
        });
        return response.json();
    },

    // MODIFIED: Removed scratchCardPin from parameters
    startExamSession: async (participantId) => {
        const response = await fetch(`${API_BASE_URL}/participants/${participantId}/start_exam_session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // No body needed if no scratch_card_pin is sent
            body: JSON.stringify({}) // Send an empty object if no other data is required
        });
        return response.json();
    },

    // MODIFIED: Removed scratchCardPin from parameters, changed to GET
    getExamQuestions: async (participantId) => {
        const response = await fetch(`${API_BASE_URL}/participants/${participantId}/questions`, {
            method: 'GET', // Changed to GET
            headers: {
                'Content-Type': 'application/json',
            },
            // No body needed for GET requests
        });
        return response.json();
    },

    // MODIFIED: Removed scratchCardPin from parameters
    submitExam: async (participantId, answers, behavioralData = {}) => {
        const response = await fetch(`${API_BASE_URL}/participants/${participantId}/submit_exam`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                answers,
                behavioral_data: behavioralData
            }),
        });
        return response.json();
    },

    getParticipantResults: async (participantId) => {
        const response = await fetch(`${API_BASE_URL}/participants/${participantId}/results`);
        return response.json();
    },

    // --- Admin API Calls ---
    createExam: async (examData) => {
        const response = await fetch(`${API_BASE_URL}/exams`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(examData),
        });
        return response.json();
    },

    getAllExams: async () => {
        const response = await fetch(`${API_BASE_URL}/exams`);
        return response.json();
    },

    getExamDetails: async (examId) => {
        const response = await fetch(`${API_BASE_URL}/exams/${examId}`);
        return response.json();
    },

    updateExam: async (examId, examData) => {
        const response = await fetch(`${API_BASE_URL}/exams/${examId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(examData),
        });
        return response.json();
    },

    deleteExam: async (examId) => {
        const response = await fetch(`${API_BASE_URL}/exams/${examId}`, {
            method: 'DELETE',
        });
        return response.json();
    },

    uploadPdf: async (examId, file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/upload_pdf/${examId}`, {
            method: 'POST',
            body: formData,
        });
        return response.json();
    },

    generateQuestionsFromText: async (text, numQuestions) => {
        const response = await fetch(`${API_BASE_URL}/generate_questions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, num_questions: numQuestions }),
        });
        return response.json();
    },

    generateScratchCards: async (numCards) => { // Removed examId from params
        const response = await fetch(`${API_BASE_URL}/admin/generate_scratch_cards`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_cards: numCards }), // Removed exam_id from body
        });
        return response.json();
    },

    getExamParticipantsResults: async (examId) => {
        const response = await fetch(`${API_BASE_URL}/exams/${examId}/participants_results`);
        return response.json();
    },

    getExamAnalytics: async (examId) => {
        const response = await fetch(`${API_BASE_URL}/exams/${examId}/analytics`);
        return response.json();
    }
};

export default api;