-- Create the job_reviews table
CREATE TABLE job_reviews (
    id SERIAL PRIMARY KEY,
    job_id INT NOT NULL UNIQUE, -- Ensures only one review per job
    client_id INT NOT NULL,     -- The client who left the review
    artisan_id INT NOT NULL,    -- The artisan being reviewed
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5), -- Rating from 1 to 5
    comment TEXT,               -- Optional text comment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (artisan_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add an index for faster lookup of reviews for a specific artisan
CREATE INDEX idx_job_reviews_artisan_id ON job_reviews (artisan_id);

-- Add rating aggregation columns to artisan_details table
ALTER TABLE artisan_details
ADD COLUMN average_rating NUMERIC(3, 2) DEFAULT 0.0, -- Stores average rating (e.g., 4.50)
ADD COLUMN total_reviews INT DEFAULT 0; -- Stores total number of reviews