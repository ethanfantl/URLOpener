import csv
import tkinter as tk
from tkinter import messagebox
import os
import webbrowser

class UrlManager:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Manager")
        
        self.urls = []
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.csv_file_path = os.path.join(current_directory, "websites.csv")
        self.load_urls_from_csv(self.csv_file_path)
        print(self.csv_file_path)
        
        self.url_listbox = tk.Listbox(root)
        self.url_listbox.pack(padx=10, pady=10)
        
        for url in self.urls:
            self.url_listbox.insert(tk.END, url)
        
        self.new_url_entry = tk.Entry(root)
        self.new_url_entry.pack(padx=10, pady=5)
        
        add_button = tk.Button(root, text="Add URL", command=self.add_url)
        add_button.pack(padx=10, pady=5)
        
        delete_button = tk.Button(root, text="Delete URL", command=self.delete_url)
        delete_button.pack(padx=10, pady=5)
        run_button = tk.Button(root, text="Open URLs", command=self.open_urls)
        run_button.pack(padx = 10, pady = 5)
        
    def load_urls_from_csv(self, file_path):
        try:
            with open(file_path, 'r') as csvfile:
                reader = csv.reader(csvfile)
                self.urls = list(reader)
        except FileNotFoundError:
            print("File not found when loading urls from csv")
            pass
    
    def save_urls_to_csv(self, file_path):
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self.urls)
    
    def add_url(self):
        new_url = self.new_url_entry.get()
        if new_url:
            self.urls.append([new_url])
            self.url_listbox.insert(tk.END, new_url)
            self.new_url_entry.delete(0, tk.END)
            self.save_urls_to_csv(self.csv_file_path)
    
    def delete_url(self):
        selected_index = self.url_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            del self.urls[index]
            self.url_listbox.delete(index)
            self.save_urls_to_csv(self.csv_file_path)

    def open_urls(self):
        for i in range(len(self.urls)):
            print(str(self.urls[i]))
            webbrowser.open_new_tab("https://" + str(self.urls[i]))
