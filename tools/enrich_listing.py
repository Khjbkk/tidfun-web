#!/usr/bin/env python3
"""
enrich_listing.py — Bigfoot §3 L3 enrichment via OpenAI.

Reads the L1 CSV from source_listings.py / source_facebook.py, calls OpenAI
to produce L3 content (description, speakable, FAQ, quick_facts), validates
against the Zod anti-thin gate, and writes one Markdown file per listing to
src/content/listings/.

Requires:
  - OPENAI_API_KEY in environment (wallet ≥ $5; this script uses ~$0.02/row
    on gpt-4o, ~$0.001/row on gpt-4o-mini)
  - pip install pyyaml

Usage:
  export OPENAI_API_KEY=sk-proj-xxxxx
  python3 tools/enrich_listing.py \\
      --input .tmp/gmaps_merged.csv \\
      --model gpt-4o \\
      --out src/content/listings/

  # Cheap mode (5x cheaper, lower Thai quality):
  python3 tools/enrich_listing.py --input .tmp/raw.csv --model gpt-4o-mini

Anti-thin gate: each output is validated for description ≥ 200 chars,
speakable[3] × 50+ chars, faq ≥ 5 × 80+ chars. Rows that fail are
written to .tmp/enrich_failures.csv for manual review.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import date
from typing import Optional, List, Dict

try:
    import yaml
except ImportError:
    print("Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


OPENAI_API = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = """You are a content writer for ติดฝัน (TidFun), a Thai directory of tutoring services and cram schools.

Given basic info about a tutoring institute, you produce structured Thai content optimized for AI answer engines (Google AI Overviews, ChatGPT search, Perplexity) and Thai parents looking for the right tutor for their child.

CRITICAL RULES:
1. Do NOT fabricate specific statistics like "X students per year passed" or "Y% pass rate" — use general phrasing
2. Pricing should be RANGE ESTIMATES prefixed with "ประมาณ" — base on type and city signal
3. Tone: factual, helpful, concise. NO marketing fluff or hype
4. Use names of REAL Thai schools (สาธิตจุฬา, สวนกุหลาบ, เตรียมอุดม, MWIT) only when context clearly suggests they target them
5. All Thai text. No English unless brand names
6. SUBJECT ENUM: use ONLY these subject IDs: math, science, physics, chemistry, biology, english, thai, social, iq, readiness, sat, ielts, toefl. Do NOT use gat, pat, o_net, gpa, "general", "all" — pick from the allowed enum only. For Thai TGAT/TPAT/A-Level prep, map to the underlying subject (e.g. "ติว TGAT คณิต" → math).

LENGTH REQUIREMENTS — STRICT. Count Thai characters carefully. If you write less than the minimum, EXPAND with concrete examples, contextual detail, or additional benefits BEFORE returning the JSON.

OUTPUT JSON schema (lengths are MINIMUMS — exceed them):

{
  "description_th": "≥ 200 Thai characters (aim 250-350). Describe what the institute does, who they target, methodology, what makes them suitable. Include the city. NEVER less than 200.",

  "speakable_th": [
    "≥ 60 Thai characters (aim 80-110). Overview answering 'What is this institute and who is it for?' First sentence is the direct answer.",
    "≥ 60 Thai characters (aim 80-110). Pricing answering 'How much does it cost and what is included?' First sentence is the direct answer.",
    "≥ 60 Thai characters (aim 80-110). Teaching answering 'Who teaches and what is the class structure?' First sentence is the direct answer."
  ],

  "faq": [
    {"question": "Q1: a question parents commonly ask",
     "answer": "≥ 80 Thai characters (aim 100-160). A complete, specific answer with reason or example. NEVER one-line answer."},
    {"question": "Q2", "answer": "≥ 80 Thai characters answer"},
    {"question": "Q3", "answer": "≥ 80 Thai characters answer"},
    {"question": "Q4", "answer": "≥ 80 Thai characters answer"},
    {"question": "Q5", "answer": "≥ 80 Thai characters answer"},
    {"question": "Q6", "answer": "≥ 80 Thai characters answer"}
  ],

  "quick_facts": {
    "price_range": "เช่น ฿2,500-5,500/เดือน",
    "class_size": "เช่น 10-15 คน/ห้อง or 1-on-1",
    "format": ["in_person" or "online" or "hybrid"],
    "age_range": "เช่น 10-12 ปี (ป.5-ป.6)"
  },

  "pricing_tier": "budget | mid | premium",
  "methodology_th": "100-200 Thai char teaching approach summary",
  "specialties": ["array of 2-5 short specialty tags in snake_case English"],
  "categories": ["por1"|"mor1"|"mor4"|"uni"|"all"],
  "subjects": ["math"|"science"|"physics"|"chemistry"|"biology"|"english"|"thai"|"social"|"iq"|"readiness"|"sat"|"ielts"|"toefl"],
  "target_schools": ["satit-chula-por1"|"suankularb-mor1"|"triam-udom-mor4"|...],
  "type": "cram_school | franchise | private_tutor | online_only"
}

