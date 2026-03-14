"""
Digest service for PubWatch - Researcher Publication Alert System.
Handles generation of weekly paper digests with SMTP integration, error handling, and alerting.
"""

import smtplib
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import json

from .storage import PaperStorage
from .scoring import PublicationScorer
from .notification_service import NotificationService, EmailDeliveryError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DigestService:
    """Handles generation and delivery of weekly paper digests with error handling and notifications."""

    def __init__(
        self,
        storage: PaperStorage,
        scorer: PublicationScorer,
        notification_service: Optional["NotificationService"] = None,
    ):
        """
        Initialize the digest service.

        Args:
            storage (PaperStorage): Storage instance for database access
            scorer (PublicationScorer): Scoring engine for paper relevance
            notification_service (NotificationService, optional): Email delivery service
        """
        self.storage = storage
        self.scorer = scorer
        self.notification_service = notification_service

    def generate_profile_digest(
        self, profile_id: str, user_id: str, limit: int = 10, format_type: str = "html"
    ) -> Dict:
        """
        Generate a digest for a specific profile and user.

        Args:
            profile_id (str): ID of the topic profile
            user_id (str): ID of the user receiving the digest
            limit (int): Number of papers to include in digest
            format_type (str): Content format ('html' or 'text')

        Returns:
            Dict: Digest information including content and metadata
        """
        logger.info(f"Generating digest for profile {profile_id} for user {user_id}")

        try:
            # Fetch papers associated with the profile
            papers = self.storage.fetch_papers(profile_id=profile_id, limit=limit * 3)

            if not papers:
                logger.warning(f"No papers found for profile {profile_id}")
                return {
                    "profile_id": profile_id,
                    "user_id": user_id,
                    "papers": [],
                    "format": format_type,
                    "content": "",
                    "subject": f"[PubWatch] No papers found for {profile_id}",
                    "generated_at": datetime.now(),
                }

            # Filter out excluded papers
            excluded_papers = self._get_excluded_papers(user_id, profile_id)

            filtered_papers = [p for p in papers if p["pmid"] not in excluded_papers]

            if not filtered_papers:
                logger.info(f"No non-excluded papers found for profile {profile_id}")

            # Score and sort papers using the existing scoring engine
            profile = self.storage.get_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")

            # For simplicity, we'll use sample keywords - in a real scenario this would come from profile
            # In a real implementation this would be more sophisticated
            sample_keywords = {"viral": 1.0, "treatment": 0.8, "therapy": 0.7}
            sorted_papers = self.scorer.sort_papers_by_relevance(
                filtered_papers, [sample_keywords]
            )

            # Select top N papers
            selected_papers = sorted_papers[:limit]

            # Format digest content
            subject = f"[PubWatch] Weekly Digest - {profile['name']}"
            content = self._format_digest_content(selected_papers, format_type, subject)

            return {
                "profile_id": profile_id,
                "user_id": user_id,
                "papers": selected_papers,
                "format": format_type,
                "content": content,
                "subject": subject,
                "generated_at": datetime.now(),
                "paper_count": len(selected_papers),
            }

        except Exception as e:
            logger.error(f"Error generating digest for profile {profile_id}: {e}")
            raise

    def _get_excluded_papers(self, user_id: str, profile_id: str) -> List[str]:
        """Get all PMIDs excluded by a user for a specific profile."""
        exclusions = self.storage.get_excluded_papers(
            profile_id=profile_id, user_id=user_id
        )
        return [exclusion["pmid"] for exclusion in exclusions if exclusion.get("pmid")]

    def _format_digest_content(
        self, papers: List[Dict], format_type: str, subject: str
    ) -> str:
        """
        Format paper content into a digest email.

        Args:
            papers (List[Dict]): Papers to include in the digest
            format_type (str): Content format ('html' or 'text')
            subject (str): Email subject line

        Returns:
            str: Formatted digest content
        """
        if not papers:
            if format_type == "html":
                return f"""
                <html>
                <body>
                    <h2>{subject}</h2>
                    <p>No relevant papers found for this period.</p>
                    <p>Please adjust your profile settings to receive more appropriate content.</p>
                </body>
                </html>
                """
            else:
                return f"{subject}\n\nNo relevant papers found for this period.\nPlease adjust your profile settings to receive more appropriate content."

        if format_type == "html":
            # HTML format
            html_content = [
                "<html>",
                "<head><title>PubWatch Digest</title></head>",
                '<body style="font-family: Arial, sans-serif;">',
                f"<h1>{subject}</h1>",
                "<p>Here are the top papers for your research profiles:</p>",
                "<ul>",
            ]

            for paper in papers:
                html_content.append("<li>")

                # Add title
                title = paper.get("title", "Untitled")
                html_content.append(f"<strong>{title}</strong><br/>")

                # Add authors (if available)
                authors = paper.get("authors", [])
                if isinstance(authors, list):
                    authors_str = ", ".join(authors)
                else:
                    authors_str = str(authors)
                html_content.append(f"Authors: {authors_str}<br/>")

                # Add publication date
                date = paper.get("publication_date", "Unknown date")
                html_content.append(f"Date: {date}<br/>")

                # Add DOI (if available)
                doi = paper.get("doi")
                if doi:
                    html_content.append(
                        f'DOI: <a href="https://doi.org/{doi}">{doi}</a><br/>'
                    )

                # Add abstract (shortened for brevity)
                abstract = paper.get("abstract", "")
                if abstract:
                    # Show first 200 characters of abstract
                    truncated_abstract = (
                        abstract[:200] + "..." if len(abstract) > 200 else abstract
                    )
                    html_content.append(
                        f"<p><strong>Abstract:</strong> {truncated_abstract}</p>"
                    )

                html_content.append("</li>")

            html_content.extend(
                [
                    "</ul>",
                    "<p>Thank you for using PubWatch!</p>",
                    "<p>Best regards,<br/>The PubWatch Team</p>",
                    "</body>",
                    "</html>",
                ]
            )

            return "\n".join(html_content)
        else:
            # Plain text format
            text_content = [subject, "=" * len(subject), ""]
            for i, paper in enumerate(papers, 1):
                title = paper.get("title", "Untitled")
                text_content.append(f"{i}. {title}")

                # Add authors (if available)
                authors = paper.get("authors", [])
                if isinstance(authors, list):
                    authors_str = ", ".join(authors)
                else:
                    authors_str = str(authors)
                text_content.append(f"   Authors: {authors_str}")

                # Add publication date
                date = paper.get("publication_date", "Unknown date")
                text_content.append(f"   Date: {date}")

                # Add DOI (if available)
                doi = paper.get("doi")
                if doi:
                    text_content.append(f"   DOI: https://doi.org/{doi}")

                # Add abstract (shortened for brevity)
                abstract = paper.get("abstract", "")
                if abstract:
                    # Show first 200 characters of abstract
                    truncated_abstract = (
                        abstract[:200] + "..." if len(abstract) > 200 else abstract
                    )
                    text_content.append(f"   Abstract: {truncated_abstract}")

                text_content.append("")

            text_content.extend(
                ["Thank you for using PubWatch!", "Best regards,", "The PubWatch Team"]
            )

            return "\n".join(text_content)

    def send_digest_to_user(
        self, profile_id: str, user_id: str, recipient: str, format_type: str = "html"
    ) -> Dict:
        """
        Generate a digest and send it to the specified user.

        Args:
            profile_id (str): ID of the topic profile
            user_id (str): ID of the user receiving the digest
            recipient (str): Email address of the recipient
            format_type (str): Content format ('html' or 'text')

        Returns:
            Dict: Delivery result information including success status and tracking details
        """
        delivery_result = {
            "delivery_id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "user_id": user_id,
            "recipient": recipient,
            "status": "pending",
            "error_message": None,
            "sent_at": None,
            "format": format_type,
        }

        try:
            # Generate digest
            digest = self.generate_profile_digest(
                profile_id, user_id, format_type=format_type
            )

            if not self.notification_service:
                logger.warning(
                    "No notification service configured - digest generated but not sent"
                )
                return delivery_result

            # Send email
            success = self.notification_service.send_digest_email(
                recipient=recipient,
                subject=digest["subject"],
                content=digest["content"],
                format_type=format_type,
            )

            delivery_result["status"] = "delivered" if success else "failed"
            delivery_result["sent_at"] = datetime.now().isoformat()

            # Record delivery in database (even failed deliveries)
            self._record_delivery(delivery_result, digest)

            logger.info(f"Digest sent successfully to {recipient}")

        except Exception as e:
            error_msg = str(e)
            delivery_result["status"] = "failed"
            delivery_result["error_message"] = error_msg
            delivery_result["sent_at"] = datetime.now().isoformat()
            logger.error(f"Failed to send digest to {recipient}: {error_msg}")

            # Record failure in database
            self._record_delivery(delivery_result, None)

            # Send an alert to system administrators if notification service available
            if self.notification_service and hasattr(
                self.notification_service, "send_error_notification"
            ):
                try:
                    error_details = {
                        "timestamp": datetime.now().isoformat(),
                        "error_type": type(e).__name__,
                        "message": error_msg,
                        "profile_id": profile_id,
                        "user_id": user_id,
                        "delivery_id": delivery_result["delivery_id"],
                        "action": "send_digest_email",
                        "recipients": [recipient],
                    }
                    # Admin email would be configured elsewhere
                    admin_email = (
                        "admin@example.com"  # This should come from configuration
                    )
                    self.notification_service.send_error_notification(
                        admin_email, error_details
                    )
                except Exception as admin_err:
                    logger.error(f"Failed to send error notification: {admin_err}")

            raise

        return delivery_result

    def _record_delivery(self, delivery_info: Dict, digest_info: Optional[Dict]):
        """Record delivery information in the database."""
        try:
            if not delivery_info.get("delivery_id"):
                delivery_info["delivery_id"] = str(uuid.uuid4())

            # Create delivery data for storage
            recipient = delivery_info.get("recipient", "")
            delivery_data = {
                "profile_id": delivery_info["profile_id"],
                "user_id": delivery_info["user_id"],
                "delivery_date": delivery_info.get("sent_at")
                or datetime.now().isoformat(),
                "status": delivery_info["status"],
                "format": delivery_info["format"],
                "subject": digest_info.get("subject") if digest_info else "",
                "content": digest_info.get("content") if digest_info else "",
                "recipients": json.dumps([recipient]) if recipient else "",
                "error_message": delivery_info.get("error_message"),
            }

            # Save to database
            self.storage.create_digest_delivery(delivery_data)

        except Exception as e:
            logger.error(f"Failed to record delivery: {e}")

    def get_delivery_history(
        self, profile_id: str = None, user_id: str = None, limit: int = 20
    ) -> List[Dict]:
        """
        Get digest delivery history.

        Args:
            profile_id (str, optional): Filter by specific profile
            user_id (str, optional): Filter by specific user
            limit (int): Maximum number of records to return

        Returns:
            List[Dict]: Delivery history records
        """
        return self.storage.get_digest_deliveries(
            profile_id=profile_id, user_id=user_id, limit=limit
        )


def main():
    """Example usage of the digest service."""
    try:
        # Initialize components
        storage = PaperStorage()
        scorer = PublicationScorer()

        # Note: NotificationService needs SMTP credentials and would be initialized separately
        # For testing purposes, we'll create a basic service without email capability

        digest_service = DigestService(storage, scorer)

        print("Digest service initialized successfully!")

        # Example usage:
        # preferences = storage.get_user_preferences(user_id="user123")
        # if preferences and preferences.get('email_address'):
        #     result = digest_service.send_digest_to_user(
        #         profile_id="profile456",
        #         user_id="user123",
        #         recipient=preferences['email_address'],
        #         format_type=preferences.get('preferred_format', 'html')
        #     )

    except Exception as e:
        print(f"Error initializing DigestService: {e}")


if __name__ == "__main__":
    main()
