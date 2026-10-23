#!/usr/bin/env python3
"""PDF Chemical Scanner - Scans product datasheets for chemical keywords.

Crash-hardening notes (2024 revision)
-------------------------------------
* PDF parsing is serialised behind _PARSE_LOCK. MuPDF (PyMuPDF/fitz) is a C
  library and is NOT safe to call from many threads at once; a malformed PDF
  under concurrency causes a native access violation that kills the whole
  process with no Python traceback. Downloads stay parallel, so throughput is
  barely affected (network is the bottleneck, not parsing).
* The URL currently being parsed is recorded in <output>_inflight.txt. If the
  process dies anyway, the next run moves that URL into <output>_quarantine.txt
  and skips it, so a single poisoned PDF can never block the run twice.
  Delete the quarantine file if you want those URLs retried.
* The checkpoint CSV is flushed after every row, so a hard crash costs at most
  the rows still in flight.
"""

import argparse
import csv
import gc
import io
import os
import re
import sys
import tempfile
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import requests
from tqdm import tqdm

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    import pypdf
except ImportError:
    pypdf = None

# MuPDF prints parser warnings straight to the C-level stderr, which does not
# exist in a windowed PyInstaller build. Silence it defensively.
if fitz is not None:
    try:
        fitz.TOOLS.mupdf_display_errors(False)
    except Exception:
        pass


# ==============================================================================
# LIMITS / TUNING
# ==============================================================================

EXCEL_MAX_CELL = 32767          # hard Excel limit, exceeding it raises
MAX_PHRASES = 12                # phrases kept per product (readability)
MAX_PHRASE_LEN = 300            # characters per phrase
MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PAGES = 60                  # SDS are short; don't read 500-page manuals
MAX_TEXT_CHARS = 2_000_000
CHECKPOINT_FSYNC_EVERY = 200    # flush is every row; fsync is every N rows
URL_CACHE_MAX = 25_000          # stop the cache growing without bound
GC_EVERY = 500                  # keep memory flat on very long runs

DEFAULT_WORKERS = 8             # download concurrency (parsing is serialised)
DEFAULT_TIMEOUT = 20

