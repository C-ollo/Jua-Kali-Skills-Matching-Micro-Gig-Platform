require('dotenv').config(); // Load environment variables from .env file
const cors = require('cors');
const express = require('express');
const { Pool } = require('pg'); // PostgreSQL client

const app = express();
const PORT = process.env.PORT || 5000; // Use port from .env or default to 5000

// Middleware to parse JSON bodies from incoming requests
app.use(express.json());
app.use(cors());
// --- Database Connection ---
const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});

// Test database connection
pool.connect()
    .then(() => console.log('Connected to PostgreSQL database!'))
    .catch(err => console.error('Database connection error', err.stack));


// --- Define a simple API route for testing ---
app.get('/', (req, res) => {
    res.send('Jua Kali Backend API is running!');
});

// Example: A route to fetch data from the database (placeholder for now)
app.get('/api/test-db', async (req, res) => {
    try {
        // This is just an example, assumes a table named 'users' exists for now
        // We'll define schemas later.
        const result = await pool.query('SELECT NOW()');
        res.json({
            message: 'Fetched current time from DB!',
            currentTime: result.rows[0].now
        });
    } catch (err) {
        console.error('Error executing query', err.stack);
        res.status(500).json({ error: 'Internal server error' });
    }
});


// --- Start the server ---
app.listen(PORT, () => {
    console.log(`Jua Kali Backend listening on port ${PORT}`);
});