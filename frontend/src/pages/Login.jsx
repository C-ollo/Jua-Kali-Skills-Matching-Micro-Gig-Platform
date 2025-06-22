import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; // For redirection after login

function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const navigate = useNavigate();

  const { email, password } = formData;

  const onChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(null); // Clear errors on input change
    setSuccess(null); // Clear success message on input change
  };

  const onSubmit = async (e) => {
    e.preventDefault(); // Prevent default browser form submission

    setError(null); // Clear previous errors

    try {
      const res = await axios.post('http://localhost:5000/api/auth/login', formData);

      setSuccess(res.data.msg || 'Login successful!');

      // --- IMPORTANT: Store the JWT token in localStorage ---
      // This token will be sent with subsequent requests to protected routes
      localStorage.setItem('token', res.data.token);

      // --- Optional: Store user info (excluding sensitive data) if needed client-side ---
      // localStorage.setItem('user', JSON.stringify(res.data.user));

      // Clear the form
      setFormData({
        email: '',
        password: '',
      });

      // Redirect to a protected route (e.g., /profile or /dashboard)
      // For now, let's redirect to the Home page or a new /dashboard page later
      setTimeout(() => {
        navigate('/'); // Redirect to home for now, will change to a dashboard later
        // A full application would often reload the page or update global state here
        // to reflect the logged-in status.
        window.location.reload(); // Force reload to trigger potential global state updates (for simplicity for now)
      }, 1000); // Redirect after 1 second

    } catch (err) {
      console.error('Login error:', err.response ? err.response.data : err.message);
      // Display the error message from the backend, or a generic one
      setError(err.response ? err.response.data.msg : 'Login failed. Please try again.');
    }
  };

  return (
    <div style={{ maxWidth: '500px', margin: '0 auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <h2>Login to Jua Kali</h2>
      {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}
      {success && <p style={{ color: 'green', textAlign: 'center' }}>{success}</p>}
      <form onSubmit={onSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="email" style={{ display: 'block', marginBottom: '5px' }}>Email:</label>
          <input
            type="email"
            id="email"
            name="email"
            value={email}
            onChange={onChange}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="password" style={{ display: 'block', marginBottom: '5px' }}>Password:</label>
          <input
            type="password"
            id="password"
            name="password"
            value={password}
            onChange={onChange}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
        
        <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }}>
          Login
        </button>
      </form>
    </div>
  );
}

export default Login;