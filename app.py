"""Chemical Scanner - desktop front end.

Crash-hardening notes (2024 revision)
-------------------------------------
* A windowed PyInstaller build has sys.stdout/sys.stderr == None, so every
  traceback vanishes and the app looks like it 'just closes'. The bootstrap
  block at the top of this file redirects both to crash.log next to the .exe
  and installs faulthandler, so even a native crash leaves evidence.
* The worker thread never touches Tk. It posts messages to a Queue and the
  main thread drains it. tk.after() from a background thread is NOT
  thread-safe and can abort the Tcl interpreter with no message at all.
* Closing the window during a scan now cancels the worker and waits for it
  instead of tearing the interpreter down underneath it.
"""

# ==============================================================================
# CRASH LOGGING BOOTSTRAP - must stay first, before tkinter/pandas are imported
# ==============================================================================
import faulthandler
import os
import queue
import sys
import threading
import time
import traceback


def _resolve_log_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    try:
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, "crash.log"), "a", encoding="utf-8"):
            pass
        return base
    except OSError:
        fallback = os.path.join(os.path.expanduser("~"), "ChemicalScanner")
        os.makedirs(fallback, exist_ok=True)
        return fallback


LOG_DIR = _resolve_log_dir()
CRASH_LOG_PATH = os.path.join(LOG_DIR, "crash.log")

try:
    _crash_log = open(CRASH_LOG_PATH, "a", buffering=1, encoding="utf-8", errors="replace")
except OSError:
    _crash_log = None


def log_line(message):
    if _crash_log is None:
        return
    try:
        _crash_log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        _crash_log.flush()
    except Exception:
        pass


