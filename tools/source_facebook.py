#!/usr/bin/env python3
"""
source_facebook.py — Apify Facebook Pages scraper for tutoring profiles.

Many Thai private tutors operate primarily through Facebook (no Google Maps
presence). This script complements tools/source_listings.py by scraping a list
of Facebook page URLs and writing L1 fields to a CSV.

Workflow:
  1. Collect Facebook page URLs from manual search, Pantip threads, or the
     Apify Facebook Search actor. One URL per line.
  2. Run this script with the URL file.
  3. Output CSV merges with source_listings.py output via tools/import_csv.py.

Requires:
  - APIFY_TOKEN in environment (~/.env or shell)
  - $5 free credit covers roughly 100-200 page scrapes (~$0.02-0.05 each)

Usage:
  python3 tools/source_facebook.py \\
      --urls-file .tmp/fb_urls.txt \\
      --out .tmp/raw_facebook.csv

  # Or pass URLs directly (comma-separated):
  python3 tools/source_facebook.py \\
      --urls https://facebook.com/page1,https://facebook.com/page2 \\
      --out .tmp/raw_facebook.csv
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ACTOR_ID = "apify~facebook-pages-scraper"
APIFY_API = "https://api.apify.com/v2"


def call(method, path, token, body=None, expect_json=True):
    url = f"{APIFY_API}{path}?token={token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            content = r.read()
            return json.loads(content) if expect_json else content
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}: {e.read().decode()[:300]}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--urls-file", help="Text file with one Facebook page URL per line")
    grp.add_argument("--urls", help="Comma-separated Facebook page URLs")
    parser.add_argument("--out", default=".tmp/raw_facebook.csv")
    args = parser.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("✗ APIFY_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    if args.urls_file:
        urls = [l.strip() for l in Path(args.urls_file).read_text(encoding="utf-8").splitlines() if l.strip() and l.startswith("http")]
    else:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]

    if not urls:
        print("✗ No URLs to scrape", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    actor_input = {
        "startUrls": [{"url": u} for u in urls],
        "scrapePageAds": False,
        "scrapeAboutPage": True,
        "scrapeReviews": False,
        "scrapePosts": False,
    }

    print(f"→ Running Apify actor '{ACTOR_ID}'")
    print(f"  {len(urls)} Facebook URLs to scrape")

    run = call("POST", f"/acts/{ACTOR_ID}/runs", token, body=actor_input)
    run_id = run["data"]["id"]
    print(f"  Run {run_id}\n  Waiting...", end="", flush=True)

    while True:
        time.sleep(8)
        status = call("GET", f"/actor-runs/{run_id}", token)
        s = status["data"]["status"]
        if s == "SUCCEEDED":
            print(" ✓ done")
            break
        if s in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f" ✗ {s}")
            sys.exit(1)
        print(".", end="", flush=True)

    dataset_id = status["data"]["defaultDatasetId"]
    items = json.loads(call("GET", f"/datasets/{dataset_id}/items", token, expect_json=False))
    print(f"  Got {len(items)} pages")

    fieldnames = [
        "name_th", "address_th", "city", "district", "phone",
        "website", "facebook_url", "facebook_likes", "facebook_followers",
        "about_th", "category_fb", "source_url",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for it in items:
            w.writerow({
                "name_th": (it.get("title") or it.get("name") or "").strip(),
                "address_th": (it.get("address") or "").strip(),
                "city": it.get("city") or "",
                "district": it.get("region") or "",
                "phone": it.get("phone") or "",
                "website": it.get("website") or "",
                "facebook_url": it.get("pageUrl") or it.get("url") or "",
                "facebook_likes": it.get("likes") or "",
                "facebook_followers": it.get("followers") or "",
                "about_th": (it.get("about") or it.get("intro") or "").strip()[:500],
                "category_fb": it.get("categories", [{}])[0] if it.get("categories") else "",
                "source_url": it.get("url") or "",
            })

    print(f"\n✓ Wrote {len(items)} rows to {out_path}")
    print("\nNext: paste rows to Claude for L3 enrichment (description + speakable + FAQ)")
    print("      or merge with .tmp/raw_listings.csv before tools/enrich_listing.py")


if __name__ == "__main__":
    main()