# Set to False only if you are certain your PyMuPDF build is thread-safe.
SERIALISE_PDF_PARSING = True

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/pdf,*/*",
}

FIELDNAMES = [
    "productID",
    "chemical_keywords_found",
    "chemicals_found",
    "keyword_occurrences",
    "gefahrstoff codes",
    "pdf_url",
    "keywords_phrases",
    "status",
    "failure_reason",
]

FAILURE_STATUSES = (
    "download-failed",
    "non-pdf",
    "extract-failed",
    "error",
    "no-url",
    "skipped-crash-suspect",
)


class ScanCancelled(Exception):
    """Raised when the caller asked the scan to stop early."""


class _PdfTooLarge(Exception):
    pass


# ==============================================================================
# CHEMICAL KEYWORDS DATABASE
# ==============================================================================

KEYWORDS_DE = {
    "Kontaktspray", "Druckluftspray", "Druckgasspray", "Frostspray", "Isopropanol",
    "Isopropylalkohol", "Platinenätzmittel", "Ätzmittel", "Lötfett", "Lötpaste",
    "Lötwasser", "Flussmittel", "Nachfülltinte", "Batteriesäure", "Akkusäure",
    "Elektrolyt", "Rostlöser", "Rostentferner", "Kriechöl", "Schmierspray",
    "Schmierfett", "Silikonspray", "Trennspray", "Kettenspray", "Kettenöl",
    "Schneidöl", "Bohröl", "Motoröl", "Getriebeöl", "Hydrauliköl",
    "Bremsflüssigkeit", "Kühlmittel", "Frostschutz", "Insektenentferner",
    "Dieseladditiv", "Benzinadditiv", "Resin", "Photopolymer", "3D-Druck-Harz",
    "Lösungsmittel", "Verdünner", "Nitroverdünnung", "Aceton", "Terpentin",
    "Terpentinersatz", "Brennsprit", "Brennspiritus", "Waschbenzin",
    "Reinigungsbenzin", "Petroleum", "Lampenöl", "Brennpaste", "Bioethanol",
    "Grillanzünder", "Anzündflüssigkeit", "Anzündpaste", "Feuerzeugbenzin",
    "Feuerzeuggas", "Gaskartusche", "Butangas", "Propangas", "Sprühlack",
    "Sprühfarbe", "Farbspray", "Lackspray", "Klarlack", "Bootslack",
    "Kunstharzlack", "Grundierung", "Haftgrund", "Abbeizer", "Beize",
    "Holzschutzmittel", "Holzlasur", "Imprägnierspray", "Imprägniermittel",
    "Sekundenkleber", "Montagekleber", "Kontaktkleber", "Plastikkleber",
    "Neoprenkleber", "Epoxidharz", "Giessharz", "Polyesterharz", "Härter",
    "Silikondichtmasse", "Acryldichtmasse", "Bauschaum", "Montageschaum",
    "Reiniger", "Rohrfrei", "Backofenspray", "Urinsteinentferner", "Kalkentferner",
    "Entkalker", "Fleckenentferner", "Javelwasser", "Chlorbleiche", "Wäschebleiche",
    "Schimmelentferner", "Schimmelspray", "Ammoniak", "Salzsäure", "Natronlauge",
    "Desinfektionsmittel", "Händedesinfektion", "Flächendesinfektion", "Waschmittel",
    "Weichspüler", "Unkrautvernichter", "Unkraut-Ex", "Herbizid", "Pestizid",
    "Insektizid", "Insektenspray", "Mückenspray", "Wespenspray", "Ameisenspray",
    "Ameisenmittel", "Schneckenkorn", "Rattengift", "Mäusegift", "Nagerköder",
    "Fungizid", "Biozid", "Moosentferner", "Algenvernichter", "Chlortabletten",
    "Chlorgranulat", "Flüssigchlor", "Poolchemie", "Wasserpflege", "Flüssigdünger",
    "Rasendünger", "Blumendünger", "Modellbaufarbe", "Airbrushfarbe",
    "Modellbaukleber", "Fixierspray", "Sprühfixativ", "Ölfarbe", "Nagellack",
    "Nagellackentferner", "Gel-Remover", "Acrylflüssigkeit", "Blondierpulver",
    "Oxidationsmittel", "Dauerwelle", "Enthaarungscreme", "Duftöl",
    "Ätherisches Öl", "Raumspray", "Wasseraufbereiter", "Wasserklärer",
    "Aquariumdünger", "Algenmittel Aquarium", "Nitratentferner", "Chlorentferner",
    "Flohmittel", "Zeckenmittel", "Antiparasitikum", "Entwurmungsmittel", "Stall",
    "Geruchsneutralisator", "Urinentferner", "Skiwachs", "Heisswachs",
    "Snowboardwachs", "Gleitwachs", "Zeltimprägnierung", "Schuhimprägnierung",
    "Sanitärflüssigkeit", "Liquid Nikotin", "Nikotinshot", "Base Liquid",
    "Feuerlöschspray", "Löschschaum", "Löschpulver", "Fotoentwickler", "Fixierbad",
    "Stopbad", "Stempelfarbe", "Reizgas", "Tierabwehrspray",
}

HAZARD_CODE_PATTERN = re.compile(r"\b(?:EUH\d{3}A?|[HP]\d{3})\b", re.IGNORECASE)

VALID_H_CODES = {
    *(f"H{i}" for i in range(200, 209)), *(f"H{i}" for i in range(220, 230)),
    *(f"H{i}" for i in range(240, 253)), *(f"H{i}" for i in range(260, 262)),
    *(f"H{i}" for i in range(270, 282)), "H290",
    *(f"H{i}" for i in range(300, 306)), *(f"H{i}" for i in range(310, 320)),
    *(f"H{i}" for i in range(330, 337)), *(f"H{i}" for i in range(340, 342)),
    *(f"H{i}" for i in range(350, 352)), *(f"H{i}" for i in range(360, 363)),
    *(f"H{i}" for i in range(370, 374)), *(f"H{i}" for i in range(400, 414)), "H420",
}

VALID_P_CODES = {
    *(f"P{i}" for i in range(101, 104)), *(f"P{i}" for i in range(201, 203)),
    *(f"P{i}" for i in range(210, 274)), *(f"P{i}" for i in range(280, 286)),
    *(f"P{i}" for i in range(301, 392)), *(f"P{i}" for i in range(401, 406)),
    *(f"P{i}" for i in range(410, 423)), "P501",
}

VALID_EUH_CODES = {
    "EUH001", "EUH006", "EUH014", "EUH018", "EUH019", "EUH029", "EUH031",
    "EUH032", "EUH044", "EUH059", "EUH066", "EUH070", "EUH071", "EUH201",
    "EUH201A", "EUH202", "EUH203", "EUH204", "EUH205", "EUH206", "EUH207",
    "EUH208", "EUH209", "EUH209A", "EUH210", "EUH211", "EUH212", "EUH401",
}

VALID_HAZARD_CODES = VALID_H_CODES | VALID_P_CODES | VALID_EUH_CODES


# ==============================================================================
# TEXT SANITISING
# ==============================================================================

_ILLEGAL_XLSX_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_WHITESPACE = re.compile(r"\s+")


def clean_cell(value, max_len=EXCEL_MAX_CELL):
    """Strip characters Excel refuses, drop broken surrogates, cap the length."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if not isinstance(value, str):
        return value
    text = _ILLEGAL_XLSX_CHARS.sub(" ", value)
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    text = _WHITESPACE.sub(" ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 15] + " ...[truncated]"
    return text


def sanitize_for_excel(df):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(clean_cell)
    return df


# ==============================================================================
# DIAGNOSTICS / CRASH FORENSICS
# ==============================================================================

class ScanDiagnostics:
    """Run log + 'which PDF was being parsed when we died' tracking.

    inflight file  : holds the URL currently being parsed (one line).
    quarantine file: URLs that were in flight when a previous run died.
    """

    def __init__(self, base_path):
        self.log_path = base_path + "_scan.log"
        self.inflight_path = base_path + "_inflight.txt"
        self.quarantine_path = base_path + "_quarantine.txt"
        self.lock = threading.Lock()
        self.quarantined = set()
        self.newly_quarantined = []
        self._log_fh = None
        self._inflight_fh = None

    # -- lifecycle -----------------------------------------------------
    def open(self):
        try:
            self._log_fh = open(self.log_path, "a", encoding="utf-8", errors="replace")
        except OSError:
            self._log_fh = None

        self.log("-" * 70)
        self.log(f"run started {datetime.now():%Y-%m-%d %H:%M:%S}")
        self.log(f"python={sys.version.split()[0]} frozen={getattr(sys, 'frozen', False)} "
                 f"pointer_size={8 * tuple.__itemsize__}")
        self.log(f"pymupdf={'yes' if fitz is not None else 'no'} "
                 f"pypdf={'yes' if pypdf is not None else 'no'} "
                 f"serialise_parsing={SERIALISE_PDF_PARSING}")

        # Did the previous run die mid-parse?
        crashed = []
        if os.path.exists(self.inflight_path):
            try:
                with open(self.inflight_path, encoding="utf-8", errors="replace") as fh:
                    crashed = [line.strip() for line in fh if line.strip()]
            except OSError:
                crashed = []
        if crashed:
            self.newly_quarantined = crashed
            self.log("PREVIOUS RUN DIED WHILE PARSING THESE URLS - quarantining them:")
            for url in crashed:
                self.log(f"    {url}")
            try:
                with open(self.quarantine_path, "a", encoding="utf-8", errors="replace") as fh:
                    for url in crashed:
                        fh.write(url + "\n")
            except OSError:
                pass

        if os.path.exists(self.quarantine_path):
            try:
                with open(self.quarantine_path, encoding="utf-8", errors="replace") as fh:
                    self.quarantined = {line.strip() for line in fh if line.strip()}
            except OSError:
                self.quarantined = set()
        if self.quarantined:
            self.log(f"{len(self.quarantined)} URL(s) on the quarantine list will be skipped. "
                     f"Delete '{os.path.basename(self.quarantine_path)}' to retry them.")

        try:
            self._inflight_fh = open(self.inflight_path, "w", encoding="utf-8", errors="replace")
            self._inflight_fh.flush()
        except OSError:
            self._inflight_fh = None
        return self

    def close(self, remove_inflight=True):
        if self._inflight_fh is not None:
            try:
                self._inflight_fh.close()
            except Exception:
                pass
            self._inflight_fh = None
        if remove_inflight:
            try:
                os.remove(self.inflight_path)
            except OSError:
                pass
        if self._log_fh is not None:
            try:
                self._log_fh.flush()
                self._log_fh.close()
            except Exception:
                pass
            self._log_fh = None

    # -- use -----------------------------------------------------------
    def log(self, message):
        if self._log_fh is None:
            return
        try:
            with self.lock:
                self._log_fh.write(f"[{datetime.now():%H:%M:%S}] {message}\n")
                self._log_fh.flush()
        except Exception:
            pass

    def mark_parsing(self, url):
        """Record that we are about to hand this URL to the PDF library."""
        if self._inflight_fh is None:
            return
        try:
            self._inflight_fh.seek(0)
            self._inflight_fh.truncate()
            self._inflight_fh.write(url + "\n")
            self._inflight_fh.flush()
        except Exception:
            pass

    def clear_parsing(self):
        if self._inflight_fh is None:
            return
        try:
            self._inflight_fh.seek(0)
            self._inflight_fh.truncate()
            self._inflight_fh.flush()
        except Exception:
            pass

    def is_quarantined(self, url):
        return url in self.quarantined


# ==============================================================================
# KEYWORD COMPILATION  (one regex instead of ~190)
# ==============================================================================

class KeywordMatcher:
    """Single alternation regex -> one pass over the text instead of 190."""

    def __init__(self, keywords):
        ordered = sorted(keywords, key=len, reverse=True)
        self.lookup = {kw.lower(): kw for kw in ordered}
        body = "|".join(re.escape(kw) for kw in ordered)
        self.pattern = re.compile(r"\b(?:" + body + r")\b", re.IGNORECASE)

    def finditer(self, text):
        return self.pattern.finditer(text)

    def canonical(self, matched_text):
        return self.lookup.get(matched_text.lower(), matched_text)


def compile_keywords():
    return KeywordMatcher(KEYWORDS_DE)


def _hazard_sort_key(code):
    code_upper = code.upper()
    if code_upper.startswith("H") and not code_upper.startswith("EUH"):
        return (0, int(code_upper[1:]))
    if code_upper.startswith("P"):
        return (1, int(code_upper[1:]))
    if code_upper.startswith("EUH"):
        digits = int(code_upper[3:6])
        return (2, digits, 1 if len(code_upper) > 6 else 0)
    return (3, code_upper)


def search_hazard_codes(text):
    matches = {m.upper() for m in HAZARD_CODE_PATTERN.findall(text)}
    valid = [c for c in matches if c in VALID_HAZARD_CODES]
    return sorted(valid, key=_hazard_sort_key)


# ==============================================================================
# DATA LOADING
# ==============================================================================

def load_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        try:
            df = pd.read_csv(file_path, sep=";")
            if df.shape[1] == 1:
                df = pd.read_csv(file_path, sep=",")
        except Exception:
            df = pd.read_csv(file_path, sep=",")
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    return df


# ==============================================================================
# PDF DOWNLOADING  (pooled session; curl only as last resort)
# ==============================================================================

_thread_local = threading.local()


def _get_session():
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=8, pool_maxsize=8, max_retries=0
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(HEADERS)
        _thread_local.session = session
    return session


def _fetch_with_curl(url, timeout):
    import shutil
    import subprocess

    curl_path = shutil.which("curl")
    if not curl_path:
        return None
    cmd = [curl_path, "-sS", "-L", "--max-time", str(timeout),
           "--max-filesize", str(MAX_PDF_BYTES), url]
    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=startupinfo, creationflags=creationflags,
            timeout=timeout + 5,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
    except Exception:
        pass
    return None


def fetch_pdf(url, timeout=DEFAULT_TIMEOUT, retries=2, connect_timeout=8, read_timeout=None):
    """Download a PDF. Fast path = pooled requests session, curl as fallback.

    Returns a bytearray. A 4xx response is treated as final: no retry, no curl.
    """
    read_timeout = read_timeout or timeout
    attempts = max(1, retries)
    last_err = None
    final = False

    for attempt in range(attempts):
        resp = None
        try:
            resp = _get_session().get(
                url, timeout=(connect_timeout, read_timeout), stream=True
            )
            status = resp.status_code
            if status >= 400:
                last_err = f"HTTP {status}"
                # 404/403/410 etc. will not get better by retrying or by curl.
                if 400 <= status < 500 and status not in (408, 429):
                    final = True
                    break
                raise RuntimeError(last_err)

            buf = bytearray()
            for chunk in resp.iter_content(65536):
                if not chunk:
                    continue
                buf.extend(chunk)
                if len(buf) > MAX_PDF_BYTES:
                    raise _PdfTooLarge(
                        f"PDF larger than limit ({MAX_PDF_BYTES // (1024 * 1024)} MB)"
                    )
            if buf:
                return buf
            last_err = "empty response"
        except _PdfTooLarge as exc:
            raise RuntimeError(str(exc)) from exc
        except Exception as exc:
            last_err = exc
        finally:
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass

        if attempt + 1 < attempts:
            time.sleep(0.4)

    if not final:
        data = _fetch_with_curl(url, timeout)
        if data:
            return bytearray(data)

    raise RuntimeError(f"Download failed: {last_err}")


# ==============================================================================
# PDF TEXT EXTRACTION
# ==============================================================================

# Guards the C-level PDF libraries. See module docstring.
_PARSE_LOCK = threading.Lock()


def extract_text_pymupdf(pdf_bytes):
    if fitz is None:
        raise RuntimeError("PyMuPDF not installed")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise RuntimeError("PDF is password protected")
        texts = []
        total = 0
        page_limit = min(doc.page_count, MAX_PAGES)
        for page_number in range(page_limit):
            try:
                txt = doc[page_number].get_text("text")
            except Exception:
                continue
            if txt:
                texts.append(txt)
                total += len(txt)
                if total > MAX_TEXT_CHARS:
                    break
        return "\n".join(texts)
    finally:
        try:
            doc.close()
        except Exception:
            pass


def extract_text_pypdf(pdf_bytes):
    if pypdf is None:
        raise RuntimeError("pypdf not installed")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception as exc:
            raise RuntimeError("PDF is password protected") from exc
    texts = []
    total = 0
    for page in reader.pages[:MAX_PAGES]:
        try:
            t = page.extract_text()
        except Exception:
            continue
        if t:
            texts.append(t)
            total += len(t)
            if total > MAX_TEXT_CHARS:
                break
    return "\n".join(texts)


def extract_text_with_fallback(pdf_bytes):
    last_err = None
    if fitz is not None:
        try:
            return extract_text_pymupdf(pdf_bytes), "pymupdf"
        except Exception as exc:
            last_err = exc
    if pypdf is not None:
        try:
            return extract_text_pypdf(pdf_bytes), "pypdf"
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"No extractor available. Last error: {repr(last_err)}")


def extract_text_guarded(pdf_bytes, url, diag=None):
    """Extract text with the parse lock held and the URL recorded on disk.

    Holding the lock means exactly one PDF is inside the C library at any
    moment, which (a) removes the thread race and (b) makes the inflight file
    an exact record of the PDF that killed us, if we die.
    """
    lock = _PARSE_LOCK if SERIALISE_PDF_PARSING else None
    if lock is not None:
        lock.acquire()
    try:
        if diag is not None:
            diag.mark_parsing(url)
        try:
            return extract_text_with_fallback(pdf_bytes)
        finally:
            if diag is not None:
                diag.clear_parsing()
    finally:
        if lock is not None:
            lock.release()


# ==============================================================================
# KEYWORD SEARCHING
# ==============================================================================

def is_probably_pdf(pdf_bytes):
    if not pdf_bytes:
        return False
    if bytes(pdf_bytes[:5]) == b"%PDF-":
        return True
    return b"%PDF-" in bytes(pdf_bytes[:1024])


_SENTENCE_BREAK = re.compile(r"[.!?\n]")


def _extract_phrase(text, start, end):
    window_start = max(0, start - 400)
    left = text.rfind(".", window_start, start)
    for ch in ("!", "?", "\n"):
        left = max(left, text.rfind(ch, window_start, start))
    sent_start = left + 1 if left != -1 else window_start

    match = _SENTENCE_BREAK.search(text, end, min(len(text), end + 400))
    sent_end = match.start() if match else min(len(text), end + 400)

    phrase = clean_cell(text[sent_start:sent_end], max_len=MAX_PHRASE_LEN)
    return phrase if len(phrase) > 5 else ""


def search_keywords(text, matcher):
    """One pass over the text. Returns (keywords, phrases, counts)."""
    if isinstance(matcher, dict):          # backwards compatibility
        matcher = KeywordMatcher(matcher.keys())

    counts = Counter()
    phrases = []
    seen_phrases = set()
    per_keyword = Counter()

    for match in matcher.finditer(text):
        keyword = matcher.canonical(match.group(0))
        counts[keyword] += 1
        if per_keyword[keyword] >= 2 or len(phrases) >= MAX_PHRASES:
            continue
        phrase = _extract_phrase(text, match.start(), match.end())
        if phrase and phrase not in seen_phrases:
            seen_phrases.add(phrase)
            phrases.append(phrase)
            per_keyword[keyword] += 1

    unique_keywords = sorted(counts, key=lambda item: item.lower())
    ordered_counts = {kw: counts[kw] for kw in unique_keywords}
    return unique_keywords, phrases, ordered_counts


# ==============================================================================
# ROW PROCESSING
# ==============================================================================

_url_cache = {}
_url_cache_lock = threading.Lock()


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip() in ("", "nan", "None")


def _blank_outcome():
    return {
        "chemical_keywords_found": "No",
        "chemicals_found": "",
        "keyword_occurrences": "",
        "gefahrstoff codes": "",
        "keywords_phrases": "",
        "status": "no-match",
        "failure_reason": "",
    }


def _analyse_url(url, matcher, timeout, diag=None):
    """Download + extract + search for one URL. Cached across products."""
    with _url_cache_lock:
        cached = _url_cache.get(url)
    if cached is not None:
        return cached

    outcome = _blank_outcome()

    # A PDF that killed a previous run is never opened again.
    if diag is not None and diag.is_quarantined(url):
        outcome["status"] = "skipped-crash-suspect"
        outcome["failure_reason"] = (
            "this PDF crashed a previous run and was skipped; "
            "check it manually or delete the _quarantine.txt file to retry"
        )
        return outcome

    pdf_bytes = None
    try:
        pdf_bytes = fetch_pdf(url, timeout=timeout, retries=2)
    except Exception as exc:
        outcome["status"] = "download-failed"
        outcome["failure_reason"] = clean_cell(str(exc), 500)
        if diag is not None:
            diag.log(f"download-failed {url} :: {exc}")

    try:
        if pdf_bytes:
            if not is_probably_pdf(pdf_bytes):
                outcome["status"] = "non-pdf"
                outcome["failure_reason"] = (
                    f"content too small ({len(pdf_bytes)} bytes); likely HTML/redirect"
                    if len(pdf_bytes) < 200
                    else "downloaded content does not appear to be a PDF"
                )
            else:
                try:
                    text, _method = extract_text_guarded(pdf_bytes, url, diag)
                    found, phrases, counts = search_keywords(text, matcher)
                    if found:
                        outcome["chemical_keywords_found"] = "Yes"
                        outcome["chemicals_found"] = "; ".join(found)
                        outcome["keyword_occurrences"] = "; ".join(
                            f"{kw}:{n}" for kw, n in counts.items()
                        )
                        outcome["keywords_phrases"] = " | ".join(phrases)
                        outcome["status"] = "success"
                    else:
                        outcome["status"] = "no-match"
                    # Hazard codes are searched for every readable PDF,
                    # whether or not keywords were found.
                    outcome["gefahrstoff codes"] = "; ".join(search_hazard_codes(text))
                    del text
                except Exception as exc:
                    outcome["status"] = "extract-failed"
                    outcome["failure_reason"] = clean_cell(str(exc), 500)
                    if diag is not None:
                        diag.log(f"extract-failed {url} :: {type(exc).__name__}: {exc}")
    finally:
        del pdf_bytes

    with _url_cache_lock:
        if len(_url_cache) < URL_CACHE_MAX:
            _url_cache[url] = outcome
    return outcome


def process_row(row, matcher, product_id_col, url_cols, timeout=DEFAULT_TIMEOUT,
                diag=None, cancel_event=None):
    result = {
        "productID": row.get(product_id_col),
        "chemical_keywords_found": "No",
        "chemicals_found": "",
        "keyword_occurrences": "",
        "gefahrstoff codes": "",
        "pdf_url": "",
        "keywords_phrases": "",
        "status": "no-url",
        "failure_reason": "no PDF URL in row",
    }

    if cancel_event is not None and cancel_event.is_set():
        result["status"] = "cancelled"
        result["failure_reason"] = "scan stopped by user"
        return result

    for url_col in url_cols:
        url = row.get(url_col)
        if _is_blank(url):
            continue

        url = str(url).strip()
        result["pdf_url"] = url
        outcome = _analyse_url(url, matcher, timeout, diag)
        result.update(outcome)

        if outcome["status"] in ("success", "no-match", "skipped-crash-suspect"):
            break   # PDF was handled; no point trying the next column

    return result


# ==============================================================================
# OUTPUT
# ==============================================================================

def _write_output(df_out, output_path, keep_backup_path=None):
    ext = os.path.splitext(output_path)[1].lower()

    if ext == ".csv":
        df_out.to_csv(output_path, index=False, encoding="utf-8-sig")
        return

    if ext in (".xlsx", ".xls"):
        try:
            sanitize_for_excel(df_out).to_excel(output_path, index=False)
        except PermissionError as exc:
            raise PermissionError(
                f"Permission denied while writing '{output_path}'. "
                f"Close it in Excel and retry. Results are safe in "
                f"'{keep_backup_path}'."
            ) from exc
        except Exception as exc:
            fallback = os.path.splitext(output_path)[0] + "_RESULTS.csv"
            df_out.to_csv(fallback, index=False, encoding="utf-8-sig")
            raise RuntimeError(
                f"Excel export failed ({type(exc).__name__}: {exc}). "
                f"All results were saved as CSV instead: '{fallback}'."
            ) from exc
        return

    raise ValueError("Unsupported output format. Use .xlsx, .xls or .csv")


def _validate_output_target(output_path):
    if os.path.isdir(output_path):
        raise IsADirectoryError(
            f"Output path points to a directory, not a file: '{output_path}'. "
            "Choose a filename such as scan_report.xlsx."
        )

    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    try:
        fd, probe_path = tempfile.mkstemp(prefix=".write_test_", suffix=".tmp", dir=output_dir)
        os.close(fd)
        os.remove(probe_path)
    except OSError as exc:
        raise PermissionError(
            f"Cannot write to output directory '{output_dir}'. "
            "Choose another folder with write permissions."
        ) from exc

    if os.path.exists(output_path):
        try:
            with open(output_path, "a+b"):
                pass
        except PermissionError as exc:
            raise PermissionError(
                f"Output file is locked or not writable: '{output_path}'. "
                "Close it in Excel (or any other app) and run again."
            ) from exc


def _build_error_result(row, product_id_column, reason="unexpected worker error"):
    return {
        "productID": row.get(product_id_column),
        "chemical_keywords_found": "",
        "chemicals_found": "",
        "keyword_occurrences": "",
        "gefahrstoff codes": "",
        "pdf_url": "",
        "keywords_phrases": "",
        "status": "error",
        "failure_reason": clean_cell(reason, 500),
    }


class _Checkpoint:
    """Streams every finished row to CSV so a crash never costs a full run.

    Flushed after EVERY row: a process crash loses nothing that was written,
    because flushed data already sits in the OS cache.
    """

    def __init__(self, path, existing_rows=None):
        self.path = path
        self.count = 0
        self.lock = threading.Lock()

        if existing_rows:
            # Rewrite the file de-duplicated, then append. This stops the
            # checkpoint growing duplicate rows over repeated resumes.
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
                writer.writeheader()
                for row in existing_rows:
                    writer.writerow({k: clean_cell(row.get(k, "")) for k in FIELDNAMES})
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, path)
            # NOTE: plain utf-8 on append. utf-8-sig would write a second BOM
            # in the middle of the file and corrupt a row.
            self.fh = open(path, "a", newline="", encoding="utf-8")
            self.writer = csv.DictWriter(self.fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        else:
            self.fh = open(path, "w", newline="", encoding="utf-8-sig")
            self.writer = csv.DictWriter(self.fh, fieldnames=FIELDNAMES, extrasaction="ignore")
            self.writer.writeheader()
            self.fh.flush()

    def write(self, row):
        with self.lock:
            self.writer.writerow({k: clean_cell(row.get(k, "")) for k in FIELDNAMES})
            self.count += 1
            self.fh.flush()
            if self.count % CHECKPOINT_FSYNC_EVERY == 0:
                try:
                    os.fsync(self.fh.fileno())
                except OSError:
                    pass

    def close(self):
        try:
            self.fh.flush()
            try:
                os.fsync(self.fh.fileno())
            except OSError:
                pass
            self.fh.close()
        except Exception:
            pass


def _load_checkpoint(path):
    """Return {productID: row_dict} from an existing checkpoint, de-duplicated."""
    if not os.path.exists(path):
        return {}
    try:
        done = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        if "productID" not in done.columns:
            return {}
        done = done.dropna(subset=["productID"])
        done = done.drop_duplicates(subset=["productID"], keep="last")
        done = done.fillna("")
        return {str(r["productID"]): dict(r) for _, r in done.iterrows()}
    except Exception:
        return {}


# ==============================================================================
# MAIN SCAN
# ==============================================================================

def scan_file(
    input_file,
    output_path,
    product_id_column="ProductId",
    url_columns="Url",
    sample=None,
    workers=DEFAULT_WORKERS,
    timeout=DEFAULT_TIMEOUT,
    dump_first=False,
    progress_callback=None,
    resume=False,
    cancel_event=None,
):
    url_cols = [c.strip() for c in str(url_columns).split(",") if c.strip()]

    df = load_data(input_file)

    if product_id_column not in df.columns:
        raise ValueError(f"Column '{product_id_column}' not found. Available: {list(df.columns)}")
    for url_col in url_cols:
        if url_col not in df.columns:
            raise ValueError(f"Column '{url_col}' not found. Available: {list(df.columns)}")

    if sample is not None and sample > 0:
        df = df.head(sample)

    _validate_output_target(output_path)
    base_path = os.path.splitext(output_path)[0]
    checkpoint_path = base_path + "_checkpoint.csv"

    if dump_first:
        row0 = df.iloc[0]
        url0 = row0[url_cols[0]]
        try:
            pdf_bytes = fetch_pdf(str(url0), timeout=timeout)
            text, method = extract_text_with_fallback(pdf_bytes)
            found, phrases, counts = search_keywords(text, compile_keywords())
            print(f"URL: {url0}")
            print(f"Extractor: {method}  |  text length: {len(text)}")
            print(f"Keywords: {found}")
            print(f"Hazard codes: {search_hazard_codes(text)}")
            print("--- first 2000 chars ---")
            print(text[:2000])
        except Exception as exc:
            print(f"dump-first failed: {type(exc).__name__}: {exc}")
        return pd.DataFrame()

    diag = ScanDiagnostics(base_path).open()
    _url_cache.clear()

    matcher = compile_keywords()
    rows = df.to_dict(orient="records")
    total_rows = len(rows)
    results = [None] * total_rows

    already_done = _load_checkpoint(checkpoint_path) if resume else {}
    pending = []
    for i, row in enumerate(rows):
        key = str(row.get(product_id_column))
        if key in already_done:
            results[i] = already_done[key]
        else:
            pending.append(i)

    total_urls = sum(
        1 for row in rows for url_col in url_cols if not _is_blank(row.get(url_col))
    )

    effective_workers = max(1, min(int(workers), 16))
    diag.log(f"input={input_file}")
    diag.log(f"output={output_path}")
    diag.log(f"rows={total_rows} pending={len(pending)} urls={total_urls} "
             f"workers={effective_workers} timeout={timeout} resume={resume}")

    if progress_callback:
        progress_callback(total_rows - len(pending), total_rows, total_urls)

    checkpoint = _Checkpoint(
        checkpoint_path,
        existing_rows=list(already_done.values()) if already_done else None,
    )
    completed = total_rows - len(pending)
    cancelled = False

    try:
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            futures = {
                executor.submit(
                    process_row, rows[i], matcher, product_id_column,
                    url_cols, timeout, diag, cancel_event,
                ): i
                for i in pending
            }

            disable_pbar = sys.stdout is None or progress_callback is not None
            with tqdm(total=total_rows, initial=completed, desc="Processing",
                      disable=disable_pbar) as pbar:
                for future in as_completed(futures):
                    if cancel_event is not None and cancel_event.is_set() and not cancelled:
                        cancelled = True
                        diag.log("cancellation requested; stopping")
                        for pending_future in futures:
                            pending_future.cancel()

                    idx = futures[future]
                    try:
                        results[idx] = future.result()
                    except Exception as exc:
                        results[idx] = _build_error_result(
                            rows[idx], product_id_column,
                            f"{type(exc).__name__}: {exc}",
                        )
                        diag.log(f"worker error on row {idx}: {type(exc).__name__}: {exc}")

                    if results[idx].get("status") == "cancelled":
                        results[idx] = None
                        continue

                    checkpoint.write(results[idx])
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total_rows, total_urls)
                    pbar.update(1)

                    if completed % GC_EVERY == 0:
                        gc.collect()
                        diag.log(f"progress {completed}/{total_rows}")
    finally:
        checkpoint.close()

    if cancelled or (cancel_event is not None and cancel_event.is_set()):
        diag.log(f"run cancelled at {completed}/{total_rows}; checkpoint kept")
        diag.close()
        raise ScanCancelled(
            f"Scan stopped at {completed}/{total_rows} rows. "
            f"Everything scanned so far is in:\n{checkpoint_path}"
        )

    df_out = pd.DataFrame([r for r in results if r is not None], columns=FIELDNAMES)
    df_out = df_out.fillna("")

    try:
        _write_output(df_out, output_path, keep_backup_path=checkpoint_path)
    except Exception:
        diag.log("export failed; checkpoint kept")
        diag.close()
        raise

    try:
        os.remove(checkpoint_path)   # only once the real report exists
    except OSError:
        pass

    status_counts = df_out["status"].value_counts().to_dict() if not df_out.empty else {}
    diag.log(f"run finished OK: {status_counts}")
    diag.close()

    return df_out


def main():
    parser = argparse.ArgumentParser(description="Scan PDFs for chemical keywords.")
    parser.add_argument("input_file", help="Input CSV or Excel file.")
    parser.add_argument("-o", "--output", default="results.xlsx", help="Output file (.xlsx, .xls or .csv).")
    parser.add_argument("--product-id-column", default="ProductId", help="Column name for product ID")
    parser.add_argument("--url-columns", default="Url", help="Column names for PDF URLs (comma-separated)")
    parser.add_argument("--sample", type=int, default=None, help="Process only first N rows (testing).")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Download workers (1-16).")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="PDF download timeout in seconds.")
    parser.add_argument("--resume", action="store_true", help="Continue from an existing checkpoint file.")
    parser.add_argument("--dump-first", action="store_true", help="Debug the first row and exit.")
    args = parser.parse_args()

    if args.output == "results.xlsx":
        base = os.path.splitext(os.path.basename(args.input_file))[0]
        date_str = datetime.now().strftime("%Y-%m-%d")
        suffix = "TEST" if args.sample else "FULL"
        args.output = f"results/{base}_{suffix}_{date_str}.xlsx"

    started = time.time()
    res = scan_file(
        input_file=args.input_file,
        output_path=args.output,
        product_id_column=args.product_id_column,
        url_columns=args.url_columns,
        sample=args.sample,
        workers=args.workers,
        timeout=args.timeout,
        dump_first=args.dump_first,
        resume=args.resume,
    )

    if not res.empty:
        found_count = (res["chemical_keywords_found"] == "Yes").sum()
        hazard_count = res["gefahrstoff codes"].fillna("").astype(str).str.strip().ne("").sum()
        print("\nSummary:")
        print(f"  Total processed: {len(res)}")
        print(f"  Chemical keywords found: {found_count} ({100 * found_count / len(res):.1f}%)")
        print(f"  Gefahrenstoff codes found: {hazard_count} ({100 * hazard_count / len(res):.1f}%)")
        print(f"  Elapsed: {(time.time() - started) / 60:.1f} min")
        print(f"  Report: {args.output}")


if __name__ == "__main__":
    main()