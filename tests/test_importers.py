import unittest
import sys
import os
import logging  # <--- NEW IMPORT
from unittest.mock import patch, mock_open

# Fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.importers import ImportManager

class TestImporters(unittest.TestCase):

    # --- NEW METHODS START ---
    def setUp(self):
        """Disable logging before tests start so expected errors don't print."""
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Re-enable logging after tests finish."""
        logging.disable(logging.NOTSET)

    # --- PARSING TESTS ---

    def test_23_parse_standard_bookmark(self):
        """Test parsing a standard Netscape bookmark file snippet."""
        html_content = """
        <DL><p>
            <DT><H3>Work Stuff</H3>
            <DL><p>
                <DT><A HREF="https://linkedin.com">LinkedIn</A>
            </DL><p>
        </DL><p>
        """
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake_path.html")
            
        # Expected: [(Title, URL, Group)]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], ("LinkedIn", "https://linkedin.com", "Work Stuff"))

    def test_24_parse_flat_bookmark(self):
        """Test a link with no folder/header."""
        html_content = '<DT><A HREF="https://google.com">Google</A>'
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake_path.html")
            
        self.assertEqual(data[0][2], "Imported") # Should default to "Imported"

    def test_25_parse_empty_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            data = ImportManager.parse_bookmarks_html("fake.html")
        self.assertEqual(data, [])

    def test_26_parse_malformed_html(self):
        """HTML that is missing closing tags should still work via BeautifulSoup."""
        html_content = '<A HREF="http://broken.com">Broken' # No closing </a>
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][1], "http://broken.com")

    def test_27_ignore_invalid_links(self):
        """Anchor tags without hrefs should be skipped."""
        html_content = '<a>Just Text</a>'
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        self.assertEqual(len(data), 0)

    def test_28_unicode_in_html(self):
        """Test parsing non-English characters."""
        html_content = '<A HREF="https://jp.com">日本語</A>'
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        self.assertEqual(data[0][0], "日本語")

    def test_29_file_not_found(self):
        """Ensure it returns empty list instead of crashing if file missing."""
        # We don't mock open here, we let it fail naturally to test exception handling
        data = ImportManager.parse_bookmarks_html("non_existent_file_999.html")
        self.assertEqual(data, [])

    def test_30_nested_folders(self):
        """Deeply nested structure (Logic check)."""
        # Note: Current logic only looks 1 level up. This test verifies that limitation/behavior.
        html_content = """
        <H3>Level 1</H3>
        <DL><H3>Level 2</H3>
            <DL><A HREF="http://deep.com">Deep Link</A></DL>
        </DL>
        """
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        
        # Depending on logic, it might catch Level 2 or Level 1. 
        # Based on your code 'find_previous_sibling', it should catch "Level 2".
        self.assertEqual(data[0][2], "Level 2")

if __name__ == '__main__':
    unittest.main()