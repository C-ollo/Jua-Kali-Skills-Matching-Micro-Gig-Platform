CREATE TABLE job_applications (
    id SERIAL PRIMARY KEY,
    job_id INT NOT NULL,
    artisan_id INT NOT NULL,
    bid_amount NUMERIC(10, 2), -- Optional bid amount from artisan
    message TEXT,              -- Optional message from artisan to client
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- e.g., 'pending', 'accepted', 'rejected', 'withdrawn'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (artisan_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (job_id, artisan_id) -- Ensures an artisan can apply only once per job
);

-- Optional: Add a trigger to update updated_at automatically
CREATE OR REPLACE FUNCTION update_updated_at_column_job_applications()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_job_applications_updated_at
BEFORE UPDATE ON job_applications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column_job_applications();