"""Fetch JobsDB search results and store into ApplyPilot DB.

Usage (PowerShell):
  $env:PYTHONPATH='src'
  python scripts/fetch_jobsdb.py --query "marketing" --location "Hong Kong" --limit 3 --cookies "sol_id=...; _cfuvid=..."

Notes:
- Requires Playwright: `pip install playwright` and `playwright install`.
- Run from project root with `PYTHONPATH=src` so `applypilot` package is importable.
- The script sets cookies for the `.jobsdb.com` domain using the provided cookie string.
"""
from __future__ import annotations

import argparse
import time
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

from applypilot.database import init_db, get_connection, store_jobs


def parse_cookies(cookie_str: str) -> list[dict]:
    cookies = []
    for part in cookie_str.split(";"):
        if not part.strip():
            continue
        if "=" not in part:
            continue
        name, val = part.strip().split("=", 1)
        cookies.append({
            "name": name.strip(),
            "value": val.strip(),
            "domain": ".jobsdb.com",
            "path": "/",
        })
    return cookies


def build_search_url(query: str, location: str) -> str:
    q = quote_plus(query)
    loc = quote_plus(location) if location else ""
    # JobsDB HK search URL pattern
    return f"https://hk.jobsdb.com/hk/en/Search/FindJobs?Key={q}&Location={loc}"


def extract_candidates_from_page(page, limit: int) -> list[dict]:
    anchors = page.query_selector_all("a[href*='/job/']")
    seen = set()
    jobs = []
    for a in anchors:
        try:
            href = a.get_attribute("href") or ""
            if href.startswith("/"):
                href = "https://hk.jobsdb.com" + href
            if "jobsdb" not in href:
                continue
            if href in seen:
                continue
            seen.add(href)
            title = a.inner_text().strip()[:200]
            # try to find company/location in nearby elements
            parent = a.evaluate_handle("el => el.closest('article,div')")
            company = None
            location = None
            if parent:
                try:
                    comp_el = parent.as_element().query_selector(".job-card__company, .company, .employer")
                    if comp_el:
                        company = comp_el.inner_text().strip()
                except Exception:
                    pass
            jobs.append({
                "url": href,
                "title": title or None,
                "company": company,
                "location": location,
                "description": None,
            })
            if len(jobs) >= limit:
                break
        except Exception:
            continue
    return jobs


def enrich_job_detail(page, job: dict) -> dict:
    # attempt to extract a fuller description
    try:
        # common selector areas
        selectors = ["main", "article", ".job-detail", "#jobDetail"]
        text = None
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    text = el.inner_text()
                    break
            except Exception:
                continue
        if not text:
            text = page.inner_text("body")
        job["description"] = text.strip()[:20000] if text else None
    except Exception:
        job["description"] = None
    return job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--location", default="")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--cookies", default="")
    args = parser.parse_args()

    url = build_search_url(args.query, args.location)

    init_db()
    conn = get_connection()

    with sync_playwright() as p:
        # headful for debugging; increase timeouts and add retry logic
        browser = p.chromium.launch(headless=False, slow_mo=50)
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        context = browser.new_context(user_agent=ua, locale="en-US", accept_downloads=False)

        # set common headers
        try:
            context.set_extra_http_headers({"accept-language": "en-US,en;q=0.9"})
        except Exception:
            pass

        if args.cookies:
            ck = parse_cookies(args.cookies)
            if ck:
                context.add_cookies(ck)

        page = context.new_page()
        print(f"Navigating to: {url}")

        # robust navigation with retries
        nav_attempts = 3
        nav_timeout = 180000
        for attempt in range(1, nav_attempts + 1):
            try:
                page.goto(url, timeout=nav_timeout)
                page.wait_for_load_state("networkidle", timeout=nav_timeout)
                time.sleep(1)
                break
            except Exception as e:
                print(f"Navigate attempt {attempt} failed: {e}")
                if attempt < nav_attempts:
                    time.sleep(2 * attempt)
                    continue
                else:
                    print("All navigation attempts failed.")

        jobs = extract_candidates_from_page(page, limit=args.limit)

        # Visit each job page to collect details
        detailed = []
        for j in jobs:
            try:
                print("Fetching job:", j["url"])
                page.goto(j["url"], timeout=60000)
                page.wait_for_load_state("networkidle", timeout=60000)
                time.sleep(0.5)
                enrich_job_detail(page, j)
                detailed.append({
                    "url": j.get("url"),
                    "title": j.get("title"),
                    "salary": None,
                    "description": j.get("description"),
                    "location": j.get("location"),
                })
            except Exception as e:
                print("Error fetching job detail:", e)

        if detailed:
            new, existing = store_jobs(conn, detailed, site="JobsDB", strategy="smartextract-playwright")
            print(f"Stored: {new} new, {existing} existing")
        else:
            print("No jobs found to store.")

        browser.close()


if __name__ == "__main__":
    main()
