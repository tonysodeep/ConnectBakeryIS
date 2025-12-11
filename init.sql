-- Create the second database required by the application
CREATE DATABASE IF NOT EXISTS IMS;

-- You can also optionally ensure the application user has permissions here
GRANT ALL PRIVILEGES ON IMS.* TO 'tony'@'%';
FLUSH PRIVILEGES;

-- Note: The 'PMS' database is already created by the MYSQL_DATABASE environment variable.