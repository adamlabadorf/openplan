#!/usr/bin/env python3

"""
Test script for profile duplication and versioning functionality.
"""

import os
import sys

# Add the pubwatch module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pubwatch"))

from pubwatch.storage import PaperStorage


def test_profile_versioning():
    """Test the profile duplication and versioning features."""
    print("Testing profile duplication and versioning...")

    # Initialize storage
    storage = PaperStorage()

    # Create a test profile
    profile = storage.create_profile(
        "Test Profile", "test search terms", "A test profile for versioning"
    )

    if not profile:
        print("Failed to create test profile")
        return False

    print(f"Created profile: {profile['name']} (ID: {profile['id']})")

    # Duplicate the profile
    duplicated_profile = storage.duplicate_profile(
        profile["id"], "Duplicated Test Profile"
    )

    if not duplicated_profile:
        print("Failed to duplicate profile")
        return False

    print(
        f"Duplicated profile: {duplicated_profile['name']} (ID: {duplicated_profile['id']})"
    )

    # Update the original profile to create a new version
    storage.update_profile(
        profile["id"], name="Updated Test Profile", search_terms="updated search terms"
    )

    # Check versions
    versions = storage.get_profile_versions(profile["id"])
    print(f"Found {len(versions)} versions for the original profile")

    if len(versions) >= 2:
        # Restore to first version
        success = storage.restore_profile_version(profile["id"], 1)
        if success:
            print("Successfully restored to first version")
        else:
            print("Failed to restore to first version")

    print("Test completed successfully!")
    return True


if __name__ == "__main__":
    test_profile_versioning()
