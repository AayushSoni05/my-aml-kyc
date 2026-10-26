import requests
from rapidfuzz import fuzz
from app.idp.textutil import norm_text

GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"


def find_company_in_gleif(company_name: str, min_similarity: int = 85, timeout: int = 10):
    """Returns the best matching LEI record as a dict, or None. Raises on network errors."""
    r = requests.get(GLEIF_URL, params={"filter[fulltext]": company_name, "page[size]": 5}, timeout=timeout)
    r.raise_for_status()
    best, best_score = None, 0
    for rec in r.json().get("data", []):
        e = rec["attributes"]["entity"]
        name = e["legalName"]["name"]
        score = fuzz.token_sort_ratio(norm_text(company_name), norm_text(name))
        if score > best_score:
            best_score = score
            best = {"lei": rec["attributes"]["lei"], "name": name, "status": e.get("status"),
                    "registered_as": e.get("registeredAs"),
                    "country": (e.get("legalAddress") or {}).get("country"), "similarity": score}
    return best if best and best_score >= min_similarity else None