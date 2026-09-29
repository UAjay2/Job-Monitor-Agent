"""
agent/fetcher.py
-----------------
Responsible for getting real job listings from the Adzuna API.

Adzuna aggregates real job postings (including India via country code "in")
and returns genuine apply links, company names, and descriptions -- no more
example.com placeholders.

Get your free credentials at https://developer.adzuna.com/signup, then set
them as environment variables (see the bottom of this file for how) rather
than hardcoding them directly in this file.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
ADZUNA_COUNTRY = "in"  # India
BASE_URL = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"


def fetch_new_listings(target_roles: str, location: str) -> list[dict]:
    """
    Returns a list of job listing dicts, one search per role in
    target_roles, merged together. Searching per-role (instead of joining
    them into one query string) gets meaningfully better results, since
    Adzuna treats "what" as a single search phrase rather than "match any
    of these."

    target_roles: comma-separated string, e.g. "Business Analyst, Data Analyst"
    location: city name, e.g. "Hyderabad"
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("Adzuna credentials missing -- set ADZUNA_APP_ID and ADZUNA_APP_KEY.")
        return []

    roles = [r.strip() for r in target_roles.split(",") if r.strip()]
    all_listings = []

    for role in roles:
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": role,
            "where": location,
            "results_per_page": 10,
            "content-type": "application/json",
        }

        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Adzuna request failed for role '{role}': {e}")
            continue

        for job in data.get("results", []):
            all_listings.append({
                "title": job.get("title", "Untitled"),
                "company": job.get("company", {}).get("display_name", "Unknown"),
                "location": job.get("location", {}).get("display_name", location),
                "description": job.get("description", ""),
                "apply_link": job.get("redirect_url", ""),
                "source": "Adzuna",
            })

    return all_listings


# ---------------------------------------------------------------------------
# SETTING YOUR CREDENTIALS (don't hardcode them in this file, and never
# commit them to GitHub):
#
# Windows PowerShell (for the current terminal session only):
#   $env:ADZUNA_APP_ID = "your_app_id_here"
#   $env:ADZUNA_APP_KEY = "your_app_key_here"
#   python app.py
#
# Mac/Linux:
#   export ADZUNA_APP_ID="your_app_id_here"
#   export ADZUNA_APP_KEY="your_app_key_here"
#   python app.py
#
# For a permanent setup, create a .env file (add it to .gitignore!) and use
# python-dotenv to load it automatically -- ask if you want this wired up.
# ---------------------------------------------------------------------------