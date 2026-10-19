import os
import sys
import tkinter as tk
import threading
from tkinter import filedialog, messagebox, ttk

import pandas as pd

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from scripts.pdf_chemical_scan import load_data, scan_file


class ChemicalScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chemical Scanner")
        self.geometry("1200x760")
        self.minsize(1040, 620)
        self.configure(bg="#edf2f7")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#edf2f7")
        self.style.configure("TLabel", background="#edf2f7", foreground="#24364d")
        self.style.configure("Title.TLabel", background="#edf2f7", foreground="#163a5f", font=("Segoe UI", 22, "bold"))
        self.style.configure("Subtitle.TLabel", background="#edf2f7", foreground="#4a6178", font=("Segoe UI", 10))
        self.style.configure("Section.TLabel", background="#edf2f7", foreground="#1d3557", font=("Segoe UI", 10, "bold"))
        self.style.configure("TEntry", fieldbackground="#ffffff", foreground="#1d3557", padding=6)
        self.style.configure("TCombobox", padding=6, fieldbackground="#ffffff", foreground="#1d3557")
        self.style.configure("Primary.TButton", background="#3d6fb0", foreground="#ffffff", padding=(14, 10), relief="flat")
        self.style.configure("Secondary.TButton", background="#eaf0f7", foreground="#173d63", padding=(12, 9), relief="flat")
        self.style.map("Primary.TButton", background=[("active", "#305d98"), ("pressed", "#294f84")], foreground=[("active", "#ffffff")])
        self.style.map("Secondary.TButton", background=[("active", "#dfeaf6"), ("pressed", "#d1dfef")], foreground=[("active", "#173d63")])
        self.style.configure("TLabelframe", background="#edf2f7")
        self.style.configure("TLabelframe.Label", background="#edf2f7", foreground="#1d3557", font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#1d3557")
        self.style.configure("Treeview.Heading", background="#dfeaf7", foreground="#1d3557", font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", "#cfe0f5")], foreground=[("selected", "#163a5f")])

        self.option_add("*TCombobox*Listbox*Background", "#ffffff")
        self.option_add("*TCombobox*Listbox*Foreground", "#1d3557")
        self.option_add("*TCombobox*Listbox*Font", ("Segoe UI", 10))

        self.file_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.product_id_var = tk.StringVar()
        self.pdf_url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.summary_var = tk.StringVar(value="No report generated yet")
        self.mapping_summary_var = tk.StringVar(value="No mapping selected")
        self.data_frame = pd.DataFrame()
        self.available_columns = []

        self._build_ui()
        self._set_default_output()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        top = ttk.Frame(self, padding=(24, 18, 24, 10))
        top.pack(fill="x")

        title = ttk.Label(top, text="Chemical Scanner", style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(top, text="German SDS keyword screening for product PDF review", style="Subtitle.TLabel")
        subtitle.pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(self, padding=(24, 0, 24, 20))
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=(0, 0, 18, 0))
        left.pack(side="left", fill="y")
        left.configure(width=430)

        form = ttk.Frame(left, padding=(10, 10, 10, 4))
        form.pack(fill="both")

        ttk.Label(form, text="1. Select input file", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(4, 6))
        input_row = ttk.Frame(form)
        input_row.grid(row=1, column=0, sticky="ew")
        self.input_entry = ttk.Entry(input_row, textvariable=self.file_path_var, width=48)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        browse_button = ttk.Button(input_row, text="Browse", command=self._select_input_file, style="Secondary.TButton")
        browse_button.pack(side="left")

        ttk.Label(form, text="2. Map columns", style="Section.TLabel").grid(row=2, column=0, sticky="w", pady=(20, 6))

        product_frame = ttk.Frame(form, padding=(0, 0, 0, 8))
        product_frame.grid(row=3, column=0, sticky="ew")
        ttk.Label(product_frame, text="Product ID column", style="Section.TLabel").pack(anchor="w")
        self.product_combo = ttk.Combobox(product_frame, textvariable=self.product_id_var, state="readonly", width=48)
        self.product_combo.pack(fill="x", pady=(6, 0))
        self.product_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_mapping_summary())

        url_frame = ttk.Frame(form, padding=(0, 0, 0, 0))
        url_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(url_frame, text="PDF URL column", style="Section.TLabel").pack(anchor="w")
        self.pdf_url_var = tk.StringVar()
        self.url_combo = ttk.Combobox(url_frame, textvariable=self.pdf_url_var, state="readonly", width=48)
        self.url_combo.pack(fill="x", pady=(6, 0))
        self.url_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_mapping_summary())

        mapping_display = tk.Frame(form, bg="#f3f8ff", bd=1, relief="solid", highlightbackground="#d8e4f4", highlightthickness=1, padx=10, pady=10)
        mapping_display.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(mapping_display, text="Selected mapping", style="Section.TLabel").pack(anchor="w")
        ttk.Label(mapping_display, textvariable=self.mapping_summary_var, foreground="#2f4f6b", font=("Segoe UI", 10), background="#f3f8ff", wraplength=360).pack(anchor="w", pady=(8, 0))

        ttk.Label(form, text="3. Output folder", style="Section.TLabel").grid(row=6, column=0, sticky="w", pady=(18, 6))
        output_row = ttk.Frame(form)
        output_row.grid(row=7, column=0, sticky="ew")
        self.output_entry = ttk.Entry(output_row, textvariable=self.output_path_var, width=48)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        output_button = ttk.Button(output_row, text="Browse", command=self._select_output_folder, style="Secondary.TButton")
        output_button.pack(side="left")

        actions = ttk.Frame(form)
        actions.grid(row=8, column=0, sticky="ew", pady=(18, 0))
        self.run_button = ttk.Button(actions, text="Scan file", command=self._run_scan, style="Primary.TButton")
        self.run_button.pack(side="left")
        self.open_output_button = ttk.Button(actions, text="Open output", command=self._open_output_file, style="Secondary.TButton")
        self.open_output_button.pack(side="left", padx=(10, 0))

        status_row = ttk.Frame(form)
        status_row.grid(row=9, column=0, sticky="ew", pady=(16, 0))
        ttk.Label(status_row, text="Status:", style="Section.TLabel").pack(side="left")
        ttk.Label(status_row, textvariable=self.status_var, style="Subtitle.TLabel").pack(side="left", padx=(6, 0))

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        summary_box = ttk.Frame(right, padding=(14, 14, 14, 12))
        summary_box.pack(fill="x", pady=(0, 10))
        ttk.Label(summary_box, text="Summary", style="Section.TLabel").pack(anchor="w")
        ttk.Label(summary_box, textvariable=self.summary_var, style="Subtitle.TLabel", wraplength=600).pack(anchor="w", pady=(8, 0))

        table_frame = ttk.Frame(right)
        table_frame.pack(fill="both", expand=True)
        columns = ["productID", "chemical_keywords_found", "chemicals_found", "keyword_occurrences", "status"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=145, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def _update_mapping_summary(self):
        product_id = self.product_id_var.get().strip() if self.product_id_var.get() else ""
        pdf_url = self.pdf_url_var.get().strip() if self.pdf_url_var.get() else ""

        if product_id and pdf_url:
            self.mapping_summary_var.set(f"ID: {product_id} | PDF: {pdf_url}")
        elif product_id:
            self.mapping_summary_var.set(f"ID: {product_id} | PDF: not selected")
        elif pdf_url:
            self.mapping_summary_var.set(f"ID: not selected | PDF: {pdf_url}")
        else:
            self.mapping_summary_var.set("No mapping selected")

    def _set_default_output(self):
        base = os.path.dirname(os.path.abspath(__file__))
        default_folder = os.path.join(base, "results")
        os.makedirs(default_folder, exist_ok=True)
        self.output_path_var.set(os.path.join(default_folder, "scan_report.csv"))

    def _select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF data file",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("Excel legacy", "*.xls"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self.file_path_var.set(file_path)
        try:
            df = load_data(file_path)
            self.available_columns = list(df.columns)
            self.product_combo["values"] = self.available_columns
            self.url_combo["values"] = self.available_columns
            if self.available_columns:
                self.product_combo.set(self.available_columns[0])
                candidate_pdf = next((col for col in self.available_columns if col != self.available_columns[0]), self.available_columns[0])
                self.url_combo.set(candidate_pdf)
            self._update_mapping_summary()
            self.status_var.set("File loaded")
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not read the selected file:\n{exc}")
            self.status_var.set("Load error")

    def _select_output_folder(self):
        output_dir = filedialog.askdirectory(title="Select output folder")
        if not output_dir:
            return
        filename = "scan_report.csv"
        self.output_path_var.set(os.path.join(output_dir, filename))

    def _open_output_file(self):
        output_path = self.output_path_var.get()
        if not output_path or not os.path.exists(output_path):
            messagebox.showinfo("Output file", "No output file is available yet.")
            return
        try:
            os.startfile(output_path)
        except Exception:
            messagebox.showinfo("Output file", f"Open the export here:\n{output_path}")

    def _run_scan(self):
        input_file = self.file_path_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Missing file", "Please select an input CSV or Excel file first.")
            return

        product_id_column = self.product_id_var.get().strip()
        if not product_id_column:
            messagebox.showerror("Product ID", "Please select the Product ID column.")
            return

        pdf_column = self.pdf_url_var.get().strip()
        if not pdf_column:
            messagebox.showerror("URL column", "Please select the PDF URL column.")
            return

        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Output path", "Please choose an output path.")
            return

        self.run_button.config(state="disabled")
        self.status_var.set("Scanning...")
        self.update_idletasks()

        # Run scan in background thread to keep UI responsive
        def perform_scan():
            try:
                result_df = scan_file(
                    input_file=input_file,
                    output_path=output_path,
                    product_id_column=product_id_column,
                    url_columns=pdf_column,
                    workers=4,
                    timeout=30,
                )
                self.data_frame = result_df
                self.after(0, self._on_scan_complete, result_df, output_path)
            except Exception as exc:
                self.after(0, self._on_scan_error, str(exc))

        thread = threading.Thread(target=perform_scan, daemon=True)
        thread.start()

    def _on_scan_complete(self, result_df, output_path):
        """Called from main thread after scan completes."""
        try:
            self._populate_result_table(result_df)
            found_count = int((result_df["chemical_keywords_found"] == "Yes").sum()) if not result_df.empty else 0
            total_count = len(result_df)
            self.summary_var.set(f"Processed {total_count} rows. Potential hits: {found_count}.")
            self.status_var.set("Scan complete")
            messagebox.showinfo("Scan complete", f"Results saved to:\n{output_path}")
        finally:
            self.run_button.config(state="normal")

    def _on_scan_error(self, error_msg):
        """Called from main thread if scan fails."""
        self.status_var.set("Scan failed")
        messagebox.showerror("Scan failed", error_msg)
        self.run_button.config(state="normal")

    def _populate_result_table(self, result_df):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if result_df.empty:
            return

        preview_rows = result_df.head(200).to_dict(orient="records")
        for row in preview_rows:
            values = [
                row.get("productID", ""),
                row.get("chemical_keywords_found", ""),
                row.get("chemicals_found", ""),
                row.get("keyword_occurrences", ""),
                row.get("status", ""),
            ]
            self.tree.insert("", tk.END, values=values)


def main():
    app = ChemicalScannerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
