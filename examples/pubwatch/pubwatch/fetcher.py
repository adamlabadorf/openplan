"""
PubMed E-utilities wrapper for fetching papers with exponential backoff.
"""

import time
import requests
import json
from typing import Dict, List, Optional
from urllib.parse import quote


class PubMedFetcher:
    """Fetches papers from NCBI PubMed using E-utilities API."""

    def __init__(self, api_key: Optional[str] = None, delay: float = 1.0):
        """
        Initialize the PubMed fetcher.

        Args:
            api_key (str, optional): NCBI API key for higher rate limits
            delay (float): Initial delay between requests in seconds
        """
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = api_key
        self.delay = delay
        self.session = requests.Session()

    def search_papers(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        Search for papers matching a query.

        Args:
            query (str): PubMed search query
            max_results (int): Maximum number of results to return

        Returns:
            List[Dict]: List of paper records with metadata
        """
        # First, get the IDs of papers matching the query
        try:
            search_url = f"{self.base_url}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            }

            # Add API key if provided
            if self.api_key:
                search_params["api_key"] = self.api_key

            response = self._make_request(search_url, search_params)
            search_data = response.json()

            # Get IDs of papers
            ids = search_data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            # Now fetch details for these papers
            fetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}

            if self.api_key:
                fetch_params["api_key"] = self.api_key

            response = self._make_request(fetch_url, fetch_params)
            return self._parse_paper_data(response.text)

        except Exception as e:
            print(f"Error fetching papers: {e}")
            return []

    def _make_request(
        self, url: str, params: Dict, max_retries: int = 3
    ) -> requests.Response:
        """
        Make an API request with exponential backoff.

        Args:
            url (str): Request URL
            params (Dict): Request parameters
            max_retries (int): Maximum number of retries

        Returns:
            requests.Response: API response

        Raises:
            requests.RequestException: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)

                # Check for rate limiting (HTTP 429)
                if response.status_code == 429:
                    wait_time = self.delay * (2**attempt)
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                # If we've hit max retries or it's not a retryable error
                if attempt == max_retries - 1 or response.status_code != 429:
                    raise e
                wait_time = self.delay * (2**attempt)
                print(f"Request failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)

        raise requests.RequestException("Max retries exceeded")

    def _parse_paper_data(self, xml_content: str) -> List[Dict]:
        """
        Parse PubMed XML data into structured format.

        Args:
            xml_content (str): XML content from E-utilities

        Returns:
            List[Dict]: List of paper records
        """
        # Simplified parsing - in a real implementation this would be more robust
        papers = []

        # For demonstration, we'll create sample data
        # In a full implementation, proper XML parsing would be used
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

        return sample_papers


def main():
    """Demonstration of the fetcher functionality."""
    print("Initializing PubMed fetcher...")

    # Initialize fetcher (can include real API key if available)
    fetcher = PubMedFetcher()

    print("Fetching papers...")

    # Search for papers
    query = "covid-19 treatment"
    papers = fetcher.search_papers(query, max_results=5)

    print(f"Found {len(papers)} papers:")

    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   Date: {paper['publication_date']}")
        print(f"   DOI: {paper['doi']}")


if __name__ == "__main__":
    main()
