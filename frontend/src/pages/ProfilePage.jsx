// frontend/src/pages/ProfilePage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getMyProfile, updateMyProfile } from '../api/auth';
import { useNavigate } from 'react-router-dom';
import ClipLoader from 'react-spinners/ClipLoader';

function ProfilePage() {
  console.log("ProfilePage component is rendering!");
  const { user, loading: authLoading, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    location: '',
    artisan_details: {
      bio: '',
      years_experience: 0,
      is_available: true,
      skills: [],
    },
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  console.log("ProfilePage: Current profileData state during render (top of component):", profileData);

  const fetchProfile = useCallback(async () => {
    console.log("fetchProfile: Function initiated.");
    console.log("fetchProfile: isAuthenticated:", isAuthenticated, "authLoading:", authLoading);

    if (!isAuthenticated || authLoading) {
      if (!authLoading && !isAuthenticated) {
        console.log("fetchProfile: Not authenticated or still loading auth context. Redirecting to login.");
        navigate('/login');
      } else {
        console.log("fetchProfile: Waiting for authentication context to finish loading.");
      }
      return;
    }

    setLoading(true);
    setError(null);
    try {
      console.log("fetchProfile: Attempting to call getMyProfile()...");
      const data = await getMyProfile();
      console.log("fetchProfile: getMyProfile() response data:", data);

      setProfileData({
        full_name: data.full_name || '',
        email: data.email || '',
        phone_number: data.phone_number || '',
        location: data.location || '',
        artisan_details: {
          bio: data.artisan_details?.bio || '',
          years_experience: data.artisan_details?.years_experience || 0,
          is_available: data.artisan_details?.is_available !== undefined ? data.artisan_details.is_available : true,
          skills: data.skills || [],
        },
      });
      // TEMPORARY DELAY REMOVED
      // console.log("ProfilePage: Data fetched and state set. Introducing a 5-second delay to observe.");
      // await new Promise(resolve => setTimeout(resolve, 5000));
    } catch (err) {
      console.error('fetchProfile: Failed to fetch profile (caught error):', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load profile.');
    } finally {
      setLoading(false);
      console.log("fetchProfile: finished. setLoading(false).");
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Effect to fetch profile data
  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // New Effect for component mount/unmount logging
  useEffect(() => {
    console.log("ProfilePage: useEffect (mount). User type:", user?.user_type, " isAuthenticated:", isAuthenticated);
    return () => {
      console.log("ProfilePage: useEffect (unmount).");
    };
  }, [user, isAuthenticated]); // Dependencies to re-log if user or isAuthenticated changes

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith('artisan_details.')) {
      const field = name.split('.')[1];
      setProfileData((prev) => ({
        ...prev,
        artisan_details: {
          ...prev.artisan_details,
          [field]: field === 'years_experience' ? parseInt(value) || 0 : value,
        },
      }));
    } else if (name === 'is_available') {
        setProfileData((prev) => ({
            ...prev,
            artisan_details: {
              ...prev.artisan_details,
              is_available: e.target.checked,
            },
          }));
    }
    else if (name === 'skills') {
      setProfileData((prev) => ({
        ...prev,
        artisan_details: {
            ...prev.artisan_details,
            skills: value.split(',').map(s => s.trim()).filter(s => s !== ''),
        },
      }));
    } else {
      setProfileData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const dataToUpdate = {
        full_name: profileData.full_name,
        email: profileData.email,
        phone_number: profileData.phone_number,
        location: profileData.location,
      };

      if (user?.user_type === 'artisan') {
        dataToUpdate.artisan_details = {
          bio: profileData.artisan_details.bio,
          years_experience: profileData.artisan_details.years_experience,
          is_available: profileData.artisan_details.is_available,
          skills: profileData.artisan_details.skills,
        };
      }
      console.log("handleSubmit: Data being sent for update:", dataToUpdate);
      const updatedUser = await updateMyProfile(dataToUpdate);
      console.log("handleSubmit: Update successful, response:", updatedUser);
      setMessage('Profile updated successfully!');
      setIsEditing(false);
      await fetchProfile();
    } catch (err) {
      console.error('handleSubmit: Failed to update profile (caught error):', err);
      setError(err.response?.data?.detail || err.message || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    console.log("ProfilePage: Returning loading spinner due to authLoading or local loading.");
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <ClipLoader size={50} color={"#1a73e8"} loading={true} />
        <p className="ml-3 text-xl text-gray-700">Loading profile...</p>
      </div>
    );
  }

  // Fallback if user is somehow null at this point
  if (!user) {
    console.log("ProfilePage: DEBUG: user is null at this point, value:", user);
    console.log("ProfilePage: User object is null after loading. Redirecting to /login.");
    navigate('/login');
    return null;
  }

  console.log("ProfilePage: About to render full profile JSX."); // New log before actual JSX return
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-3xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">My Profile</h1>

        {message && (
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4" role="alert">
            <p>{message}</p>
          </div>
        )}
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
            <p>Error: {error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* General User Information */}
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">Full Name</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={profileData.full_name}
              onChange={handleChange}
              readOnly={!isEditing}
              className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={profileData.email}
              onChange={handleChange}
              readOnly={!isEditing}
              className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>
          <div>
            <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700">Phone Number</label>
            <input
              type="text"
              id="phone_number"
              name="phone_number"
              value={profileData.phone_number}
              onChange={handleChange}
              readOnly={!isEditing}
              className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700">Location</label>
            <input
              type="text"
              id="location"
              name="location"
              value={profileData.location}
              onChange={handleChange}
              readOnly={!isEditing}
              className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            />
          </div>

          {/* Artisan Specific Information (Conditionally Rendered) */}
          {user?.user_type === 'artisan' && (
            <div className="pt-4 border-t border-gray-200 mt-6">
              <h2 className="text-xl font-bold text-gray-700 mb-4">Artisan Details</h2>
              <div>
                <label htmlFor="artisan_details.bio" className="block text-sm font-medium text-gray-700">Bio</label>
                <textarea
                  id="artisan_details.bio"
                  name="artisan_details.bio"
                  value={profileData.artisan_details.bio}
                  onChange={handleChange}
                  readOnly={!isEditing}
                  rows="3"
                  className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
                ></textarea>
              </div>
              <div>
                <label htmlFor="artisan_details.years_experience" className="block text-sm font-medium text-gray-700">Years of Experience</label>
                <input
                  type="number"
                  id="artisan_details.years_experience"
                  name="artisan_details.years_experience"
                  value={profileData.artisan_details.years_experience}
                  onChange={handleChange}
                  readOnly={!isEditing}
                  min="0"
                  className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
                />
              </div>
              <div className="flex items-center mt-2">
                <input
                  type="checkbox"
                  id="is_available"
                  name="is_available"
                  checked={profileData.artisan_details.is_available}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_available" className="ml-2 block text-sm font-medium text-gray-700">Available for Work</label>
              </div>
              <div>
                <label htmlFor="artisan_details.skills" className="block text-sm font-medium text-gray-700">Skills (comma-separated)</label>
                <input
                  type="text"
                  id="artisan_details.skills"
                  name="skills"
                  value={profileData.artisan_details.skills.join(', ')}
                  onChange={handleChange}
                  readOnly={!isEditing}
                  className={`mt-1 block w-full px-3 py-2 border ${isEditing ? 'border-gray-300' : 'border-transparent'} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
                  placeholder="e.g., Plumbing, Electrical, Carpentry"
                />
              </div>
            </div>
          )}

          <div className="flex justify-end gap-4 mt-6">
            {!isEditing && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
              >
                Edit Profile
              </button>
            )}

            {isEditing && (
              <>
                <button
                  type="submit"
                  className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    setLoading(true);
                    fetchProfile();
                  }}
                  className="bg-gray-400 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-md transition duration-300"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </form>

        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-blue-600 hover:text-blue-800 font-semibold py-2 px-4 rounded-md"
          >
            Back to Dashboard
          </button>
          <button
            onClick={logout}
            className="ml-4 bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-6 rounded-md transition duration-300"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;