def log_exception(label, exc_type, exc_value, exc_tb):
    log_line(f"UNHANDLED EXCEPTION ({label}):")
    if _crash_log is None:
        return
    try:
        _crash_log.write("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        _crash_log.flush()
    except Exception:
        pass


if _crash_log is not None:
    log_line("=" * 70)
    log_line("session start")
    try:
        # Catches hard crashes (access violation / stack overflow) as well.
        faulthandler.enable(_crash_log)
    except Exception:
        pass
    if sys.stderr is None:
        sys.stderr = _crash_log
    if sys.stdout is None:
        sys.stdout = _crash_log

sys.excepthook = lambda t, v, tb: log_exception("main", t, v, tb)
try:
    threading.excepthook = lambda a: log_exception(
        f"thread:{a.thread.name if a.thread else '?'}",
        a.exc_type, a.exc_value, a.exc_traceback,
    )
except Exception:
    pass

# ==============================================================================
# Normal imports
# ==============================================================================
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

# --- Tuning -------------------------------------------------------------
SCAN_WORKERS = 8           # download concurrency. PDF parsing is serialised
                           # inside the scanner, so raising this past ~12 only
                           # adds memory pressure, not speed.
SCAN_TIMEOUT = 20          # per-download timeout in seconds
UI_REFRESH_SECONDS = 0.15  # throttle progress updates
UI_POLL_MS = 120           # how often the main thread drains the queue
# ------------------------------------------------------------------------

APP_ICON_FILE = "chemical_chemistry_laboratory_icon_192522.ico"
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # In a PyInstaller build, __file__ lives in a temp folder that is deleted
    # on exit. Anything the user keeps must go next to the real .exe.
    APP_ROOT = os.path.dirname(sys.executable)
    CODE_ROOT = getattr(sys, "_MEIPASS", APP_ROOT)
else:
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    CODE_ROOT = APP_ROOT

if CODE_ROOT not in sys.path:
    sys.path.insert(0, CODE_ROOT)

log_line(f"frozen={IS_FROZEN} app_root={APP_ROOT} code_root={CODE_ROOT}")

try:
    from scripts.pdf_chemical_scan import load_data, scan_file, ScanCancelled
except Exception:
    log_exception("import scripts.pdf_chemical_scan", *sys.exc_info())
    try:
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showerror(
            "Startup failed",
            "The scanner module could not be loaded.\n\n"
            f"Details were written to:\n{CRASH_LOG_PATH}",
        )
        _root.destroy()
    except Exception:
        pass
    raise SystemExit(1)


class ChemicalScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Any exception inside a Tk callback lands here instead of vanishing.
        self.report_callback_exception = self._report_tk_exception

        self.title("Chemical Scanner")
        self._apply_window_icon()
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
        self.style.configure("Warn.TLabel", background="#edf2f7", foreground="#b03a2e", font=("Segoe UI", 10))
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
        self.progress_var = tk.StringVar(value="Scanned 0/0 (0.0%)")
        self.url_total_var = tk.StringVar(value="Total URLs: 0")
        self.summary_var = tk.StringVar(value="No report generated yet")
        self.mapping_summary_var = tk.StringVar(value="No mapping selected")

        self.data_frame = pd.DataFrame()
        self.available_columns = []
        self.latest_total_urls = 0
        self.scan_running = False
        self.last_checkpoint = ""
        self._last_ui_update = 0.0
        self._scan_started = 0.0

        # Thread -> UI communication. A Queue is thread-safe; tk.after is not.
        self.ui_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.scan_thread = None
        self._closing = False

        self._build_ui()
        self._set_default_output()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(UI_POLL_MS, self._pump_ui_queue)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
    def _report_tk_exception(self, exc_type, exc_value, exc_tb):
        log_exception("tk-callback", exc_type, exc_value, exc_tb)
        try:
            messagebox.showerror(
                "Unexpected error",
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"Details were written to:\n{CRASH_LOG_PATH}",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------
    def _resource_path(self, *parts):
        return os.path.join(CODE_ROOT, *parts)

    def _apply_window_icon(self):
        """Never let a missing icon take the app down."""
        try:
            icon_path = self._resource_path("assets", APP_ICON_FILE)
            if not os.path.exists(icon_path):
                log_line(f"WARNING: app icon not found: {icon_path}")
                return
            self.iconbitmap(icon_path)
        except Exception as exc:
            log_line(f"WARNING: failed to apply app icon: {exc}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        top = ttk.Frame(self, padding=(24, 18, 24, 10))
        top.pack(fill="x")
        ttk.Label(top, text="Chemical Scanner", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="German SDS keyword screening for product PDF review",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

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
        self.browse_button = ttk.Button(input_row, text="Browse", command=self._select_input_file, style="Secondary.TButton")
        self.browse_button.pack(side="left")

        ttk.Label(form, text="2. Map columns", style="Section.TLabel").grid(row=2, column=0, sticky="w", pady=(20, 6))

        product_frame = ttk.Frame(form, padding=(0, 0, 0, 8))
        product_frame.grid(row=3, column=0, sticky="ew")
        ttk.Label(product_frame, text="Product ID column", style="Section.TLabel").pack(anchor="w")
        self.product_combo = ttk.Combobox(product_frame, textvariable=self.product_id_var, state="readonly", width=48)
        self.product_combo.pack(fill="x", pady=(6, 0))
        self.product_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_mapping_summary())

        url_frame = ttk.Frame(form, padding=(0, 0, 0, 0))
        url_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(url_frame, text="PDF URL column", style="Section.TLabel").pack(anchor="w")
        self.url_combo = ttk.Combobox(url_frame, textvariable=self.pdf_url_var, state="readonly", width=48)
        self.url_combo.pack(fill="x", pady=(6, 0))
        self.url_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_mapping_summary())

        mapping_display = tk.Frame(form, bg="#f3f8ff", bd=1, relief="solid",
                                   highlightbackground="#d8e4f4", highlightthickness=1, padx=10, pady=10)
        mapping_display.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(mapping_display, text="Selected mapping", style="Section.TLabel").pack(anchor="w")
        ttk.Label(mapping_display, textvariable=self.mapping_summary_var, foreground="#2f4f6b",
                  font=("Segoe UI", 10), background="#f3f8ff", wraplength=360).pack(anchor="w", pady=(8, 0))

        ttk.Label(form, text="3. Output file (.xlsx or .csv)", style="Section.TLabel").grid(row=6, column=0, sticky="w", pady=(18, 6))
        output_row = ttk.Frame(form)
        output_row.grid(row=7, column=0, sticky="ew")
        self.output_entry = ttk.Entry(output_row, textvariable=self.output_path_var, width=48)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.output_button = ttk.Button(output_row, text="Browse", command=self._select_output_file, style="Secondary.TButton")
        self.output_button.pack(side="left")

        actions = ttk.Frame(form)
        actions.grid(row=8, column=0, sticky="ew", pady=(18, 0))
        self.run_button = ttk.Button(actions, text="Scan file", command=self._run_scan, style="Primary.TButton")
        self.run_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Stop", command=self._request_stop,
                                      style="Secondary.TButton", state="disabled")
        self.stop_button.pack(side="left", padx=(10, 0))
        self.open_output_button = ttk.Button(actions, text="Open output", command=self._open_output_file, style="Secondary.TButton")
        self.open_output_button.pack(side="left", padx=(10, 0))

        status_row = ttk.Frame(form)
        status_row.grid(row=9, column=0, sticky="ew", pady=(16, 0))
        ttk.Label(status_row, text="Status:", style="Section.TLabel").pack(side="left")
        ttk.Label(status_row, textvariable=self.status_var, style="Subtitle.TLabel").pack(side="left", padx=(6, 0))

        progress_row = ttk.Frame(form)
        progress_row.grid(row=10, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(progress_row, textvariable=self.progress_var, style="Subtitle.TLabel").pack(anchor="w")
        ttk.Label(progress_row, textvariable=self.url_total_var, style="Subtitle.TLabel").pack(anchor="w", pady=(2, 4))
        self.progress_bar = ttk.Progressbar(progress_row, orient="horizontal", mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x")

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        summary_box = ttk.Frame(right, padding=(14, 14, 14, 12))
        summary_box.pack(fill="x", pady=(0, 10))
        ttk.Label(summary_box, text="Summary", style="Section.TLabel").pack(anchor="w")
        ttk.Label(summary_box, textvariable=self.summary_var, style="Subtitle.TLabel", wraplength=600).pack(anchor="w", pady=(8, 0))

        table_frame = ttk.Frame(right)
        table_frame.pack(fill="both", expand=True)
        columns = ["productID", "chemical_keywords_found", "gefahrstoff codes", "chemicals_found", "status"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=145, anchor="w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def _update_mapping_summary(self):
        product_id = (self.product_id_var.get() or "").strip()
        pdf_url = (self.pdf_url_var.get() or "").strip()
        if product_id and pdf_url:
            self.mapping_summary_var.set(f"ID: {product_id} | PDF: {pdf_url}")
        elif product_id:
            self.mapping_summary_var.set(f"ID: {product_id} | PDF: not selected")
        elif pdf_url:
            self.mapping_summary_var.set(f"ID: not selected | PDF: {pdf_url}")
        else:
            self.mapping_summary_var.set("No mapping selected")

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    def _default_output_dir(self):
        """Never return a PyInstaller temp folder - it is deleted on exit."""
        candidates = []
        if IS_FROZEN:
            candidates.append(os.path.join(os.path.expanduser("~"), "Documents", "ChemicalScanner"))
            candidates.append(os.path.join(APP_ROOT, "results"))
        else:
            candidates.append(os.path.join(APP_ROOT, "results"))
        candidates.append(os.path.join(os.path.expanduser("~"), "ChemicalScanner"))
        for folder in candidates:
            try:
                os.makedirs(folder, exist_ok=True)
                return folder
            except OSError:
                continue
        return os.path.expanduser("~")

    def _set_default_output(self):
        self.output_path_var.set(os.path.join(self._default_output_dir(), "scan_report.xlsx"))

    def _guess_column(self, columns, keywords, fallback_index=0):
        for col in columns:
            lowered = str(col).lower()
            if any(key in lowered for key in keywords):
                return col
        return columns[fallback_index] if columns else ""

    # ------------------------------------------------------------------
    # File selection
    # ------------------------------------------------------------------
    def _select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF data file",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"),
                       ("Excel legacy", "*.xls"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self.file_path_var.set(file_path)
        self.status_var.set("Loading file...")
        self.update_idletasks()
        try:
            df = load_data(file_path)
            self.available_columns = [str(c) for c in df.columns]
            if not self.available_columns:
                raise ValueError("The file has no columns / no header row.")
            self.product_combo["values"] = self.available_columns
            self.url_combo["values"] = self.available_columns

            id_col = self._guess_column(self.available_columns, ("productid", "product_id", "id", "artikel"), 0)
            url_col = self._guess_column(
                [c for c in self.available_columns if c != id_col] or self.available_columns,
                ("url", "pdf", "link", "href"), 0)
            self.product_combo.set(id_col)
            self.url_combo.set(url_col)
            self._update_mapping_summary()
            self.status_var.set(f"File loaded ({len(df)} rows)")
        except Exception as exc:
            log_exception("load_data", *sys.exc_info())
            messagebox.showerror("Load error", f"Could not read the selected file:\n{exc}")
            self.status_var.set("Load error")

    def _select_output_file(self):
        output_path = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".xlsx",
            initialfile="scan_report.xlsx",
            initialdir=self._default_output_dir(),
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not output_path:
            return
        self.output_path_var.set(output_path)

    def _open_output_file(self):
        output_path = self.output_path_var.get()
        if not output_path or not os.path.exists(output_path):
            if self.last_checkpoint and os.path.exists(self.last_checkpoint):
                output_path = self.last_checkpoint
            else:
                messagebox.showinfo("Output file", "No output file is available yet.")
                return
        try:
            os.startfile(output_path)
        except Exception:
            messagebox.showinfo("Output file", f"Open the export here:\n{output_path}")

    # ------------------------------------------------------------------
    # Thread -> UI queue
    # ------------------------------------------------------------------
    def _pump_ui_queue(self):
        """Runs on the main thread only. The worker never touches Tk."""
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "progress":
                    self._update_progress(*payload)
                elif kind == "done":
                    self._on_scan_complete(*payload)
                elif kind == "error":
                    self._on_scan_error(*payload)
                elif kind == "cancelled":
                    self._on_scan_cancelled(*payload)
        except queue.Empty:
            pass
        except Exception:
            log_exception("ui-pump", *sys.exc_info())
        finally:
            if not self._closing:
                self.after(UI_POLL_MS, self._pump_ui_queue)

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------
    def _run_scan(self):
        if self.scan_running:
            return

        input_file = self.file_path_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Missing file", "Please select an input CSV or Excel file first.")
            return

        product_id_column = (self.product_id_var.get() or "").strip()
        if not product_id_column:
            messagebox.showerror("Product ID", "Please select the Product ID column.")
            return

        pdf_column = (self.pdf_url_var.get() or "").strip()
        if not pdf_column:
            messagebox.showerror("URL column", "Please select the PDF URL column.")
            return

        if pdf_column == product_id_column:
            messagebox.showerror("Column mapping",
                                 "Product ID and PDF URL cannot be the same column.")
            return

        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Output path", "Please choose an output path.")
            return

        _, ext = os.path.splitext(output_path)
        ext = ext.lower()
        if not ext:
            output_path = f"{output_path}.xlsx"
            self.output_path_var.set(output_path)
        elif ext == ".xls":
            # pandas 2.x cannot write the legacy .xls format at all.
            output_path = output_path[:-4] + ".xlsx"
            self.output_path_var.set(output_path)
            messagebox.showinfo("Output path",
                                "The legacy .xls format is not supported.\n"
                                f"The report will be saved as:\n{output_path}")
        elif ext not in {".xlsx", ".csv"}:
            messagebox.showerror("Output path", "Output file must end with .xlsx or .csv")
            return

        self.last_checkpoint = os.path.splitext(output_path)[0] + "_checkpoint.csv"
        if os.path.exists(self.last_checkpoint):
            keep = messagebox.askyesno(
                "Resume previous scan?",
                f"A checkpoint from an interrupted scan was found:\n{self.last_checkpoint}\n\n"
                "Yes = continue where it stopped (much faster)\n"
                "No  = start over from the first row",
            )
            resume = bool(keep)
            if not resume:
                try:
                    os.remove(self.last_checkpoint)
                except OSError:
                    pass
        else:
            resume = False

        self.cancel_event.clear()
        self.scan_running = True
        self.run_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.browse_button.config(state="disabled")
        self.output_button.config(state="disabled")
        self.status_var.set("Scanning...")
        self._update_progress(0, 0, 0)
        self._last_ui_update = 0.0
        self._scan_started = time.time()
        self.update_idletasks()

        log_line(f"scan start: input={input_file} output={output_path} "
                 f"workers={SCAN_WORKERS} timeout={SCAN_TIMEOUT} resume={resume}")

        started = self._scan_started
        ui_queue = self.ui_queue
        cancel_event = self.cancel_event

        def perform_scan():
            try:
                def on_progress(completed, total_rows, total_urls):
                    # Throttle: 24k row-by-row updates would flood the queue.
                    now = time.time()
                    is_final = total_rows > 0 and completed >= total_rows
                    if is_final or (now - self._last_ui_update) >= UI_REFRESH_SECONDS:
                        self._last_ui_update = now
                        ui_queue.put(("progress", (completed, total_rows, total_urls)))

                result_df = scan_file(
                    input_file=input_file,
                    output_path=output_path,
                    product_id_column=product_id_column,
                    url_columns=pdf_column,
                    workers=SCAN_WORKERS,
                    timeout=SCAN_TIMEOUT,
                    progress_callback=on_progress,
                    resume=resume,
                    cancel_event=cancel_event,
                )
                self.data_frame = result_df
                ui_queue.put(("done", (result_df, output_path, time.time() - started)))
            except ScanCancelled as exc:
                log_line(f"scan cancelled: {exc}")
                ui_queue.put(("cancelled", (str(exc),)))
            except Exception as exc:
                log_exception("scan worker", *sys.exc_info())
                ui_queue.put(("error", (f"{type(exc).__name__}: {exc}",)))

        self.scan_thread = threading.Thread(target=perform_scan, name="scan", daemon=True)
        self.scan_thread.start()

    def _request_stop(self):
        if not self.scan_running:
            return
        self.cancel_event.set()
        self.stop_button.config(state="disabled")
        self.status_var.set("Stopping after current downloads...")

    def _finish_scan_ui(self):
        self.scan_running = False
        self.scan_thread = None
        self.run_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.browse_button.config(state="normal")
        self.output_button.config(state="normal")

    def _on_scan_complete(self, result_df, output_path, elapsed_seconds):
        """Called on the main thread after the scan completes."""
        try:
            self._populate_result_table(result_df)
            if result_df.empty:
                self.summary_var.set("Scan returned no rows.")
                self.status_var.set("Scan complete (empty)")
                messagebox.showinfo("Scan complete", "The scan produced no rows.")
                return

            total_count = len(result_df)
            found_count = int((result_df["chemical_keywords_found"] == "Yes").sum())
            hazard_count = int(result_df["gefahrstoff codes"].fillna("").astype(str).str.strip().ne("").sum())
            status_counts = result_df["status"].value_counts().to_dict()
            failed = sum(v for k, v in status_counts.items()
                         if k in ("download-failed", "non-pdf", "extract-failed", "error", "no-url"))
            skipped = int(status_counts.get("skipped-crash-suspect", 0))

            self._update_progress(total_count, total_count, self.latest_total_urls)
            summary = (
                f"Processed {total_count} rows in {elapsed_seconds / 60:.1f} min. "
                f"Keyword hits: {found_count}. Gefahrstoff-Code hits: {hazard_count}. "
                f"PDFs not readable: {failed}."
            )
            if skipped:
                summary += (f" Skipped as crash suspects: {skipped} "
                            f"(see the *_quarantine.txt file next to the report).")
            self.summary_var.set(summary)
            self.status_var.set("Scan complete")
            log_line(f"scan complete: {status_counts}")
            messagebox.showinfo("Scan complete", f"Results saved to:\n{output_path}")
        except Exception as exc:
            log_exception("on_scan_complete", *sys.exc_info())
            self.status_var.set("Scan finished with a display error")
            messagebox.showerror(
                "Display error",
                f"The scan finished and the report was written, but the summary "
                f"could not be built:\n{type(exc).__name__}: {exc}",
            )
        finally:
            self._finish_scan_ui()

    def _on_scan_cancelled(self, message):
        self.status_var.set("Scan stopped")
        self.summary_var.set(message)
        messagebox.showinfo("Scan stopped", message)
        self._finish_scan_ui()

    def _on_scan_error(self, error_msg):
        """Called on the main thread if the scan or the export fails."""
        self.status_var.set("Scan failed")
        checkpoint = self.last_checkpoint
        if checkpoint and os.path.exists(checkpoint):
            self.summary_var.set(
                "Export failed, but every scanned row was saved to:\n"
                f"{checkpoint}\n"
                "Use 'Open output' to view it, or run again and choose Resume."
            )
            messagebox.showerror(
                "Export failed",
                f"{error_msg}\n\n"
                "YOUR RESULTS WERE NOT LOST.\n"
                f"They are saved here:\n{checkpoint}",
            )
        else:
            self.summary_var.set("Scan failed before any results were produced.")
            messagebox.showerror("Scan failed", error_msg)
        self._finish_scan_ui()

    def _update_progress(self, completed, total_rows, total_urls):
        self.latest_total_urls = total_urls
        percent = 0.0 if total_rows <= 0 else (completed / total_rows) * 100

        eta_text = ""
        if self.scan_running and completed > 0 and total_rows > completed:
            elapsed = time.time() - self._scan_started
            if elapsed > 5:
                remaining = (elapsed / completed) * (total_rows - completed)
                eta_text = f"  -  about {remaining / 60:.0f} min left"

        self.progress_var.set(f"Scanned {completed}/{total_rows} ({percent:.1f}%){eta_text}")
        self.url_total_var.set(f"Total URLs: {total_urls}")
        self.progress_bar["value"] = percent
        if total_rows > 0 and completed < total_rows:
            self.status_var.set(f"Scanning... {completed}/{total_rows}")

    def _populate_result_table(self, result_df):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if result_df.empty:
            return
        for row in result_df.head(200).to_dict(orient="records"):
            values = [
                row.get("productID", ""),
                row.get("chemical_keywords_found", ""),
                str(row.get("gefahrstoff codes", ""))[:120],
                str(row.get("chemicals_found", ""))[:120],
                row.get("status", ""),
            ]
            self.tree.insert("", tk.END, values=values)

    def _on_close(self):
        if self.scan_running:
            leave = messagebox.askyesno(
                "Scan in progress",
                "A scan is still running. Closing now stops it.\n\n"
                "Rows already scanned stay in the checkpoint file and you can resume later.\n\n"
                "Close anyway?",
            )
            if not leave:
                return
            # Stop the worker cleanly BEFORE tearing down the interpreter.
            self.cancel_event.set()
            self.status_var.set("Stopping, please wait...")
            try:
                self.update_idletasks()
            except Exception:
                pass
            thread = self.scan_thread
            if thread is not None and thread.is_alive():
                log_line("waiting for scan thread to stop")
                thread.join(timeout=30)
                if thread.is_alive():
                    log_line("scan thread did not stop within 30s")

        self._closing = True
        log_line("session end")
        self.destroy()


def main():
    try:
        app = ChemicalScannerApp()
    except Exception:
        log_exception("startup", *sys.exc_info())
        try:
            messagebox.showerror(
                "Startup failed",
                f"The app could not start.\n\nDetails were written to:\n{CRASH_LOG_PATH}",
            )
        except Exception:
            pass
        raise SystemExit(1)

    app.mainloop()

    # A worker thread stuck in a socket read can crash the interpreter during
    # shutdown. Everything important is already flushed to disk, so leave hard.
    if threading.active_count() > 1:
        log_line("exiting with worker threads still alive; forcing exit")
        if _crash_log is not None:
            try:
                _crash_log.flush()
            except Exception:
                pass
        os._exit(0)

    if _crash_log is not None:
        try:
            _crash_log.flush()
        except Exception:
            pass


if __name__ == "__main__":
    main()