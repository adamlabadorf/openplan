# Digest Delivery and Notification System Specification

## Overview

The digest delivery system is a core feature of the PubWatch research literature collection system. It automates the process of generating weekly paper digests for researchers, ranking papers by relevance to their defined topic profiles.

## Components

### 1. Digest Generation Service
- **Purpose**: Automated weekly generation of personalized paper digests
- **Functionality**:
  - Collects papers associated with each topic profile
  - Ranks papers by relevance using the scoring engine
  - Compiles top N most relevant papers per profile
  - Generates formatted digest reports (HTML and plain text)
  - Sends email notifications to researchers

### 2. Notification System
- **Purpose**: Deliver paper digests to researchers via email
- **Functionality**:
  - Email delivery infrastructure
  - Customizable notification preferences
  - Error handling and logging for delivery failures
  - Support for different digest formats

## Technical Requirements

### API Specification

#### Digest Generation Endpoints
```
GET /api/digests/profile/{profile_id}
  Query Parameters: 
    - limit: Number of papers to include (default: 10)
    - format: content format (html, text)
    - start_date: Filter papers from this date
    - end_date: Filter papers until this date

POST /api/digests/generate
  Body:
    - profile_ids: List of profile IDs to generate digests for
    - send_email: Boolean indicating if email should be sent
    - recipients: List of recipient email addresses
    - format: Digest content format (html, text)

GET /api/digests/reports
  Query Parameters:
    - profile_id: Specific profile ID
    - start_date: Start date for report period
    - end_date: End date for report period
    - limit: Number of digests to include
```

#### Notification Preferences Endpoints
```
GET /api/users/{user_id}/preferences
POST /api/users/{user_id}/preferences
  Body:
    - email: Email address for notifications
    - notification_format: preferred format (html, text)
    - digest_frequency: delivery frequency (daily, weekly, monthly)
    - included_profile_ids: profiles to include in digests
    - excluded_profile_ids: profiles to exclude from digests
```

### Database Schema Changes

#### 1. User Profiles Table Enhancement
```sql
-- Add user_id column to profile table for better user association
ALTER TABLE profiles ADD COLUMN user_id TEXT;
```

#### 2. Notification Preferences Table
```sql
CREATE TABLE IF NOT EXISTS notification_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    email_address TEXT,
    preferred_format TEXT DEFAULT 'html', -- html or text
    digest_frequency TEXT DEFAULT 'weekly', -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Add user_id as a foreign key constraint to profiles table
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

#### 3. Digest History and Delivery Tracking Table
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

#### 4. Paper Exclusion Table

```sql
CREATE TABLE IF NOT EXISTS paper_exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    user_id TEXT NOT NULL,
    excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT, -- optional reason for exclusion
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    UNIQUE(profile_id, pmid, user_id)
);
```

### Implementation Guidelines

#### 1. Digest Generation Workflow
1. Schedule weekly digest generation service (using cron or similar)
2. For each active topic profile:
   - Retrieve all papers associated with the profile within the time period
   - Filter out papers marked as excluded by the user
   - Rank papers using the existing PublicationScorer engine
   - Select top N papers (default: 10)
3. Format digest content according to user preferences:
   - HTML format with clean, readable structure
   - Plain text version for accessibility
4. Store digest in digest_deliveries table with status "pending"
5. Send email notification if configured for delivery

#### 2. Email Delivery System
1. Use SMTP for email delivery
2. Support for different content formats:
   - HTML: Rich formatting with paper metadata and links
   - Plain Text: Clean, readable text version
3. Email templates for different contexts:
   - Weekly digest summary email
   - Error notification email when delivery fails
4. Batching and throttling to respect rate limits
5. Proper error handling and retry mechanisms

#### 3. Notification Preferences Management
1. Allow researchers to define their preferred content formats
2. Support different delivery frequencies (daily, weekly, monthly)
3. Provide mechanism for excluding specific papers or profiles from digests
4. Store user preferences in the notification_preferences table

### Configuration Requirements

#### Environment Variables
- `SMTP_HOST`: SMTP server address for email delivery
- `SMTP_PORT`: SMTP server port
- `SMTP_USERNAME`: Email authentication username
- `SMTP_PASSWORD`: Email authentication password  
- `DIGEST_LIMIT`: Default number of papers per digest (default: 10)
- `DIGEST_FREQUENCY`: How often digests should be generated (weekly)

#### Configuration Options
```
{
  "preferences": {
    "format": "html", 
    "frequency": "weekly",
    "included_profiles": ["profile_1", "profile_2"],
    "excluded_profiles": [],
    "email": "researcher@example.com"
  },
  "digest_template": {
    "subject_prefix": "[PubWatch] Weekly Digest - ",
    "greeting": "Dear Researcher,",
    "summary": "Here are the top papers for your research profiles:",
    "paper_format": "{title} by {authors}\n{date} | DOI: {doi}\n{abstract}\n\n",
    "closing": "Best regards,\nThe PubWatch Team"
  }
}
```

### Error Handling and Logging

#### System Errors
1. **Database Connection Failures**: Retry mechanism with exponentially increasing backoff
2. **Email Delivery Failures**: Log error, retry up to 3 times, then notify user of delivery issue
3. **API Rate Limiting**: Queue requests with jittered delay implementation
4. **Paper Score Calculation Failures**: Skip individual papers and continue processing

#### Logging Requirements
- All digest generation operations must be logged
- Email delivery attempts should be tracked with success/failure status
- User preference updates should be auditable
- System errors should trigger appropriate alerts to administrators

### Metrics and Monitoring

#### Key Performance Indicators
1. **Delivery Success Rate**: Percentage of digests successfully delivered
2. **Processing Time**: Time taken to generate a digest for a profile
3. **User Engagement**: Number of users receiving digests weekly
4. **Paper Relevance**: Percentage of papers in digests that are rated relevant by researchers

#### Monitoring Requirements
- Real-time dashboard showing digest delivery statistics
- Error rate monitoring with alerting thresholds
- Usage analytics for different user preferences and profile usage