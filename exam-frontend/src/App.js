// src/App.js
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';

// Import your components
import RegistrationForm from './components/RegistrationForm';
import StudentLogin from './components/StudentLogin';
import ExamDashboard from './components/ExamDashboard';
import ExamResults from './components/ExamResults';
import AdminPanel from './components/AdminPanel'; // A placeholder for now

function Home() {
  const navigate = useNavigate();
  return (
    <div className="container">
      <h1>Online Exam Portal</h1>
      <p>Welcome! Please register or log in to take an exam.</p>
      <div className="nav-links">
        <button onClick={() => navigate('/register')}>Register for Exam</button>
        <button onClick={() => navigate('/login')}>Student Login</button>
        {/* Optional: Admin Panel Link */}
        <button onClick={() => navigate('/admin')}>Admin Panel (Placeholder)</button>
      </div>
    </div>
  );
}

function App() {
  // Centralized state to pass participant data across components
  const [participantData, setParticipantData] = useState({
    participantId: null,
    registrationId: null,
    examId: null,
    scratchCardPin: null,
    examDetails: null, // Stores duration, pass_percentage etc.
    startedAt: null
  });

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/register"
            element={<RegistrationForm setParticipantData={setParticipantData} />}
          />
          <Route
            path="/login"
            element={<StudentLogin setParticipantData={setParticipantData} />}
          />
          <Route
            path="/exam-dashboard"
            element={<ExamDashboard participantData={participantData} />}
          />
          <Route
            path="/results/:participantId"
            element={<ExamResults />}
          />
          <Route
            path="/admin"
            element={<AdminPanel />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;