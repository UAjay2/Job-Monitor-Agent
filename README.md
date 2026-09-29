# Job Monitor Agent

A small AI agent that fetches job listings, scores them against your resume
using NLP, and surfaces the best matches on a React dashboard.

## Architecture

```
[Scheduler] -> [Fetcher] -> [Matcher/Scorer] -> [SQLite DB] -> [React Dashboard]
```

- **fetcher.py** – gets raw job listings (mock data by default; swap in a
  real API or scraper once the pipeline works)
- **matcher.py** – scores each listing against your resume using TF-IDF +
  cosine similarity (upgradeable to an LLM call for smarter reasoning)
- **scheduler.py** – the agent loop: fetch -> score -> filter -> save,
  running automatically every few hours or on demand
- **database.py** – all SQLite reads/writes in one place
- **app.py** – Flask REST API the dashboard talks to
- **frontend/src/App.jsx** – React dashboard: view matches, run a manual
  scan, mark listings as applied/ignored

## Backend setup

```bash
pip install -r requirements.txt
python app.py
```

This starts the API at `http://localhost:5000` and creates `job_monitor.db`
automatically on first run.

Before the agent finds real matches, add your profile:

```bash
curl -X POST http://localhost:5000/api/profile \
  -H "Content-Type: application/json" \
  -d '{
    "skills": "Python, Flask, React, SQL, NLP",
    "target_roles": "Business Analyst, Junior Developer, Data Analyst",
    "location": "Hyderabad",
    "resume_text": "PASTE YOUR FULL RESUME TEXT HERE"
  }'
```

Then trigger a scan:

```bash
curl -X POST http://localhost:5000/api/trigger-scan
```

## Frontend setup

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios
# replace the generated src/App.jsx with the one from this project
npm run dev
```

Open the printed localhost URL to see the dashboard.

## Next steps / upgrade path

1. Replace the mock fetcher with a real job board API or scraper.
2. Replace the TF-IDF matcher with an LLM call (Claude/GPT) that returns a
   score _and_ a reason -- this is what turns the project from "an ML
   script" into "an AI agent" for interview purposes.
3. Extend into a multi-agent system: one agent finds listings, a second
   scores them, a third drafts a personalized outreach message for your
   top matches.
