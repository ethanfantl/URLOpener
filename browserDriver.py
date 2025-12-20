import csv
import tkinter as tk
from tkinter import ttk, messagebox
import os
import webbrowser
import json

class UrlManager:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Manager Pro")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")

        # {"GroupName": ["url1", "url2", "etc"]} for each URL
        self.data = {"All URLs": []}
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.current_directory, "url_data.json")
        
        self.load_data()
        self.setup_ui()
        self.refresh_tree()

    def setup_ui(self):
        # Styling
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=('Segoe UI', 10))
    
        #column headers
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))

        # --- Top Section: Entry and Controls ---
        top_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        top_frame.pack(fill="x", padx=20)

        tk.Label(top_frame, text="URL:", bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(top_frame, width=40)
        self.url_entry.grid(row=0, column=1, padx=5)

        tk.Label(top_frame, text="Group:", bg="#f0f0f0").grid(row=1, column=0, sticky="w")
        self.group_entry = ttk.Combobox(top_frame, values=list(self.data.keys()))
        self.group_entry.set("All URLs")
        self.group_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        add_btn = ttk.Button(top_frame, text="Add/Assign", command=self.add_url)
        add_btn.grid(row=0, column=2, rowspan=2, padx=5, sticky="nsew")

        # --- Middle Section: Treeview ---
        self.tree = ttk.Treeview(self.root, columns=("URL"), show="tree headings")
        self.tree.heading("#0", text="Groups / Websites")
        self.tree.pack(expand=True, fill="both", padx=20, pady=10)

        # --- Bottom Section: Actions ---
        btn_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        btn_frame.pack(fill="x", padx=20)

        ttk.Button(btn_frame, text="Open Selected", command=self.open_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_item).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Open Entire Group", command=self.open_group).pack(side="right", padx=2)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {"All URLs": []}

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def refresh_tree(self):
        #clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        #re create tree
        for group, urls in self.data.items():
            folder = self.tree.insert("", "end", text=group, open=True)
            for url in urls:
                self.tree.insert(folder, "end", text=url, values=(url,))
        
        # Update dropdown values
        self.group_entry['values'] = list(self.data.keys())

    def add_url(self):
        url = self.url_entry.get().strip()
        group = self.group_entry.get().strip()

        if not url:
            return
        if url not in self.data["All URLs"]:
            self.data["All URLs"].append(url)

        # Create group if doesn't exist and add URL
        if group not in self.data:
            self.data[group] = []
        
        if url not in self.data[group]:
            self.data[group].append(url)

        self.save_data()
        self.refresh_tree()
        self.url_entry.delete(0, tk.END)

    def delete_item(self):
        selected = self.tree.selection()
        if not selected: return
        
        item_text = self.tree.item(selected[0])['text']
        parent_id = self.tree.parent(selected[0])

        if parent_id == "": #means its a group
            if item_text == "All URLs":
                messagebox.showwarning("Access Denied", "Cannot delete the master list.")
                return
            del self.data[item_text]
        else: #url
            parent_group = self.tree.item(parent_id)['text']
            
            if parent_group == "All URLs":
                for g in list(self.data.keys()):
                    if item_text in self.data[g]:
                        self.data[g].remove(item_text)
            else:
                self.data[parent_group].remove(item_text)
            
            # if a group is empty, should ask if we want to delete that group
            if parent_group != "All URLs" and len(self.data[parent_group]) == 0:
                answer = messagebox.askyesno("Empty Group", f"'{parent_group}' is now empty. Delete group?")
                if answer:
                    del self.data[parent_group]

        self.save_data()
        self.refresh_tree()

    def open_selected(self):
        selected = self.tree.selection()
        if not selected: return
        url = self.tree.item(selected[0])['text']
        full_url = url if url.startswith("http") else "https://" + url
        webbrowser.open_new_tab(full_url)

    def open_group(self):
        selected = self.tree.selection()
        if not selected: return
        group_name = self.tree.item(selected[0])['text']
        
        if group_name in self.data:
            for url in self.data[group_name]:
                full_url = url if url.startswith("http") else "https://" + url
                webbrowser.open_new_tab(full_url)

if __name__ == "__main__":
    root = tk.Tk()
    app = UrlManager(root)
    root.mainloop()