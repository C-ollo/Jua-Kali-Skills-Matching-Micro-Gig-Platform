import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  RouterProvider,
} from 'react-router-dom'; // <--- ADD THIS IMPORT
import App from './App.jsx';
import './index.css';

// Import placeholder components (we'll create these next)
import Home from './pages/Home.jsx';       // <--- ADD THIS IMPORT
import Register from './pages/Register.jsx'; // <--- ADD THIS IMPORT
import Login from './pages/Login.jsx';     // <--- ADD THIS IMPORT

// Define your routes
const router = createBrowserRouter([
  {
    path: '/',
    element: <App />, // App will serve as our layout component
    children: [ // Nested routes for pages that use App's layout
      {
        index: true, // This makes it the default child route for '/'
        element: <Home />,
      },
      {
        path: 'register', // Accessible at /register
        element: <Register />,
      },
      {
        path: 'login', // Accessible at /login
        element: <Login />,
      },
    ],
  },
  // You can add other top-level routes here if needed later
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} /> {/* <--- USE RouterProvider */}
  </React.StrictMode>,
);