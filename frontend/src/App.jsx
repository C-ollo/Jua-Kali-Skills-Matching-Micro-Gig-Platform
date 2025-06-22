import { Outlet, Link } from 'react-router-dom';
import './App.css'; 

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Jua Kali Platform</h1>
        <nav>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', gap: '20px' }}>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/register">Register</Link></li>
            <li><Link to="/login">Login</Link></li>
          </ul>
        </nav>
        <hr /> {/* Simple separator */}
      </header>

      <main>
        <Outlet /> {/* This is where the child routes (Home, Register, Login) will be rendered */}
      </main>

      {/* Optional: Add a footer here later */}
    </div>
  );
}

export default App;