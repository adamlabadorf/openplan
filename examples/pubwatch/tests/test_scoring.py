"""
Test cases for the PublicationScorer functionality.
"""

import unittest
from pubwatch.scoring import PublicationScorer


class TestPublicationScorer(unittest.TestCase):
    """Tests for PublicationScorer class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scorer = PublicationScorer()

    def test_score_publication_basic(self):
        """Test basic publication scoring functionality."""
        paper = {
            "title": "Novel treatment of viral infections",
            "abstract": "This study investigates new treatment approaches for viral infections...",
            "authors": ["Smith J", "Johnson A"],
        }

        profile_keywords = [
            {"viral": 1.0, "treatment": 0.8},
            {"infection": 0.9, "therapy": 0.7},
        ]

        overall_score, profile_scores = self.scorer.score_publication(
            paper, profile_keywords, {}
        )

        # Basic check - scores should be between 0 and 1
        self.assertGreaterEqual(overall_score, 0)
        self.assertLessEqual(overall_score, 1)

        # Profile scores should also be properly calculated
        self.assertIsInstance(profile_scores, dict)
        self.assertEqual(len(profile_scores), 2)

    def test_sort_papers_by_relevance(self):
        """Test sorting of papers by relevance."""
        papers = [
            {"title": "Paper A", "abstract": "viral treatment"},
            {"title": "Paper B", "abstract": "infection therapy"},
            {"title": "Paper C", "abstract": "general research"},
        ]

        profile_keywords = [
            {"viral": 1.0, "treatment": 0.8},
        ]

        sorted_papers = self.scorer.sort_papers_by_relevance(papers, profile_keywords)

        # Check that we get a list back
        self.assertIsInstance(sorted_papers, list)
        self.assertEqual(len(sorted_papers), 3)

    def test_get_paper_text(self):
        """Test extraction of text from paper."""
        paper = {
            "title": "Test Paper",
            "abstract": "This is an abstract",
            "authors": ["Author A", "Author B"],
        }

        text = self.scorer._get_paper_text(paper)

        # Check that text contains all components
        self.assertIn("test paper", text)
        self.assertIn("this is an abstract", text)
        self.assertIn("author a", text)
        self.assertIn("author b", text)

    def test_calculate_profile_score(self):
        """Test calculation of profile scores."""
        paper_text = "viral treatment infection therapy"
        keywords = {"viral": 1.0, "treatment": 0.8, "infection": 0.9}

        score = self.scorer._calculate_profile_score(paper_text, keywords)

        # Score should be between 0 and 1
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)


if __name__ == "__main__":
    unittest.main()