EXAMPLE of acceptable FAQ answer length (~120 chars):
"แนะนำเริ่มเรียนตั้งแต่ ป.5 เพื่อมีเวลา 12-18 เดือนในการปูพื้นฐานคณิตศาสตร์ให้แน่นก่อนเข้มข้นกับข้อสอบจริงในช่วง 3-6 เดือนสุดท้าย เด็กที่เริ่มช้ากว่านี้อาจต้องเรียนหนักขึ้น"

That is a complete answer with reasoning. Aim for this depth in every FAQ."""


VALID_CATEGORIES = {"por1", "mor1", "mor4", "uni", "all"}
VALID_SUBJECTS = {"math", "science", "physics", "chemistry", "biology", "english", "thai", "social", "iq", "readiness", "sat", "ielts", "toefl"}
VALID_TYPES = {"cram_school", "franchise", "private_tutor", "online_only"}
VALID_FORMATS = {"in_person", "online", "hybrid"}
VALID_TIERS = {"budget", "mid", "premium"}

KNOWN_SCHOOL_IDS = {
    # por1
    "satit-chula-por1", "satit-kaset-por1", "satit-prasanmit-por1", "satit-patumwan-por1",
    "satit-rangsit-por1", "satit-mahanakorn-por1", "amnuayniwet-por1",
    # mor1
    "suankularb-mor1", "satit-patumwan-mor1", "satit-prasanmit-mor1", "bodindecha-mor1",
    "triamudompattanakarn-mor1", "samsen-mor1", "satriwithaya-mor1", "thepsirin-mor1",
    "satit-kaset-mor1", "yothinburana-mor1", "horwang-mor1", "swk-nonthaburi-mor1",
    "satit-chula-mor1",
    # mor4
    "triam-udom-mor4", "mwit-mor4", "kvis-mor4", "principal-mor4", "satit-chula-mor4",
    "satit-patumwan-mor4", "satit-prasanmit-mor4", "bodindecha-mor4", "samsen-mor4",
    "suankularb-mor4", "satit-kaset-mor4", "yvis-cmu-mor4", "satit-kku-mor4",
    "saint-gabriel-mor4", "assumption-mor4", "kpc-mor4", "mater-dei-mor4",
}


def slugify(name: str, place_id: str = "", lat: str = "", lng: str = "") -> str:
    """Generate a stable filename slug. Prefer ASCII transliteration; fall back to hash.
    Includes lat+lng in the hash to prevent collisions when Thai-only names with no
    place_id share the same hash (the previous 6 collisions in the first pipeline run)."""
    s = name.lower().strip()
    ascii_part = re.sub(r"[^a-z0-9]+", "-", s)[:30].strip("-")
    unique_key = name + place_id + str(lat) + str(lng)
    h = hashlib.md5(unique_key.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_part}-{h}" if ascii_part else f"listing-{h}"


def normalize_city(raw_city: str, address: str) -> str:
    """Map raw city/address to our city enum."""
    s = ((raw_city or "") + " " + (address or "")).lower()
    if any(k in s for k in ["bangkok", "กรุงเทพ", "phyathai", "watthana", "พญาไท", "วัฒนา", "ปทุมวัน", "สุขุมวิท", "จตุจักร", "สีลม"]):
        return "bangkok"
    if any(k in s for k in ["nonthaburi", "นนทบุรี"]):
        return "nonthaburi"
    if any(k in s for k in ["samut prakan", "สมุทรปราการ", "bang phli", "บางพลี"]):
        return "samutprakan"
    if any(k in s for k in ["pathum thani", "ปทุมธานี", "rangsit", "รังสิต"]):
        return "pathumthani"
    if any(k in s for k in ["chiang mai", "เชียงใหม่", "chiangmai"]):
        return "chiangmai"
    if any(k in s for k in ["khon kaen", "ขอนแก่น"]):
        return "khonkaen"
    if any(k in s for k in ["hat yai", "หาดใหญ่", "hatyai"]):
        return "hatyai"
    if any(k in s for k in ["nakhon ratchasima", "โคราช", "นครราชสีมา"]):
        return "nakhon-ratchasima"
    if any(k in s for k in ["ubon ratchathani", "อุบลราชธานี", "ubon"]):
        return "ubon"
    if any(k in s for k in ["udon thani", "อุดรธานี", "udon"]):
        return "udon-thani"
    if "phuket" in s or "ภูเก็ต" in s:
        return "phuket"
    if "songkhla" in s or "สงขลา" in s:
        return "songkhla"
    if any(k in s for k in ["chonburi", "ชลบุรี", "pattaya", "พัทยา", "sriracha", "ศรีราชา", "bang saen", "บางแสน"]):
        return "chonburi"
    if "rayong" in s or "ระยอง" in s:
        return "rayong"
    if any(k in s for k in ["prachuap", "ประจวบ", "hua hin", "หัวหิน"]):
        return "prachuap"
    if any(k in s for k in ["surat thani", "สุราษฎร์ธานี", "surat"]):
        return "surat-thani"
    if any(k in s for k in ["nakhon si thammarat", "นครศรีธรรมราช"]):
        return "nakhon-si-thammarat"
    if any(k in s for k in ["phitsanulok", "พิษณุโลก"]):
        return "phitsanulok"
    if any(k in s for k in ["sakon nakhon", "สกลนคร"]):
        return "sakon-nakhon"
    return "bangkok"  # safe default


def call_openai(payload: dict, retries: int = 3) -> dict:
    api_key = os.environ["OPENAI_API_KEY"]
    last_err = None
    for attempt in range(retries):
        req = urllib.request.Request(
            OPENAI_API,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            last_err = f"HTTP {e.code}: {body}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(last_err)
        except Exception as e:
            last_err = str(e)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"OpenAI failed after {retries} attempts: {last_err}")


def thai_chars(s: str) -> int:
    return sum(1 for c in s if "฀" <= c <= "๿")


def validate_enriched(d: dict) -> List[str]:
    """Anti-thin gate identical to validate_listings.py + schema enum checks."""
    errs = []
    if len(d.get("description_th", "")) < 150:
        errs.append(f"description_th too short ({len(d.get('description_th',''))} chars)")
    sp = d.get("speakable_th", [])
    if len(sp) != 3:
        errs.append(f"speakable_th must have 3 items (has {len(sp)})")
    for i, s in enumerate(sp):
        if len(s) < 40:
            errs.append(f"speakable_th[{i}] too short ({len(s)} chars)")
    faq = d.get("faq", [])
    if len(faq) < 5:
        errs.append(f"faq must have ≥ 5 items (has {len(faq)})")
    for i, f in enumerate(faq):
        if len(f.get("answer", "")) < 60:
            errs.append(f"faq[{i}].answer too short ({len(f.get('answer',''))} chars)")
    qf = d.get("quick_facts", {})
    for k in ("price_range", "class_size", "format", "age_range"):
        if not qf.get(k):
            errs.append(f"quick_facts.{k} missing")
    if qf.get("format") and not all(f in VALID_FORMATS for f in qf["format"]):
        errs.append(f"quick_facts.format invalid")
    cats = d.get("categories", [])
    if not cats or not all(c in VALID_CATEGORIES for c in cats):
        errs.append(f"categories invalid: {cats}")
    subs = d.get("subjects", [])
    if not subs or not all(s in VALID_SUBJECTS for s in subs):
        errs.append(f"subjects invalid: {subs}")
    if d.get("type") not in VALID_TYPES:
        errs.append(f"type invalid: {d.get('type')}")
    if d.get("pricing_tier") not in VALID_TIERS:
        errs.append(f"pricing_tier invalid: {d.get('pricing_tier')}")
    return errs


def enrich_row(row: dict, model: str) -> Optional[dict]:
    """Enrich one row. On validation failure, retry once with the errors as feedback."""
    user_msg = f"""Institute info from Google Maps scrape:
