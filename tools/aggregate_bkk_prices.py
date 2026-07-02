#!/usr/bin/env python3
"""
aggregate_bkk_prices.py — Aggregate Bangkok tutor price stats from listings.

Reads src/content/listings/*.md frontmatter, filters city=bangkok, parses the
`quick_facts.price_range` field, and outputs percentile stats grouped by:
  - overall Bangkok
  - by subject (math, english, ...)
  - by category / grade (por1, mor4, tcas, ...)
  - by district
  - by listing type (cram_school, tutor, ...)

Stats reported per group: n, min, p25, median (p50), p75, max, mean.

Price formats handled:
  ฿1,000-1,500/ชม.
  ประมาณ ฿2,500-5,500/เดือน
  ฿4,500/เดือน            (single value → both min & max)
  ฿10,000-30,000          (no unit → grouped under "unspecified")

Groups are kept separate per unit (/เดือน, /ชม., /คอร์ส, ...) — mixing units
would corrupt medians. The report also normalizes /เดือน → hourly equivalent
using the assumption 1 month ≈ 8 hours of instruction (see NOTE below).

Usage:
  python3 tools/aggregate_bkk_prices.py
  python3 tools/aggregate_bkk_prices.py --output .tmp/blog-strategy/bkk_price_stats.json

NOTE on hourly conversion: standard cram-school format is 2 hours × 1 session/week
= 8 hours/month. Adjust HOURS_PER_MONTH if the site's typical rhythm differs.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
LISTINGS_DIR = ROOT / "src" / "content" / "listings"
DEFAULT_OUTPUT = ROOT / ".tmp" / "blog-strategy" / "bkk_price_stats.json"

HOURS_PER_MONTH = 8  # 2h × 1 session/wk ≈ 8h/month — adjust if needed

# ฿X,XXX-X,XXX/unit  or  ฿X,XXX/unit  or  no unit
PRICE_RE = re.compile(
    r"฿\s*([\d,]+)\s*(?:-\s*([\d,]+))?\s*(?:/\s*([^\s\"']+))?"
)


def load_frontmatter(md_path: Path) -> dict | None:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None


def parse_price(raw: str) -> tuple[float, float, str] | None:
    """Return (min_price, max_price, unit) or None if unparseable."""
    if not raw:
        return None
    m = PRICE_RE.search(raw)
    if not m:
        return None
    lo = float(m.group(1).replace(",", ""))
    hi = float(m.group(2).replace(",", "")) if m.group(2) else lo
    unit = (m.group(3) or "").strip().rstrip(".") or "unspecified"
    # Normalize common unit variants
    unit_map = {
        "ชม": "ชม.",
        "ชั่วโมง": "ชม.",
        "เดือน": "เดือน",
        "คอร์ส": "คอร์ส",
        "หลักสูตร": "คอร์ส",
        "ภาคการศึกษา": "เทอม",
        "เทอม": "เทอม",
        "สอบ": "สอบ",
        "ปี": "ปี",
    }
    unit = unit_map.get(unit, unit)
    return lo, hi, unit


def summarize(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    xs = sorted(values)
    return {
        "n": len(xs),
        "min": xs[0],
        "p25": statistics.quantiles(xs, n=4)[0] if len(xs) >= 4 else xs[0],
        "median": statistics.median(xs),
        "p75": statistics.quantiles(xs, n=4)[2] if len(xs) >= 4 else xs[-1],
        "max": xs[-1],
        "mean": round(statistics.mean(xs), 2),
    }


def aggregate(listings: list[dict]) -> dict:
    """Group by (unit, dimension) and summarize midpoint prices."""
    # buckets[unit][dim][group_key] = [midpoints]
    buckets: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for L in listings:
        parsed = parse_price(L.get("price_range", ""))
        if not parsed:
            continue
        lo, hi, unit = parsed
        mid = (lo + hi) / 2

        # overall
        buckets[unit]["overall"]["bangkok"].append(mid)

        # by subject
        for s in L.get("subjects") or []:
            buckets[unit]["by_subject"][s].append(mid)

        # by category (grade / exam)
        for c in L.get("categories") or []:
            buckets[unit]["by_category"][c].append(mid)

        # by district (strip "เขต" prefix for cleaner keys)
        d = (L.get("district") or "").strip()
        if d:
            d_clean = d.replace("เขต", "").strip() or d
            buckets[unit]["by_district"][d_clean].append(mid)

        # by listing type
        t = L.get("type")
        if t:
            buckets[unit]["by_type"][t].append(mid)

    # Reduce to stats
    out: dict = {}
    for unit, dims in buckets.items():
        out[unit] = {}
        for dim, groups in dims.items():
            out[unit][dim] = {
                k: summarize(v) for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))
            }
    return out


def add_hourly_equivalents(stats: dict) -> dict:
    """Add a synthetic 'hourly_equivalent' block from /เดือน using HOURS_PER_MONTH."""
    monthly = stats.get("เดือน")
    if not monthly:
        return stats

    hourly: dict = {}
    for dim, groups in monthly.items():
        hourly[dim] = {}
        for key, s in groups.items():
            if s.get("n", 0) == 0:
                continue
            hourly[dim][key] = {
                "n": s["n"],
                "min": round(s["min"] / HOURS_PER_MONTH, 2),
                "p25": round(s["p25"] / HOURS_PER_MONTH, 2),
                "median": round(s["median"] / HOURS_PER_MONTH, 2),
                "p75": round(s["p75"] / HOURS_PER_MONTH, 2),
                "max": round(s["max"] / HOURS_PER_MONTH, 2),
                "mean": round(s["mean"] / HOURS_PER_MONTH, 2),
            }
    stats["hourly_equivalent_from_monthly"] = {
        "assumption": f"{HOURS_PER_MONTH} hours/month (2h × 1 session/wk)",
        "source_unit": "เดือน",
        "data": hourly,
    }
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--city", default="bangkok", help="city slug to filter (default: bangkok)")
    args = ap.parse_args()

    if not LISTINGS_DIR.exists():
        print(f"Listings dir not found: {LISTINGS_DIR}", file=sys.stderr)
        return 1

    all_files = sorted(LISTINGS_DIR.glob("*.md"))
    matched: list[dict] = []
    skipped_no_fm = 0
    skipped_no_price = 0

    for f in all_files:
        fm = load_frontmatter(f)
        if not fm:
            skipped_no_fm += 1
            continue
        if fm.get("city") != args.city:
            continue
        qf = fm.get("quick_facts") or {}
        price = qf.get("price_range")
        if not price:
            skipped_no_price += 1
            continue
        matched.append(
            {
                "slug": f.stem,
                "price_range": price,
                "subjects": fm.get("subjects") or [],
                "categories": fm.get("categories") or [],
                "district": fm.get("district"),
                "type": fm.get("type"),
            }
        )

    if not matched:
        print(f"No listings matched city={args.city}", file=sys.stderr)
        return 1

    stats = aggregate(matched)
    stats = add_hourly_equivalents(stats)

    report = {
        "city": args.city,
        "generated_from": f"{len(all_files)} listing files",
        "matched_city": len(matched),
        "skipped_no_frontmatter": skipped_no_fm,
        "matched_missing_price": skipped_no_price,
        "notes": [
            "Midpoint of (min, max) used per listing before aggregation.",
            "Groups kept separate per unit — do not compare medians across units.",
            "hourly_equivalent_from_monthly assumes 8 hours/month (adjust HOURS_PER_MONTH).",
            "Consumers of this data should cite 'tidfun.org internal dataset, N=X listings, updated <date>'.",
        ],
        "stats": stats,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"  city={args.city} · matched={len(matched)} · units={list(stats.keys())}")
    overall = stats.get("เดือน", {}).get("overall", {}).get(args.city, {})
    if overall:
        print(
            f"  monthly overall: n={overall['n']} · median=฿{overall['median']:,.0f}"
            f" · p25=฿{overall['p25']:,.0f} · p75=฿{overall['p75']:,.0f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
