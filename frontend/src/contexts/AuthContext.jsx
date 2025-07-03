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

  // Function to fetch and set user profile (THIS IS THE FUNCTION)
  const fetchUserProfile = async (authToken) => {
    if (!authToken) {
      setUser(null);
      setLoading(false);
      console.log("AuthContext: fetchUserProfile completed (no token). User null, Loading false."); // ADDED LOG
      return;
    }
    try {
      const profile = await getMyProfile();
      setUser(profile);
      console.log("AuthContext: fetchUserProfile SUCCESS. User set, profile:", profile); // ADDED LOG
    } catch (error) {
      console.error('Failed to fetch user profile:', error.response?.data || error.message);
      // If token is invalid/expired, clear it and redirect to login
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      // Explicitly navigate to login if the error indicates invalid token (e.g., 401, 404)
      if (error.response?.status === 401 || error.response?.status === 404) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
      console.log("AuthContext: fetchUserProfile finally block. Loading set to false."); // ADDED LOG
    }
  };

  // Effect to run on initial load or when token changes to check for existing token
  useEffect(() => {
    console.log("AuthContext useEffect: token changed or initial load. Token:", token);
    fetchUserProfile(token);
  }, [token]); // This effect runs whenever the token state changes

  // Function to handle user login
  const login = async (credentials) => {
    try {
      setLoading(true); // Indicate loading when login starts
      const response = await apiLoginUser(credentials);
      localStorage.setItem('token', response.access_token);
      setToken(response.access_token);
      // No need to fetch profile here; the useEffect for token will trigger fetchUserProfile
      navigate('/dashboard'); // Navigate to dashboard after successful login
    } catch (error) {
      console.error('Login failed in AuthContext:', error);
      throw error; // Re-throw to be caught by the login page
    } finally {
        // setLoading(false); // Do not set loading false here; let fetchUserProfile handle it after token update
    }
  };

  // Function to handle user registration
  const register = async (userData) => {
    try {
      setLoading(true); // Indicate loading when register starts
      const response = await apiRegisterUser(userData);
      // For registration, directly log in the user if successful
      // Or simply navigate to login page
      localStorage.setItem('token', response.access_token); // Assuming register returns a token
      setToken(response.access_token);
      navigate('/dashboard'); // Redirect to dashboard after successful registration and login
      return response;
    } catch (error) {
      console.error('Registration failed in AuthContext:', error);
      throw error;
    } finally {
        // setLoading(false); // Do not set loading false here; let fetchUserProfile handle it after token update
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    navigate('/login'); // Redirect to login page after logout
  };

  // --- Start of conditional rendering for initial AuthProvider loading state ---
  // This ensures the app doesn't render until authentication status is known
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading user data...</p>
      </div>
    );
  }
  // --- End of conditional rendering for initial AuthProvider loading state ---

  const authContextValue = {
    user,
    token,
    isAuthenticated: !!token && !!user, // True if token and user data exist
    loading, // Make sure loading is always available
    login,
    register,
    logout,
    // Helper to check user type
    isClient: user && user.user_type === 'client',
    isArtisan: user && user.user_type === 'artisan',
    isAdmin: user && user.user_type === 'admin',
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the AuthContext
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};