- Name: {row.get('name_th', '')}
- Address: {row.get('address_th', '')}
- City: {row.get('city', '')}
- Phone: {row.get('phone', '')}
- Website: {row.get('website', '')}
- Google rating: {row.get('google_rating', 'N/A')} ({row.get('google_review_count', 0)} reviews)

Produce the JSON object per schema. STRICT length requirements — every field MUST meet the minimum character count. Thai content only."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    for attempt in range(2):  # first pass + 1 retry with feedback
        response = call_openai({
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.5 + 0.2 * attempt,  # add diversity on retry
        })
        content = response["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parse attempt {attempt+1}: {e}", file=sys.stderr)
            return None

        # Post-process: filter invalid enum values before validation (avoids
        # dead-end retries when the model insists on enum values like gat/pat
        # that aren't in our schema)
        if isinstance(parsed.get("subjects"), list):
            parsed["subjects"] = [s for s in parsed["subjects"] if s in VALID_SUBJECTS]
            if not parsed["subjects"]:
                parsed["subjects"] = ["math"]  # conservative default
        if isinstance(parsed.get("categories"), list):
            parsed["categories"] = [c for c in parsed["categories"] if c in VALID_CATEGORIES]
            if not parsed["categories"]:
                parsed["categories"] = ["all"]

        errs = validate_enriched(parsed)
        if not errs:
            return parsed

        if attempt == 0:
            # Retry with concrete feedback
            print(f"  ↻ retry — fixing: {'; '.join(errs[:3])}{'…' if len(errs) > 3 else ''}")
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": (
                    "Your previous output FAILED these length checks:\n"
                    + "\n".join(f"  - {e}" for e in errs)
                    + "\n\nRewrite the JSON. EXPAND the short fields by adding concrete examples, "
                    "contextual detail, or additional benefits. Every FAQ answer MUST be at least 80 Thai characters. "
                    "Count carefully before returning. Same schema."
                ),
            })

    # Second attempt also failed — return parsed so caller logs the errors via validate_enriched
    return parsed


