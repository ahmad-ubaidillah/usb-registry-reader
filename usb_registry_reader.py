import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from Registry import Registry
import threading
import struct
import os

class RegistryHiveReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Registry Hive Reader")
        self.root.geometry("800x600")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure("Custom.TButton", padding=5)
        self.style.configure("Custom.TProgressbar", thickness=20)
        
        self.setup_gui()
        self.setup_shortcuts()
        
    def setup_gui(self):
        # Menu Bar
        self.create_menu()
        
        # Main Toolbar
        self.create_toolbar()
        
        # Search Frame
        self.create_search_frame()
        
        # Progress Section
        self.create_progress_section()
        
        # Text Area
        self.create_text_area()
        
        # Status Bar
        self.create_status_bar()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open (Ctrl+O)", command=self.load_file)
        file_menu.add_command(label="Export (Ctrl+S)", command=self.export_result)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy (Ctrl+C)", command=self.copy_to_clipboard)
        edit_menu.add_command(label="Find (Ctrl+F)", 
                            command=lambda: self.search_entry.focus())
        
    def create_toolbar(self):
        self.btn_frame = ttk.Frame(self.root)
        self.btn_frame.pack(pady=5)
        
        self.btn_open = ttk.Button(self.btn_frame, text="Open .hiv/.dat File", 
                                  command=self.load_file, style="Custom.TButton")
        self.btn_open.pack(side=tk.LEFT, padx=5)
        
        self.btn_copy = ttk.Button(self.btn_frame, text="Copy Result", 
                                  command=self.copy_to_clipboard, style="Custom.TButton")
        self.btn_copy.pack(side=tk.LEFT, padx=5)
        
        self.btn_export = ttk.Button(self.btn_frame, text="Export Result", 
                                    command=self.export_result, style="Custom.TButton")
        self.btn_export.pack(side=tk.LEFT, padx=5)
        
    def create_search_frame(self):
        self.search_frame = ttk.Frame(self.root)
        self.search_frame.pack(pady=5)
        
        ttk.Label(self.search_frame, text="Search:").pack(side=tk.LEFT, padx=2)
        
        self.search_entry = ttk.Entry(self.search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self.search_frame, text="Search", 
                  command=self.search_text).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self.search_frame, text="Clear", 
                  command=self.clear_search).pack(side=tk.LEFT, padx=2)
        
    def create_progress_section(self):
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", 
                                          length=600, mode="determinate",
                                          style="Custom.TProgressbar")
        self.progress_bar.pack(pady=5)
        
        self.progress_label = ttk.Label(self.root, text="")
        self.progress_label.pack()
        
    def create_text_area(self):
        self.text_frame = ttk.Frame(self.root)
        self.text_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.text = tk.Text(self.text_frame, wrap=tk.NONE)
        self.text.grid(row=0, column=0, sticky="nsew")
        
        scroll_y = ttk.Scrollbar(self.text_frame, orient="vertical", 
                               command=self.text.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        
        scroll_x = ttk.Scrollbar(self.text_frame, orient="horizontal", 
                                command=self.text.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        self.text.configure(yscrollcommand=scroll_y.set, 
                          xscrollcommand=scroll_x.set)
        
        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        
    def create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, 
                                   anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_shortcuts(self):
        self.root.bind('<Control-o>', lambda e: self.load_file())
        self.root.bind('<Control-c>', lambda e: self.copy_to_clipboard())
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<Control-s>', lambda e: self.export_result())
        self.search_entry.bind('<Return>', lambda e: self.search_text())
        
    def parse_recent_docs(self, key):
        output = []
        mru_order = []
        value_data = {}

        for val in key.values():
            name = val.name()
            if name == "MRUListEx":
                raw = val.value()
                mru_order = list(struct.iter_unpack("<I", raw))
                mru_order = [i[0] for i in mru_order if i[0] != 0xFFFFFFFF]
            else:
                value_data[name] = val.value()

        sorted_entries = []
        for i in mru_order:
            keyname = str(i)
            if keyname in value_data:
                data = value_data[keyname]
                try:
                    text = data.decode("utf-16-le", errors="ignore").split("\x00")[0]
                    sorted_entries.append(f"  {i}. {text}")
                except Exception as e:
                    sorted_entries.append(f"  {i}. (decode error): {e}")

        if sorted_entries:
            output.append("[RecentDocs Decoded]")
            # Tambahkan timestamp dari key RecentDocs
            ts = key.timestamp()
            lastwrite = ts.strftime('%Y-%m-%d %H:%M:%S UTC')
            output.append(f"LastWrite Time: {lastwrite}")
            output.extend(sorted_entries)
            output.append("")

        return output

    def read_hive_file(self, filepath, progress_callback):
        # Tambahkan check ukuran file
        file_size = os.path.getsize(filepath)
        if file_size > 100_000_000:  # 100MB
            if not messagebox.askyesno("Large File", 
                f"File size is {file_size/1_000_000:.1f}MB. This might take a while. Continue?"):
                return "Operation cancelled by user."
        
        # Kode read_hive_file Anda tetap sama
        try:
            reg = Registry.Registry(filepath)
            root_key = reg.root()
            output = []
            all_keys = []

            def collect_all_keys(key):
                all_keys.append(key)
                for subkey in key.subkeys():
                    collect_all_keys(subkey)

            collect_all_keys(root_key)
            total = len(all_keys)

            for idx, key in enumerate(all_keys):
                try:
                    path = key.path()
                    # Perbaikan penggunaan ts.strftime()
                    ts = key.timestamp()
                    lastwrite = ts.strftime('%Y-%m-%d %H:%M:%S UTC')
                    output.append(f"[Key] {path} (LastWrite: {lastwrite})")

                    if "RecentDocs" in path:
                        parsed = self.parse_recent_docs(key)
                        output.extend(parsed)

                    for val in key.values():
                        try:
                            name = val.name() or "(Default)"
                            val_type = val.value_type_str()
                            val_data = val.value()
                            output.append(f"  - {name} ({val_type}): {val_data}")
                        except Exception as ve:
                            output.append(f"  - [Value Error] {ve}")

                    output.append("")
                    progress_callback(int((idx + 1) / total * 100))
                except Exception as ke:
                    output.append(f"[Key Error] {ke}")
                    output.append("")

            output.append(f"\n[Summary] Total keys processed: {total}")
            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"
        
    def load_file(self):
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("Hive or DAT files", "*.hiv *.dat"), ("All files", "*.*")]
            )
            if not filepath:
                return

            if not os.path.exists(filepath):
                messagebox.showerror("Error", "File not found!")
                return

            self.text.delete("1.0", tk.END)
            self.text.tag_remove("highlight", "1.0", tk.END)
            self.progress_bar["value"] = 0
            self.progress_label.config(text="Loading...")
            self.status_bar.config(text=f"Loading file: {filepath}")
            self.root.title(f"Registry Hive Reader - {os.path.basename(filepath)}")

            self.btn_open.state(["disabled"])
            self.btn_copy.state(["disabled"])
            self.btn_export.state(["disabled"])

            def on_progress(percent):
                self.progress_bar["value"] = percent
                self.progress_label.config(text=f"Loading... {percent}%")
                self.root.update_idletasks()

            def task():
                content = self.read_hive_file(filepath, on_progress)
                self.text.insert(tk.END, content)
                self.progress_bar["value"] = 100
                self.progress_label.config(text="Done ✅")
                self.status_bar.config(text=f"Loaded: {filepath}")
                self.btn_open.state(["!disabled"])
                self.btn_copy.state(["!disabled"])
                self.btn_export.state(["!disabled"])

            threading.Thread(target=task).start()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.btn_open.state(["!disabled"])
            self.btn_copy.state(["!disabled"])
            self.btn_export.state(["!disabled"])
            self.status_bar.config(text="Error occurred")
            
    def copy_to_clipboard(self):
        content = self.text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        self.status_bar.config(text="Content copied to clipboard")
        messagebox.showinfo("Copied", "Result copied to clipboard!")
        
    def export_result(self):
        content = self.text.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No content to export!")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_bar.config(text=f"Exported to: {filepath}")
                messagebox.showinfo("Success", "Content exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
        
    def search_text(self):
        self.text.tag_remove("highlight", "1.0", tk.END)
        search_term = self.search_entry.get()
        if not search_term:
            return

        idx = "1.0"
        count = 0
        while True:
            idx = self.text.search(search_term, idx, nocase=1, stopindex=tk.END)
            if not idx:
                break
            lastidx = f"{idx}+{len(search_term)}c"
            self.text.tag_add("highlight", idx, lastidx)
            idx = lastidx
            count += 1
            
        self.text.tag_config("highlight", background="yellow", foreground="black")
        self.status_bar.config(text=f"Found {count} matches")

    def clear_search(self):
        """Clear search field and remove highlights"""
        self.search_entry.delete(0, tk.END)
        self.text.tag_remove("highlight", "1.0", tk.END)
        self.status_bar.config(text="Search cleared")
        
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()
            
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = RegistryHiveReader()
    app.run()
