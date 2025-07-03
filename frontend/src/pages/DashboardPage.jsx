// frontend/src/pages/DashboardPage.jsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext'; // Import useAuth
import { Link } from 'react-router-dom';

function DashboardPage() {
  const { user, logout, isClient, isArtisan, isAdmin } = useAuth(); // Get user and logout from context

  if (!user) {
    // This case should ideally be handled by PrivateRoute,
    // but a fallback for extra safety is good.
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">No user data found. Redirecting...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-indigo-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-lg">
        <h1 className="text-3xl font-bold text-center text-indigo-800 mb-6">
          Welcome to Your Dashboard!
        </h1>
        <div className="text-lg text-gray-700 space-y-2 mb-6">
          <p>
            **Logged in as:**{' '}
            <span className="font-semibold text-indigo-600">{user.full_name}</span>
          </p>
          <p>
            **Email:** <span className="font-semibold">{user.email}</span>
          </p>
          <p>
            **User Type:**{' '}
            <span className="font-semibold capitalize text-purple-600">
              {user.user_type}
            </span>
          </p>
          {user.location && (
            <p>
              **Location:** <span className="font-semibold">{user.location}</span>
            </p>
          )}

          {/* Display Artisan-specific details if available */}
          {isArtisan && user.artisan_details && (
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <h2 className="text-xl font-semibold text-yellow-800 mb-2">Artisan Details:</h2>
              <p>
                **Bio:** <span className="font-medium">{user.artisan_details.bio || 'N/A'}</span>
              </p>
              <p>
                **Experience:**{' '}
                <span className="font-medium">{user.artisan_details.years_experience} years</span>
              </p>
              <p>
                **Rating:**{' '}
                <span className="font-medium">
                  {user.artisan_details.average_rating ? user.artisan_details.average_rating.toFixed(1) : 'N/A'} (
                  {user.artisan_details.total_reviews} reviews)
                </span>
              </p>
              <p>
                **Available:**{' '}
                <span className="font-medium">
                  {user.artisan_details.is_available ? 'Yes' : 'No'}
                </span>
              </p>
              {user.skills && user.skills.length > 0 && (
                <p>
                  **Skills:**{' '}
                  <span className="font-medium">{user.skills.join(', ')}</span>
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-center gap-4 mt-6">
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          >
            Logout
          </button>
          {/* Add more links/buttons based on user type */}
          {isClient && (
            <Link to="/client/jobs/post" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md inline-flex items-center justify-center">
              Post a Job
            </Link>
          )}
          {isArtisan && (
            <Link to="/artisan/jobs" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md inline-flex items-center justify-center">
              Browse Jobs
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;