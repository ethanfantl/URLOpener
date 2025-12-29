import sqlite3
import logging
from datetime import datetime
from urllib.parse import urlparse

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.memory_conn = None
        
        # If we are testing in memory, we MUST keep one connection open forever
        # otherwise the DB is wiped every time a function finishes.
        if self.db_name == ":memory:":
            self.memory_conn = sqlite3.connect(":memory:")
            # Allow accessing columns by name if needed later
            self.memory_conn.row_factory = sqlite3.Row 
            
        self.init_db()

    def _get_conn(self):
        """Helper to get the correct connection context."""
        if self.memory_conn:
            return self.memory_conn
        else:
            return sqlite3.connect(self.db_name)

    def init_db(self):
        try:
            # We don't use 'with' here because we don't want to close memory connections
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    url TEXT NOT NULL UNIQUE, 
                    group_id INTEGER,
                    favicon_blob BLOB,
                    last_opened DATETIME,
                    FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", ("General",))
            conn.commit()
            
            # Only close if it's a file connection
            if not self.memory_conn:
                conn.close()
                
        except sqlite3.Error as e:
            logging.error(f"Database Initialization Error: {e}")

    def get_groups(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            result = [row[0] for row in cursor.execute("SELECT name FROM groups")]
            return result
        finally:
            if not self.memory_conn:
                conn.close()

    def add_group(self, name):
        conn = self._get_conn()
        try:
            conn.cursor().execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error adding group: {e}")
        finally:
            if not self.memory_conn:
                conn.close()

    def delete_group(self, group_name):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM groups WHERE name=?", (group_name,))
            result = cursor.fetchone()
            if result:
                group_id = result[0]
                cursor.execute("DELETE FROM urls WHERE group_id=?", (group_id,))
                cursor.execute("DELETE FROM groups WHERE id=?", (group_id,))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error deleting group: {e}")
        finally:
            if not self.memory_conn:
                conn.close()

    def add_url(self, url, group_name, favicon_data=None):
        conn = self._get_conn()
        try:
            domain = urlparse(url).netloc
            title = domain if domain else url
            
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM groups WHERE name=?", (group_name,))
            group_id = cursor.fetchone()
            
            if group_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO urls (title, url, group_id, favicon_blob, last_opened)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, url, group_id[0], favicon_data, datetime.now().isoformat()))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error adding URL: {e}")
        finally:
            if not self.memory_conn:
                conn.close()

    def bulk_add_urls(self, url_data_list):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            unique_groups = {item[2] for item in url_data_list}
            for g in unique_groups:
                cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (g,))
            
            cursor.execute("SELECT name, id FROM groups")
            # Handle tuple output from fetchall
            group_map = {row[0]: row[1] for row in cursor.fetchall()}

            insert_list = []
            for title, url, g_name in url_data_list:
                g_id = group_map.get(g_name)
                if g_id:
                    insert_list.append((title, url, g_id, None, datetime.now().isoformat()))
            
            cursor.executemany("""
                INSERT OR IGNORE INTO urls (title, url, group_id, favicon_blob, last_opened)
                VALUES (?, ?, ?, ?, ?)
            """, insert_list)
            conn.commit()
            return len(insert_list)
        except sqlite3.Error as e:
            logging.error(f"Bulk Import Error: {e}")
            return 0
        finally:
            if not self.memory_conn:
                conn.close()

    def get_urls_by_group(self, group_name):
        query = """
            SELECT u.id, u.title, u.url, u.favicon_blob 
            FROM urls u
            JOIN groups g ON u.group_id = g.id
            WHERE g.name = ?
        """
        if group_name == "All URLs":
            query = "SELECT id, title, url, favicon_blob FROM urls"
            
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            if group_name == "All URLs":
                return cursor.execute(query).fetchall()
            return cursor.execute(query, (group_name,)).fetchall()
        finally:
            if not self.memory_conn:
                conn.close()

    def delete_url(self, url_id):
        conn = self._get_conn()
        try:
            conn.cursor().execute("DELETE FROM urls WHERE id=?", (url_id,))
            conn.commit()
        finally:
            if not self.memory_conn:
                conn.close()