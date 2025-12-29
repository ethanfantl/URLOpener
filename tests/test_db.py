import unittest
import sys
import os
import sqlite3

# Ensure we can import the database module from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        """
        Runs before EVERY test method.
        Creates a fresh, isolated in-memory database so tests don't interfere with each other.
        """
        self.db = DatabaseManager(":memory:")

    def tearDown(self):
        """
        Runs after EVERY test method.
        Closes the database connection to prevent memory leaks and ensure clean state.
        """
        if self.db.memory_conn:
            self.db.memory_conn.close()

    # --- GROUP MANAGEMENT TESTS ---

    def test_add_new_group_successfully(self):
        """
        Verifies that a standard group name can be added to the database
        and successfully retrieved.
        """
        self.db.add_group("Work")
        groups = self.db.get_groups()
        self.assertIn("Work", groups)

    def test_add_duplicate_group_does_not_create_duplicate(self):
        """
        Verifies that adding the same group name twice does not crash the app
        or create two entries. The second attempt should be silently ignored.
        """
        self.db.add_group("Work")
        self.db.add_group("Work")
        groups = self.db.get_groups()
        # Expect 2 groups: The default 'General' + the one 'Work' we just added.
        self.assertEqual(len(groups), 2) 

    def test_database_initializes_with_default_general_group(self):
        """
        Verifies that a fresh database is never empty; it should always
        contain the 'General' group by default to prevent orphaned URLs.
        """
        groups = self.db.get_groups()
        self.assertIn("General", groups)

    def test_delete_existing_group(self):
        """
        Verifies that a group can be successfully removed from the database list.
        """
        self.db.add_group("Temporary")
        self.db.delete_group("Temporary")
        groups = self.db.get_groups()
        self.assertNotIn("Temporary", groups)

    def test_deleting_group_removes_associated_urls(self):
        """
        Verifies Referential Integrity: When a folder/group is deleted, 
        all URLs inside that folder must also be deleted to prevent data orphans.
        """
        self.db.add_group("FolderX")
        self.db.add_url("http://example.com", "FolderX")
        
        # Action: Delete the group
        self.db.delete_group("FolderX")
        
        # Check: Are the URLs gone?
        urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(urls), 0)

    def test_add_group_with_special_characters_and_emojis(self):
        """
        Verifies that the database handles non-standard characters (Unicode/Emojis)
        correctly, which is important for modern user input.
        """
        name = "🚀 Startups & Money $$$"
        self.db.add_group(name)
        self.assertIn(name, self.db.get_groups())

    # --- URL MANAGEMENT TESTS ---

    def test_add_valid_url_to_group(self):
        """
        Verifies the happy path: Adding a standard URL to an existing group.
        Checks if the URL is stored and associated with the correct group.
        """
        self.db.add_url("https://google.com", "General")
        urls = self.db.get_urls_by_group("General")
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0][2], "https://google.com")

    def test_add_url_generates_title_from_domain_if_missing(self):
        """
        Verifies that if we add a URL without explicitly providing a title,
        the system automatically extracts a readable title (domain name) from the URL string.
        """
        self.db.add_url("https://www.github.com", "General")
        urls = self.db.get_urls_by_group("General")
        
        # 'urlparse' logic usually extracts 'www.github.com' as the netloc
        self.assertEqual(urls[0][1], "www.github.com")

    def test_add_duplicate_url_is_ignored(self):
        """
        Verifies uniqueness constraints: The same URL should not be added twice,
        preventing clutter in the user's list.
        """
        self.db.add_url("https://unique.com", "General")
        self.db.add_url("https://unique.com", "General") # Should be ignored
        
        urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(urls), 1)

    def test_add_url_to_non_existent_group_fails_silently(self):
        """
        Verifies error handling: If we try to add a URL to a group that doesn't exist,
        it should not crash the app. Ideally, the operation is skipped.
        """
        self.db.add_url("https://lost.com", "Ghost Group")
        urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(urls), 0)

    def test_retrieve_urls_filtered_by_specific_group(self):
        """
        Verifies filtering logic: When asking for URLs in 'Music', we should 
        NOT see URLs that belong to 'General'.
        """
        self.db.add_group("Music")
        self.db.add_url("http://spotify.com", "Music")
        self.db.add_url("https://google.com", "General")
        
        music_urls = self.db.get_urls_by_group("Music")
        self.assertEqual(len(music_urls), 1)
        self.assertEqual(music_urls[0][2], "http://spotify.com")

    def test_retrieve_all_urls_across_groups(self):
        """
        Verifies the 'All URLs' view: It should aggregate links from every 
        single group into one list.
        """
        self.db.add_group("A")
        self.db.add_group("B")
        self.db.add_url("http://a.com", "A")
        self.db.add_url("http://b.com", "B")
        
        all_items = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(all_items), 2)

    def test_delete_specific_url(self):
        """
        Verifies that a specific URL can be deleted by its ID.
        """
        self.db.add_url("https://delete.me", "General")
        
        # Step 1: Fetch the ID of the newly added URL
        urls = self.db.get_urls_by_group("General")
        url_id = urls[0][0]
        
        # Step 2: Delete it
        self.db.delete_url(url_id)
        
        # Step 3: Verify it is gone
        urls_after = self.db.get_urls_by_group("General")
        self.assertEqual(len(urls_after), 0)

    def test_bulk_add_multiple_urls_successfully(self):
        """
        Verifies the bulk import feature allows adding a list of tuples 
        (Title, URL, Group) all at once.
        """
        data = [
            ("Google", "https://google.com", "General"),
            ("Yahoo", "https://yahoo.com", "General")
        ]
        count = self.db.bulk_add_urls(data)
        self.assertEqual(count, 2)

    def test_bulk_add_creates_missing_groups_automatically(self):
        """
        Verifies smart import logic: If a bulk import contains a group name 
        that doesn't exist yet (e.g., 'New Group 123'), it should be created automatically.
        """
        data = [("Site", "https://site.com", "New Group 123")]
        self.db.bulk_add_urls(data)
        
        self.assertIn("New Group 123", self.db.get_groups())

    def test_bulk_add_skips_existing_urls(self):
        """
        Verifies bulk import robustness: If the import list contains URLs that 
        are already in the DB, they should be skipped without causing errors.
        """
        self.db.add_url("https://exists.com", "General")
        
        data = [
            ("Exists", "https://exists.com", "General"), # Duplicate
            ("New", "https://new.com", "General")        # New
        ]
        self.db.bulk_add_urls(data)
        
        # Total should be 2: The original one + the new one. The duplicate is ignored.
        all_urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(all_urls), 2)

    # --- SECURITY & ROBUSTNESS TESTS ---

    def test_security_sql_injection_in_group_name(self):
        """
        Verifies that malicious SQL input in the Group Name field is sanitized.
        Input like "'); DROP TABLE urls; --" should be treated as text, not code.
        """
        evil_name = "General'); DROP TABLE urls; --"
        self.db.add_group(evil_name)
        
        # If injection worked, the 'urls' table would be missing and this would crash.
        try:
            self.db.get_urls_by_group("All URLs")
        except sqlite3.OperationalError:
            self.fail("SQL Injection vulnerability detected in add_group!")

    def test_security_sql_injection_in_url_field(self):
        """
        Verifies that malicious SQL input in the URL field is sanitized.
        """
        evil_url = "http://evil.com', 1, NULL, NULL); --"
        self.db.add_url(evil_url, "General")
        
        urls = self.db.get_urls_by_group("General")
        self.assertEqual(len(urls), 1)
        # The URL should be stored literally as the string above, not executed.
        self.assertTrue(urls[0][2].startswith("http://evil.com"))

    def test_robustness_handle_very_long_strings(self):
        """
        Verifies the database doesn't crash on extremely long inputs (buffer overflow checks).
        """
        long_name = "A" * 1000
        self.db.add_group(long_name)
        self.assertIn(long_name, self.db.get_groups())

    def test_robustness_handle_empty_url_string(self):
        """
        Verifies the database handles an empty string gracefully without crashing.
        (Note: UI validation normally catches this, but the DB layer should be safe too).
        """
        self.db.add_url("", "General") 
        # Pass if no exception is raised

    def test_database_schema_integrity(self):
        """
        Verifies that the database tables are actually created upon initialization.
        This ensures the 'init_db' method works correctly.
        """
        # Create a separate temporary instance just for this test
        temp_db = DatabaseManager(":memory:")
        try:
            cursor = temp_db.get_groups() 
            # If tables didn't exist, get_groups would raise "no such table" error
            self.assertTrue(len(cursor) >= 1)
        finally:
            # Explicit cleanup for this temporary instance
            if temp_db.memory_conn:
                temp_db.memory_conn.close()

    def test_initialization_creates_default_group_explicit_check(self):
        """
        A specific check to ensure the first group created is always named 'General'.
        """
        groups = self.db.get_groups()
        self.assertEqual(groups[0], "General")

if __name__ == '__main__':
    unittest.main()