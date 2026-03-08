"""
Main entry point for PubWatch - Researcher Publication Alert System
"""

import argparse
import json
from .fetcher import PubMedFetcher
from .storage import PaperStorage


def main():
    """Main entry point to run pubwatch commands."""
    parser = argparse.ArgumentParser(
        description="PubWatch - Automated Literature Collection"
    )
    parser.add_argument(
        "command", choices=["fetch", "list", "profile"], help="Command to execute"
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

    args = parser.parse_args()

    if args.command == "fetch":
        fetch_command(args)
    elif args.command == "list":
        list_command(args)
    elif args.command == "profile":
        profile_command(args)


def fetch_command(args):
    """Handle fetching papers."""
    print(f"Fetching papers for profile: {args.profile}")

    # Initialize components
    fetcher = PubMedFetcher()
    storage = PaperStorage()

    # In a real implementation, we would load the actual search terms from a profile
    if args.query:
        search_terms = args.query
    else:
        # Default query for demonstration purposes
        search_terms = (
            "covid-19 treatment"
            if args.profile == "covid-19 research"
            else "viral pathogen"
        )

    print(f"Searching with terms: {search_terms}")

    # Fetch papers (in this demo, we'll just show mock data)
    papers = fetcher.search_papers(search_terms, max_results=args.limit)

    if papers:
        print(f"Found {len(papers)} papers:")
        for paper in papers:
            print(f"  - {paper['title']}")

        # Store papers
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
