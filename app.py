"""
app.py
------
The Flask entry point. Exposes a small REST API that the React dashboard
talks to, and starts the background agent scheduler when the server boots.

Run with:  python app.py
Then the API is live at http://localhost:5000
"""

import os 
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import (
    init_db, get_profile, save_profile,
    get_all_listings, update_listing_status,
)
from scheduler import run_agent_cycle, start_background_scheduler

app = Flask(__name__)
CORS(app)  # allows the React dev server (different port) to call this API


@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    """Returns the stored resume profile, or 404 if none is set yet."""
    profile = get_profile()
    if not profile:
        return jsonify({"error": "no profile set"}), 404
    return jsonify(profile)


@app.route("/api/profile", methods=["POST"])
def api_save_profile():
    """
    Save/update the profile the matcher scores listings against.
    Expects JSON body: { skills, target_roles, location, resume_text }
    """
    data = request.get_json()
    save_profile(
        skills=data.get("skills", ""),
        target_roles=data.get("target_roles", ""),
        location=data.get("location", ""),
        resume_text=data.get("resume_text", ""),
    )
    return jsonify({"status": "saved"})


@app.route("/api/listings", methods=["GET"])
def api_get_listings():
    """Returns every saved listing, best fit_score first -- feeds the dashboard table."""
    return jsonify(get_all_listings())


@app.route("/api/listings/<int:listing_id>/status", methods=["POST"])
def api_update_status(listing_id):
    """
    Called when the user clicks a status button in the dashboard
    (e.g. mark as 'applied' or 'ignored').
    Expects JSON body: { "status": "applied" }
    """
    data = request.get_json()
    update_listing_status(listing_id, data.get("status", "new"))
    return jsonify({"status": "updated"})


@app.route("/api/trigger-scan", methods=["POST"])
def api_trigger_scan():
    """
    Manual 'Run Now' button in the dashboard, instead of waiting for the
    next scheduled cycle. Runs the full agent loop synchronously and
    returns a summary immediately.
    """
    result = run_agent_cycle()
    return jsonify(result)


if __name__ == "__main__":
    init_db()                        # create tables if they don't exist
    start_background_scheduler(6)    # auto-run every 6 hours
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
