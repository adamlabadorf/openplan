# PubWatch Database Schema Specification
## Digest Delivery and Notification System

### Overview
This document specifies the database schema changes required for implementing the digest delivery and notification system in the PubWatch research literature collection platform.

### Schema Changes

#### 1. Enhanced Profiles Table
```sql
-- Add user_id to profiles table for better user association
ALTER TABLE profiles ADD COLUMN user_id TEXT;

-- Add additional columns for more robust profile management
ALTER TABLE profiles ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE profiles ADD COLUMN notification_preferences TEXT; -- JSON storage of preference data
```

#### 2. Notification Preferences Table
```sql
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
```

#### 3. Digest Deliveries Table
```sql
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
```

#### 4. Paper Exclusions Table
```sql
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
```

#### 5. User Profile Association Table
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE(user_id, profile_id)
);
```

### Schema Relationships

1. **Profiles ↔ User Profiles**: One-to-Many
   - A profile can be associated with multiple users via user_profiles table
   - A user can have multiple profiles through user_profiles association

2. **Profiles ↔ Digest Deliveries**: One-to-Many  
   - Each profile can generate multiple digest deliveries over time

3. **Users ↔ Notification Preferences**: One-to-One
   - Each user has exactly one notifications preference record

4. **Profiles ↔ Paper Exclusions**: One-to-Many
   - A profile can have many paper exclusions from different users

### Indexes

#### Performance Optimizations
```sql
-- Index for frequently queried digest deliveries by profile and date
CREATE INDEX IF NOT EXISTS idx_digest_deliveries_profile_date 
ON digest_deliveries(profile_id, delivery_date);

-- Index for email delivery tracking
CREATE INDEX IF NOT EXISTS idx_digest_deliveries_status_date 
ON digest_deliveries(status, delivery_date);

-- Index for paper exclusions by profile and PMID
CREATE INDEX IF NOT EXISTS idx_paper_exclusions_profile_pmid 
ON paper_exclusions(profile_id, pmid);

-- Index for user-based paper exclusions
CREATE INDEX IF NOT EXISTS idx_paper_exclusions_user_profile 
ON paper_exclusions(user_id, profile_id);

-- Index for notification preferences by user
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user 
ON notification_preferences(user_id);
```

### Data Types and Constraints

#### Core Fields
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT (All tables)
- **created_at**: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

#### Text Fields
- All string fields use TEXT data type with appropriate length constraints
- Email addresses should be validated during insert/update operations

#### Foreign Key Constraints
- Maintains referential integrity between related tables
- Cascading deletes for related records when parent records are deleted

### Migration Script Example

```sql
-- Migration script to update database schema
BEGIN TRANSACTION;

-- Add new columns to profiles table
ALTER TABLE profiles ADD COLUMN user_id TEXT;
ALTER TABLE profiles ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE profiles ADD COLUMN notification_preferences TEXT;

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    email_address TEXT,
    preferred_format TEXT DEFAULT 'html',
    digest_frequency TEXT DEFAULT 'weekly',
    included_profile_ids TEXT,
    excluded_profile_ids TEXT,
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
    status TEXT DEFAULT 'pending',
    format TEXT,
    subject TEXT,
    content TEXT, 
    recipients TEXT,
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
    reason TEXT,
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
```

### Data Validation Rules

1. **Email Format**: Validate email addresses using regex patterns
2. **Profile ID Uniqueness**: Profile IDs must be unique within the profiles table
3. **User ID Consistency**: All references to user_id should have valid existence in notification_preferences
4. **Format Constraints**: 
   - format field (digest content) must be either 'html' or 'text'
   - digest_frequency must be one of: 'daily', 'weekly', 'monthly'
5. **Status Values**: 
   - digest status must be one of: 'pending', 'delivered', 'failed'

### Backup and Restore Considerations

The schema design supports:
1. **Regular automated backups** of all tables
2. **Snapshot capability** for restoring specific states
3. **Incremental update support** for schema evolution
4. **Data export capabilities** through SQL queries

### Security Considerations

1. **Data Sensitivity**: User email addresses and preferences are sensitive data
2. **Access Controls**: Implement proper database user permissions
3. **Encryption**: Sensitive fields should be encrypted at rest
4. **Auditing**: All modification operations should be logged for compliance