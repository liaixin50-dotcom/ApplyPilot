"""Heuristic scorer: lightweight fallback when LLM is unavailable.

Scores jobs 1-10 by keyword overlap between resume and job description.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from collections import Counter

from applypilot.config import RESUME_PATH
from applypilot.database import get_connection


def tokenize(text: str) -> list[str]:
    text = text.lower()
    toks = re.findall(r"[a-z0-9+#]+", text)
    return toks


def score_from_overlap(resume: str, job_text: str) -> tuple[int, str, str]:
    r_toks = tokenize(resume)
    j_toks = tokenize(job_text)
    if not j_toks:
        return 1, "", "No job text"

    r_counts = Counter(r_toks)
    common = [t for t in set(j_toks) if t in r_counts]
    match_count = sum(min(r_counts[t], j_toks.count(t)) for t in common)
    # baseline: fraction of unique job tokens matched
    frac = len(common) / max(1, len(set(j_toks)))
    # map frac to 1-10
    score = int(1 + round(frac * 9))
    keywords = ", ".join(sorted(common)[:10])
    reasoning = f"Matched {len(common)} keywords; fraction={frac:.2f}; matches={match_count}"
    return score, keywords, reasoning


def main():
    conn = get_connection()
    resume = RESUME_PATH.read_text(encoding="utf-8")
    rows = conn.execute("SELECT url, title, full_description FROM jobs WHERE full_description IS NOT NULL").fetchall()
    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    for row in rows:
        url = row[0]
        title = row[1]
        desc = row[2] or ""
        score, keywords, reasoning = score_from_overlap(resume, desc[:8000])
        conn.execute(
            "UPDATE jobs SET fit_score = ?, score_reasoning = ?, scored_at = ? WHERE url = ?",
            (score, f"{keywords}\n{reasoning}", now, url),
        )
        updated += 1
    conn.commit()
    print(f"Updated {updated} jobs with heuristic scores.")


if __name__ == '__main__':
    main()
