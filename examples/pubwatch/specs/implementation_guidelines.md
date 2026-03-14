# Implementation Guidelines for Digest Delivery and Notification System

## Overview

This document provides detailed implementation guidelines for developing the digest delivery and notification system in the PubWatch research literature collection platform. It outlines the step-by-step approach to building the core functionality based on the existing codebase architecture.

## Architecture Approach

### 1. Service Layer Design
The digest system should be implemented as a service layer with clear separation between:
- **API Layer**: REST endpoints for user interaction
- **Business Logic Layer**: Digest generation and notification handling
- **Data Access Layer**: Database operations using existing storage patterns

### 2. Core Components to Implement

#### A. Digest Generation Service
```python
class DigestService:
    def __init__(self, storage: PaperStorage, scorer: PublicationScorer):
        self.storage = storage
        self.scorer = scorer
        
    def generate_digest(self, profile_id: str, user_id: str, 
                       format_type: str = 'html', limit: int = 10) -> dict:
        # Fetch papers associated with the profile
        papers = self.storage.fetch_papers(profile_id=profile_id, limit=limit*2)
        
        # Filter out excluded papers
        excluded_papers = self.get_excluded_papers(user_id, profile_id)
        papers = [p for p in papers if p['pmid'] not in excluded_papers]
        
        # Score and rank papers
        ranked_papers = self.scorer.sort_papers_by_relevance(papers, profile_keywords)
        
        # Select top N papers
        selected_papers = ranked_papers[:limit]
        
        # Format content
        content = self.format_digest_content(selected_papers, format_type)
        
        return {
            'profile_id': profile_id,
            'papers': selected_papers,
            'format': format_type,
            'content': content,
            'generated_at': datetime.now()
        }
```

#### B. Notification Service
```python
class NotificationService:
    def __init__(self, smtp_host: str, smtp_port: int, 
                 smtp_username: str, smtp_password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        
    def send_digest_email(self, recipient: str, subject: str, 
                         content: str, format_type: str = 'html') -> bool:
        # Create email message with appropriate format
        msg = MIMEText(content, format_type)
        msg['Subject'] = subject
        msg['To'] = recipient
        
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email delivery failed: {e}")
            return False
```

#### C. Background Scheduler
```python
class DigestScheduler:
    def __init__(self, digest_service: DigestService, 
                 notification_service: NotificationService):
        self.digest_service = digest_service
        self.notification_service = notification_service
        
    def run_weekly_digests(self):
        # Get all active profiles and users with preferences
        active_profiles = get_active_profiles()
        for profile in active_profiles:
            users = get_users_for_profile(profile['id'])
            for user in users:
                preferences = get_user_preferences(user['id'])
                digest = self.digest_service.generate_digest(
                    profile['id'], user['id'], 
                    preferences['preferred_format']
                )
                if preferences['email_address'] and preferences['is_active']:
                    success = self.notification_service.send_digest_email(
                        preferences['email_address'],
                        digest['subject'],
                        digest['content'],
                        digest['format']
                    )
                    self.record_delivery(profile['id'], user['id'], 
                                       digest, success)
```

## Implementation Steps

### Step 1: Database Migration
1. Review existing database schema in `storage.py`
2. Run migration script to add new tables and columns:
   - Add `notification_preferences` table
   - Add `digest_deliveries` table  
   - Add `paper_exclusions` table
3. Create appropriate indexes for performance

### Step 2: New Storage Methods
Add the following methods to `PaperStorage` class:

```python
def get_user_preferences(self, user_id: str) -> dict:
    """Retrieve notification preferences for a user."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM notification_preferences WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            # Convert JSON strings back to dicts
            return {
                'id': row[0],
                'user_id': row[1],
                'email_address': row[2],
                'preferred_format': row[3],
                'digest_frequency': row[4],
                'included_profile_ids': json.loads(row[5]) if row[5] else [],
                'excluded_profile_ids': json.loads(row[6]) if row[6] else [],
                'is_active': bool(row[7]),
                'created_at': row[8],
                'updated_at': row[9]
            }
        return None
    finally:
        conn.close()

def save_user_preferences(self, preferences: dict) -> bool:
    """Save notification preferences for a user."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    try:
        # Handle JSON serialization
        included_profiles = json.dumps(preferences.get('included_profile_ids', []))
        excluded_profiles = json.dumps(preferences.get('excluded_profile_ids', []))
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO notification_preferences 
            (user_id, email_address, preferred_format, digest_frequency,
             included_profile_ids, excluded_profile_ids, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                preferences['user_id'],
                preferences.get('email_address'),
                preferences.get('preferred_format', 'html'),
                preferences.get('digest_frequency', 'weekly'),
                included_profiles,
                excluded_profiles,
                preferences.get('is_active', True)
            )
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving preferences: {e}")
        return False
    finally:
        conn.close()
```

### Step 3: Digest Service Implementation

Create a new `digest_service.py` file with:

