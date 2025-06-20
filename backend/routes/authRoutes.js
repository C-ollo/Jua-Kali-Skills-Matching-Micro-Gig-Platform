const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

// jwtSecret will be accessed directly from process.env, which is loaded in server.js
const jwtSecret = process.env.JWT_SECRET;

// Export a function that creates and returns the router,
// allowing the pool to be passed in from server.js
module.exports = (pool) => {
    // --- REGISTER USER ---
    // POST /api/auth/register
    router.post('/register', async (req, res) => {
        const { full_name, email, phone_number, password, user_type, location, bio, years_experience, skills } = req.body;

        // 1. Basic Input Validation
        if (!full_name || !email || !phone_number || !password || !user_type) {
            return res.status(400).json({ msg: 'Please enter all required fields' });
        }
        if (!['client', 'artisan'].includes(user_type)) {
            return res.status(400).json({ msg: 'Invalid user type specified' });
        }
        if (user_type === 'artisan' && (!location || !bio || !skills || !Array.isArray(skills) || skills.length === 0)) {
             return res.status(400).json({ msg: 'Artisan registration requires location, bio, and at least one skill.' });
        }

        try {
            // 2. Check for existing user (by email or phone number)
            const userExists = await pool.query(
                'SELECT id FROM users WHERE email = $1 OR phone_number = $2',
                [email, phone_number]
            );

            if (userExists.rows.length > 0) {
                return res.status(400).json({ msg: 'User with this email or phone number already exists' });
            }

            // 3. Hash Password
            const salt = await bcrypt.genSalt(10);
            const password_hash = await bcrypt.hash(password, salt);

            // 4. Insert new user into the 'users' table
            const newUser = await pool.query(
                `INSERT INTO users (full_name, email, phone_number, password_hash, user_type, location)
                 VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, full_name, email, phone_number, user_type, location`,
                [full_name, email, phone_number, password_hash, user_type, location]
            );

            const user_id = newUser.rows[0].id;

            // 5. If user_type is 'artisan', create an entry in 'artisan_details'
            if (user_type === 'artisan') {
                await pool.query(
                    `INSERT INTO artisan_details (user_id, bio, years_experience)
                     VALUES ($1, $2, $3)`,
                    [user_id, bio, years_experience || 0]
                );

                const skillResults = await pool.query(
                    `SELECT id FROM skills WHERE name = ANY($1::text[])`,
                    [skills]
                );

                if (skillResults.rows.length !== skills.length) {
                    console.warn('Some provided skills not found in database:', skills.filter(s => !skillResults.rows.map(r => r.name).includes(s)));
                }

                const artisanSkillsValues = skillResults.rows.map(row => `(${user_id}, ${row.id})`).join(',');
                if (artisanSkillsValues) {
                     await pool.query(
                        `INSERT INTO artisan_skills (artisan_id, skill_id)
                         VALUES ${artisanSkillsValues}`
                    );
                }
            }

            // 6. Generate JWT (JSON Web Token)
            const payload = {
                user: {
                    id: user_id,
                    user_type: user_type,
                    email: email
                }
            };

            jwt.sign(
                payload,
                jwtSecret,
                { expiresIn: '1h' },
                (err, token) => {
                    if (err) throw err;
                    res.status(201).json({
                        msg: 'User registered successfully!',
                        token,
                        user: {
                            id: user_id,
                            full_name,
                            email,
                            phone_number,
                            user_type,
                            location
                        }
                    });
                }
            );

        } catch (err) {
            console.error('Error during registration:', err.message);
            res.status(500).json({ msg: 'Server error' });
        }
    });

    // POST /api/auth/login
router.post('/login', async (req, res) => {
    const { email, password } = req.body;

    // 1. Basic Input Validation
    if (!email || !password) {
        return res.status(400).json({ msg: 'Please enter all fields' });
    }

    try {
        // 2. Check if user exists by email
        const userResult = await pool.query(
            'SELECT id, full_name, email, phone_number, password_hash, user_type FROM users WHERE email = $1',
            [email]
        );

        const user = userResult.rows[0];

        if (!user) {
            // User not found
            return res.status(400).json({ msg: 'Invalid Credentials' });
        }

        // 3. Compare provided password with hashed password from DB
        const isMatch = await bcrypt.compare(password, user.password_hash);

        if (!isMatch) {
            // Passwords don't match
            return res.status(400).json({ msg: 'Invalid Credentials' });
        }

        // 4. Generate JWT
        const payload = {
            user: {
                id: user.id,
                user_type: user.user_type,
                email: user.email
            }
        };

        jwt.sign(
            payload,
            jwtSecret, // The secret from process.env.JWT_SECRET
            { expiresIn: '1h' }, // Token expires in 1 hour
            (err, token) => {
                if (err) throw err;
                res.json({
                    msg: 'Logged in successfully!',
                    token,
                    user: {
                        id: user.id,
                        full_name: user.full_name,
                        email: user.email,
                        phone_number: user.phone_number,
                        user_type: user.user_type
                    }
                });
            }
        );

    } catch (err) {
        console.error('Error during login:', err.message);
        res.status(500).json({ msg: 'Server error' });
    }
});

    return router;
};