import React, { useState } from 'react';
import MessageBox from './MessageBox'; // Import the MessageBox component

const LoginForm = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [studentPin, setStudentPin] = useState('');
  const [examCode, setExamCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState('info');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    // Client-side validation for student PIN (4 digits, numeric)
    if (studentPin.length !== 4 || !/^\d+$/.test(studentPin)) {
      setMessage('Student PIN must be exactly 4 digits.');
      setMessageType('error');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/api/student_login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, student_pin: studentPin, exam_code: examCode }),
      });
      const data = await response.json();

      if (response.ok) {
        setMessage('Login successful!');
        setMessageType('success');
        onLoginSuccess(data); // Call parent callback to update auth context
      } else {
        setMessage(data.error || 'Login failed.');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Login error:', error);
      setMessage('Network error or server is unreachable. Please check your backend server.');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-xl border border-gray-200 mt-10">
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Student Login</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="loginEmail" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            id="loginEmail"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <div>
          <label htmlFor="loginStudentPin" className="block text-sm font-medium text-gray-700 mb-1">4-Digit PIN</label>
          <input
            type="password"
            id="loginStudentPin"
            value={studentPin}
            onChange={(e) => setStudentPin(e.target.value)}
            maxLength="4"
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <div>
          <label htmlFor="loginExamCode" className="block text-sm font-medium text-gray-700 mb-1">5-Digit Exam Code</label>
          <input
            type="text"
            id="loginExamCode"
            value={examCode}
            onChange={(e) => setExamCode(e.target.value)}
            maxLength="5"
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={loading}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <MessageBox message={message} type={messageType} onClose={() => setMessage(null)} />
    </div>
  );
};

export default LoginForm;