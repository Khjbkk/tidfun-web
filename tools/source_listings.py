#!/usr/bin/env python3
"""
source_listings.py — Bigfoot §3 STEP 3 sourcing via Apify.

Calls the Apify google-maps-scraper actor with a Thai-language search,
waits for completion, downloads the dataset, and writes a raw CSV with
L1 (BASE) fields per content.config.ts.

Requires:
  - APIFY_TOKEN in environment (~/.env or shell)
    Get yours at: https://console.apify.com/account/integrations
  - First-time users: $5 free credit (≈ 66 places at ~$0.075 each)

Usage:
  export APIFY_TOKEN=apify_api_xxxxx
  python3 tools/source_listings.py \\
      --query "สถาบันกวดวิชา" \\
      --location "Bangkok, Thailand" \\
      --limit 50 \\
      --out .tmp/raw_listings.csv

The output CSV maps to L1 fields ready for tools/enrich_listing.py or
manual enrichment via Claude in batches.
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

ACTOR_ID = "compass~crawler-google-places"
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
    parser = argparse.ArgumentParser(description="Apify Google Maps scraper for Thai tutoring listings")
    parser.add_argument("--query", required=True, help="Search terms (Thai works), e.g. 'สถาบันกวดวิชา'")
    parser.add_argument("--location", required=True, help="Location query, e.g. 'Bangkok, Thailand'")
    parser.add_argument("--limit", type=int, default=50, help="Max places per search (cost = ~$0.075 each)")
    parser.add_argument("--out", default=".tmp/raw_listings.csv")
    parser.add_argument("--language", default="th")
    parser.add_argument("--country", default="th")
    args = parser.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("✗ APIFY_TOKEN not set. Add to ~/.env or run:", file=sys.stderr)
        print("    export APIFY_TOKEN=apify_api_xxxxx", file=sys.stderr)
        print("  Get yours at https://console.apify.com/account/integrations", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    actor_input = {
        "searchStringsArray": [args.query],
        "locationQuery": args.location,
        "maxCrawledPlacesPerSearch": args.limit,
        "language": args.language,
        "countryCode": args.country,
        "deeperCityScrape": False,
        "scrapeReviews": False,
        "scrapeReviewerName": False,
    }

    estimated_cost = args.limit * 0.0075
    print(f"→ Running Apify actor '{ACTOR_ID}'")
    print(f"  Query: '{args.query}' near '{args.location}'")
    print(f"  Limit: {args.limit} places  (estimated cost: ~${estimated_cost:.2f})")
    print()

    # Start the actor
    run = call("POST", f"/acts/{ACTOR_ID}/runs", token, body=actor_input)
    run_id = run["data"]["id"]
    print(f"  Started run {run_id}")

    # Poll until done
    print("  Waiting for completion...", end="", flush=True)
    while True:
        time.sleep(8)
        status = call("GET", f"/actor-runs/{run_id}", token)
        s = status["data"]["status"]
        if s in ("SUCCEEDED",):
            print(" ✓ done")
            break
        if s in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f" ✗ {s}")
            sys.exit(1)
        print(".", end="", flush=True)

    # Download dataset items
    dataset_id = status["data"]["defaultDatasetId"]
    print(f"  Fetching dataset {dataset_id}...")
    items_raw = call(
        "GET", f"/datasets/{dataset_id}/items", token, expect_json=False,
    )
    items = json.loads(items_raw)
    print(f"  Got {len(items)} place records")

    # Map to L1 schema fields
    fieldnames = [
        "name_th", "address_th", "lat", "lng", "city", "district",
        "phone", "website", "facebook_url",
        "google_rating", "google_review_count",
        "place_id", "source_url",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for it in items:
            phones = it.get("phoneUnformatted") or it.get("phone") or ""
            w.writerow({
                "name_th": (it.get("title") or "").strip(),
                "address_th": (it.get("address") or "").strip(),
                "lat": it.get("location", {}).get("lat") or "",
                "lng": it.get("location", {}).get("lng") or "",
                "city": it.get("city") or "",
                "district": it.get("neighborhood") or "",
                "phone": phones,
                "website": it.get("website") or "",
                "facebook_url": "",
                "google_rating": it.get("totalScore") or "",
                "google_review_count": it.get("reviewsCount") or "",
                "place_id": it.get("placeId") or "",
                "source_url": it.get("url") or "",
            })

    print(f"\n✓ Wrote {len(items)} rows to {out_path}")
    print("\nNext step — enrich to L3:")
    print(f"  Option A (Claude): paste the CSV to Claude in batches of 5-10 rows")
    print(f"  Option B (OpenAI): python3 tools/enrich_listing.py --input {out_path}")
    print("  Then: python3 tools/import_csv.py --input <enriched.csv>")
    print("        python3 tools/validate_listings.py")
    print("        npm run build")


if __name__ == "__main__":
    main()
