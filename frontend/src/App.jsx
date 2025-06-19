import { useState, useEffect } from 'react';
import './App.css'; // Keep your existing CSS import

function App() {
  const [backendMessage, setBackendMessage] = useState('Loading message from backend...');
  const [dbTime, setDbTime] = useState('Fetching DB time...');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Function to fetch the root message
    const fetchRootMessage = async () => {
      try {
        const response = await fetch('http://localhost:5000/'); // Adjust port if different
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.text(); // For plain text response
        setBackendMessage(data);
      } catch (err) {
        console.error("Failed to fetch root message:", err);
        setError("Failed to connect to backend root.");
      }
    };

    // Function to fetch the database time
    const fetchDbTime = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/test-db'); // Adjust port if different
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json(); // For JSON response
        setDbTime(data.currentTime);
      } catch (err) {
        console.error("Failed to fetch DB time:", err);
        setError("Failed to connect to backend DB endpoint.");
      }
    };

    fetchRootMessage();
    fetchDbTime();
  }, []); // Empty dependency array means this runs once on mount

  return (
    <div className="App">
      <header className="App-header">
        <h1>Jua Kali Platform</h1>
        <p>Frontend (React) is running!</p>

        {error && <p style={{ color: 'red' }}>Error: {error}</p>}

        <h2>Backend Communication Test:</h2>
        <p>Root message from backend: <strong>{backendMessage}</strong></p>
        <p>Current time from DB: <strong>{dbTime}</strong></p>

        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </header>
    </div>
  );
}

export default App;