```python
class DigestService:
    def __init__(self, storage: PaperStorage, scorer: PublicationScorer):
        self.storage = storage
        self.scorer = scorer
        
    def get_excluded_papers(self, user_id: str, profile_id: str) -> list:
        """Get all PMIDs excluded by a user for a specific profile."""
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT pmid FROM paper_exclusions WHERE user_id = ? AND profile_id = ?",
                (user_id, profile_id)
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()
            
    def generate_profile_digest(self, profile_id: str, user_id: str, 
                               limit: int = 10, format_type: str = 'html') -> dict:
        """Generate digest for a specific profile and user."""
        # Fetch papers from the database
        papers = self.storage.fetch_papers(profile_id=profile_id, limit=limit * 3)
        
        # Filter out excluded papers
        excluded_papers = self.get_excluded_papers(user_id, profile_id)
        filtered_papers = [p for p in papers if p['pmid'] not in excluded_papers]
        
        # Score and sort papers
        profile = self.storage.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
            
        # For simplicity, using sample keywords - in practice this would be from the profile
        sample_keywords = {"viral": 1.0, "treatment": 0.8, "therapy": 0.7}
        sorted_papers = self.scorer.sort_papers_by_relevance(
            filtered_papers, [sample_keywords]
        )
        
        # Select top N papers
        selected_papers = sorted_papers[:limit]
        
        # Format digest content
        subject = f"[PubWatch] Weekly Digest - {profile['name']}"
        content = self._format_digest_content(selected_papers, format_type, subject)
        
        # Record the delivery in database
        delivery_id = self._record_delivery(profile_id, user_id, subject, 
                                          content, format_type)
        
        return {
            'delivery_id': delivery_id,
            'profile_id': profile_id,
            'user_id': user_id,
            'papers': selected_papers,
            'format': format_type,
            'content': content,
            'subject': subject,
            'generated_at': datetime.now()
        }
        
    def _record_delivery(self, profile_id: str, user_id: str, 
                        subject: str, content: str, format_type: str) -> str:
        """Record delivery in database."""
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()
        
        try:
            # Generate a unique delivery ID
            delivery_id = str(uuid.uuid4())
            
            cursor.execute(
                """
                INSERT INTO digest_deliveries 
                (id, profile_id, user_id, subject, content, format)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    delivery_id,
                    profile_id,
                    user_id,
                    subject,
                    content,
                    format_type
                )
            )
            conn.commit()
            return delivery_id
        finally:
            conn.close()
```

### Step 4: API Endpoints Implementation

Add the following endpoints to the command-line interface in `__main__.py`:

```python
def digest_command(args):
    """Handle digest commands."""
    storage = PaperStorage()
    scorer = PublicationScorer()
    digest_service = DigestService(storage, scorer)
    
    if args.generate:
        # Generate and send digest
        try:
            if args.profile_ids:
                profile_ids = args.profile_ids.split(',')
            else:
                profile_ids = [args.profile] if args.profile else []
                
            for profile_id in profile_ids:
                digest = digest_service.generate_profile_digest(
                    profile_id, 
                    args.user_id,
                    limit=args.limit,
                    format_type=args.format
                )
                print(f"Generated digest for {profile_id}")
        except Exception as e:
            print(f"Error generating digest: {e}")
    elif args.history:
        # Get delivery history
        deliveries = storage.get_digest_history(
            profile_id=args.profile,
            user_id=args.user_id,
            limit=args.limit
        )
        print("Digest History:")
        for delivery in deliveries:
            print(f"- {delivery['delivery_date']} - {delivery['subject']} ({delivery['status']})")

# Add arguments to parser
parser.add_argument("--generate", action="store_true", help="Generate digest")
parser.add_argument("--profile-ids", help="Comma separated list of profile IDs")
parser.add_argument("--user-id", help="User ID for the digest")
parser.add_argument("--history", action="store_true", help="Get delivery history")
parser.add_argument("--format", default="html", help="digest content format (html or text)")
```

### Step 5: Integration with Existing System

1. **Profile Versioning**: The new system should integrate with the existing profile versioning
2. **User Management**: Use existing user profiles system for associating users with profiles  
3. **Scoring Engine**: Leverage existing PublicationScorer for paper ranking
4. **Database Storage**: Utilize existing storage infrastructure and SQLite structure

## Testing Strategy

### Unit Tests Required
1. **Digest Generation Service**:
   - Test paper selection and ranking
   - Test different format outputs (HTML, text)
   - Test exclusion filtering
   - Test edge cases (no papers, empty profiles)

2. **Notification Service**:
   - Test email sending capability
   - Test error handling for failed deliveries
   - Test different content formats

3. **Database Integration**:
   - Test schema changes
   - Test user preference storage and retrieval
   - Test exclusion management

### Integration Tests
1. End-to-end digest generation flow
2. Full integration with existing paper fetching system  
3. Email delivery process testing
4. Error handling in various failure scenarios

## Performance Considerations

1. **Caching**: Cache frequently accessed user preferences
2. **Batch Processing**: Process multiple profiles in batches for efficiency
3. **Database Optimization**: Use indexes on frequently queried fields
4. **Asynchronous Processing**: Consider using task queues for expensive operations

## Security Requirements

1. **Authentication**: All API endpoints require authentication
2. **Authorization**: Validate user access to specific profiles and preferences
3. **Data Protection**: Secure handling of email addresses and personal information
4. **Rate Limiting**: Implement rate limiting on digest generation requests

## Deployment Considerations

1. **Migration Strategy**: Provide backward compatibility during schema updates
2. **Monitoring**: Implement logging for delivery success/failure
3. **Error Recovery**: Build resilience against intermittent failures
4. **Configuration Management**: Use environment variables for SMTP settings

## Monitoring and Logging

### Key Metrics to Track
- Digest generation time per profile
- Email delivery success rate
- User engagement with digests
- Error rates during processing
- Database query performance

### Log Levels
- **INFO**: Successful digest deliveries, regular operations
- **WARN**: Delivery failures, potential issues 
- **ERROR**: System errors, exceptions that need attention