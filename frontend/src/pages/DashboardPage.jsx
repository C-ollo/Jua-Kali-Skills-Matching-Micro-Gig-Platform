// frontend/src/pages/DashboardPage.jsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function DashboardPage() {
  const { user, logout, loading, isAuthenticated } = useAuth(); // Get user, logout, and loading state from AuthContext
  const navigate = useNavigate();

  // Show loading state if authentication context is still loading
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading dashboard...</p>
      </div>
    );
  }

  // If for some reason user is null but not loading (e.g., direct access without token)
  if (!user) {
    navigate('/login'); // Redirect to login if not authenticated
    return null; // Don't render anything
  }
  

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Welcome to Your Dashboard, {user.full_name}!</h1>

        <div className="mb-8">
          <p className="text-lg text-gray-700">This is your central hub for managing your Juakali activities.</p>
          <p className="text-md text-gray-600 mt-2">
            You are logged in as a <span className="font-semibold text-blue-600 capitalize">{user.user_type}</span>.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Link to Profile Page */}
          <div className="bg-blue-50 p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold text-blue-800 mb-2">My Profile</h2>
            <p className="text-gray-700 mb-3">View and update your personal details and {user.user_type === 'artisan' ? 'artisan information and skills.' : 'contact information.'}</p>
            <button
              onClick={() => navigate('/profile')}
              className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
            >
              Go to Profile
            </button>
          </div>

          {/* Conditional Sections based on user type */}
          {user.user_type === 'client' && (
            <div className="bg-green-50 p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h2 className="text-xl font-semibold text-green-800 mb-2">Post a New Job</h2>
              <p className="text-gray-700 mb-3">Describe your service needs and connect with skilled artisans.</p>
              <button
                onClick={() => alert('Navigate to Post Job page (Coming Soon!)')}
                className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
              >
                Post Job
              </button>
            </div>
          )}

          {user.user_type === 'artisan' && (
            <div className="bg-purple-50 p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h2 className="text-xl font-semibold text-purple-800 mb-2">Manage My Services</h2>
              <p className="text-gray-700 mb-3">Create, update, or view your offered services and availability.</p>
              <button
                onClick={() => alert('Navigate to Manage Services page (Coming Soon!)')}
                className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
              >
                Manage Services
              </button>
            </div>
          )}

          <div className="bg-yellow-50 p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold text-yellow-800 mb-2">View Listings</h2>
            <p className="text-gray-700 mb-3">Browse available jobs or artisans in your area.</p>
            <button
              onClick={() => alert('Navigate to View Listings page (Coming Soon!)')}
              className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
            >
              View Listings
            </button>
          </div>

          {/* Add more sections as needed */}

        </div>

        <div className="mt-8 text-center">
          <button
            onClick={logout}
            className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-6 rounded-md transition duration-300"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;