// frontend/src/api/auth.js
import api from './axios';

export const registerUser = async (userData) => {
  try {
    const response = await api.post('/auth/register', userData);
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const loginUser = async (credentials) => {
  try {
    // Corrected: Send a JSON object with 'email' and 'password'
    // Axios will automatically set Content-Type to application/json
    const response = await api.post('/auth/login', { // Corrected path and data format
      email: credentials.email,
      password: credentials.password
    });
    return response.data; // Returns token data (access_token, token_type)
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getMyProfile = async () => {
    try {
        const response = await api.get('/auth/me');
        return response.data;
    } catch (error) {
        throw error.response?.data || error.message;
    }
};