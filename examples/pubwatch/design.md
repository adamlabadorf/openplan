# Design: Email Delivery Service

## Overview
This document outlines the design of the email delivery service that integrates with an SMTP service to deliver weekly digest emails to researchers. It includes handling successful deliveries, retries on failures, and error reporting.

## Architecture
- **Core Service**: EmailDeliveryService class that handles SMTP integration
- **Retry Mechanism**: Exponential backoff retry for up to 3 attempts
- **Error Handling**: Comprehensive error handling for invalid email addresses and service failures
- **Logging**: Success and failure logging with timestamps and recipient details

## Component Details

### EmailDeliveryService Class
- `send_digest(email_address, digest_content)`: Main method to send a digest
  - Validates email format
  - Attempts delivery via SMTP
  - Implements retry logic with exponential backoff
  - Logs success/failure events
  
### Retry Logic
- Uses exponential backoff with randomization (jitter)
- Maximum of 3 retry attempts
- Backoff time increases exponentially: 1s, 2s, 4s

### Error Handling
- Invalid email address detection and logging
- SMTP service unavailability with retry mechanism
- System alerts for persistent failures
- Detailed logs for troubleshooting

## Integration Points
- SMTP configuration parameters
- Notification service for system alerts
- Digest storage and retrieval services
- Profile management for email settings

## Data Models
### DigestDelivery
- `delivery_id`: Unique identifier
- `recipient_email`: Email address of the recipient
- `status`: Delivery status (success, failed)
- `timestamp`: When the delivery attempt occurred
- `retry_count`: Number of retries attempted

## API Endpoints
- POST /api/digest/deliver - Trigger delivery to a specific researcher
- GET /api/digest/{delivery_id}/status - Check status of a delivery attempt

## Configuration Parameters
- smtp_host: SMTP server host
- smtp_port: SMTP server port
- smtp_username: SMTP authentication username
- smtp_password: SMTP authentication password  
- retry_attempts: Maximum number of retry attempts (default: 3)
- retry_delay_base: Base delay for exponential backoff (in seconds)