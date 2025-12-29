import logging
from bs4 import BeautifulSoup

class ImportManager:
    @staticmethod
    def parse_bookmarks_html(filepath):
        extracted_data = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            
            links = soup.find_all('a')
            for link in links:
                url = link.get('href')
                title = link.text
                group_name = "Imported"
                
                parent_dl = link.find_parent('dl')
                if parent_dl:
                    prev_tag = parent_dl.find_previous_sibling()
                    if prev_tag and prev_tag.name == 'h3':
                        group_name = prev_tag.text
                
                if url and title:
                    extracted_data.append((title, url, group_name))
        except Exception as e:
            logging.error(f"Parsing Error: {e}")
        return extracted_data