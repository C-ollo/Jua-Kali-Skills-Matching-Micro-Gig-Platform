import React, { useState } from 'react';
import axios from 'axios'; // <--- IMPORT AXIOS
import { useNavigate } from 'react-router-dom'; // <--- IMPORT useNavigate for redirection

function Register() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    user_type: 'client', // Default to client
    location: '',
    bio: '',
    years_experience: '',
    skills: [], // Array to hold selected skills (for artisans)
  });

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const navigate = useNavigate(); // Hook to get the navigate function

  // Destructure formData for easier access
  const { full_name, email, phone_number, password, user_type, location, bio, years_experience, skills } = formData;

  // Handle changes for all input fields
  const onChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(null); // Clear errors on input change
    setSuccess(null); // Clear success message on input change
  };

  // Handle skill selection for artisans (simple comma-separated string for now)
  const onSkillsChange = (e) => {
    setFormData({ ...formData, skills: e.target.value.split(',').map(s => s.trim()).filter(s => s !== '') });
  };

  // Handle form submission
  const onSubmit = async (e) => {
    e.preventDefault(); // Prevent default browser form submission

    setError(null); // Clear previous errors

    // Client-side validation (basic)
    if (user_type === 'artisan' && (!location || !bio || skills.length === 0)) {
        setError('Artisan registration requires location, bio, and at least one skill.');
        return;
    }
    if (password.length < 6) {
        setError('Password must be at least 6 characters long.');
        return;
    }

    try {
      // Prepare data for the backend, only sending relevant fields
      const dataToSend = {
        full_name,
        email,
        phone_number,
        password,
        user_type,
        location: user_type === 'artisan' ? location : '', // Only send location if artisan
      };

      if (user_type === 'artisan') {
        dataToSend.bio = bio;
        dataToSend.years_experience = parseInt(years_experience); // Ensure it's a number
        dataToSend.skills = skills;
      }

      const res = await axios.post('http://localhost:5000/api/auth/register', dataToSend);

      setSuccess(res.data.msg || 'Registration successful!');
      // Optionally clear form or redirect after success
      setFormData({
        full_name: '',
        email: '',
        phone_number: '',
        password: '',
        user_type: 'client',
        location: '',
        bio: '',
        years_experience: '',
        skills: [],
      });
      // Redirect to login page after a short delay
      setTimeout(() => {
        navigate('/login');
      }, 2000); // Redirect after 2 seconds
      
    } catch (err) {
      console.error('Registration error:', err.response ? err.response.data : err.message);
      setError(err.response ? err.response.data.msg : 'Server error during registration.');
    }
  };

  return (
    <div style={{ maxWidth: '500px', margin: '0 auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <h2>Register for Jua Kali</h2>
      {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}
      {success && <p style={{ color: 'green', textAlign: 'center' }}>{success}</p>}
      <form onSubmit={onSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="full_name" style={{ display: 'block', marginBottom: '5px' }}>Full Name:</label>
          <input
            type="text"
            id="full_name"
            name="full_name"
            value={full_name}
            onChange={onChange}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
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
          <label htmlFor="phone_number" style={{ display: 'block', marginBottom: '5px' }}>Phone Number (M-Pesa):</label>
          <input
            type="text"
            id="phone_number"
            name="phone_number"
            value={phone_number}
            onChange={onChange}
            required
            pattern="[0-9]{10,}" // Basic pattern for phone numbers (at least 10 digits)
            title="Please enter a valid phone number (digits only, e.g., 2547XXXXXXXX)"
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
            minLength="6"
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="user_type" style={{ display: 'block', marginBottom: '5px' }}>I am a:</label>
          <select
            id="user_type"
            name="user_type"
            value={user_type}
            onChange={onChange}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
          >
            <option value="client">Client</option>
            <option value="artisan">Artisan</option>
          </select>
        </div>

        {/* Conditional fields for Artisans */}
        {user_type === 'artisan' && (
          <>
            <div style={{ marginBottom: '15px' }}>
              <label htmlFor="location" style={{ display: 'block', marginBottom: '5px' }}>Location:</label>
              <input
                type="text"
                id="location"
                name="location"
                value={location}
                onChange={onChange}
                required={user_type === 'artisan'}
                placeholder="e.g., Nairobi - CBD, Kisumu - Milimani"
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label htmlFor="bio" style={{ display: 'block', marginBottom: '5px' }}>Bio/Description:</label>
              <textarea
                id="bio"
                name="bio"
                value={bio}
                onChange={onChange}
                required={user_type === 'artisan'}
                rows="4"
                placeholder="Tell us about your skills and experience..."
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
              ></textarea>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label htmlFor="years_experience" style={{ display: 'block', marginBottom: '5px' }}>Years of Experience:</label>
              <input
                type="number"
                id="years_experience"
                name="years_experience"
                value={years_experience}
                onChange={onChange}
                min="0"
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label htmlFor="skills" style={{ display: 'block', marginBottom: '5px' }}>Skills (comma-separated):</label>
              <input
                type="text"
                id="skills"
                name="skills"
                value={skills.join(', ')} // Display array as comma-separated string
                onChange={onSkillsChange} // Use specific handler for skills
                required={user_type === 'artisan'}
                placeholder="e.g., Plumbing, Electrical Repair, Carpentry"
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box', border: '1px solid #ddd', borderRadius: '4px' }}
              />
              <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
                Enter skills exactly as they appear in your backend's `skills` table (e.g., "Plumbing", "Electrical Repair", "Carpentry").
              </small>
            </div>
          </>
        )}

        <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }}>
          Register
        </button>
      </form>
    </div>
  );
}

export default Register;