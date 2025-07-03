// frontend/src/pages/LoginPage.jsx
import React, { useState } from 'react';
// import { loginUser } from '../api/auth'; // No longer needed directly
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Import useAuth

function LoginPage() {
  const [credentials, setCredentials] = useState({
    email: '',
    password: '',
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null); // Keep as null
  const navigate = useNavigate();
  const { login } = useAuth(); // Get login function from context

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials((prevCreds) => ({ ...prevCreds, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError(null); // Clear previous errors

    try {
      await login(credentials); // Use context's login function
      setMessage('Login successful!'); // This message might not be seen due to redirect
      // navigate('/dashboard'); // Redirection is handled by AuthContext now
    } catch (err) {
      console.error('Login error:', err);
      setError(err); // Set the error object for display
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">Login</h1>
        {message && <p className="text-green-600 text-center mb-4">{message}</p>}

        {error && (
          <div className="text-red-600 text-center mb-4 p-2 border border-red-300 bg-red-50 rounded">
            {typeof error === 'string' ? (
              error
            ) : (
              Array.isArray(error.detail) ? (
                <ul className="list-disc list-inside text-left">
                  {error.detail.map((errItem, index) => (
                    <li key={index}>
                      {errItem.loc && errItem.loc.length > 1 ? `${errItem.loc[1]}: ` : ''}
                      {errItem.msg}
                    </li>
                  ))}
                </ul>
              ) : (
                'An unexpected error occurred. ' + (error.message || JSON.stringify(error))
              )
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              value={credentials.email}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Login
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;