"""
Publication Scoring Engine for PubWatch - Researcher Publication Alert System
"""

import sqlite3
from typing import Dict, List, Tuple
from collections import Counter


class PublicationScorer:
    """Scores publications against topic profiles based on keyword matching."""

    def __init__(self, db_path: str = "papers.db"):
        """
        Initialize the publication scorer.

        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path

    def score_publication(
        self,
        paper: Dict,
        profile_keywords: List[Dict],
        profile_weights: Dict[str, float],
    ) -> Tuple[float, Dict[str, float]]:
        """
        Score a publication against topic profiles.

        Args:
            paper (Dict): Publication data with title and abstract
            profile_keywords (List[Dict]): List of keyword sets for each profile
            profile_weights (Dict[str, float]): Weights for each profile

        Returns:
            Tuple[float, Dict[str, float]]: Overall score (0-1) and individual profile scores
        """
        # Get the complete text from paper title, abstract, and authors
        paper_text = self._get_paper_text(paper)

        # Initialize profile scores
        profile_scores = {}

        # Score against each profile
        for i, keywords in enumerate(profile_keywords):
            profile_id = f"profile_{i}"
            score = self._calculate_profile_score(paper_text, keywords)
            profile_scores[profile_id] = score

        # Calculate weighted average of all profile scores
        if not profile_scores:
            overall_score = 0.0
        else:
            total_weighted_score = 0.0
            total_weight = 0.0

            for profile_id, score in profile_scores.items():
                weight = profile_weights.get(profile_id, 1.0)
                total_weighted_score += score * weight
                total_weight += weight

            if total_weight > 0:
                overall_score = total_weighted_score / total_weight
            else:
                overall_score = 0.0

        return overall_score, profile_scores

    def _get_paper_text(self, paper: Dict) -> str:
        """
        Combine relevant text from publication for scoring.

        Args:
            paper (Dict): Paper metadata

        Returns:
            str: Combined text content
        """
        text_parts = []

        # Add title and abstract
        if paper.get("title"):
            text_parts.append(paper["title"])
        if paper.get("abstract"):
            text_parts.append(paper["abstract"])
        if paper.get("authors"):
            # Add authors as text to match keyword patterns
            if isinstance(paper["authors"], list):
                text_parts.extend(paper["authors"])
            else:
                text_parts.append(paper["authors"])

        return " ".join(text_parts).lower()

    def _calculate_profile_score(self, paper_text: str, keywords: Dict) -> float:
        """
        Calculate score for a single profile based on keyword matching.

        Args:
            paper_text (str): Text content from publication
            keywords (Dict): Keywords with importances

        Returns:
            float: Score between 0 and 1
        """
        # Convert paper text to word frequency count
        words = paper_text.split()
        word_counts = Counter(words)

        # Initialize score components
        matched_importance = 0.0
        total_importance = 0.0

        # For each keyword in the profile, check matches and sum up importance
        for keyword, importance in keywords.items():
            if keyword.lower() in paper_text:
                # Use frequency of keyword in document to amplify score
                frequency = word_counts.get(keyword.lower(), 0)
                matched_importance += importance * frequency
                total_importance += importance

        # Normalize the overall match score to between 0 and 1
        return matched_importance / total_importance if total_importance > 0 else 0.0

    def sort_papers_by_relevance(
        self, papers: List[Dict], profile_keywords: List[Dict]
    ) -> List[Dict]:
        """
        Sort papers by descending relevance score.
        For identical scores, sort alphabetically by title.

        Args:
            papers (List[Dict]): Papers to sort
            profile_keywords (List[Dict]): Keywords for matching

        Returns:
            List[Dict]: Sorted papers
        """
        # Score each paper and add to list
        scored_papers = []
        for paper in papers:
            overall_score, _ = self.score_publication(paper, profile_keywords, {})
            scored_papers.append((paper, overall_score))

        # Sort by score (descending) then by title (ascending) for ties
        scored_papers.sort(key=lambda x: (-x[1], x[0]["title"].lower()))

        # Return only papers without scores
        return [paper for paper, _ in scored_papers]

    def get_profile_scores(self, profile_id: str) -> Dict[str, Dict]:
        """
        Get score information for a specific topic profile.

        Args:
            profile_id (str): ID of the topic profile

        Returns:
            Dict[str, Dict]: Scores and metadata for the profile
        """
        # In a real implementation, this would access the profiles database
        # For now we'll return an empty structure
        return {}

    def get_papers_with_scores(self, profile_id: str) -> List[Dict]:
        """
        Get papers from database with scores for given profile.

        Args:
            profile_id (str): Topic profile ID

        Returns:
            List[Dict]: Papers with their scores and metadata
        """
        # This would connect to the database and retrieve papers
        # For now, we'll return basic placeholder structure
        return []
