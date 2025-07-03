// frontend/src/api/axios.js
import axios from 'axios';

// Base URL for your FastAPI backend
// Make sure this matches where your backend is running
const API_BASE_URL = 'http://localhost:5000/api'; // Your FastAPI backend URL

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// You can add interceptors here later for things like authentication tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token'); // Get token from local storage
    if (token) {
      config.headers.Authorization = `Bearer ${token}`; // Attach token to every request
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional: Add a response interceptor to handle token expiry or other global errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Example: If 401 Unauthorized due to expired token, redirect to login
    if (error.response && error.response.status === 401 && error.response.config.url !== '/auth/token') {
      // You might want a more robust way to handle this, e.g., using React Context
      console.error("Unauthorized: Token might be expired or invalid. Redirecting to login...");
      // window.location.href = '/login'; // Or use navigate from react-router-dom
    }
    return Promise.reject(error);
  }
);


export default api;