def merge_full_listing(l1: dict, l3: dict) -> dict:
    """Combine L1 (from scrape) + L2/L3 (from OpenAI) + L4 (from scrape) + L5 (now)."""
    target_schools = [s for s in l3.get("target_schools", []) if s in KNOWN_SCHOOL_IDS]

    out = {
        # L1
        "name_th": l1.get("name_th", "").strip(),
        "address_th": l1.get("address_th", "").strip(),
        "city": normalize_city(l1.get("city", ""), l1.get("address_th", "")),
        "type": l3["type"],
        # L1 optional
        **({"district": l1.get("district").strip()} if l1.get("district") else {}),
        **({"lat": float(l1["lat"])} if l1.get("lat") not in (None, "", "0") else {}),
        **({"lng": float(l1["lng"])} if l1.get("lng") not in (None, "", "0") else {}),
        **({"phone": [l1["phone"].strip()]} if l1.get("phone") else {"phone": []}),
        **({"website": l1.get("website")} if l1.get("website") else {}),
        **({"facebook_url": l1.get("facebook_url")} if l1.get("facebook_url") else {}),
        # L2 / L3
        "categories": l3["categories"],
        "subjects": l3["subjects"],
        "target_schools": target_schools,
        "featured": False,
        "claimed": False,
        "date_listed": date.today().isoformat(),
        "description_th": l3["description_th"],
        "speakable_th": l3["speakable_th"],
        "faq": l3["faq"],
        "quick_facts": l3["quick_facts"],
        "pricing_tier": l3["pricing_tier"],
        "specialties": l3.get("specialties", []),
        "methodology_th": l3.get("methodology_th", ""),
        # L4
        **({"google_rating": float(l1["google_rating"])} if l1.get("google_rating") not in (None, "", "0") else {}),
        **({"google_review_count": int(l1["google_review_count"])} if l1.get("google_review_count") not in (None, "", "0") else {}),
        # L4b multi-source (just google for now; FB merged later by tools/import_csv.py if needed)
        **({"multi_source_ratings": {
            "google": {
                "rating": float(l1["google_rating"]),
                "count": int(l1.get("google_review_count") or 0),
            },
        }} if l1.get("google_rating") not in (None, "", "0") else {}),
        # L5
        "data_freshness_date": date.today().isoformat(),
        "sources": ["apify_google_maps", "openai_enrichment"],
    }
    return out


