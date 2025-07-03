// frontend/src/components/PrivateRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const PrivateRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();

  console.log("PrivateRoute: Rendering for path.", { isAuthenticated, loading, user, allowedRoles }); // NEW LOG

  if (loading) {
    console.log("PrivateRoute: Loading authentication status."); // NEW LOG
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Checking authentication...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log("PrivateRoute: Not authenticated. Redirecting to /login."); // NEW LOG
    return <Navigate to="/login" replace />;
  }

  // Check roles only if allowedRoles is provided
  if (allowedRoles && user && !allowedRoles.includes(user.user_type)) {
    console.log(`PrivateRoute: User role '${user.user_type}' not in allowed roles [${allowedRoles.join(', ')}]. Redirecting to /dashboard.`); // NEW LOG
    return <Navigate to="/dashboard" replace />;
  }

  console.log("PrivateRoute: Authenticated and authorized. Rendering children."); // NEW LOG
  return children;
};

export default PrivateRoute;