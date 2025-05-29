import React, { useState } from 'react';
import MessageBox from './MessageBox'; // Import the MessageBox component

const RegistrationForm = ({ onRegisterSuccess }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [scratchCardPin, setScratchCardPin] = useState('');
  const [studentPin, setStudentPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState('info');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null); // Clear previous messages

    // Client-side validation for student PIN (4 digits, numeric)
    if (studentPin.length !== 4 || !/^\d+$/.test(studentPin)) {
      setMessage('Student PIN must be exactly 4 digits.');
      setMessageType('error');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/api/register_for_exam', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, scratch_card_pin: scratchCardPin, student_pin: studentPin }),
      });
      const data = await response.json();

      if (response.ok) {
        setMessage(`Registration successful! Your Exam Code is: ${data.exam_code} and your Login PIN is: ${data.your_login_pin}. Please remember these for login.`);
        setMessageType('success');
        onRegisterSuccess(data); // Call parent callback to update auth context
      } else {
        setMessage(data.error || data.message || 'Registration failed.');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Registration error:', error);
      setMessage('Network error or server is unreachable. Please check your backend server.');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-xl border border-gray-200 mt-10">
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Register for Exam</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <div>
          <label htmlFor="scratchCardPin" className="block text-sm font-medium text-gray-700 mb-1">Scratch Card PIN</label>
          <input
            type="text"
            id="scratchCardPin"
            value={scratchCardPin}
            onChange={(e) => setScratchCardPin(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <div>
          <label htmlFor="studentPin" className="block text-sm font-medium text-gray-700 mb-1">Create 4-Digit PIN</label>
          <input
            type="password"
            id="studentPin"
            value={studentPin}
            onChange={(e) => setStudentPin(e.target.value)}
            maxLength="4"
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out"
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={loading}
        >
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <MessageBox message={message} type={messageType} onClose={() => setMessage(null)} />
    </div>
  );
};

export default RegistrationForm;