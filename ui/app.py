import customtkinter as ctk
import webbrowser
import threading
import requests
import logging
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image
from tkinter import filedialog, messagebox

# Import from our other modules
from database.db_manager import DatabaseManager
from utils.importers import ImportManager
import config

class UrlManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("URL Manager Pro")
        self.geometry("1000x650")
        
        # Initialize Logic
        self.db = DatabaseManager(config.DB_NAME)
        self.current_group = "All URLs"
        self.image_cache = []

        # Setup Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()
        self.refresh_groups()
        self.refresh_urls()

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1) 
        self.sidebar_frame.grid_rowconfigure(5, weight=0)

        # Logo
        logo_label = ctk.CTkLabel(self.sidebar_frame, text="My Links", font=ctk.CTkFont(size=20, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Add URL Input
        self.entry_url = ctk.CTkEntry(self.sidebar_frame, placeholder_text="https://...")
        self.entry_url.grid(row=1, column=0, padx=10, pady=5)
        
        add_btn = ctk.CTkButton(self.sidebar_frame, text="+ Add Link", command=self.start_add_url_thread)
        add_btn.grid(row=2, column=0, padx=10, pady=5)

        # Import Button
        import_btn = ctk.CTkButton(self.sidebar_frame, text="Import Bookmarks", 
                                   fg_color="#333", hover_color="#444", 
                                   command=self.import_bookmarks)
        import_btn.grid(row=3, column=0, padx=10, pady=15, sticky="n")

        # Group List
        self.group_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="Groups")
        self.group_scroll.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        # Add Group Input
        self.entry_group = ctk.CTkEntry(self.sidebar_frame, placeholder_text="New Group Name")
        self.entry_group.grid(row=5, column=0, padx=10, pady=5)
        
        add_grp_btn = ctk.CTkButton(self.sidebar_frame, text="Create Group", 
                                    fg_color="#1f538d", hover_color="#14375e",
                                    command=self.create_group)
        add_grp_btn.grid(row=6, column=0, padx=10, pady=(0, 20))

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.header_label = ctk.CTkLabel(self.main_frame, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.pack(anchor="w", pady=(0, 20))

        self.url_container = ctk.CTkScrollableFrame(self.main_frame)
        self.url_container.pack(fill="both", expand=True)

    def refresh_groups(self):
        # Clear existing widgets
        for widget in self.group_scroll.winfo_children():
            widget.destroy()

        # 1. "All URLs" Button (Always at top, cannot be deleted)
        btn_all = ctk.CTkButton(self.group_scroll, text="All URLs", 
                                fg_color="#444444", hover_color="#555555",
                                command=lambda: self.select_group("All URLs"))
        btn_all.pack(fill="x", pady=2)

        # 2. Render User Groups
        groups = self.db.get_groups()
        for group in groups:
            # Create a container frame for the row
            row_frame = ctk.CTkFrame(self.group_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            # Group Name Button (Takes up most space)
            btn_group = ctk.CTkButton(row_frame, text=group, 
                                      fg_color="#3a3a3a", hover_color="#505050",
                                      command=lambda g=group: self.select_group(g))
            btn_group.bind("<Double-Button-1>", lambda event, g=group: self.open_group_urls(g))
            btn_group.pack(side="left", fill="x", expand=True, padx=(0, 5))

            # Delete Group Button (Small Red 'X')
            # We prevent deleting the 'General' group to act as a safe default
            if group != "General":
                btn_del = ctk.CTkButton(row_frame, text="×", width=30, 
                                        fg_color="#c42b1c", hover_color="#a81b0f",
                                        command=lambda g=group: self.delete_group_confirm(g))
                btn_del.pack(side="right")

    def select_group(self, group_name):
        self.current_group = group_name
        self.header_label.configure(text=group_name)
        self.refresh_urls()

    def open_group_urls(self, group_name):
        if group_name == "All URLs":
            return
        
        urls = self.db.get_urls_by_group(group_name)
        if not urls:
            return

        if len(urls) > 5:
            confirm = messagebox.askyesno("Open Tabs", f"You are about to open {len(urls)} tabs. Continue?")
            if not confirm:
                return

        for _, _, url, _ in urls:
            webbrowser.open_new_tab(url)

    def create_group(self):
        name = self.entry_group.get().strip()
        if name:
            self.db.add_group(name)
            self.entry_group.delete(0, 'end')
            self.refresh_groups()

    def create_url_card(self, data, row, col):
        uid, title, url, icon_blob = data
        card = ctk.CTkFrame(self.url_container, corner_radius=10)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

        try:
            if icon_blob:
                img = Image.open(BytesIO(icon_blob))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
            else:
                ctk_img = None
        except:
            ctk_img = None
            
        if ctk_img:
            self.image_cache.append(ctk_img)
            lbl_icon = ctk.CTkLabel(card, text="", image=ctk_img)
            lbl_icon.pack(side="left", padx=10, pady=10)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        display_title = title if len(title) < 25 else title[:22] + "..."
        lbl_title = ctk.CTkLabel(info_frame, text=display_title, font=("Segoe UI", 14, "bold"), anchor="w")
        lbl_title.pack(fill="x", pady=(5,0))
        
        lbl_url = ctk.CTkLabel(info_frame, text=url[:30]+"...", text_color="gray", anchor="w")
        lbl_url.pack(fill="x")

        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side="right", padx=10)

        btn_del = ctk.CTkButton(action_frame, text="Delete", width=50, 
                                fg_color="#c42b1c", hover_color="#a81b0f",
                                command=lambda: self.delete_url_confirm(uid))
        btn_del.pack(side="right", padx=5)

        btn_open = ctk.CTkButton(action_frame, text="Open", width=50, command=lambda u=url: webbrowser.open_new_tab(u))
        btn_open.pack(side="right", padx=5)

    def delete_url_confirm(self, uid):
        self.db.delete_url(uid)
        self.refresh_urls()
    
    def delete_group_confirm(self, group_name):
        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Delete Group", 
            f"Are you sure you want to delete '{group_name}'?\n\nThis will delete ALL links inside this group."
        )
        
        if confirm:
            self.db.delete_group(group_name)
            
            # If we deleted the group we are currently looking at, switch back to All URLs
            if self.current_group == group_name:
                self.select_group("All URLs")
            else:
                self.refresh_groups()

    def import_bookmarks(self):
        filepath = filedialog.askopenfilename(
            title="Select Bookmarks File",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
        )
        if not filepath: return
        threading.Thread(target=self.process_import, args=(filepath,), daemon=True).start()

    def process_import(self, filepath):
        data = ImportManager.parse_bookmarks_html(filepath)
        if not data: return
        count = self.db.bulk_add_urls(data)
        self.after(0, lambda: self.finish_import(count))

    def finish_import(self, count):
        messagebox.showinfo("Import Complete", f"Successfully processed {count} bookmarks.")
        self.refresh_groups()
        self.refresh_urls()

    def start_add_url_thread(self):
        url = self.entry_url.get().strip()
        if not url: return
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        threading.Thread(target=self.process_add_url, args=(url, self.current_group), daemon=True).start()

    def process_add_url(self, url, group):
        try:
            domain = urlparse(url).netloc
            icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
            response = requests.get(icon_url, timeout=3)
            favicon_data = response.content if response.status_code == 200 else None
            self.db.add_url(url, group if group != "All URLs" else "General", favicon_data)
            self.after(0, self.finish_add_url)
        except Exception:
            self.db.add_url(url, group if group != "All URLs" else "General", None)
            self.after(0, self.finish_add_url)

    def finish_add_url(self):
        self.entry_url.delete(0, 'end')
        self.refresh_urls()

    def refresh_urls(self):
        # Clear existing widgets in the scrollable frame
        for widget in self.url_container.winfo_children():
            widget.destroy()
        self.image_cache.clear()

        # Fetch URLs from DB
        urls = self.db.get_urls_by_group(self.current_group)
        
        col_count = 0
        row_count = 0
        
        # Create a card for each URL
        for url_data in urls:
            self.create_url_card(url_data, row_count, col_count)
            col_count += 1
            if col_count > 2: # 3 columns wide
                col_count = 0
                row_count += 1