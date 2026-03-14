"""
Email notification service for PubWatch - Researcher Publication Alert System.
Handles SMTP integration for delivering weekly digest emails with retry logic and error handling.
"""

import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Custom exception for email delivery failures."""

    pass


class NotificationService:
    """Handles email delivery for PubWatch digests with retry logic and error notifications."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        """
        Initialize the notification service.

        Args:
            smtp_host (str): SMTP server host
            smtp_port (int): SMTP server port
            smtp_username (str): Email authentication username
            smtp_password (str): Email authentication password
            max_retries (int): Maximum number of retry attempts for deliveries
            base_delay (float): Base delay in seconds for exponential backoff
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.max_retries = max_retries
        self.base_delay = base_delay

        # Validate SMTP configuration
        if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
            raise ValueError("All SMTP configuration parameters are required")

    def send_digest_email(
        self, recipient: str, subject: str, content: str, format_type: str = "html"
    ) -> bool:
        """
        Send a digest email to the specified recipient with retry logic.

        Args:
            recipient (str): Email address of the recipient
            subject (str): Email subject line
            content (str): Email body content
            format_type (str): Content format ('html' or 'text')

        Returns:
            bool: True if delivery succeeded, False otherwise

        Raises:
            EmailDeliveryError: If all retry attempts fail
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Create email message
                msg = MIMEMultipart()
                msg["From"] = self.smtp_username
                msg["To"] = recipient
                msg["Subject"] = subject

                # Add body content based on format type
                if format_type == "html":
                    msg.attach(MIMEText(content, "html"))
                else:
                    msg.attach(MIMEText(content, "plain"))

                # Connect to SMTP server and send email
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()

                logger.info(f"Successfully sent digest to {recipient}")

                # Create success log entry with timestamp and recipient details
                success_log = {
                    "timestamp": datetime.now().isoformat(),
                    "recipient": recipient,
                    "status": "success",
                    "delivery_id": str(uuid.uuid4()),
                    "subject": subject,
                }
                logger.info(f"Delivery log: {success_log}")

                return True

            except smtplib.SMTPRecipientsRefused as e:
                # Handle case when email address is invalid
                logger.error(f"Invalid recipient email address {recipient}: {e}")
                error_msg = f"Invalid recipient email address: {recipient}"
                raise EmailDeliveryError(error_msg) from e

            except smtplib.SMTPException as e:
                logger.warning(f"SMTP error on attempt {attempt + 1}: {e}")

                # If this is the last attempt, raise the error
                if attempt == self.max_retries:
                    error_msg = f"Failed to deliver email after {self.max_retries + 1} attempts: {e}"
                    logger.error(error_msg)
                    raise EmailDeliveryError(error_msg)

                # Calculate delay with exponential backoff
                delay = self.base_delay * (2**attempt)
                logger.info(f"Retrying delivery in {delay:.2f} seconds...")
                time.sleep(delay)

            except Exception as e:
                # For non-SMTP errors, log them and retry
                logger.warning(f"Non-SMTP error on attempt {attempt + 1}: {e}")

                # If this is the last attempt, raise the error
                if attempt == self.max_retries:
                    error_msg = f"Failed to deliver email after {self.max_retries + 1} attempts: {e}"
                    logger.error(error_msg)
                    raise EmailDeliveryError(error_msg)

                # Calculate delay with exponential backoff
                delay = self.base_delay * (2**attempt)
                logger.info(f"Retrying delivery in {delay:.2f} seconds...")
                time.sleep(delay)

        return False

    def send_error_notification(self, admin_email: str, error_details: Dict) -> bool:
        """
        Send an error notification email to system administrators.

        Args:
            admin_email (str): Email address of the administrator
            error_details (Dict): Dictionary containing error information

        Returns:
            bool: True if notification was sent successfully
        """
        try:
            subject = f"[PubWatch Alert] Digest Delivery Error - {error_details.get('timestamp', '')}"

            # Create a structured error message
            content = f"""
            PubWatch Digest Delivery System Error Report
            
            Error Details:
            ==============
            Timestamp: {error_details.get("timestamp", "Unknown")}
            Error Type: {error_details.get("error_type", "Unknown")}
            Message: {error_details.get("message", "No message provided")}
            
            Affected Components:
            ===================
            Profile ID: {error_details.get("profile_id", "Unknown")}
            User ID: {error_details.get("user_id", "Unknown")}
            Delivery ID: {error_details.get("delivery_id", "Unknown")}
            
            Error Context:
            ==============
            Action: {error_details.get("action", "Unknown action")}
            Recipients: {error_details.get("recipients", "None")}
            
            Troubleshooting Steps:
            ======================
            1. Check SMTP configuration
            2. Verify recipient addresses
            3. Review system logs for detailed error information
            4. Ensure email server is accessible
            
            This is an automated notification. Please investigate and resolve the issue.
            """

            # Log that we're sending the error alert
            logger.info(f"Sending error notification to {admin_email}")

            return self.send_digest_email(admin_email, subject, content, "plain")

        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False

    def batch_send_emails(self, email_batches: List[Dict]) -> Dict[str, int]:
        """
        Send emails in batches with individual retry handling.

        Args:
            email_batches (List[Dict]): List of email dictionaries with keys:
                - recipient: Email address
                - subject: Email subject
                - content: Email body
                - format_type: Content format ('html' or 'text')

        Returns:
            Dict[str, int]: Summary statistics of delivery attempts
        """
        results = {"success_count": 0, "failure_count": 0, "failed_recipients": []}

        for batch in email_batches:
            try:
                recipient = batch.get("recipient")
                if not recipient:
                    logger.warning("Skipping email - no recipient specified")
                    continue

                success = self.send_digest_email(
                    recipient=recipient,
                    subject=batch.get("subject", "PubWatch Digest"),
                    content=batch.get("content", ""),
                    format_type=batch.get("format_type", "html"),
                )

                if success:
                    results["success_count"] += 1
                else:
                    results["failure_count"] += 1
                    results["failed_recipients"].append(recipient)

            except EmailDeliveryError as e:
                logger.error(f"Failed to send email to {batch.get('recipient')}: {e}")
                results["failure_count"] += 1
                results["failed_recipients"].append(batch.get("recipient", "Unknown"))

        return results


def main():
    """Example usage of the notification service."""
    # This would be configured via environment variables in a real application
    try:
        # Example configuration (these would come from env vars)
        smtp_host = "smtp.example.com"
        smtp_port = 587
        smtp_username = "user@example.com"
        smtp_password = "your-password-here"

        # Initialize service
        notification_service = NotificationService(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            max_retries=3,
            base_delay=1.0,
        )

        print("Notification service initialized successfully!")

        # Example email sending (uncomment for testing)
        # success = notification_service.send_digest_email(
        #     recipient="test@example.com",
        #     subject="Test Digest",
        #     content="<h1>Test Digest Content</h1>",
        #     format_type='html'
        # )

    except Exception as e:
        print(f"Error initializing NotificationService: {e}")


if __name__ == "__main__":
    main()
