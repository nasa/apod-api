#!/usr/bin/env python3
"""Verify the documented APOD API contract against the patched local service."""
import json
import urllib.request

BASE = "http://127.0.0.1:5000/v1/apod/"


def get(qs):
    req = urllib.request.Request(f"{BASE}{qs}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


# 1. documented contract: url matches the permalink
s, d = get("?date=2015-10-11")
print(f"[1] date=2015-10-11 HTTP {s} | url == permalink: {d.get('url') == d.get('permalink')} | {d.get('title')}")

# 2. video entry: no crash
s, d = get("?date=2026-09-13")
print(f"[2] video 260913 HTTP {s} | media_type: {d.get('media_type')} | url == permalink: {d.get('url') == d.get('permalink')}")

# 3. start_date extends to today
s, d = get("?start_date=2026-08-01")
dates = [x.get("date") for x in d]
print(f"[3] start_date HTTP {s} | {len(d)} items | {dates[-1]} -> {dates[0]}")

# 4. exact count
s, d = get("?count=3")
print(f"[4] count=3 HTTP {s} | {len(d)} items")

# 5. long range without duplicates
s, d = get("?start_date=2026-07-01&end_date=2026-09-14")
dates = [x.get("date") for x in d]
print(f"[5] 76-day range HTTP {s} | {len(d)} items | duplicates: {len(dates) - len(set(dates))}")

# 6. unknown date -> 400
s, d = get("?date=banana")
print(f"[6] banana HTTP {s} | msg: {d.get('msg', '')[:60]}")

# 7. permalinks preserved in lists
s, d = get("?start_date=2026-08-01")
ok = all(x.get("url", "").startswith("https://science.nasa.gov/") for x in d)
print(f"[7] lists: url is a science.nasa.gov permalink everywhere: {ok}")
