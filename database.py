"""
database.py
-----------
Handles all SQLite database setup and queries for the job monitor agent.
Keeping DB logic in one file means app.py and agent/*.py never write raw SQL
directly -- they just call these functions.
"""

import sqlite3
from datetime import datetime

DB_PATH = "job_monitor.db"


def get_connection():
    """Open a connection with row access by column name (like a dict)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call every startup."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY,
            skills TEXT,
            target_roles TEXT,
            location TEXT,
            resume_text TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            description TEXT,
            apply_link TEXT,
            source TEXT,
            date_found TIMESTAMP,
            fit_score REAL,
            category TEXT,
            status TEXT DEFAULT 'new',
            UNIQUE(title, company)  -- prevents saving the exact same listing twice
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TIMESTAMP,
            listings_found INTEGER,
            new_matches INTEGER,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_profile():
    """Return the single stored profile row as a plain dict."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def save_profile(skills, target_roles, location, resume_text):
    """Insert or overwrite the one profile row (id is always 1)."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO profile (id, skills, target_roles, location, resume_text)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            skills=excluded.skills,
            target_roles=excluded.target_roles,
            location=excluded.location,
            resume_text=excluded.resume_text
    """, (skills, target_roles, location, resume_text))
    conn.commit()
    conn.close()


def save_listing(listing):
    """
    Insert a new job listing. If a listing with the same title+company
    already exists, silently skip it (INSERT OR IGNORE) so re-running
    the agent doesn't create duplicates.
    """
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO job_listings
        (title, company, location, description, apply_link, source,
         date_found, fit_score, category, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
    """, (
        listing["title"], listing["company"], listing["location"],
        listing["description"], listing["apply_link"], listing["source"],
        datetime.now(), listing["fit_score"], listing["category"]
    ))
    conn.commit()
    conn.close()


def get_all_listings():
    """Return every listing, best matches first -- what the dashboard reads."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM job_listings ORDER BY fit_score DESC, date_found DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_listing_status(listing_id, status):
    """Called when the user clicks 'Applied' / 'Ignore' in the dashboard."""
    conn = get_connection()
    conn.execute(
        "UPDATE job_listings SET status = ? WHERE id = ?", (status, listing_id)
    )
    conn.commit()
    conn.close()


def log_agent_run(listings_found, new_matches, status="success"):
    """Record one agent cycle so you can show a history / debug failures."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO agent_runs (run_time, listings_found, new_matches, status)
        VALUES (?, ?, ?, ?)
    """, (datetime.now(), listings_found, new_matches, status))
    conn.commit()
    conn.close()
