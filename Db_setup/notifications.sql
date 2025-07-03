-- Create the notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,              -- The recipient of the notification
    message TEXT NOT NULL,             -- The notification message
    notification_type VARCHAR(50) NOT NULL, -- e.g., 'job_status_update', 'new_review', 'new_application'
    entity_id INT,                     -- ID of the related entity (e.g., job_id, review_id, application_id)
    is_read BOOLEAN DEFAULT FALSE,     -- Whether the user has seen/read the notification
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add an index for faster lookup of notifications for a specific user
CREATE INDEX idx_notifications_user_id ON notifications (user_id);
-- Add an index for faster lookup of unread notifications
CREATE INDEX idx_notifications_is_read ON notifications (is_read);