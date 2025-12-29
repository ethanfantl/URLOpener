import unittest
import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager

class TestDatabase(unittest.TestCase):
    def tearDown(self):
        """Runs after EVERY test. Closes the DB connection."""
        if self.db.memory_conn:
            self.db.memory_conn.close()

    def setUp(self):
        """Runs before EVERY test. Creates a fresh in-memory DB."""
        self.db = DatabaseManager(":memory:")

    # --- GROUP TESTS (6 Tests) ---

    def test_01_add_group(self):
        self.db.add_group("Work")
        groups = self.db.get_groups()
        self.assertIn("Work", groups)

    def test_02_add_duplicate_group(self):
        """Ensure adding the same group twice doesn't crash or duplicate."""
        self.db.add_group("Work")
        self.db.add_group("Work")
        groups = self.db.get_groups()
        # Should be 2 because "General" is always created by default + "Work"
        self.assertEqual(len(groups), 2) 

    def test_03_get_groups_initial_state(self):
        """Ensure 'General' exists by default."""
        groups = self.db.get_groups()
        self.assertIn("General", groups)

    def test_04_delete_group(self):
        self.db.add_group("Temporary")
        self.db.delete_group("Temporary")
        groups = self.db.get_groups()
        self.assertNotIn("Temporary", groups)

    def test_05_delete_group_cascades_urls(self):
        """If a group is deleted, its URLs should vanish too."""
        self.db.add_group("FolderX")
        self.db.add_url("http://example.com", "FolderX")
        self.db.delete_group("FolderX")
        
        urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(urls), 0)

    def test_06_special_char_groups(self):
        """Test Emojis and symbols in group names."""
        name = "🚀 Startups & Money $$$"
        self.db.add_group(name)
        self.assertIn(name, self.db.get_groups())

    # --- URL TESTS (10 Tests) ---

    def test_07_add_url_basic(self):
        self.db.add_url("https://google.com", "General")
        urls = self.db.get_urls_by_group("General")
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0][2], "https://google.com")

    def test_08_add_url_auto_title(self):
        """Test that title is extracted from domain if not provided."""
        self.db.add_url("https://www.github.com", "General")
        urls = self.db.get_urls_by_group("General")
        # urlparse.netloc should make title 'www.github.com'
        self.assertEqual(urls[0][1], "www.github.com")

    def test_09_add_duplicate_url(self):
        """URLs must be UNIQUE in the database."""
        self.db.add_url("https://unique.com", "General")
        self.db.add_url("https://unique.com", "General") # Should be ignored
        urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(urls), 1)

    def test_10_add_url_to_non_existent_group(self):
        """Adding a URL to a fake group should fail silently (or be handled)."""
        self.db.add_url("https://lost.com", "Ghost Group")
        urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(urls), 0)

    def test_11_get_urls_by_specific_group(self):
        self.db.add_group("Music")
        self.db.add_url("https://spotify.com", "Music")
        self.db.add_url("https://google.com", "General")
        
        music_urls = self.db.get_urls_by_group("Music")
        self.assertEqual(len(music_urls), 1)
        self.assertEqual(music_urls[0][2], "https://spotify.com")

    def test_12_get_all_urls(self):
        self.db.add_group("A")
        self.db.add_group("B")
        self.db.add_url("http://a.com", "A")
        self.db.add_url("http://b.com", "B")
        
        all_items = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(all_items), 2)

    def test_13_delete_url(self):
        self.db.add_url("https://delete.me", "General")
        # Need to fetch ID to delete
        urls = self.db.get_urls_by_group("General")
        url_id = urls[0][0]
        
        self.db.delete_url(url_id)
        urls_after = self.db.get_urls_by_group("General")
        self.assertEqual(len(urls_after), 0)

    def test_14_bulk_add_simple(self):
        data = [
            ("Google", "https://google.com", "General"),
            ("Yahoo", "https://yahoo.com", "General")
        ]
        count = self.db.bulk_add_urls(data)
        self.assertEqual(count, 2)

    def test_15_bulk_add_creates_new_groups(self):
        """Bulk add should automatically create groups if they don't exist."""
        data = [("Site", "https://site.com", "New Group 123")]
        self.db.bulk_add_urls(data)
        
        self.assertIn("New Group 123", self.db.get_groups())

    def test_16_bulk_add_skips_duplicates(self):
        self.db.add_url("https://exists.com", "General")
        
        data = [
            ("Exists", "https://exists.com", "General"),
            ("New", "https://new.com", "General")
        ]
        count = self.db.bulk_add_urls(data)
        # Should only insert 1, because 1 already existed
        # Note: Your bulk logic returns length of insert_list, so we verify DB count instead
        all_urls = self.db.get_urls_by_group("All URLs")
        self.assertEqual(len(all_urls), 2)

    # --- SECURITY & ROBUSTNESS (6 Tests) ---

    def test_17_sql_injection_group(self):
        """Attempt to drop table via group name."""
        evil_name = "General'); DROP TABLE urls; --"
        self.db.add_group(evil_name)
        # If injection worked, getting urls would crash
        try:
            self.db.get_urls_by_group("All URLs")
        except sqlite3.OperationalError:
            self.fail("SQL Injection vulnerability detected in add_group!")

    def test_18_sql_injection_url(self):
        """Attempt SQL injection in URL field."""
        evil_url = "http://evil.com', 1, NULL, NULL); --"
        self.db.add_url(evil_url, "General")
        urls = self.db.get_urls_by_group("General")
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0][2].startswith("http://evil.com"))

    def test_19_very_long_string(self):
        """Test database limit handling."""
        long_name = "A" * 1000
        self.db.add_group(long_name)
        self.assertIn(long_name, self.db.get_groups())

    def test_20_empty_strings(self):
        """Empty URL should probably be handled (though UI prevents it)."""
        # If DB allows it, it allows it. We just verify it doesn't crash.
        self.db.add_url("", "General") 
        # Note: In real app, UI validation stops this.

    def test_21_schema_integrity(self):
        """Verify tables actually exist."""
        # Create a separate instance just for this test
        temp_db = DatabaseManager(":memory:")
        try:
            cursor = temp_db.get_groups() 
            self.assertTrue(len(cursor) >= 1)
        finally:
            # CLEANUP: Explicitly close the connection to prevent ResourceWarning
            if temp_db.memory_conn:
                temp_db.memory_conn.close()

    def test_22_init_creates_default_group(self):
        # Already covered by test 03, but specific check for "General"
        groups = self.db.get_groups()
        self.assertEqual(groups[0], "General")

if __name__ == '__main__':
    unittest.main()