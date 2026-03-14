# PubWatch API Specification
## Digest Delivery and Notification System

### Overview
This document specifies the API endpoints for the digest delivery and notification system within the PubWatch research literature collection platform.

### Base URL
`/api`

### Authentication
All endpoints require valid authentication using JWT tokens. The token must be included in the Authorization header:
```
Authorization: Bearer <jwt-token>
```

## Endpoints

### 1. Digest Endpoints

#### Generate Digest for Profile
```
POST /digests/generate
```

**Description**: Generates a digest report for specified topic profiles.

**Request Body**:
```json
{
  "profile_ids": ["profile-123", "profile-456"],
  "send_email": true,
  "recipients": ["researcher@example.com"],
  "format": "html",
  "include_excluded": false,
  "limit": 10
}
```

**Response Codes**:
- `200 OK`: Digest generated successfully
- `400 Bad Request`: Invalid parameters or profile IDs
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Server error during processing

#### Get Profile Digest
```
GET /digests/profile/{profile_id}
```

**Query Parameters**:
- `limit` (optional, integer): Maximum number of papers to include (default: 10)
- `format` (optional, string): Content format ("html" or "text", default: "html")
- `start_date` (optional, date): Filter papers from this date
- `end_date` (optional, date): Filter papers until this date
- `include_excluded` (optional, boolean): Include excluded papers (default: false)

**Response Body**:
```json
{
  "profile_id": "profile-123",
  "profile_name": "COVID-19 Research",
  "generated_at": "2023-12-15T08:00:00Z",
  "papers": [
    {
      "pmid": "12345678",
      "title": "Novel Therapeutic Approaches",
      "authors": ["Smith J", "Johnson A"],
      "abstract": "This study investigates...",
      "publication_date": "2023-12-15",
      "doi": "10.1234/ijv2023.12345",
      "relevance_score": 0.92,
      "is_excluded": false
    }
  ],
  "total_papers": 25,
  "format": "html"
}
```

#### Get Digest History
```
GET /digests/history
```

**Query Parameters**:
- `profile_id` (optional, string): Filter by specific profile
- `user_id` (optional, string): Filter by specific user
- `limit` (optional, integer): Maximum number of records to return (default: 20)
- `offset` (optional, integer): Offset for pagination (default: 0)

**Response Body**:
```json
{
  "deliveries": [
    {
      "id": "delivery-123",
      "profile_id": "profile-123",
      "user_id": "user-456",
      "delivery_date": "2023-12-15T08:00:00Z",
      "status": "delivered", 
      "format": "html",
      "subject": "[PubWatch] Weekly Digest - COVID-19 Research",
      "recipients": ["researcher@example.com"],
      "error_message": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### 2. Notification Preference Endpoints

#### Get User Preferences
```
GET /users/{user_id}/preferences
```

**Response Body**:
```json
{
  "user_id": "user-456",
  "email_address": "researcher@example.com",
  "preferred_format": "html",
  "digest_frequency": "weekly",
  "included_profile_ids": ["profile-123"],
  "excluded_profile_ids": ["profile-456"],
  "is_active": true,
  "created_at": "2023-12-01T10:00:00Z",
  "updated_at": "2023-12-15T08:00:00Z"
}
```

#### Update User Preferences
```
PUT /users/{user_id}/preferences
```

**Request Body**:
```json
{
  "email_address": "researcher@example.com",
  "preferred_format": "html",
  "digest_frequency": "weekly",
  "included_profile_ids": ["profile-123"],
  "excluded_profile_ids": ["profile-456"]
}
```

**Response**: 
```json
{
  "user_id": "user-456",
  "email_address": "researcher@example.com",
  "preferred_format": "html",
  "digest_frequency": "weekly",
  "included_profile_ids": ["profile-123"],
  "excluded_profile_ids": ["profile-456"],
  "is_active": true,
  "created_at": "2023-12-01T10:00:00Z",
  "updated_at": "2023-12-15T09:00:00Z"
}
```

### 3. Paper Exclusion Endpoints

#### Mark Paper as Excluded
```
POST /papers/{pmid}/exclude
```

**Request Body**:
```json
{
  "profile_id": "profile-123",
  "reason": "Not relevant to current research focus"
}
```

**Response**: 
```json
{
  "pmid": "12345678",
  "profile_id": "profile-123",
  "excluded_at": "2023-12-15T09:00:00Z",
  "reason": "Not relevant to current research focus"
}
```

#### Remove Paper Exclusion
```
DELETE /papers/{pmid}/exclude
```

**Query Parameters**:
- `profile_id`: The profile from which to remove the exclusion

**Response**: 
```json
{
  "pmid": "12345678",
  "profile_id": "profile-123",
  "status": "removed"
}
```

#### Get Excluded Papers
```
GET /papers/excluded
```

**Query Parameters**:
- `profile_id` (optional, string): Filter by specific profile
- `user_id` (optional, string): Filter by specific user

**Response Body**:
```json
{
  "exclusions": [
    {
      "pmid": "12345678",
      "profile_id": "profile-123",
      "user_id": "user-456",
      "excluded_at": "2023-12-15T09:00:00Z",
      "reason": "Not relevant to current research focus"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## Data Models

### Digest Delivery Model
```json
{
  "id": "delivery-123",
  "profile_id": "profile-123",
  "user_id": "user-456", 
  "delivery_date": "2023-12-15T08:00:00Z",
  "status": "delivered",
  "format": "html",
  "subject": "[PubWatch] Weekly Digest - Profile Name",
  "content": "<html>...</html>",
  "recipients": ["researcher@example.com"],
  "error_message": null,
  "created_at": "2023-12-15T08:00:00Z",
  "updated_at": "2023-12-15T08:00:00Z"
}
```

### Notification Preferences Model
```json
{
  "user_id": "user-456",
  "email_address": "researcher@example.com",
  "preferred_format": "html",
  "digest_frequency": "weekly",
  "included_profile_ids": ["profile-123"],
  "excluded_profile_ids": ["profile-456"],
  "is_active": true,
  "created_at": "2023-12-01T10:00:00Z",
  "updated_at": "2023-12-15T08:00:00Z"
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "profile_id",
        "reason": "Profile ID is required"
      }
    ]
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request parameters failed validation
- `PROFILE_NOT_FOUND`: Specified profile does not exist
- `USER_NOT_FOUND`: Specified user does not exist  
- `EMAIL_DELIVERY_FAILED`: Email could not be sent
- `DATABASE_ERROR`: Database operation failed

## Versioning

API version: `v1`

All endpoints are prefixed with `/api/v1/` for clarity, though the examples above omit this prefix.

## Rate Limits

- Maximum 100 requests per minute per authenticated user
- Burst limit of 50 requests within a 30-second window
- Exceeding limits will result in HTTP 429 responses