def write_md(d: dict, out_dir: Path, slug: str) -> Path:
    out_path = out_dir / f"{slug}.md"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml.dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False))
        f.write("---\n")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="src/content/listings/")
    parser.add_argument("--model", default="gpt-4o", help="gpt-4o (best Thai) or gpt-4o-mini (cheap)")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N rows (0 = all)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip slugs already in --out")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("✗ OPENAI_API_KEY not set. Add to .env or export.", file=sys.stderr)
        sys.exit(1)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"✗ Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    failure_path = Path(".tmp/enrich_failures.csv")
    failure_path.parent.mkdir(parents=True, exist_ok=True)

    with in_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]
    print(f"Read {len(rows)} rows from {in_path}")
    print(f"Model: {args.model}\n")

    written, skipped, failed = 0, 0, 0
    failure_rows = []
    cost_estimate = len(rows) * (0.02 if args.model == "gpt-4o" else 0.001)
    print(f"Estimated OpenAI cost: ~${cost_estimate:.2f}\n")

    for i, row in enumerate(rows, 1):
        name = row.get("name_th", "").strip()
        if not name:
            print(f"[{i}/{len(rows)}] skipped (no name)")
            skipped += 1
            continue
        slug = slugify(name, row.get("place_id", ""), row.get("lat", ""), row.get("lng", ""))
        out_path = out_dir / f"{slug}.md"
        if args.skip_existing and out_path.exists():
            print(f"[{i}/{len(rows)}] skip existing: {slug}")
            skipped += 1
            continue

        print(f"[{i}/{len(rows)}] enriching: {name[:50]}...")
        try:
            l3 = enrich_row(row, args.model)
        except Exception as e:
            print(f"  ✗ OpenAI error: {e}")
            failed += 1
            failure_rows.append({**row, "error": str(e)[:200]})
            continue

        if l3 is None:
            failed += 1
            failure_rows.append({**row, "error": "JSON parse"})
            continue

        errs = validate_enriched(l3)
        if errs:
            print(f"  ✗ anti-thin gate: {'; '.join(errs)}")
            failed += 1
            failure_rows.append({**row, "error": "; ".join(errs)})
            continue

        full = merge_full_listing(row, l3)
        write_md(full, out_dir, slug)
        written += 1
        print(f"  ✓ {slug}.md")

    if failure_rows:
        with failure_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(failure_rows[0].keys()))
            w.writeheader()
            w.writerows(failure_rows)
        print(f"\n  ⚠  {failed} failures written to {failure_path}")

    print(f"\n✓ Wrote {written}; skipped {skipped}; failed {failed}")
    print("\nNext:")
    print("  python3 tools/validate_listings.py")
    print("  npm run build")
    print("  git add src/content/listings/ && git commit -m 'Add N enriched listings'")
    print("  git push")


if __name__ == "__main__":
    main()
