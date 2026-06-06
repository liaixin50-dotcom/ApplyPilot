"""Enrich Jobs in DB by visiting their job detail pages and saving full_description.

Usage:
  $env:PYTHONPATH='src'
  python scripts/enrich_jobsdb.py --limit 10
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
import argparse

from playwright.sync_api import sync_playwright

from applypilot.database import get_connection


def extract_text_from_page(page):
    selectors = ["main", "article", ".job-detail", "#jobDetail", ".job-description", ".jd"]
    text = None
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                text = el.inner_text()
                if text and len(text) > 50:
                    return text.strip()
        except Exception:
            continue
    try:
        text = page.inner_text("body")
    except Exception:
        text = None
    return text.strip() if text else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--cookies", default="")
    args = parser.parse_args()

    conn = get_connection()
    rows = conn.execute("SELECT url FROM jobs WHERE full_description IS NULL LIMIT ?", (args.limit,)).fetchall()
    urls = [r[0] for r in rows]
    if not urls:
        print("No jobs need enrichment.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        context = browser.new_context(user_agent=ua, locale="en-US")
        page = context.new_page()

        for url in urls:
            try:
                print("Visiting:", url)
                page.goto(url, timeout=180000)
                page.wait_for_load_state("networkidle", timeout=180000)
                time.sleep(1)
                text = extract_text_from_page(page)
                now = datetime.now(timezone.utc).isoformat()
                if text:
                    conn.execute(
                        "UPDATE jobs SET full_description = ?, detail_scraped_at = ?, detail_error = NULL WHERE url = ?",
                        (text, now, url),
                    )
                    conn.commit()
                    print("Updated full_description for:", url[:80])
                else:
                    conn.execute(
                        "UPDATE jobs SET detail_error = ? WHERE url = ?",
                        ("no_detail_found", url),
                    )
                    conn.commit()
                    print("No detail found for:", url)
            except Exception as e:
                print("Error visiting", url, e)
                conn.execute(
                    "UPDATE jobs SET detail_error = ? WHERE url = ?",
                    (str(e), url),
                )
                conn.commit()

        browser.close()


if __name__ == "__main__":
    main()
