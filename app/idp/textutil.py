import re
import unicodedata
from datetime import date
from typing import Optional

def normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NKFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return " ".join(s.split())

def normalize_id(s: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").upper())

def parse_iso(s) -> Optional[date]:
   if isinstance(s, date):
        return s
   try:
       return date.fromisoformat(s)
   except (ValueError, TypeError):
        return None
    
   