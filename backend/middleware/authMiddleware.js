const jwt = require('jsonwebtoken');

// Make sure JWT_SECRET is available; it should be loaded by dotenv in server.js
const jwtSecret = process.env.JWT_SECRET;

module.exports = function (req, res, next) {
    // Get token from header
    // The token is usually sent as 'x-auth-token' or 'Authorization: Bearer <token>'
    const token = req.header('x-auth-token');

    // Check if no token
    if (!token) {
        return res.status(401).json({ msg: 'No token, authorization denied' });
    }

    // Verify token
    try {
        // jwt.verify takes the token, the secret, and a callback
        // It decodes the payload if the token is valid
        const decoded = jwt.verify(token, jwtSecret);

        // Attach the decoded user payload to the request object
        // So, any subsequent route handlers can access req.user
        req.user = decoded.user;
        next(); // Call next middleware/route handler
    } catch (err) {
        // If verification fails (e.g., token is expired or tampered)
        res.status(401).json({ msg: 'Token is not valid' });
    }
};