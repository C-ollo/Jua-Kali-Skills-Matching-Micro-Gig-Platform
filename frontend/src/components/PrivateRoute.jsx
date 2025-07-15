// frontend/src/components/PrivateRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const PrivateRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-secondary">
        <p className="text-xl text-brand-text-primary">Checking authentication...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.user_type)) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-brand-secondary p-4">
        <p className="text-xl text-red-500 mb-4">Access Denied: You do not have permission to view this page.</p>
        <button
          onClick={() => window.history.back()} // Go back to the previous page
          className="bg-brand-primary hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-md transition duration-300"
        >
          Go Back
        </button>
      </div>
    );
  }

  return children;
};

export default PrivateRoute;