-- Enable uuid-ossp extension if you decide to use UUIDs later, but SERIAL is fine for now
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('client', 'artisan')), -- Enforce user_type
    location VARCHAR(255),
    profile_picture_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: artisan_details
CREATE TABLE artisan_details (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, -- If user is deleted, delete artisan_details
    bio TEXT,
    average_rating NUMERIC(2,1) DEFAULT 0.0,
    total_reviews INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    portfolio_urls TEXT[], -- Array of text URLs
    years_experience INTEGER
);

-- Table: skills
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Insert some initial common skills (optional, but good for testing)
INSERT INTO skills (name) VALUES
('Plumbing'),
('Electrical Repair'),
('Carpentry'),
('Welding'),
('Painting'),
('Masonry'),
('Tailoring'),
('Hairdressing'),
('Appliance Repair'),
('Motorcycle Repair'),
('Driving Services'),
('Cleaning Services');

-- Table: artisan_skills (Junction Table for many-to-many relationship)
CREATE TABLE artisan_skills (
    artisan_id INTEGER REFERENCES artisan_details(user_id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (artisan_id, skill_id) -- Composite primary key
);

-- Table: jobs
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES users(id),
    artisan_id INTEGER REFERENCES users(id), -- NULL initially until assigned
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    required_skill_id INTEGER NOT NULL REFERENCES skills(id),
    location VARCHAR(255) NOT NULL,
    budget NUMERIC(10,2),
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'accepted', 'in_progress', 'completed', 'cancelled', 'disputed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Table: reviews
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE, -- One review per job
    client_id INTEGER NOT NULL REFERENCES users(id),
    artisan_id INTEGER NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5), -- Rating between 1 and 5
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance on frequently queried columns
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_phone ON users (phone_number);
CREATE INDEX idx_users_type ON users (user_type);
CREATE INDEX idx_jobs_client_id ON jobs (client_id);
CREATE INDEX idx_jobs_artisan_id ON jobs (artisan_id);
CREATE INDEX idx_jobs_skill_id ON jobs (required_skill_id);
CREATE INDEX idx_jobs_status ON jobs (status);
CREATE INDEX idx_artisan_details_rating ON artisan_details (average_rating);
CREATE INDEX idx_reviews_artisan_id ON reviews (artisan_id);