import unittest
import sys
import os
import logging
from unittest.mock import patch, mock_open

# Ensure we can import the utils module from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.importers import ImportManager

class TestImporters(unittest.TestCase):

    def setUp(self):
        """
        Runs before each test.
        Disables logging to keep the test output clean, as some tests intentionally 
        trigger errors (like 'File Not Found') that would otherwise print to the console.
        """
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """
        Runs after each test.
        Re-enables logging so normal application behavior isn't affected.
        """
        logging.disable(logging.NOTSET)

    # --- HTML PARSING TESTS ---

    def test_parse_standard_netscape_bookmark_structure(self):
        """
        Verifies parsing of the standard 'Netscape Bookmark File Format' used by 
        Chrome, Edge, and Firefox. It checks if the parser correctly associates 
        a link inside a <DL> list with the <H3> header preceding it (the Group name).
        """
        # 
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
            
        # Expected result: A list containing one tuple: (Title, URL, Group Name)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], ("LinkedIn", "https://linkedin.com", "Work Stuff"))

    def test_parse_flat_bookmark_without_folder_defaults_to_imported(self):
        """
        Verifies that if a bookmark is found at the root level (not inside any folder/header),
        it is assigned to a default group named 'Imported' instead of crashing or being lost.
        """
        html_content = '<DT><A HREF="https://google.com">Google</A>'
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake_path.html")
            
        self.assertEqual(data[0][2], "Imported") 

    def test_parse_empty_file_returns_empty_list(self):
        """
        Verifies that parsing an empty file returns an empty list rather than 
        raising an error.
        """
        with patch("builtins.open", mock_open(read_data="")):
            data = ImportManager.parse_bookmarks_html("fake.html")
        self.assertEqual(data, [])

    def test_parse_malformed_html_missing_closing_tags(self):
        """
        Verifies the robustness of BeautifulSoup integration. Even if the HTML 
        is "ugly" (missing closing </a> or <p> tags), the parser should still 
        extract the URL and Title correctly.
        """
        html_content = '<A HREF="http://broken.com">Broken' # No closing </a>
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][1], "http://broken.com")

    def test_ignore_invalid_links_without_href(self):
        """
        Verifies data quality: Anchor tags <a> that contain text but no actual 
        HREF link (common in separators or JS buttons) should be ignored.
        """
        html_content = '<a>Just Text</a>'
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        self.assertEqual(len(data), 0)

    def test_parse_unicode_characters_in_titles(self):
        """
        Verifies that non-English characters (Japanese, Emoji, etc.) in bookmark 
        titles are preserved correctly during import.
        """
        html_content = '<A HREF="https://jp.com">日本語</A>'
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        self.assertEqual(data[0][0], "日本語")

    def test_file_not_found_returns_empty_list_gracefully(self):
        """
        Verifies error handling: If the user selects a file that doesn't exist 
        (or moves it before clicking Open), the function should catch the IO error, 
        log it, and return an empty list instead of crashing the app.
        """
        # We do NOT use mock_open here because we WANT the real open() to fail.
        data = ImportManager.parse_bookmarks_html("non_existent_file_999.html")
        self.assertEqual(data, [])

    def test_parse_nested_folder_structure(self):
        """
        Verifies logic for nested folders. If a link is deep inside 'Level 1 > Level 2',
        the parser should correctly associate it with the nearest parent folder ('Level 2').
        """
        html_content = """
        <H3>Level 1</H3>
        <DL><H3>Level 2</H3>
            <DL><A HREF="http://deep.com">Deep Link</A></DL>
        </DL>
        """
        with patch("builtins.open", mock_open(read_data=html_content)):
            data = ImportManager.parse_bookmarks_html("fake.html")
        
        # Based on 'find_previous_sibling' logic, it grabs the immediate header.
        self.assertEqual(data[0][2], "Level 2")

if __name__ == '__main__':
    unittest.main()