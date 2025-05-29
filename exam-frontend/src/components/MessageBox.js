import React from 'react';

// Reusable component for displaying messages (info, success, error, warning)
const MessageBox = ({ message, type = 'info', onClose }) => {
  if (!message) return null; // Don't render if no message is provided

  // Define Tailwind CSS classes for different message types
  const bgColor = {
    info: 'bg-blue-100 border-blue-400 text-blue-700',
    success: 'bg-green-100 border-green-400 text-green-700',
    error: 'bg-red-100 border-red-400 text-red-700',
    warning: 'bg-yellow-100 border-yellow-400 text-yellow-700',
  }[type];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`relative ${bgColor} border rounded-lg shadow-xl p-6 max-w-sm w-full`}>
        <div className="text-lg font-semibold mb-4">{type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <p className="mb-6">{message}</p>
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-700 text-2xl font-bold"
        >
          &times; {/* Close button icon */}
        </button>
        <button
          onClick={onClose}
          className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition duration-200"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default MessageBox;