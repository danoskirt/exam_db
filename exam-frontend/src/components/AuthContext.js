import React, { createContext, useState } from 'react';

// Create a context for authentication state
export const AuthContext = createContext(null);

// AuthProvider component to wrap your application and provide auth state
export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [participantId, setParticipantId] = useState(null);
  const [registrationId, setRegistrationId] = useState(null);
  const [examId, setExamId] = useState(null);
  const [examCode, setExamCode] = useState(null);
  const [examName, setExamName] = useState(null);
  const [durationMinutes, setDurationMinutes] = useState(null);
  const [passPercentage, setPassPercentage] = useState(null);
  const [startedAt, setStartedAt] = useState(null); // Timestamp when exam started
  const [submittedAt, setSubmittedAt] = useState(null); // Timestamp when exam submitted
  const [participantName, setParticipantName] = useState(null);
  const [participantEmail, setParticipantEmail] = useState(null);

  // Function to update authentication state upon successful login/registration
  const login = (data) => {
    setIsLoggedIn(true);
    setParticipantId(data.participant_id);
    setRegistrationId(data.registration_id);
    setExamId(data.exam_id);
    setExamCode(data.exam_code);
    setExamName(data.exam_name);
    setDurationMinutes(data.duration_minutes);
    setPassPercentage(data.pass_percentage);
    setStartedAt(data.started_at);
    setSubmittedAt(data.submitted_at);
    setParticipantName(data.participant_name);
    setParticipantEmail(data.participant_email);
  };

  // Function to clear authentication state upon logout
  const logout = () => {
    setIsLoggedIn(false);
    setParticipantId(null);
    setRegistrationId(null);
    setExamId(null);
    setExamCode(null);
    setExamName(null);
    setDurationMinutes(null);
    setPassPercentage(null);
    setStartedAt(null);
    setSubmittedAt(null);
    setParticipantName(null);
    setParticipantEmail(null);
  };

  // Functions to update specific time-related states
  const updateStartedAt = (time) => setStartedAt(time);
  const updateSubmittedAt = (time) => setSubmittedAt(time);

  // The value object provided to consumers of this context
  const value = {
    isLoggedIn,
    participantId,
    registrationId,
    examId,
    examCode,
    examName,
    durationMinutes,
    passPercentage,
    startedAt,
    submittedAt,
    participantName,
    participantEmail,
    login,
    logout,
    updateStartedAt,
    updateSubmittedAt,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};