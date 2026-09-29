"""
agent/scheduler.py
-------------------
This is the "agent loop" itself: fetch -> score -> filter -> save -> log.
Runs automatically every few hours, and can also be triggered manually
(the Flask "run now" endpoint calls run_agent_cycle() directly).
"""

import schedule
import time
import threading

from fetcher import fetch_new_listings
from matcher import score_listing, categorize
from database import save_listing, get_profile, log_agent_run

MIN_SCORE_TO_SAVE = 5


def run_agent_cycle():
    """
    One full pass of the agent: get the user's profile, fetch fresh listings,
    score each one against the resume, and save the ones worth seeing.
    Returns a small summary dict so callers (like the Flask endpoint) can
    report back to the user immediately.
    """
    profile = get_profile()
    if not profile:
        print("No profile found -- add one via POST /api/profile first.")
        return {"error": "no profile set"}

    listings = fetch_new_listings(profile["target_roles"], profile["location"])

    new_matches = 0
    for listing in listings:
        score = score_listing(listing["description"], profile["resume_text"])
        listing["fit_score"] = score
        listing["category"] = categorize(score)

        if score >= MIN_SCORE_TO_SAVE:
            save_listing(listing)
            new_matches += 1

    log_agent_run(listings_found=len(listings), new_matches=new_matches)
    print(f"Agent cycle complete: {len(listings)} found, {new_matches} saved.")

    return {"listings_found": len(listings), "new_matches": new_matches}


def start_background_scheduler(interval_hours: int = 6):
    """
    Kicks off a background thread that runs run_agent_cycle() on a timer,
    without blocking the main Flask app from serving requests.
    """
    schedule.every(interval_hours).hours.do(run_agent_cycle)

    def loop():
        while True:
            schedule.run_pending()
            time.sleep(60)  # check every minute whether it's time to run

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"Background scheduler started (every {interval_hours}h).")
