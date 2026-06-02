import os
import re
import json
import sys
from threading import Lock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TYPES_CACHE_FILE = 'device_types_cache.json'
DATES_CACHE_FILE = 'serial_dates_cache.json'
CACHE_LOCK = Lock()

def normalize_date(date_str):
    if not date_str:
        return "1900-01-01"
    
    m = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str.strip())
    if m:
        try:
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
        except ValueError:
            return "1900-01-01"
    else:
        m_year = re.search(r'\b((?:18|19|20)\d{2})\b', date_str)
        if m_year:
            return f"{m_year.group(1)}-01-01"
        return "1900-01-01"
        
    if year < 1800 or year > 2026:
        year = 1900
        
    if 13 <= month <= 53:
        month = max(1, min(12, int(month * 7 / 30.4) + 1))
    if month < 1 or month > 12:
        month = 1
        
    if day < 1 or day > 28:
        day = 1
        
    return f"{year:04d}-{month:02d}-{day:02d}"

def load_json_cache(filename):
    with CACHE_LOCK:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

def save_json_cache(filename, data):
    with CACHE_LOCK:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache {filename}: {e}", file=sys.stderr)
