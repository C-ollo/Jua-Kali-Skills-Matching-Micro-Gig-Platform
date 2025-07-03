// frontend/src/App.jsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './index.css';

// Import your page components
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';

// Import PrivateRoute
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Authenticated Routes */}
      {/* Example: Dashboard accessible by any authenticated user */}
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardPage />
          </PrivateRoute>
        }
      />

      {/* Example: Client-specific dashboard, only accessible by clients */}
      {/* <Route
        path="/client/dashboard"
        element={
          <PrivateRoute allowedRoles={['client']}>
            <ClientDashboardPage /> // You'd create this page
          </PrivateRoute>
        }
      /> */}

      {/* Example: Artisan-specific dashboard, only accessible by artisans */}
      {/* <Route
        path="/artisan/dashboard"
        element={
          <PrivateRoute allowedRoles={['artisan']}>
            <ArtisanDashboardPage /> // You'd create this page
          </PrivateRoute>
        }
      /> */}

      {/* Example: Admin dashboard, only accessible by admins */}
      {/* <Route
        path="/admin/dashboard"
        element={
          <PrivateRoute allowedRoles={['admin']}>
            <AdminDashboardPage /> // You'd create this page
          </PrivateRoute>
        }
      /> */}

      {/* Catch-all for 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;