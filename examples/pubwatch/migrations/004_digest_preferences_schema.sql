-- Migration script for digest delivery preferences schema
-- This migration implements database schema changes required for digest delivery and notification system

BEGIN TRANSACTION;

-- Add new columns to profiles table if they don't exist
-- This is a safe check to avoid errors if columns already exist
-- Note: In SQLite, we don't have easy ALTER TABLE ADD COLUMN with constraints,
-- so we'll recreate the table if needed or use a different approach

-- Check if required columns exist in profiles table
-- Since we're implementing this as a migration, we'll make assumptions about the current structure

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    email_address TEXT,
    preferred_format TEXT DEFAULT 'html', -- html or text
    digest_frequency TEXT DEFAULT 'weekly', -- daily, weekly, monthly
    included_profile_ids TEXT, -- JSON array of profile IDs to include
    excluded_profile_ids TEXT, -- JSON array of profile IDs to exclude
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create digest_deliveries table
CREATE TABLE IF NOT EXISTS digest_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    delivery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending', -- pending, delivered, failed
    format TEXT, -- html or text
    subject TEXT,
    content TEXT, 
    recipients TEXT, -- comma-separated email addresses
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (user_id) REFERENCES notification_preferences(user_id)
);

-- Create paper_exclusions table  
CREATE TABLE IF NOT EXISTS paper_exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    user_id TEXT NOT NULL,
    excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT, -- optional reason for exclusion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    UNIQUE(profile_id, pmid, user_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_digest_deliveries_profile_date 
ON digest_deliveries(profile_id, delivery_date);

CREATE INDEX IF NOT EXISTS idx_digest_deliveries_status_date 
ON digest_deliveries(status, delivery_date);

CREATE INDEX IF NOT EXISTS idx_paper_exclusions_profile_pmid 
ON paper_exclusions(profile_id, pmid);

CREATE INDEX IF NOT EXISTS idx_paper_exclusions_user_profile 
ON paper_exclusions(user_id, profile_id);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_user 
ON notification_preferences(user_id);

COMMIT;