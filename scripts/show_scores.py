from applypilot.database import get_connection, get_jobs_by_stage

conn = get_connection()
jobs = get_jobs_by_stage(conn, stage='scored', limit=5)
for j in jobs:
    print(f"score={j.get('fit_score')}	title={j.get('title')}")
    print(f"url={j.get('url')}")
    sr = j.get('score_reasoning') or ''
    print(f"reasoning={sr.splitlines()[0] if sr else ''}\n")
