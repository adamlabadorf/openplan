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

        # Create profile_versions table for version tracking of profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                name TEXT,
                description TEXT,
                search_terms TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
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

        # Create notification_preferences table for digest delivery preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                email_address TEXT,
                preferred_format TEXT DEFAULT 'html',
                digest_frequency TEXT DEFAULT 'weekly',
                included_profile_ids TEXT,
                excluded_profile_ids TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create digest_deliveries table to track delivery history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS digest_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                delivery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                format TEXT,
                subject TEXT,
                content TEXT,
                recipients TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create paper_exclusions table to track papers excluded from digests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_exclusions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                pmid TEXT NOT NULL,
                user_id TEXT NOT NULL,
                excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user notification preferences."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, email_address, preferred_format, digest_frequency,
                   included_profile_ids, excluded_profile_ids, is_active,
                   created_at, updated_at 
            FROM notification_preferences 
            WHERE user_id = ?
        """,
            (user_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "email_address": row[2],
                "preferred_format": row[3],
                "digest_frequency": row[4],
                "included_profile_ids": row[5],
                "excluded_profile_ids": row[6],
                "is_active": bool(row[7]),
                "created_at": row[8],
                "updated_at": row[9],
            }
        return None

    def update_user_preferences(
        self, user_id: str, preferences: Dict
    ) -> Optional[Dict]:
        """Update user notification preferences."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # First check if preferences exist for this user
        existing = self.get_user_preferences(user_id)

        if existing:
            # Update existing preferences
            cursor.execute(
                """
                UPDATE notification_preferences 
                SET email_address = ?, preferred_format = ?, digest_frequency = ?,
                    included_profile_ids = ?, excluded_profile_ids = ?, is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                (
                    preferences.get("email_address"),
                    preferences.get("preferred_format"),
                    preferences.get("digest_frequency"),
                    preferences.get("included_profile_ids"),
                    preferences.get("excluded_profile_ids"),
                    preferences.get("is_active", True),
                    user_id,
                ),
            )
        else:
            # Insert new preferences
            cursor.execute(
                """
                INSERT INTO notification_preferences 
                (user_id, email_address, preferred_format, digest_frequency,
                 included_profile_ids, excluded_profile_ids, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    preferences.get("email_address"),
                    preferences.get("preferred_format"),
                    preferences.get("digest_frequency"),
                    preferences.get("included_profile_ids"),
                    preferences.get("excluded_profile_ids"),
                    preferences.get("is_active", True),
                ),
            )

        conn.commit()
        conn.close()

        # Return the updated/created preferences
        return self.get_user_preferences(user_id)

    def get_digest_deliveries(
        self,
        profile_id: str = None,
        user_id: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict]:
        """Get digest delivery history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if profile_id and user_id:
            cursor.execute(
                """
                SELECT id, profile_id, user_id, delivery_date, status, format,
                       subject, content, recipients, error_message, created_at, updated_at
                FROM digest_deliveries 
                WHERE profile_id = ? AND user_id = ?
                ORDER BY delivery_date DESC
                LIMIT ? OFFSET ?
            """,
                (profile_id, user_id, limit, offset),
            )
        elif profile_id:
            cursor.execute(
                """
                SELECT id, profile_id, user_id, delivery_date, status, format,
                       subject, content, recipients, error_message, created_at, updated_at
                FROM digest_deliveries 
                WHERE profile_id = ?
                ORDER BY delivery_date DESC
                LIMIT ? OFFSET ?
            """,
                (profile_id, limit, offset),
            )
        elif user_id:
            cursor.execute(
                """
                SELECT id, profile_id, user_id, delivery_date, status, format,
                       subject, content, recipients, error_message, created_at, updated_at
                FROM digest_deliveries 
                WHERE user_id = ?
                ORDER BY delivery_date DESC
                LIMIT ? OFFSET ?
            """,
                (user_id, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT id, profile_id, user_id, delivery_date, status, format,
                       subject, content, recipients, error_message, created_at, updated_at
                FROM digest_deliveries 
                ORDER BY delivery_date DESC
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

        rows = cursor.fetchall()
        conn.close()

        deliveries = []
        for row in rows:
            deliveries.append(
                {
                    "id": row[0],
                    "profile_id": row[1],
                    "user_id": row[2],
                    "delivery_date": row[3],
                    "status": row[4],
                    "format": row[5],
                    "subject": row[6],
                    "content": row[7],
                    "recipients": row[8],
                    "error_message": row[9],
                    "created_at": row[10],
                    "updated_at": row[11],
                }
            )

        return deliveries

    def get_top_papers(
        self,
        profile_ids: List[str],
        limit: int = 10,
        start_date: str = None,
        end_date: str = None,
        include_excluded: bool = False,
    ) -> List[Dict]:
        """Retrieve top papers for specified profiles."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Start building the query
        query = """
            SELECT p.id, p.pmid, p.title, p.authors, p.abstract, p.publication_date, p.doi, 
                   p.profile_id, p.fetched_at
            FROM papers p
            WHERE p.profile_id IN ({})
        """.format(",".join("?" * len(profile_ids)))

        params = profile_ids

        # Add date filters if provided
        if start_date:
            query += " AND p.publication_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND p.publication_date <= ?"
            params.append(end_date)

        # Order by publication date (most recent first) and limit results
        query += " ORDER BY p.publication_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        papers = []
        for row in rows:
            papers.append(
                {
                    "id": row[0],
                    "pmid": row[1],
                    "title": row[2],
                    "authors": row[3],
                    "abstract": row[4],
                    "publication_date": row[5],
                    "doi": row[6],
                    "profile_id": row[7],
                    "fetched_at": row[8],
                }
            )

        return papers

    def create_digest_delivery(self, delivery_data: Dict) -> Dict:
        """Create a new digest delivery record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO digest_deliveries 
            (profile_id, user_id, delivery_date, status, format,
             subject, content, recipients, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                delivery_data.get("profile_id"),
                delivery_data.get("user_id"),
                delivery_data.get("delivery_date"),
                delivery_data.get("status", "pending"),
                delivery_data.get("format"),
                delivery_data.get("subject"),
                delivery_data.get("content"),
                delivery_data.get("recipients"),
                delivery_data.get("error_message"),
            ),
        )

        delivery_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Return the created delivery record
        return self.get_digest_delivery(delivery_id)

    def get_digest_delivery(self, delivery_id: int) -> Optional[Dict]:
        """Get a specific digest delivery by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, profile_id, user_id, delivery_date, status, format,
                   subject, content, recipients, error_message, created_at, updated_at
            FROM digest_deliveries 
            WHERE id = ?
        """,
            (delivery_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "profile_id": row[1],
                "user_id": row[2],
                "delivery_date": row[3],
                "status": row[4],
                "format": row[5],
                "subject": row[6],
                "content": row[7],
                "recipients": row[8],
                "error_message": row[9],
                "created_at": row[10],
                "updated_at": row[11],
            }
        return None

    def get_excluded_papers(
        self,
        profile_id: str = None,
        user_id: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict]:
        """Get excluded papers by profile or user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if profile_id and user_id:
            cursor.execute(
                """
                SELECT id, profile_id, pmid, user_id, excluded_at, reason, created_at
                FROM paper_exclusions 
                WHERE profile_id = ? AND user_id = ?
                ORDER BY excluded_at DESC
                LIMIT ? OFFSET ?
            """,
                (profile_id, user_id, limit, offset),
            )
        elif profile_id:
            cursor.execute(
                """
                SELECT id, profile_id, pmid, user_id, excluded_at, reason, created_at
                FROM paper_exclusions 
                WHERE profile_id = ?
                ORDER BY excluded_at DESC
                LIMIT ? OFFSET ?
            """,
                (profile_id, limit, offset),
            )
        elif user_id:
            cursor.execute(
                """
                SELECT id, profile_id, pmid, user_id, excluded_at, reason, created_at
                FROM paper_exclusions 
                WHERE user_id = ?
                ORDER BY excluded_at DESC
                LIMIT ? OFFSET ?
            """,
                (user_id, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT id, profile_id, pmid, user_id, excluded_at, reason, created_at
                FROM paper_exclusions 
                ORDER BY excluded_at DESC
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

        rows = cursor.fetchall()
        conn.close()

        exclusions = []
        for row in rows:
            exclusions.append(
                {
                    "id": row[0],
                    "profile_id": row[1],
                    "pmid": row[2],
                    "user_id": row[3],
                    "excluded_at": row[4],
                    "reason": row[5],
                    "created_at": row[6],
                }
            )

        return exclusions

    def mark_paper_excluded(
        self, pmid: str, profile_id: str, user_id: str, reason: str = None
    ) -> Dict:
        """Mark a paper as excluded from notifications."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if exclusion already exists
        cursor.execute(
            """
            SELECT id FROM paper_exclusions 
            WHERE profile_id = ? AND pmid = ? AND user_id = ?
        """,
            (profile_id, pmid, user_id),
        )

        existing = cursor.fetchone()

        if not existing:
            cursor.execute(
                """
                INSERT INTO paper_exclusions (profile_id, pmid, user_id, reason)
                VALUES (?, ?, ?, ?)
            """,
                (profile_id, pmid, user_id, reason),
            )

            exclusion_id = cursor.lastrowid
        else:
            # Update existing exclusion
            cursor.execute(
                """
                UPDATE paper_exclusions 
                SET reason = ? 
                WHERE id = ?
            """,
                (reason, existing[0]),
            )

            exclusion_id = existing[0]

        conn.commit()
        conn.close()

        # Return the created/updated exclusion record
        return self.get_paper_exclusion(exclusion_id)

    def get_paper_exclusion(self, exclusion_id: int) -> Optional[Dict]:
        """Get a specific paper exclusion by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, profile_id, pmid, user_id, excluded_at, reason, created_at
            FROM paper_exclusions 
            WHERE id = ?
        """,
            (exclusion_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "profile_id": row[1],
                "pmid": row[2],
                "user_id": row[3],
                "excluded_at": row[4],
                "reason": row[5],
                "created_at": row[6],
            }
        return None

    def remove_paper_exclusion(self, pmid: str, profile_id: str, user_id: str) -> bool:
        """Remove a paper exclusion."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM paper_exclusions 
            WHERE profile_id = ? AND pmid = ? AND user_id = ?
        """,
            (profile_id, pmid, user_id),
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

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

    def create_profile_version(self, profile_id: str):
        """
        Create a version record for the given profile.

        Args:
            profile_id (str): The ID of the profile to version

        Returns:
            bool: True if version created successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current profile data
            cursor.execute(
                """
                SELECT name, description, search_terms 
                FROM profiles 
                WHERE id = ?
            """,
                (profile_id,),
            )

            row = cursor.fetchone()
            if not row:
                return False

            name, description, search_terms = row

            # Get the maximum version number for this profile
            cursor.execute(
                """
                SELECT COALESCE(MAX(version_number), 0) 
                FROM profile_versions 
                WHERE profile_id = ?
            """,
                (profile_id,),
            )

            max_version = cursor.fetchone()[0]
            version_number = max_version + 1

            # Insert new version record
            cursor.execute(
                """
                INSERT INTO profile_versions 
                (profile_id, version_number, name, description, search_terms)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    profile_id,
                    version_number,
                    name or "",
                    description or "",
                    search_terms or "",
                ),
            )

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Database error creating profile version: {e}")
            return False
        finally:
            conn.close()

    def duplicate_profile(self, profile_id: str, new_name: str = None):
        """
        Duplicate an existing profile with a new name.

        Args:
            profile_id (str): ID of the profile to duplicate
            new_name (str, optional): New name for the duplicated profile

        Returns:
            dict: The new profile information or None if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get the original profile data
            cursor.execute(
                """
                SELECT id, name, description, search_terms, parent_profile_id
                FROM profiles 
                WHERE id = ? AND is_deleted = FALSE
            """,
                (profile_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            original_id, name, description, search_terms, parent_profile_id = row

            # Generate a new unique ID for the duplicated profile
            import uuid

            new_profile_id = str(uuid.uuid4())

            # If no new name specified, use the original with " (copy)" suffix
            if new_name is None:
                new_name = f"{name} (copy)"

            # Create the new profile
            cursor.execute(
                """
                INSERT INTO profiles 
                (id, name, description, search_terms, parent_profile_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    new_profile_id,
                    new_name,
                    description or "",
                    search_terms or "",
                    original_id,
                ),
            )

            conn.commit()

            # Create version record for the original profile
            self.create_profile_version(profile_id)

            return {
                "id": new_profile_id,
                "name": new_name,
                "description": description or "",
                "search_terms": search_terms or "",
                "parent_profile_id": original_id,
            }

        except sqlite3.Error as e:
            print(f"Database error duplicating profile: {e}")
            return None
        finally:
            conn.close()

    def create_profile_version(self, profile_id: str):
        """
        Create a version record for the given profile.

        Args:
            profile_id (str): The ID of the profile to version

        Returns:
            bool: True if version created successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current profile data
            cursor.execute(
                """
                SELECT name, description, search_terms 
                FROM profiles 
                WHERE id = ?
            """,
                (profile_id,),
            )

            row = cursor.fetchone()
            if not row:
                return False

            name, description, search_terms = row

            # Get the maximum version number for this profile
            cursor.execute(
                """
                SELECT COALESCE(MAX(version_number), 0) 
                FROM profile_versions 
                WHERE profile_id = ?
            """,
                (profile_id,),
            )

            max_version = cursor.fetchone()[0]
            version_number = max_version + 1

            # Insert new version record
            cursor.execute(
                """
                INSERT INTO profile_versions 
                (profile_id, version_number, name, description, search_terms)
                VALUES (?, ?, ?, ?, ?)
            """,
                (profile_id, version_number, name, description, search_terms),
            )

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Database error creating profile version: {e}")
            return False
        finally:
            conn.close()

    def duplicate_profile(self, profile_id: str, new_name: str = None):
        """
        Duplicate an existing profile with a new name.

        Args:
            profile_id (str): ID of the profile to duplicate
            new_name (str, optional): New name for the duplicated profile

        Returns:
            dict: The new profile information or None if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get the original profile data
            cursor.execute(
                """
                SELECT id, name, description, search_terms, parent_profile_id
                FROM profiles 
                WHERE id = ? AND is_deleted = FALSE
            """,
                (profile_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            original_id, name, description, search_terms, parent_profile_id = row

            # Generate a new unique ID for the duplicated profile
            import uuid

            new_profile_id = str(uuid.uuid4())

            # If no new name specified, use the original with " (copy)" suffix
            if new_name is None:
                new_name = f"{name} (copy)"

            # Create the new profile
            cursor.execute(
                """
                INSERT INTO profiles 
                (id, name, description, search_terms, parent_profile_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (new_profile_id, new_name, description, search_terms, original_id),
            )

            conn.commit()

            # Create version record for the original profile
            self.create_profile_version(profile_id)

            return {
                "id": new_profile_id,
                "name": new_name,
                "description": description,
                "search_terms": search_terms,
                "parent_profile_id": original_id,
            }

        except sqlite3.Error as e:
            print(f"Database error duplicating profile: {e}")
            return None
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

    def restore_profile_version(self, profile_id: str, version_number: int):
        """
        Restore a specific version of a profile.

        Args:
            profile_id (str): The ID of the profile to restore
            version_number (int): Version number to restore

        Returns:
            bool: True if restoration was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get the version data
            cursor.execute(
                """
                SELECT name, description, search_terms 
                FROM profile_versions 
                WHERE profile_id = ? AND version_number = ?
            """,
                (profile_id, version_number),
            )

            row = cursor.fetchone()
            if not row:
                return False

            name, description, search_terms = row

            # Update the profile with historical data
            cursor.execute(
                """
                UPDATE profiles 
                SET name = ?, description = ?, search_terms = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (name, description, search_terms, profile_id),
            )

            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"Database error restoring profile version: {e}")
            return False
        finally:
            conn.close()

    def get_profile_versions(self, profile_id: str):
        """
        Retrieve version history for the given profile.

        Args:
            profile_id (str): The ID of the profile to retrieve versions for

        Returns:
            list: List of version records or empty list if none found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, version_number, name, description, search_terms, created_at
                FROM profile_versions 
                WHERE profile_id = ?
                ORDER BY version_number ASC
            """,
                (profile_id,),
            )

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            versions = []
            for row in rows:
                version = dict(zip(columns, row))
                versions.append(version)

            return versions

        except sqlite3.Error as e:
            print(f"Database error retrieving profile versions: {e}")
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
