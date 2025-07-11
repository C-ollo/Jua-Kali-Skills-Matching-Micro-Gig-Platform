// frontend/src/pages/ProfilePage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getMyProfile, updateMyProfile } from '../api/auth'; // Ensure updateMyProfile is imported

const ProfilePage = () => {
  const { user, loading: authLoading, isAuthenticated, fetchUserProfile, token } = useAuth(); // Get fetchUserProfile and token
  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    location: '',
    artisan_details: {
      bio: '',
      years_experience: '',
      is_available: true, // Default or fetch from user.artisan_details
      skills: [], // Initialize as an empty array
    },
  });
  const [loading, setLoading] = useState(true); // Local loading state for fetching/updating
  const [isEditing, setIsEditing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);

  console.log("ProfilePage component is rendering!");

  // Effect to fetch profile data on mount or when user/token changes
  useEffect(() => {
    console.log("ProfilePage: useEffect (mount or user/token change). isAuthenticated:", isAuthenticated, "authLoading:", authLoading);

    const fetchProfile = async () => {
      // Only fetch if authenticated and authLoading is false
      if (isAuthenticated && !authLoading && user) {
        setLoading(true); // Start local loading
        setMessage('');
        setError(null);
        try {
          console.log("ProfilePage: Attempting to call getMyProfile()...");
          const data = await getMyProfile();
          console.log("ProfilePage: getMyProfile successful. Data:", data);
          setProfileData({
            full_name: data.full_name || '',
            email: data.email || '',
            phone_number: data.phone_number || '',
            location: data.location || '',
            artisan_details: {
              bio: data.artisan_details?.bio || '',
              years_experience: data.artisan_details?.years_experience || '',
              is_available: data.artisan_details?.is_available ?? true, // Use nullish coalescing for boolean
              skills: data.artisan_details?.skills || [], // Ensure skills is an array
            },
          });
        } catch (err) {
          console.error('ProfilePage: Error fetching profile:', err);
          setError(err);
          setMessage('Failed to load profile. Please try again.');
        } finally {
          setLoading(false); // End local loading
        }
      } else if (!isAuthenticated && !authLoading) {
        // If not authenticated after auth loading, consider redirecting or showing login prompt
        // (Though PrivateRoute should handle this, good to log)
        console.log("ProfilePage: Not authenticated after auth loading. Cannot fetch profile.");
        setLoading(false); // Stop loading if not authenticated
      }
    };

    fetchProfile();

    return () => {
      console.log("ProfilePage: useEffect (cleanup/unmount).");
    };
  }, [isAuthenticated, authLoading, user, token]); // Re-run if these context values change

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (name in profileData) {
      // For top-level fields
      setProfileData((prev) => ({ ...prev, [name]: value }));
    } else if (name in profileData.artisan_details) {
      // For nested artisan_details fields
      setProfileData((prev) => ({
        ...prev,
        artisan_details: {
          ...prev.artisan_details,
          [name]: type === 'checkbox' ? checked : value,
        },
      }));
    } else if (name === 'skills_input') {
      // Special handling for skills input if it's a single string
      setProfileData((prev) => ({
        ...prev,
        artisan_details: {
          ...prev.artisan_details,
          // Split by comma and trim each skill
          skills: value.split(',').map(s => s.trim()).filter(s => s !== ''),
        },
      }));
    }
  };

  const handleEditToggle = () => {
    setIsEditing((prev) => !prev);
    setMessage(''); // Clear messages when toggling edit mode
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); // Start local loading for update
    setMessage('');
    setError(null);

    try {
      // Construct the data payload for the API
      const dataToUpdate = {
        full_name: profileData.full_name,
        email: profileData.email,
        phone_number: profileData.phone_number,
        location: profileData.location,
      };

      // Conditionally add artisan_details if the user is an artisan
      if (user && user.user_type === 'artisan') {
        dataToUpdate.artisan_details = {
          bio: profileData.artisan_details.bio,
          years_experience: parseInt(profileData.artisan_details.years_experience) || 0, // Ensure it's an int
          is_available: profileData.artisan_details.is_available,
          skills: profileData.artisan_details.skills, // Send as array of strings
        };
      }

      console.log("ProfilePage: Sending update payload:", dataToUpdate);
      const updatedProfile = await updateMyProfile(dataToUpdate);
      console.log("ProfilePage: Profile update successful. New data:", updatedProfile);

      setMessage('Profile updated successfully!');
      setError(null);
      setIsEditing(false); // Exit edit mode after successful update

      // IMPORTANT: Update AuthContext's user state to reflect changes
      // This will trigger re-renders in components using useAuth, like Navbar
      // For this to work, you might need an `updateUser` function in AuthContext
      // or simply refetch the user profile using the existing `fetchUserProfile`
      fetchUserProfile(token); // Re-fetch the user profile to update context

    } catch (err) {
      console.error('ProfilePage: Error updating profile:', err);
      setError(err);
      setMessage(`Failed to update profile: ${err.detail || err.message || 'Unknown error'}`);
    } finally {
      setLoading(false); // End local loading
    }
  };

  if (authLoading || loading) { // Check both AuthContext loading and local loading
    console.log("ProfilePage: Returning loading spinner due to authLoading or local loading.");
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading profile data...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    console.log("ProfilePage: Not authenticated or user not available after loading. Displaying message.");
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Please log in to view your profile.</p>
      </div>
    );
  }

  // Determine if it's an artisan for conditional rendering
  const isArtisan = user.user_type === 'artisan';

  return (
    <div className="min-h-screen bg-gray-50 p-6 flex justify-center items-start">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-2xl mt-8">
        <h2 className="text-3xl font-extrabold text-gray-900 mb-6 text-center">Your Profile</h2>

        {message && (
          <div className={`p-3 mb-4 rounded-md ${error ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
          </div>
        )}

        <div className="text-right mb-4">
          <button
            onClick={handleEditToggle}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {isEditing ? 'Cancel Edit' : 'Edit Profile'}
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* General User Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              {isEditing ? (
                <input
                  type="text"
                  name="full_name"
                  value={profileData.full_name}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="mt-1 text-gray-900">{profileData.full_name}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              {isEditing ? (
                <input
                  type="email"
                  name="email"
                  value={profileData.email}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="mt-1 text-gray-900">{profileData.email}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Phone Number</label>
              {isEditing ? (
                <input
                  type="text"
                  name="phone_number"
                  value={profileData.phone_number}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="mt-1 text-gray-900">{profileData.phone_number}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Location</label>
              {isEditing ? (
                <input
                  type="text"
                  name="location"
                  value={profileData.location}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="mt-1 text-gray-900">{profileData.location}</p>
              )}
            </div>
          </div>

          {/* Artisan Specific Details (conditionally rendered) */}
          {isArtisan && (
            <div className="border-t border-gray-200 pt-6 mt-6">
              <h3 className="text-2xl font-semibold text-gray-800 mb-4">Artisan Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Bio</label>
                  {isEditing ? (
                    <textarea
                      name="bio"
                      value={profileData.artisan_details.bio}
                      onChange={handleChange}
                      rows="3"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    ></textarea>
                  ) : (
                    <p className="mt-1 text-gray-900">{profileData.artisan_details.bio || 'N/A'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Years Experience</label>
                  {isEditing ? (
                    <input
                      type="number"
                      name="years_experience"
                      value={profileData.artisan_details.years_experience}
                      onChange={handleChange}
                      min="0"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : (
                    <p className="mt-1 text-gray-900">{profileData.artisan_details.years_experience || '0'} years</p>
                  )}
                </div>
                <div className="col-span-1 md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Skills (comma-separated)</label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="skills_input" // Use a distinct name for the input
                      value={profileData.artisan_details.skills.join(', ')} // Join array for display
                      onChange={handleChange}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : (
                    <p className="mt-1 text-gray-900">{profileData.artisan_details.skills.join(', ') || 'N/A'}</p>
                  )}
                </div>
                <div className="col-span-1 md:col-span-2 flex items-center">
                    {isEditing ? (
                        <>
                            <input
                                type="checkbox"
                                name="is_available"
                                id="is_available"
                                checked={profileData.artisan_details.is_available}
                                onChange={handleChange}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <label htmlFor="is_available" className="ml-2 block text-sm text-gray-900">
                                Available for Jobs
                            </label>
                        </>
                    ) : (
                        <p className="mt-1 text-gray-900">
                            Status: <span className={`font-semibold ${profileData.artisan_details.is_available ? 'text-green-600' : 'text-red-600'}`}>
                                {profileData.artisan_details.is_available ? 'Available' : 'Not Available'}
                            </span>
                        </p>
                    )}
                </div>
              </div>
            </div>
          )}

          {isEditing && (
            <div className="mt-8 flex justify-end">
              <button
                type="submit"
                className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                disabled={loading} // Disable button while loading
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;