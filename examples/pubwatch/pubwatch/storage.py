"""
Local storage for fetched papers.
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional
from pathlib import Path


class PaperStorage:
    """Handles local storage of papers with metadata."""

    def __init__(self, db_path: str = "papers.db"):
        """
        Initialize the paper storage.

        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create papers table for storing paper metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pmid TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                publication_date TEXT,
                doi TEXT,
                profile_id TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create profiles table to track different topic profiles with enhanced schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                search_terms TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                parent_profile_id TEXT,
                FOREIGN KEY (parent_profile_id) REFERENCES profiles(id)
            )
        """)

        # Create profile_keywords table to support hierarchical topic organization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                importance REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            )
        """)

        # Create user_profiles table to link users to their profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            )
        """)

        conn.commit()
        conn.close()

    def save_paper(self, paper: Dict, profile_id: str):
        """
        Save a paper to the database.

        Args:
            paper (Dict): Paper metadata
            profile_id (str): ID of the topic profile this paper matches
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO papers 
                (pmid, title, authors, abstract, publication_date, doi, profile_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    paper.get("pmid"),
                    paper.get("title"),
                    ", ".join(paper.get("authors", [])),
                    paper.get("abstract"),
                    paper.get("publication_date"),
                    paper.get("doi"),
                    profile_id,
                ),
            )

            conn.commit()

        except sqlite3.Error as e:
            print(f"Database error saving paper: {e}")
        finally:
            conn.close()

    def save_profile(
        self, profile_id: str, name: str, search_terms: str, description: str = ""
    ):
        """
        Save a topic profile.

        Args:
            profile_id (str): Unique identifier for the profile
            name (str): Name of the profile
            search_terms (str): Search terms used for this profile
            description (str): Description of the profile
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO profiles 
                (id, name, description, search_terms, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (profile_id, name, description, search_terms),
            )

            conn.commit()

        except sqlite3.Error as e:
            print(f"Database error saving profile: {e}")
        finally:
            conn.close()

    def create_profile(
        self,
        name: str,
        search_terms: str,
        description: str = "",
        parent_profile_id: str = None,
    ):
        """
        Create a new topic profile.

        Args:
            name (str): Name of the profile
            search_terms (str): Search terms used for this profile
            description (str): Description of the profile
            parent_profile_id (str, optional): Parent profile ID for hierarchical relationships

        Returns:
            dict: Created profile information
        """
        import uuid

        profile_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO profiles 
                (id, name, description, search_terms, parent_profile_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (profile_id, name, description, search_terms, parent_profile_id),
            )

            conn.commit()

            return {
                "id": profile_id,
                "name": name,
                "description": description,
                "search_terms": search_terms,
                "parent_profile_id": parent_profile_id,
            }

        except sqlite3.Error as e:
            print(f"Database error creating profile: {e}")
            return None
        finally:
            conn.close()

    def get_profile(self, profile_id: str):
        """
        Retrieve a topic profile by ID.

        Args:
            profile_id (str): Unique identifier for the profile

        Returns:
            dict: Profile information or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, name, description, search_terms, created_at, updated_at, parent_profile_id
                FROM profiles 
                WHERE id = ? AND is_deleted = FALSE
            """,
                (profile_id,),
            )

            row = cursor.fetchone()

            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "search_terms": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "parent_profile_id": row[6],
                }
            else:
                return None

        except sqlite3.Error as e:
            print(f"Database error retrieving profile: {e}")
            return None
        finally:
            conn.close()

    def update_profile(
        self,
        profile_id: str,
        name: str = None,
        search_terms: str = None,
        description: str = None,
    ):
        """
        Update an existing topic profile.

        Args:
            profile_id (str): Unique identifier for the profile
            name (str, optional): Updated name
            search_terms (str, optional): Updated search terms
            description (str, optional): Updated description

        Returns:
            bool: True if updated successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Build dynamic update query
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)

            if search_terms is not None:
                updates.append("search_terms = ?")
                params.append(search_terms)

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            updates.append("updated_at = CURRENT_TIMESTAMP")

            if not updates:
                return False

            query = f"UPDATE profiles SET {', '.join(updates)} WHERE id = ?"
            params.append(profile_id)

            cursor.execute(query, params)

            conn.commit()

            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"Database error updating profile: {e}")
            return False
        finally:
            conn.close()

    def delete_profile(self, profile_id: str):
        """
        Soft-delete a topic profile by ID.

        Args:
            profile_id (str): Unique identifier for the profile

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE profiles 
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (profile_id,),
            )

            conn.commit()

            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"Database error deleting profile: {e}")
            return False
        finally:
            conn.close()

    def list_profiles(self, user_id: str = None):
        """
        List all active topic profiles.

        Args:
            user_id (str, optional): Filter by specific user's profiles

        Returns:
            list: List of profile dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if user_id:
                # Join with user_profiles table to filter by user
                cursor.execute(
                    """
                    SELECT p.id, p.name, p.description, p.search_terms, 
                           p.created_at, p.updated_at, p.parent_profile_id
                    FROM profiles p
                    JOIN user_profiles up ON p.id = up.profile_id
                    WHERE p.is_deleted = FALSE AND up.user_id = ?
                    ORDER BY p.created_at DESC
                """,
                    (user_id,),
                )
            else:
                cursor.execute("""
                    SELECT id, name, description, search_terms, created_at, updated_at, parent_profile_id
                    FROM profiles 
                    WHERE is_deleted = FALSE
                    ORDER BY created_at DESC
                """)

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            profiles = []
            for row in rows:
                profile = dict(zip(columns, row))
                profiles.append(profile)

            return profiles

        except sqlite3.Error as e:
            print(f"Database error listing profiles: {e}")
            return []
        finally:
            conn.close()

    def fetch_papers(
        self, profile_id: str = None, limit: int = 10, offset: int = 0
    ) -> List[Dict]:
        """
        Fetch papers from the database.

        Args:
            profile_id (str, optional): Filter by specific profile
            limit (int): Maximum number of papers to return
            offset (int): Offset for pagination

        Returns:
            List[Dict]: List of paper records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if profile_id:
                cursor.execute(
                    """
                    SELECT * FROM papers 
                    WHERE profile_id = ? 
                    ORDER BY fetched_at DESC 
                    LIMIT ? OFFSET ?
                """,
                    (profile_id, limit, offset),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM papers 
                    ORDER BY fetched_at DESC 
                    LIMIT ? OFFSET ?
                """,
                    (limit, offset),
                )

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            papers = []
            for row in rows:
                paper = dict(zip(columns, row))
                # Convert authors string back to list
                if paper.get("authors"):
                    paper["authors"] = paper["authors"].split(", ")
                papers.append(paper)

            return papers

        except sqlite3.Error as e:
            print(f"Database error fetching papers: {e}")
            return []
        finally:
            conn.close()


def main():
    """Demonstration of the storage functionality."""
    print("Initializing paper storage...")

    # Initialize storage
    storage = PaperStorage()

    # Save sample profiles
    storage.save_profile("covid-research", "COVID-19 Research", "covid-19 treatment")
    storage.save_profile("viral-pathogens", "Viral Pathogens", "virus pathogen")

    print("Sample profiles saved.")

    # Sample paper data
    sample_paper = {
        "pmid": "12345678",
        "title": "Novel therapeutic approach to viral infections",
        "authors": ["Smith J", "Johnson A"],
        "abstract": "This study investigates new treatment approaches for viral infections...",
        "publication_date": "2023-12-15",
        "doi": "10.1234/ijv2023.12345",
    }

    # Save a paper
    storage.save_paper(sample_paper, "viral-pathogens")
    print("Sample paper saved.")

    # Fetch papers
    papers = storage.fetch_papers(limit=5)
    print(f"Fetched {len(papers)} papers:")

    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']} (PMID: {paper['pmid']})")


if __name__ == "__main__":
    main()
