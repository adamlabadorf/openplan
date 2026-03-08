#!/usr/bin/env python3
"""
Demonstration of PubWatch functionality.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pubwatch"))

from pubwatch.fetcher import PubMedFetcher
from pubwatch.storage import PaperStorage


def demo():
    """Run a demonstration of the PubWatch system."""
    print("=== PubWatch - Researcher Publication Alert System Demo ===\n")

    # Initialize components
    print("1. Initializing PubMed Fetcher...")
    fetcher = PubMedFetcher()

    print("2. Initializing Local Storage...")
    storage = PaperStorage()

    print("\n3. Setting up topic profiles...")
    # Save some sample profiles
    storage.save_profile("covid-research", "COVID-19 Research", "covid-19 treatment")
    storage.save_profile("viral-pathogens", "Viral Pathogens", "virus pathogen")
    print("   - COVID-19 Research profile created")
    print("   - Viral Pathogens profile created")

    print("\n4. Fetching papers for COVID-19 research...")
    # In a real system, this would call the actual NCBI API
    # For demo purposes, we'll show what would happen
    print("   Fetching papers with search term: 'covid-19 treatment'")

    # Simulating fetch results
    print("   [Simulated] Fetched 2 papers:")
    print("   - Novel therapeutic approach to viral infections")
    print("   - Genomic analysis of emerging pathogens")

    # Save papers to storage
    sample_papers = [
        {
            "title": "Novel therapeutic approach to viral infections",
            "authors": ["Smith J", "Johnson A", "Williams B"],
            "abstract": "This study investigates new treatment approaches for viral infections...",
            "publication_date": "2023-12-15",
            "doi": "10.1234/ijv2023.12345",
            "pmid": "12345678",
        },
        {
            "title": "Genomic analysis of emerging pathogens",
            "authors": ["Brown C", "Davis E"],
            "abstract": "Genomic sequencing was performed on recently identified pathogens...",
            "publication_date": "2023-11-30",
            "doi": "10.1234/pmed2023.56789",
            "pmid": "87654321",
        },
    ]

    for paper in sample_papers:
        storage.save_paper(paper, "covid-research")

    print("   Papers saved to local database")

    print("\n5. Listing stored papers...")
    papers = storage.fetch_papers(profile_id="covid-research", limit=10)
    if papers:
        print(f"   Found {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"   {i}. {paper['title']}")
            print(f"      Authors: {', '.join(paper['authors'])}")
            print(f"      Date: {paper['publication_date']}")
            print(f"      DOI: {paper['doi']}")
    else:
        print("   No papers found.")


if __name__ == "__main__":
    demo()
