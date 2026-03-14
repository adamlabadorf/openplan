"""
Main entry point for PubWatch - Researcher Publication Alert System
"""

import argparse
import json
from .fetcher import PubMedFetcher
from .storage import PaperStorage
from .digest_service import DigestService
from .scoring import PublicationScorer
from .notification_service import NotificationService


def preferences_command(args):
    """Handle preference management commands."""
    storage = PaperStorage()

    if args.user_id:
        # Get current preferences
        preferences = storage.get_user_preferences(args.user_id)
        if preferences:
            print("Current preferences:")
            for key, value in preferences.items():
                print(f"  {key}: {value}")
        else:
            print("No preferences found for this user.")
    elif args.user_id and (
        args.email
        or args.format
        or args.frequency
        or args.included_profiles
        or args.excluded_profiles
    ):
        # Update preferences
        preferences = {}
        if args.email:
            preferences["email_address"] = args.email
        if args.format:
            preferences["preferred_format"] = args.format
        if args.frequency:
            preferences["digest_frequency"] = args.frequency
        if args.included_profiles:
            preferences["included_profile_ids"] = args.included_profiles
        if args.excluded_profiles:
            preferences["excluded_profile_ids"] = args.excluded_profiles

        updated_preferences = storage.update_user_preferences(args.user_id, preferences)
        print("Updated preferences:")
        for key, value in updated_preferences.items():
            print(f"  {key}: {value}")
    else:
        print("Usage: pubwatch preferences --user-id <user_id> [options]")
        print("Options:")
        print("  --email <address>: Set email address")
        print("  --format <html|text>: Set preferred format")
        print("  --frequency <daily|weekly|monthly>: Set delivery frequency")
        print("  --included-profiles <profile1,profile2>: Comma-separated list")
        print("  --excluded-profiles <profile1,profile2>: Comma-separated list")


def digest_command(args):
    """Handle digest commands."""
    storage = PaperStorage()
    scorer = PublicationScorer()

    # Initialize notification service if SMTP configuration is available
    notification_service = None
    try:
        import os

        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

        # Only create notification service if all required config is present
        if smtp_host and smtp_username and smtp_password:
            notification_service = NotificationService(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
            )
        else:
            print(
                "Warning: SMTP configuration incomplete. Email delivery will not be available."
            )
    except Exception as e:
        print(
            f"Warning: Failed to initialize SMTP configuration for email delivery: {e}"
        )

    digest_service = DigestService(storage, scorer, notification_service)

    if args.generate:
        # Generate and potentially send digest
        try:
            if args.profile_ids:
                profile_ids = args.profile_ids.split(",")
            else:
                profile_ids = [args.profile] if args.profile else []

            for profile_id in profile_ids:
                print(f"Generating digest for {profile_id}.")
                digest = digest_service.generate_profile_digest(
                    profile_id, args.user_id, limit=args.limit, format_type=args.format
                )
                print(f"Generated digest with {digest['paper_count']} papers")

                # If sending via email is requested and notification service available
                if args.send_email and notification_service:
                    print(f"Sending digest to user {args.user_id}.")
                    if args.recipient:
                        recipient = args.recipient
                    else:
                        preferences = storage.get_user_preferences(args.user_id)
                        recipient = (
                            preferences.get("email_address") if preferences else None
                        )

                    if recipient:
                        delivery_result = digest_service.send_digest_to_user(
                            profile_id,
                            args.user_id,
                            recipient=recipient,
                            format_type=args.format,
                        )
                        print(f"Delivery status: {delivery_result['status']}")
                    else:
                        print("No recipient email address found for user")
                elif args.send_email and not notification_service:
                    print(
                        "Email sending requested but no SMTP configuration available."
                    )

        except Exception as e:
            print(f"Error generating digest: {e}")
    elif args.history:
        # Get delivery history
        deliveries = digest_service.get_delivery_history(
            profile_id=args.profile, user_id=args.user_id, limit=args.limit
        )
        print("Digest History:")
        for delivery in deliveries:
            print(
                f"- {delivery['delivery_date']} - {delivery['subject']} ({delivery['status']})"
            )
    elif args.send:
        # Send specific digest to a user
        if not args.profile or not args.user_id or not args.recipient:
            print(
                "Usage: pubwatch digest --send --profile <profile_id> --user-id <user_id> --recipient <email>"
            )
        else:
            try:
                delivery_result = digest_service.send_digest_to_user(
                    args.profile,
                    args.user_id,
                    recipient=args.recipient,
                    format_type=args.format,
                )
                print(f"Delivery status: {delivery_result['status']}")
            except Exception as e:
                print(f"Error sending digest: {e}")


