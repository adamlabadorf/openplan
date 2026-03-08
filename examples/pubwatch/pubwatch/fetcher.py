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
        """Parse PubMed XML (efetch retmode=xml) into structured dicts."""
        import xml.etree.ElementTree as ET

        papers = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return papers

        for article in root.findall(".//PubmedArticle"):
            medline = article.find("MedlineCitation")
            if medline is None:
                continue

            pmid_el = medline.find("PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            art = medline.find("Article")
            if art is None:
                continue

            # Title
            title_el = art.find("ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else ""

            # Abstract
            abstract_el = art.find("Abstract/AbstractText")
            abstract = "".join(abstract_el.itertext()) if abstract_el is not None else ""

            # Authors
            authors = []
            for author in art.findall("AuthorList/Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                initials = author.findtext("Initials", "")
                name = f"{last} {initials}" if initials else f"{last} {fore}"
                if name.strip():
                    authors.append(name.strip())

            # Publication date
            pub_date = art.find("Journal/JournalIssue/PubDate")
            if pub_date is not None:
                year = pub_date.findtext("Year", "")
                month = pub_date.findtext("Month", "")
                day = pub_date.findtext("Day", "")
                pub_date_str = "-".join(p for p in [year, month, day] if p)
            else:
                pub_date_str = ""

            # DOI
            doi = ""
            for id_el in article.findall(".//ArticleId"):
                if id_el.get("IdType") == "doi":
                    doi = id_el.text or ""

            papers.append({
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "publication_date": pub_date_str,
                "doi": doi,
            })

        return papers


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
