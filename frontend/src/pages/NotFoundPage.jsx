// frontend/src/src/pages/NotFoundPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';

function NotFoundPage() {
  return (
    <div className="min-h-screen bg-red-100 flex flex-col items-center justify-center text-red-800">
      <h1 className="text-6xl font-bold mb-4">404</h1>
      <p className="text-xl mb-8">Page Not Found</p>
      <Link to="/" className="text-blue-600 hover:underline">
        Go to Home
      </Link>
    </div>
  );
}

export default NotFoundPage;