def main():
    """Main entry point to run pubwatch commands."""
    parser = argparse.ArgumentParser(
        description="PubWatch - Automated Literature Collection"
    )
    parser.add_argument(
        "command",
        choices=["fetch", "list", "profile", "preferences", "digest"],
        help="Command to execute",
    )
    parser.add_argument("--profile", help="Topic profile name to use")
    parser.add_argument("--query", help="Search query for fetching papers")
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of papers"
    )

    # Profile management arguments
    parser.add_argument("--name", help="Profile name")
    parser.add_argument("--description", help="Profile description")
    parser.add_argument("--search-terms", help="Search terms for the profile")
    parser.add_argument("--profile-id", help="Specific profile ID")
    parser.add_argument("--duplicate", action="store_true", help="Duplicate a profile")
    parser.add_argument("--restore", type=int, help="Restore a specific version number")

    # Preferences arguments
    parser.add_argument("--user-id", help="User identifier for preferences")
    parser.add_argument("--email", help="User email address")
    parser.add_argument(
        "--format", default="html", help="Preferred digest format (html or text)"
    )
    parser.add_argument("--frequency", help="Digest frequency (daily, weekly, monthly)")
    parser.add_argument(
        "--included-profiles", help="Comma-separated list of included profile IDs"
    )
    parser.add_argument(
        "--excluded-profiles", help="Comma-separated list of excluded profile IDs"
    )

    # Digest arguments
    parser.add_argument("--generate", action="store_true", help="Generate digest")
    parser.add_argument("--profile-ids", help="Comma separated list of profile IDs")
    parser.add_argument(
        "--send-email", action="store_true", help="Send email with digest"
    )
    parser.add_argument("--recipient", help="Recipient email address for sending")
    parser.add_argument(
        "--send", action="store_true", help="Send specific digest to recipient"
    )

    args = parser.parse_args()

    if args.command == "fetch":
        fetch_command(args)
    elif args.command == "list":
        list_command(args)
    elif args.command == "profile":
        profile_command(args)
    elif args.command == "preferences":
        preferences_command(args)
    elif args.command == "digest":
        digest_command(args)


def fetch_command(args):
    """Handle fetching papers."""
    print(f"Fetching papers for profile: {args.profile}")

    # Initialize components
    fetcher = PubMedFetcher()
    storage = PaperStorage()

    # Get search terms - either from command line or from stored profile
    if args.query:
        search_terms = args.query
    else:
        # Try to get search terms from the stored profile
        try:
            profile = storage.get_profile(args.profile)
            if profile and profile.get("search_terms"):
                search_terms = profile["search_terms"]
            else:
                # Default query for demonstration purposes
                search_terms = (
                    "covid-19 treatment"
                    if args.profile == "covid-19 research"
                    else "viral pathogen"
                )
        except Exception:
            # Default fallback
            search_terms = (
                "covid-19 treatment"
                if args.profile == "covid-19 research"
                else "viral pathogen"
            )

    print(f"Searching with terms: {search_terms}")

    # Fetch papers from PubMed API
    papers = fetcher.search_papers(search_terms, max_results=args.limit)

    if papers:
        print(f"Found {len(papers)} papers:")
        for paper in papers:
            print(f"  - {paper['title']}")

        # Store papers with profile association
        for paper in papers:
            storage.save_paper(paper, args.profile or "default")

        print("Papers saved to local database.")
    else:
        print("No papers found.")


def list_command(args):
    """Handle listing papers."""
    print(f"Listing papers for profile: {args.profile}")

    # Initialize storage
    storage = PaperStorage()

    # Fetch and display papers
    papers = storage.fetch_papers(profile_id=args.profile, limit=args.limit)

    if papers:
        print(f"Found {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            print(
                f"   Authors: {', '.join(paper['authors']) if isinstance(paper['authors'], list) else paper['authors']}"
            )
            print(f"   Date: {paper['publication_date']}")
            print(f"   DOI: {paper['doi']}")
            print()
    else:
        print("No papers found.")


def profile_command(args):
    """Handle profile management commands."""
    storage = PaperStorage()

    if args.name and args.search_terms:
        # Create new profile
        profile = storage.create_profile(args.name, args.search_terms, args.description)
        if profile:
            print(f"Created profile: {profile['name']} (ID: {profile['id']})")
        else:
            print("Failed to create profile")
    elif args.profile_id and args.duplicate:
        # Duplicate existing profile
        new_profile = storage.duplicate_profile(args.profile_id, args.name)
        if new_profile:
            print(
                f"Duplicated profile: {new_profile['name']} (ID: {new_profile['id']})"
            )
        else:
            print("Failed to duplicate profile")
    elif args.profile_id and args.restore:
        # Restore a specific version
        success = storage.restore_profile_version(args.profile_id, args.restore)
        if success:
            print(f"Restored profile {args.profile_id} to version {args.restore}")
        else:
            print(
                f"Failed to restore profile {args.profile_id} to version {args.restore}"
            )
    elif args.profile_id:
        # Get specific profile
        profile = storage.get_profile(args.profile_id)
        if profile:
            print(json.dumps(profile, indent=2))
        else:
            print("Profile not found")
    else:
        # List all profiles
        profiles = storage.list_profiles()
        print(f"Found {len(profiles)} profiles:")
        for profile in profiles:
            print(f"- {profile['name']} ({profile['id']})")


if __name__ == "__main__":
    main()
