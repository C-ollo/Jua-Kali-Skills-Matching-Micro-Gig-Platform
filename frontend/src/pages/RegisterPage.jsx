// frontend/src/pages/RegisterPage.jsx
import React, { useState } from 'react';
// import { registerUser } from '../api/auth'; // No longer needed directly
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Import useAuth

function RegisterPage() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    user_type: 'client',
    location: '',
    bio: '',
    years_experience: '',
    skills: '',
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null); // Keep as null
  const navigate = useNavigate();
  const { register } = useAuth(); // Get register function from context

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError(null);

    try {
      const dataToRegister = { ...formData };
      if (dataToRegister.years_experience !== '') {
        dataToRegister.years_experience = parseInt(dataToRegister.years_experience);
      } else {
        delete dataToRegister.years_experience;
      }

      if (dataToRegister.skills) {
        dataToRegister.skills = dataToRegister.skills.split(',').map(s => s.trim()).filter(s => s);
      } else {
        dataToRegister.skills = [];
      }

      if (dataToRegister.user_type === 'client') {
        delete dataToRegister.bio;
        delete dataToRegister.years_experience;
        delete dataToRegister.skills;
        if (dataToRegister.location === '') dataToRegister.location = null;
      } else if (dataToRegister.user_type === 'artisan') {
        if (dataToRegister.location === '') {
            setError({detail: [{msg: "Location is required for artisans.", loc: ["body", "location"]}]});
            return;
        }
        if (dataToRegister.bio === '') dataToRegister.bio = null;
        if (dataToRegister.years_experience === null || isNaN(dataToRegister.years_experience)) dataToRegister.years_experience = null;
        if (dataToRegister.skills.length === 0) dataToRegister.skills = null;
      }

      const result = await register(dataToRegister); // Use context's register function
      setMessage('Registration successful! You can now log in.');
      console.log('Registration successful:', result);
      navigate('/login');
    } catch (err) {
      console.error('Registration error:', err);
      setError(err); // Set the error object for display
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">Register</h1>
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
            <label className="block text-sm font-medium text-gray-700">Full Name</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Phone Number</label>
            <input
              type="text"
              name="phone_number"
              value={formData.phone_number}
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
              value={formData.password}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">User Type</label>
            <select
              name="user_type"
              value={formData.user_type}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="client">Client</option>
              <option value="artisan">Artisan</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Location (e.g., Nairobi)</label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required={formData.user_type === 'artisan'}
            />
          </div>

          {formData.user_type === 'artisan' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">Bio</label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleChange}
                  rows="3"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                ></textarea>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Years of Experience</label>
                <input
                  type="number"
                  name="years_experience"
                  value={formData.years_experience}
                  onChange={handleChange}
                  min="0"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Skills (comma-separated, e.g., "Plumbing, Electrical")</label>
                <input
                  type="text"
                  name="skills"
                  value={formData.skills}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </>
          )}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Register
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;