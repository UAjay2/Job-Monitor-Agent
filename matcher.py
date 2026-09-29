"""
agent/matcher.py
-----------------
The "reasoning" piece of the agent. Given a job description and your resume
text, it produces a fit score from 0-100.

Starts with TF-IDF + cosine similarity (classic NLP, uses scikit-learn which
sits right next to the NLTK skills you already have). A clearly marked
upgrade path below shows how to swap this for an LLM call later, which is
what turns this from "an ML script" into "an agent that reasons."
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def score_listing(job_description: str, resume_text: str) -> float:
    """
    Returns a 0-100 similarity score between a job description and a resume.

    How it works:
    1. TfidfVectorizer turns both texts into weighted word-frequency vectors,
       downweighting common words ("the", "and") and upweighting distinctive
       ones ("Flask", "NLP", "SQL").
    2. cosine_similarity measures the angle between those two vectors --
       1.0 means identical topic focus, 0.0 means no overlap at all.
    3. We multiply by 100 and round for a human-readable score.
    """
    if not job_description or not resume_text:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text, job_description])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    return round(similarity * 100, 1)


def categorize(score: float) -> str:
    """Buckets a numeric score into the labels used across your job search."""
    if score >= 80:
        return "Apply First"
    elif score >= 60:
        return "Good Match"
    else:
        return "Stretch"


# ---------------------------------------------------------------------------
# UPGRADE PATH (do this once the basic version works end-to-end):
#
# Replace the body of score_listing() with a call to the Claude API, sending
# both texts and asking for a JSON response like:
#   {"score": 82, "reason": "Strong match on Python, SQL, and Flask; missing
#    2 years experience requirement"}
#
# This is the step that turns the project from "TF-IDF script" into
# "AI agent" for your resume/interviews -- the model reasons about *why*
# something matches, not just word-overlap statistics.
# ---------------------------------------------------------------------------
