// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { loginUser as apiLoginUser, registerUser as apiRegisterUser, getMyProfile } from '../api/auth';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // This single useEffect will handle both initial load and token changes
  useEffect(() => {
    const loadUserData = async () => {
      if (token) { // If a token exists (either from localStorage on mount or after login)
        setLoading(true); // Indicate that we are loading user data
        try {
          const profile = await getMyProfile(); // Attempt to fetch user profile
          setUser(profile); // Set user data if successful

          // Immediately after successful profile load, navigate to dashboard
          // unless we are already on the dashboard page.
          if (profile && window.location.pathname !== '/dashboard') {
            navigate('/dashboard');
          }
        } catch (error) {
          console.error('Failed to fetch user profile or validate token:', error.response?.data || error.message);
          // If fetching fails (e.g., invalid token, 401, 404), clear the token
          localStorage.removeItem('token');
          setToken(null); // This will clear the token, and thus 'user' will remain null
          setUser(null); // Ensure user is explicitly null

          // Only redirect to login if we are not already on the login page,
          // to prevent infinite redirect loops on a bad token.
          if (window.location.pathname !== '/login') {
             navigate('/login');
          }
        } finally {
          setLoading(false); // Always set loading to false after the attempt
        }
      } else { // No token exists or token was just cleared (e.g., on logout)
        setUser(null); // Ensure user is null
        setLoading(false); // Not loading anything
      }
    };

    loadUserData(); // Call the async function inside useEffect
  }, [token, navigate]); // **CRITICAL FIX**: Depend on 'token' and 'navigate'

  // Login function
  const login = async (credentials) => {
    try {
      const data = await apiLoginUser(credentials);
      localStorage.setItem('token', data.token); // Store the token from the backend response
      setToken(data.token); // Update state, which will now trigger the useEffect above
      return { success: true };
    } catch (error) {
      console.error('Login failed in AuthContext:', error);
      throw error; // Re-throw the error so LoginPage can display it
    }
  };

  // Register function (assuming it might also log in or set a token)
  const register = async (userData) => {
    try {
      const result = await apiRegisterUser(userData);
      // If registration also returns a token and logs in the user directly
      if (result.token) {
          localStorage.setItem('token', result.token);
          setToken(result.token); // This will also trigger the useEffect
      }
      return { success: true, user: result.user };
    } catch (error) {
      console.error('Registration failed in AuthContext:', error);
      throw error;
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token'); // Clear token from storage
    setToken(null); // Clear token state, triggering useEffect to clear user and redirect
    // The navigation to /login is now handled by the useEffect as well, which is cleaner.
  };

  // Conditional Rendering for Loading State
  // Displays a loading message while user data is being fetched (e.g., on initial load).
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading user data...</p>
      </div>
    );
  }

  // Define authContextValue. It's placed after the 'if (loading)' block
  // to ensure it's always defined when the component proceeds to render the Provider.
  const authContextValue = {
    user, // The current logged-in user's data
    token, // The JWT token
    isAuthenticated: !!token && !!user, // Convenience boolean: true if token and user data exist
    loading, // The current loading status of the authentication context
    login, // Function to log in a user
    register, // Function to register a new user
    logout, // Function to log out a user

    // Helper booleans to check user type for conditional rendering/access control
    isClient: user && user.user_type === 'client',
    isArtisan: user && user.user_type === 'artisan',
    isAdmin: user && user.user_type === 'admin',
  };

  // Render the AuthContext Provider, making the authContextValue available to all children.
  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook 'useAuth' to easily consume the AuthContext in any component.
export const useAuth = () => {
  const context = useContext(AuthContext);
  // Throw an error if useAuth is called outside of an AuthProvider,
  // indicating a setup issue.
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};