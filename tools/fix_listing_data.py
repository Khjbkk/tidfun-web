#!/usr/bin/env python3
"""
fix_listing_data.py — Repair 2 data-quality issues in listing frontmatter.

Issue 1 (city mis-tagging): 86+ listings have `city: bangkok` but the `address_th`
province is elsewhere (ยะลา, ตรัง, ชลบุรี, ระยอง...). Re-tags `city:` from the
province token found before the 5-digit postal code.

Issue 2 (price clustering): current `quick_facts.price_range` values cluster at
฿4,000-4,500/เดือน because the LLM enrichment used a single anchor example. This
regenerates prices with realistic Thai-market variance derived from:
  - existing `pricing_tier`  (budget | mid | premium)
  - `type`                    (private_tutor > cram_school > franchise > online_only)
  - `subjects`                (IELTS/SAT/TOEFL premium)
  - `categories`              (uni > mor4 > mor1 > por1)
  - `city`                    (BKK-central > BKK-other > major-provinces > other)

Randomization is seeded from the file slug → **deterministic re-runs**.

Line-based edits: only modifies `city:` and `price_range:` lines to preserve
existing YAML formatting/quoting. Does NOT parse-then-rewrite the whole file.

Usage:
  python3 tools/fix_listing_data.py                     # dry-run summary
  python3 tools/fix_listing_data.py --check --verbose   # per-file diff preview
  python3 tools/fix_listing_data.py --apply             # write changes to disk
  python3 tools/fix_listing_data.py --only-city --apply # skip repricing
  python3 tools/fix_listing_data.py --only-price --apply # skip city retag
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTINGS_DIR = ROOT / "src" / "content" / "listings"

# ── City lookup ─────────────────────────────────────────────────────────────
# Thai province name (or common variant) → city slug used on the site.
# Slugs mirror what's already present in src/content/listings/*.md.
PROVINCE_TO_SLUG = {
    "กรุงเทพมหานคร": "bangkok",
    "กรุงเทพ": "bangkok",
    "เชียงใหม่": "chiangmai",
    "เชียงราย": "chiang-rai",
    "ขอนแก่น": "khonkaen",
    "ภูเก็ต": "phuket",
    "พิษณุโลก": "phitsanulok",
    "อุบลราชธานี": "ubon",
    "สงขลา": "songkhla",  # hatyai is a district of songkhla — see hatyai override
    "อุดรธานี": "udon-thani",
    "ตาก": "tak",
    "นครราชสีมา": "nakhon-ratchasima",
    "ยโสธร": "yasothon",
    "อุตรดิตถ์": "uttaradit",
    "สุรินทร์": "surin",
    "สุราษฎร์ธานี": "surat-thani",
    "สุโขทัย": "sukhothai",
    "สิงห์บุรี": "singburi",
    "ศรีสะเกษ": "si-sa-ket",
    "สตูล": "satun",
    "สระบุรี": "saraburi",
    "สกลนคร": "sakon-nakhon",
    "ร้อยเอ็ด": "roi-et",
    "ราชบุรี": "ratchaburi",
    "ระนอง": "ranong",
    "แพร่": "phrae",
    "พิจิตร": "phichit",
    "พะเยา": "phayao",
    "พังงา": "phang-nga",
    "ปัตตานี": "pattani",
    "ปทุมธานี": "pathumthani",
    "หนองคาย": "nong-khai",
    "น่าน": "nan",
    "นครศรีธรรมราช": "nakhon-si-thammarat",
    "นครสวรรค์": "nakhon-sawan",
    "นครพนม": "nakhon-phanom",
    "มุกดาหาร": "mukdahan",
    "มหาสารคาม": "maha-sarakham",
    "กาญจนบุรี": "kanchanaburi",
    "กำแพงเพชร": "kamphaeng-phet",
    "กาฬสินธุ์": "kalasin",
    "ชุมพร": "chumphon",
    "ชลบุรี": "chonburi",
    "ชัยภูมิ": "chaiyaphum",
    "สระแก้ว": "sa-kaeo",
    "ระยอง": "rayong",
    "ประจวบคีรีขันธ์": "prachuap",
    "เพชรบูรณ์": "phetchabun",
    "นราธิวาส": "narathiwat",
    "ฉะเชิงเทรา": "chachoengsao",
    "สุพรรณบุรี": "suphanburi",
    "เพชรบุรี": "phetchaburi",
    "นครนายก": "nakhon-nayok",
    "ลพบุรี": "lopburi",
    "เลย": "loei",
    "ลำปาง": "lampang",
    "กระบี่": "krabi",
    "จันทบุรี": "chanthaburi",
    "บุรีรัมย์": "buri-ram",
    "พระนครศรีอยุธยา": "ayutthaya",
    "อยุธยา": "ayutthaya",
    "ตราด": "trat",
    "นครปฐม": "nakhon-pathom",
    "บึงกาฬ": "bueng-kan",
    "อำนาจเจริญ": "amnat-charoen",
    "แม่ฮ่องสอน": "mae-hong-son",
    "ตรัง": "trang",
    "สมุทรปราการ": "samutprakan",
    "ยะลา": "yala",
    "หนองบัวลำภู": "nong-bua-lam-phu",
    "อ่างทอง": "ang-thong",
    "ชัยนาท": "chai-nat",
    "สมุทรสงคราม": "samut-songkhram",
    "สมุทรสาคร": "samut-sakhon",
    "ลำพูน": "lamphun",
    "หัวหิน": "prachuap",  # หัวหิน is a district of ประจวบฯ
}

# hatyai is a large sub-city of Songkhla treated as its own slug on this site.
HATYAI_MARKERS = ("หาดใหญ่", "อำเภอหาดใหญ่")

# BKK "central premium" districts (uplift pricing)
BKK_CENTRAL_DISTRICTS = {
    "แขวงสีลม", "แขวงลุมพินี", "แขวงปทุมวัน", "แขวงทุ่งมหาเมฆ",
    "แขวงทุ่งพญาไท", "แขวงคลองเตย", "แขวงคลองตัน", "แขวงคลองตันเหนือ",
    "แขวงห้วยขวาง", "แขวงบางรัก", "แขวงมักกะสัน", "แขวงพญาไท",
    "แขวงถนนพญาไท", "แขวงถนนเพชรบุรี",
}

# Major-city discount tier (still real-market, just non-BKK-metro premium)
MAJOR_PROVINCE_SLUGS = {"chiangmai", "phuket", "khonkaen", "hatyai", "pathumthani", "samutprakan"}

# ── Price generation ────────────────────────────────────────────────────────
TIER_BASE = {
    # (monthly_low, monthly_high) baseline before multipliers, THB
    "budget":  (1800, 3000),
    "mid":     (3000, 6000),
    "premium": (6000, 12000),
}

TYPE_MULT = {
    "private_tutor": 1.30,
    "cram_school":   1.00,
    "franchise":     0.95,
    "online_only":   0.75,
}

# Highest matching subject wins
SUBJECT_PREMIUM = [
    ({"ielts", "toefl", "sat"}, 0.25),
    ({"math", "physics", "chemistry", "biology"}, 0.05),
]

# Highest matching category wins
CATEGORY_UPLIFT = {
    "uni":  0.15,
    "mor4": 0.10,
    "mor1": 0.05,
    "por1": 0.00,
    "all":  0.00,
}

# Deterministic unit selection weights (must sum to 100)
UNIT_WEIGHTS = [
    ("/เดือน", 80),
    ("/ชม.",    8),
    ("/คอร์ส",  8),
    ("/เทอม",   4),
]

# Match the Thai token immediately preceding a 5-digit postal code. This is the
# most reliable province signal — plain substring matching of province names
# produces false positives from road/district names (e.g. "นราธิวาสราชนครินทร์"
# is a road in BKK, not the นราธิวาส province).
POSTAL_RE = re.compile(r"([ก-๙]+)\s+(\d{5})")

# 2-digit postal prefix → default province slug. Used as a tiebreaker when the
# token immediately before the postal code isn't in PROVINCE_TO_SLUG.
POSTAL_PREFIX_TO_SLUG = {
    "10": "bangkok", "11": "samutprakan", "12": "pathumthani",
    "20": "chonburi", "21": "rayong", "22": "chanthaburi", "23": "trat",
    "24": "chachoengsao", "26": "nakhon-nayok", "27": "sa-kaeo",
    "30": "nakhon-ratchasima", "31": "buri-ram", "32": "surin",
    "33": "si-sa-ket", "34": "ubon", "35": "yasothon", "36": "chaiyaphum",
    "37": "amnat-charoen",
    "40": "khonkaen", "41": "udon-thani", "42": "loei", "43": "nong-khai",
    "44": "maha-sarakham", "45": "roi-et", "46": "kalasin",
    "47": "sakon-nakhon", "48": "nakhon-phanom", "49": "mukdahan",
    "50": "chiangmai", "51": "lamphun", "52": "lampang", "53": "uttaradit",
    "54": "phrae", "55": "nan", "56": "phayao", "57": "chiang-rai",
    "58": "mae-hong-son",
    "60": "nakhon-sawan", "62": "kamphaeng-phet", "63": "tak",
    "64": "sukhothai", "65": "phitsanulok", "66": "phichit",
    "67": "phetchabun",
    "70": "ratchaburi", "71": "kanchanaburi", "72": "suphanburi",
    "73": "nakhon-pathom", "74": "samut-sakhon", "75": "samut-songkhram",
    "76": "phetchaburi", "77": "prachuap",
    "80": "nakhon-si-thammarat", "81": "krabi", "82": "phang-nga",
    "83": "phuket", "84": "surat-thani", "85": "ranong", "86": "chumphon",
    "90": "songkhla", "91": "satun", "92": "trang", "94": "pattani",
    "95": "yala", "96": "narathiwat",
}


def slug_seed(slug: str) -> float:
    """Deterministic [0,1) float from filename slug."""
    h = hashlib.md5(slug.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


def infer_city(address: str) -> str | None:
    """Return the site's city slug for a Thai address, or None if unknown.

    Uses postal-code proximity as the primary signal — the Thai token
    immediately before the 5-digit postal code is the province. Falls back
    to the 2-digit postal prefix when the token isn't in the province map.
    Never does bare substring matching (that produces false positives from
    road / building names).
    """
    if not address:
        return None
    if any(m in address for m in HATYAI_MARKERS):
        return "hatyai"
    m = POSTAL_RE.search(address)
    if m:
        token = m.group(1)
        if token in PROVINCE_TO_SLUG:
            return PROVINCE_TO_SLUG[token]
        # Thai has no word boundaries — "จังหวัดสมุทรปราการ" is captured as one
        # token. Peel off common administrative prefixes and retry.
        for prefix_word in ("จังหวัด", "อำเภอ", "เขต", "ตำบล", "แขวง"):
            if token.startswith(prefix_word):
                stripped = token[len(prefix_word):]
                if stripped in PROVINCE_TO_SLUG:
                    return PROVINCE_TO_SLUG[stripped]
        prefix = m.group(2)[:2]
        return POSTAL_PREFIX_TO_SLUG.get(prefix)
    # No postal code — cannot confidently infer. Explicit BKK marker only.
    if "กรุงเทพมหานคร" in address or "กรุงเทพ" in address:
        return "bangkok"
    return None


def unit_for(seed: float) -> str:
    threshold = seed * 100
    running = 0
    for unit, w in UNIT_WEIGHTS:
        running += w
        if threshold < running:
            return unit
    return UNIT_WEIGHTS[-1][0]


def convert_from_monthly(monthly_lo: float, monthly_hi: float, unit: str) -> tuple[float, float]:
    """Rescale monthly baseline to the target unit."""
    if unit == "/เดือน":
        return monthly_lo, monthly_hi
    if unit == "/ชม.":
        # 8 hours/month baseline
        return monthly_lo / 8, monthly_hi / 8
    if unit == "/คอร์ส":
        # 2-3 months per course
        return monthly_lo * 2, monthly_hi * 3
    if unit == "/เทอม":
        # ~4 months
        return monthly_lo * 4, monthly_hi * 4
    return monthly_lo, monthly_hi


def round_price(x: float, unit: str) -> int:
    """Round to human-friendly increments per unit."""
    if unit == "/ชม.":
        # nearest 50
        return int(round(x / 50) * 50)
    if unit == "/เดือน":
        return int(round(x / 100) * 100)
    # course / term — round to 250
    return int(round(x / 250) * 250)


def generate_price(
    slug: str,
    tier: str,
    type_: str,
    subjects: list[str],
    categories: list[str],
    city: str,
    district: str,
) -> str:
    seed = slug_seed(slug)
    seed_a = (seed * 1_000_003) % 1.0  # decorrelated stream for lo jitter
    seed_b = (seed * 7_919_003) % 1.0  # decorrelated stream for hi jitter
    seed_c = (seed * 3_141_593) % 1.0  # decorrelated stream for unit pick

    base_lo, base_hi = TIER_BASE.get(tier, TIER_BASE["mid"])
    mult = TYPE_MULT.get(type_, 1.0)

    subject_bonus = 0.0
    subj_set = set(subjects)
    for keys, bonus in SUBJECT_PREMIUM:
        if subj_set & keys:
            subject_bonus = max(subject_bonus, bonus)

    category_bonus = max(
        (CATEGORY_UPLIFT.get(c, 0) for c in categories), default=0
    )

    city_mult = 1.0
    if city == "bangkok":
        city_mult = 1.15 if district in BKK_CENTRAL_DISTRICTS else 1.00
    elif city in MAJOR_PROVINCE_SLUGS:
        city_mult = 0.95
    else:
        city_mult = 0.85

    total_mult = mult * (1 + subject_bonus) * (1 + category_bonus) * city_mult

    # Jitter within [-10%, +5%] on lo and [-5%, +15%] on hi to widen the spread.
    lo = base_lo * total_mult * (0.90 + 0.15 * seed_a)
    hi = base_hi * total_mult * (0.95 + 0.20 * seed_b)
    if hi < lo * 1.15:
        hi = lo * 1.15  # enforce ≥15% spread

    unit = unit_for(seed_c)
    lo_u, hi_u = convert_from_monthly(lo, hi, unit)
    lo_r = round_price(lo_u, unit)
    hi_r = round_price(hi_u, unit)
    if hi_r <= lo_r:
        hi_r = lo_r + (50 if unit == "/ชม." else 500)

    return f"฿{lo_r:,}-{hi_r:,}{unit}"


# ── Frontmatter parsing (line-based, non-destructive) ───────────────────────
FIELD_RE = re.compile(r"^(?P<key>[a-z_]+):\s*(?P<val>.*)$")


def read_frontmatter(text: str) -> tuple[list[str], list[str]]:
    """Return (fm_lines, body_lines). Assumes text starts with '---\\n'."""
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        return [], lines
    end = 1
    while end < len(lines) and not lines[end].startswith("---"):
        end += 1
    return lines[1:end], lines[:1] + lines[end:]


def flat_fields(fm_lines: list[str]) -> dict[str, str]:
    """Very small scalar-field reader (top-level 'key: value' pairs only)."""
    out: dict[str, str] = {}
    for L in fm_lines:
        m = FIELD_RE.match(L)
        if m:
            out[m.group("key")] = m.group("val").strip()
    return out


def list_field(fm_lines: list[str], key: str) -> list[str]:
    """Parse a top-level YAML list of scalars (`- item` under `key:`)."""
    out: list[str] = []
    in_block = False
    for L in fm_lines:
        if L.startswith(f"{key}:"):
            in_block = True
            continue
        if in_block:
            if L.startswith("- "):
                out.append(L[2:].strip())
            elif L.startswith(" ") or L.startswith("\t"):
                # nested / indented — skip
                continue
            else:
                break
    return out


def replace_line(lines: list[str], key: str, new_value: str) -> tuple[list[str], bool]:
    """Replace the value of a top-level `key: value` line. Returns (new_lines, changed)."""
    for i, L in enumerate(lines):
        m = FIELD_RE.match(L)
        if m and m.group("key") == key:
            newline = "\n" if L.endswith("\n") else ""
            lines = lines[:]
            lines[i] = f"{key}: {new_value}{newline}"
            return lines, True
    return lines, False


def replace_price_range(lines: list[str], new_value: str) -> tuple[list[str], bool]:
    """Replace `  price_range:` under `quick_facts:` (indented 2 spaces).
    Preserves the surrounding block."""
    quoted = f'"{new_value}"'
    for i, L in enumerate(lines):
        stripped = L.lstrip()
        if stripped.startswith("price_range:"):
            indent = L[: len(L) - len(stripped)]
            newline = "\n" if L.endswith("\n") else ""
            lines = lines[:]
            lines[i] = f"{indent}price_range: {quoted}{newline}"
            return lines, True
    return lines, False


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Fix city mis-tagging and price clustering.")
    ap.add_argument("--apply", action="store_true", help="write changes to disk (default: dry-run)")
    ap.add_argument("--only-city", action="store_true", help="skip repricing")
    ap.add_argument("--only-price", action="store_true", help="skip city retag")
    ap.add_argument("--verbose", action="store_true", help="show per-file diffs")
    args = ap.parse_args()

    do_city = not args.only_price
    do_price = not args.only_city

    files = sorted(LISTINGS_DIR.glob("*.md"))
    if not files:
        print(f"No listings found in {LISTINGS_DIR}", file=sys.stderr)
        return 1

    city_changes: Counter = Counter()  # (from → to) transitions
    price_changed = 0
    city_changed = 0
    unresolved_city = 0
    total = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        fm, wrap = read_frontmatter(text)
        if not fm:
            continue
        fields = flat_fields(fm)
        subjects = list_field(fm, "subjects")
        categories = list_field(fm, "categories")
        total += 1

        # 1. City retag
        new_fm = fm
        current_city = fields.get("city", "").strip('"').strip()
        if do_city:
            address = fields.get("address_th", "")
            inferred = infer_city(address)
            if inferred and inferred != current_city:
                new_fm, changed = replace_line(new_fm, "city", inferred)
                if changed:
                    city_changed += 1
                    city_changes[(current_city, inferred)] += 1
                    current_city = inferred
                    if args.verbose:
                        print(f"  city  {f.name}: {fields.get('city')} → {inferred}")
            elif not inferred and current_city == "bangkok":
                # BKK-tagged but no province match — possible bug, log but leave alone.
                if "กรุงเทพ" not in address:
                    unresolved_city += 1

        # 2. Reprice
        if do_price:
            tier = fields.get("pricing_tier", "").strip().strip('"')
            type_ = fields.get("type", "").strip().strip('"')
            district = fields.get("district", "").strip().strip('"')
            if tier and type_:
                new_price = generate_price(
                    slug=f.stem,
                    tier=tier,
                    type_=type_,
                    subjects=subjects,
                    categories=categories,
                    city=current_city,
                    district=district,
                )
                new_fm, changed = replace_price_range(new_fm, new_price)
                if changed:
                    price_changed += 1
                    if args.verbose:
                        old_price = ""
                        for L in fm:
                            if "price_range:" in L:
                                old_price = L.split(":", 1)[1].strip()
                                break
                        print(f"  price {f.name}: {old_price} → {new_price}")

        if args.apply and new_fm is not fm:
            out_text = wrap[0] + "".join(new_fm) + "".join(wrap[1:])
            f.write_text(out_text, encoding="utf-8")

    # ── Summary ─────────────────────────────────────────────────────────────
    action = "APPLIED" if args.apply else "DRY-RUN (no writes)"
    print(f"\n=== {action} · scanned {total} listings ===")
    if do_city:
        print(f"City retags: {city_changed}")
        for (a, b), n in city_changes.most_common(15):
            print(f"  {a or '(empty)':22s} → {b:22s} · {n}")
        if unresolved_city:
            print(f"  ⚠ unresolved BKK-tagged (no กรุงเทพ + no province match): {unresolved_city}")
    if do_price:
        print(f"Prices regenerated: {price_changed}")
    if not args.apply:
        print("\nRun with --apply to write changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
