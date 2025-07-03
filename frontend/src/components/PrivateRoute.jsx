// frontend/src/components/PrivateRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Import useAuth

const PrivateRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Checking authentication...</p>
      </div>
    ); // Or a loading spinner
  }

  if (!isAuthenticated) {
    // Not authenticated, redirect to login page
    return <Navigate to="/login" replace />;
  }

  // If allowedRoles are specified, check user's role
  if (allowedRoles && user && !allowedRoles.includes(user.user_type)) {
    console.warn(`Access denied for user type '${user.user_type}'. Required roles: ${allowedRoles.join(', ')}`);
    // If authenticated but not authorized for this role, redirect to a dashboard or unauthorized page
    return <Navigate to="/dashboard" replace />; // Or a specific /unauthorized page
  }

  return children; // If authenticated and authorized, render the child components
};

export default PrivateRoute;