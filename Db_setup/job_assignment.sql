ALTER TABLE jobs
ADD COLUMN assigned_artisan_id INT;

ALTER TABLE jobs
ADD CONSTRAINT fk_assigned_artisan
FOREIGN KEY (assigned_artisan_id)
REFERENCES users(id)
ON DELETE SET NULL; -- If the assigned artisan's account is deleted, set this field to NULL