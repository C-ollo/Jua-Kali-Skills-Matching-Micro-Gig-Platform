// frontend/src/App.jsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom'; // Import BrowserRouter and Navigate
import './index.css';

// Import your page components
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';
import ProfilePage from './pages/ProfilePage';
import JobDetailPage from './pages/JobDetailPage';

import ServicesPage from './pages/ServicesPage';

import ArtisanProfilePage from './pages/ArtisanProfilePage';

import AboutUsPage from './pages/AboutUsPage';
import ContactPage from './pages/ContactPage';
import TermsPage from './pages/TermsPage';
import PrivacyPage from './pages/PrivacyPage';

// Import AuthProvider and useAuth from your context
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Import PrivateRoute - Ensure this file exists at src/components/PrivateRoute.jsx
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
      <AuthProvider> {/* Wrap your routes with AuthProvider to provide auth context */}
        <Routes>
          {/* Public Routes */}
          {/* Note: I'm making '/' redirect to login, as it's common for authenticated apps. 
                     If you want a public homepage, keep <Route path="/" element={<HomePage />} />
                     and remove the Navigate below. */}
          <Route path="/" element={<Navigate replace to="/home" />} /> {/* Redirect root to login */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/services" element={<ServicesPage />} />
          <Route path="/artisans/:artisan_id" element={<ArtisanProfilePage />} />
          <Route path="/about" element={<AboutUsPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/privacy" element={<PrivacyPage />} /> {/* Keep HomePage if you want a public one */}

          {/* Authenticated Routes */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <ProfilePage />
              </PrivateRoute>
            }
          />

          {/* Catch-all for 404 - make sure NotFoundPage component exists */}
          {/* If you don't have NotFoundPage, change to <Route path="*" element={<Navigate replace to="/login" />} /> */}
          <Route
            path="/jobs/:job_id"
            element={
              <PrivateRoute>
                <JobDetailPage />
              </PrivateRoute>
            }
          />
          {/* Catch-all for 404 - make sure NotFoundPage component exists */}
          {/* If you don't have NotFoundPage, change to <Route path="*" element={<Navigate replace to="/login" />} /> */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
  );
}

export default App;