import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getMyProfile, updateMyProfile } from '../api/auth';
import { useNavigate, Link } from 'react-router-dom';

const ProfilePage = () => {
  const { user, loading: authLoading, isAuthenticated, fetchUserProfile, token, logout } = useAuth();
  const navigate = useNavigate();
  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    location: '',
    artisan_details: {
      bio: '',
      years_experience: '',
      is_available: true,
      skills: [],
    },
  });
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [reviewsError, setReviewsError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      if (isAuthenticated && !authLoading && user) {
        setLoading(true);
        setMessage('');
        setError(null);
        try {
          const data = await getMyProfile();
          setProfileData({
            full_name: data.full_name || '',
            email: data.email || '',
            phone_number: data.phone_number || '',
            location: data.location || '',
            artisan_details: {
              bio: data.artisan_details?.bio || '',
              years_experience: data.artisan_details?.years_experience || '',
              is_available: data.artisan_details?.is_available ?? true,
              skills: data.artisan_details?.skills || [],
            },
          });
        } catch (err) {
          console.error('ProfilePage: Error fetching profile:', err);
          setError(err);
          setMessage('Failed to load profile. Please try again.');
        } finally {
          setLoading(false);
        }
      } else if (!isAuthenticated && !authLoading) {
        setLoading(false);
      }
    };

    fetchProfile();

    return () => {
      // Cleanup function
    };
  }, [isAuthenticated, authLoading, user, token]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (name in profileData) {
      setProfileData((prev) => ({ ...prev, [name]: value }));
    } else if (name in profileData.artisan_details) {
      setProfileData((prev) => ({
        ...prev,
        artisan_details: {
          ...prev.artisan_details,
          [name]: type === 'checkbox' ? checked : value,
        },
      }));
    } else if (name === 'skills_input') {
      setProfileData((prev) => ({
        ...prev,
        artisan_details: {
          ...prev.artisan_details,
          skills: value.split(',').map(s => s.trim()).filter(s => s !== ''),
        },
      }));
    }
  };

  const handleEditToggle = () => {
    setIsEditing((prev) => !prev);
    setMessage('');
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError(null);

    try {
      const dataToUpdate = {
        full_name: profileData.full_name,
        email: profileData.email,
        phone_number: profileData.phone_number,
        location: profileData.location,
      };

      if (user && user.user_type === 'artisan') {
        dataToUpdate.artisan_details = {
          bio: profileData.artisan_details.bio,
          years_experience: parseInt(profileData.artisan_details.years_experience) || 0,
          is_available: profileData.artisan_details.is_available,
          skills: profileData.artisan_details.skills,
        };
      }

      const updatedProfile = await updateMyProfile(dataToUpdate);

      setMessage('Profile updated successfully!');
      setError(null);
      setIsEditing(false);

      fetchUserProfile(token);

    } catch (err) {
      console.error('ProfilePage: Error updating profile:', err);
      setError(err);
      setMessage(`Failed to update profile: ${err.detail || err.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading profile data...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Please log in to view your profile.</p>
      </div>
    );
  }

  const isArtisan = user.user_type === 'artisan';

  return (
    <div className="relative flex size-full min-h-screen flex-col bg-white group/design-root overflow-x-hidden">
      <div className="layout-container flex h-full grow flex-col">
        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#f5f1f0] px-10 py-3">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 text-[#181211] cursor-pointer" onClick={() => navigate('/home')}>
              <div className="size-4">
                <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <g clipPath="url(#clip0_6_543)">
                    <path
                      d="M42.1739 20.1739L27.8261 5.82609C29.1366 7.13663 28.3989 10.1876 26.2002 13.7654C24.8538 15.9564 22.9595 18.3449 20.6522 20.6522C18.3449 22.9595 15.9564 24.8538 13.7654 26.2002C10.1876 28.3989 7.13663 29.1366 5.82609 27.8261L20.1739 42.1739C21.4845 43.4845 24.5355 42.7467 28.1133 40.548C30.3042 39.2016 32.6927 37.3073 35 35C37.3073 32.6927 39.2016 30.3042 40.548 28.1133C42.7467 24.5355 43.4845 21.4845 42.1739 20.1739Z"
                      fill="currentColor"
                    />
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M7.24189 26.4066C7.31369 26.4411 7.64204 26.5637 8.52504 26.3738C9.59462 26.1438 11.0343 25.5311 12.7183 24.4963C14.7583 23.2426 17.0256 21.4503 19.238 19.238C21.4503 17.0256 23.2426 14.7583 24.4963 12.7183C25.5311 11.0343 26.1438 9.59463 26.3738 8.52504C26.5637 7.64204 26.4411 7.31369 26.4066 7.24189C26.345 7.21246 26.143 7.14535 25.6664 7.1918C24.9745 7.25925 23.9954 7.5498 22.7699 8.14278C20.3369 9.32007 17.3369 11.4915 14.4142 14.4142C11.4915 17.3369 9.32007 20.3369 8.14278 22.7699C7.5498 23.9954 7.25925 24.9745 7.1918 25.6664C7.14534 26.143 7.21246 26.345 7.24189 26.4066ZM29.9001 10.7285C29.4519 12.0322 28.7617 13.4172 27.9042 14.8126C26.465 17.1544 24.4686 19.6641 22.0664 22.0664C19.6641 24.4686 17.1544 26.465 14.8126 27.9042C13.4172 28.7617 12.0322 29.4519 10.7285 29.9001L21.5754 40.747C21.6001 40.7606 21.8995 40.931 22.8729 40.7217C23.9424 40.4916 25.3821 39.879 27.0661 38.8441C29.1062 37.5904 31.3734 35.7982 33.5858 33.5858C35.7982 31.3734 37.5904 29.1062 38.8441 27.0661C39.879 25.3821 40.4916 23.9425 40.7216 22.8729C40.931 21.8995 40.7606 21.6001 40.747 21.5754L29.9001 10.7285ZM29.2403 4.41187L43.5881 18.7597C44.9757 20.1473 44.9743 22.1235 44.6322 23.7139C44.2714 25.3919 43.4158 27.2666 42.252 29.1604C40.8128 31.5022 38.8165 34.012 36.4142 36.4142C34.012 38.8165 31.5022 40.8128 29.1604 42.252C27.2666 43.4158 25.3919 44.2714 23.7139 44.6322C22.1235 44.9743 20.1473 44.9757 18.7597 43.5881L4.41187 29.2403C3.29027 28.1187 3.08209 26.5973 3.21067 25.2783C3.34099 23.9415 3.8369 22.4852 4.54214 21.0277C5.96129 18.0948 8.43335 14.7382 11.5858 11.5858C14.7382 8.43335 18.0948 5.9613 21.0277 4.54214C22.4852 3.8369 23.9415 3.34099 25.2783 3.21067C26.5973 3.08209 28.1187 3.29028 29.2403 4.41187Z"
                      fill="currentColor"
                    />
                  </g>
                  <defs>
                    <clipPath id="clip0_6_543"><rect width="48" height="48" fill="white" /></clipPath>
                  </defs>
                </svg>
              </div>
              <h2 className="text-[#181211] text-lg font-bold leading-tight tracking-[-0.015em]">SkillConnect</h2>
            </div>
            <div className="flex items-center gap-9">
              <a className="text-[#181211] text-sm font-medium leading-normal" href="/services">Find Services</a>
              <a className="text-[#181211] text-sm font-medium leading-normal" href="/about">About Us</a>
              <a className="text-[#181211] text-sm font-medium leading-normal" href="/contact">Contact</a>
            </div>
          </div>
          <div className="flex flex-1 justify-end gap-8">
            {isAuthenticated ? (
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/profile')}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f35120] text-white text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Profile</span>
                </button>
                <button
                  onClick={logout}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f5f1f0] text-[#181211] text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/register')}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f35120] text-white text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Sign Up</span>
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f5f1f0] text-[#181211] text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Log In</span>
                </button>
              </div>
            )}
          </div>
        </header>
        <div className="px-40 flex flex-1 justify-center py-5">
          <div className="layout-content-container flex flex-col max-w-[960px] flex-1">
            <div className="flex flex-col gap-10 px-4 py-10 @container">
              <h2 className="text-3xl font-extrabold text-brand-text-primary mb-6 text-center">Your Profile</h2>

              {message && (
                <div className={`p-3 mb-4 rounded-md ${error ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                  {message}
                </div>
              )}

              <div className="text-right mb-4">
                <button
                  onClick={handleEditToggle}
                  className="px-4 py-2 bg-brand-primary text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-2"
                >
                  {isEditing ? 'Cancel Edit' : 'Edit Profile'}
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-brand-text-secondary">Full Name</label>
                    {isEditing ? (
                      <input
                        type="text"
                        name="full_name"
                        value={profileData.full_name}
                        onChange={handleChange}
                        className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                      />
                    ) : (
                      <p className="mt-1 text-brand-text-primary">{profileData.full_name}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-brand-text-secondary">Email</label>
                    {isEditing ? (
                      <input
                        type="email"
                        name="email"
                        value={profileData.email}
                        onChange={handleChange}
                        className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                      />
                    ) : (
                      <p className="mt-1 text-brand-text-primary">{profileData.email}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-brand-text-secondary">Phone Number</label>
                    {isEditing ? (
                      <input
                        type="text"
                        name="phone_number"
                        value={profileData.phone_number}
                        onChange={handleChange}
                        className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                      />
                    ) : (
                      <p className="mt-1 text-brand-text-primary">{profileData.phone_number}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-brand-text-secondary">Location</label>
                    {isEditing ? (
                      <input
                        type="text"
                        name="location"
                        value={profileData.location}
                        onChange={handleChange}
                        className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                      />
                    ) : (
                      <p className="mt-1 text-brand-text-primary">{profileData.location}</p>
                    )}
                  </div>
                </div>

                {isArtisan && (
                  <div className="border-t border-brand-border pt-6 mt-6">
                    <h3 className="text-2xl font-semibold text-brand-text-primary mb-4">Artisan Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-brand-text-secondary">Bio</label>
                        {isEditing ? (
                          <textarea
                            name="bio"
                            value={profileData.artisan_details.bio}
                            onChange={handleChange}
                            rows="3"
                            className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          />
                        ) : (
                          <p className="mt-1 text-brand-text-primary">{profileData.artisan_details.bio || 'N/A'}</p>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-brand-text-secondary">Years Experience</label>
                        {isEditing ? (
                          <input
                            type="number"
                            name="years_experience"
                            value={profileData.artisan_details.years_experience}
                            onChange={handleChange}
                            min="0"
                            className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          />
                        ) : (
                          <p className="mt-1 text-brand-text-primary">{profileData.artisan_details.years_experience || '0'} years</p>
                        )}
                      </div>
                      <div className="col-span-1 md:col-span-2">
                        <label className="block text-sm font-medium text-brand-text-secondary">Skills (comma-separated)</label>
                        {isEditing ? (
                          <input
                            type="text"
                            name="skills_input"
                            value={profileData.artisan_details.skills.join(', ')}
                            onChange={handleChange}
                            className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          />
                        ) : (
                          <p className="mt-1 text-brand-text-primary">{profileData.artisan_details.skills.join(', ') || 'N/A'}</p>
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
                              className="h-4 w-4 text-brand-primary focus:ring-brand-primary border-brand-border rounded"
                            />
                            <label htmlFor="is_available" className="ml-2 block text-sm text-brand-text-primary">
                              Available for Jobs
                            </label>
                          </>
                        ) : (
                          <p className="mt-1 text-brand-text-primary">
                            Status: <span className={`font-semibold ${profileData.artisan_details.is_available ? 'text-green-600' : 'text-red-600'}`}>
                              {profileData.artisan_details.is_available ? 'Available' : 'Not Available'}
                            </span>
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="border-t border-brand-border pt-6 mt-6">
                      <h3 className="text-2xl font-semibold text-brand-text-primary mb-4">Reviews</h3>
                      {reviewsLoading ? (
                        <p className="text-brand-text-secondary">Loading reviews...</p>
                      ) : reviewsError ? (
                        <p className="text-red-500">{reviewsError}</p>
                      ) : reviews.length === 0 ? (
                        <p className="text-brand-text-secondary">No reviews yet.</p>
                      ) : (
                        <div className="space-y-4">
                          <p className="text-lg font-semibold text-brand-text-secondary">
                            Average Rating: {profileData.artisan_details.average_rating ? profileData.artisan_details.average_rating.toFixed(1) : 'N/A'} ({profileData.artisan_details.total_reviews} reviews)
                          </p>
                          <ul className="space-y-3">
                            {reviews.map((review) => (
                              <li key={review.id} className="bg-brand-secondary p-3 rounded-md shadow-sm border border-brand-border">
                                <p className="text-md font-semibold text-brand-text-primary">Rating: {review.rating} / 5</p>
                                <p className="text-brand-text-secondary text-sm">Comment: {review.comment || 'No comment provided.'}</p>
                                <p className="text-brand-text-secondary text-xs">
                                  By: {review.client_full_name || 'Anonymous'} on {new Date(review.created_at).toLocaleDateString()}
                                </p>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {isEditing && (
                  <div className="mt-8 flex justify-end">
                    <button
                      type="submit"
                      className="px-6 py-3 bg-brand-primary text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-2"
                      disabled={loading}
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                )}
              </form>
            </div>
          </div>
        </div>
        <footer className="flex justify-center">
          <div className="flex max-w-[960px] flex-1 flex-col">
            <footer className="flex flex-col gap-6 px-5 py-10 text-center @container">
              <div className="flex flex-wrap items-center justify-center gap-6 @[480px]:flex-row @[480px]:justify-around">
                <a className="text-[#8a6a60] text-base font-normal leading-normal min-w-40" href="/terms">Terms of Service</a>
                <a className="text-[#8a6a60] text-base font-normal leading-normal min-w-40" href="/privacy">Privacy Policy</a>
                <a className="text-[#8a6a60] text-base font-normal leading-normal min-w-40" href="/contact">Contact Us</a>
              </div>
              <p className="text-[#8a6a60] text-base font-normal leading-normal">@2024 SkillConnect. All rights reserved.</p>
            </footer>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default ProfilePage;