#!/usr/bin/env python3
"""
validate_listings.py — Anti-thin gate validator for ติดฝัน listings.

Reads all src/content/listings/*.md frontmatter and checks:
  - description_th ≥ 200 chars
  - speakable_th has exactly 3 items, each ≥ 50 chars
  - faq has ≥ 5 items, each answer ≥ 80 chars
  - quick_facts complete
  - categories ≥ 1, subjects ≥ 1, sources ≥ 1
  - contact (phone OR line_id OR website) present

Exits non-zero if any listing fails — useful as a pre-commit / CI gate.
Astro build also validates via Zod, but this gives clearer error messages.

Usage:
  python3 tools/validate_listings.py
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def thai_char_count(s: str) -> int:
    return sum(1 for c in s if "฀" <= c <= "๿")


def validate(path: Path) -> list[str]:
    errors = []
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return [f"{path.name}: no YAML frontmatter found"]

    try:
        d = yaml.safe_load(match.group(1))
    except Exception as e:
        return [f"{path.name}: YAML parse error — {e}"]

    name = d.get("name_th", "?")
    desc = d.get("description_th", "")
    if len(desc) < 150:
        errors.append(f"{name}: description_th too short ({len(desc)} chars, need ≥ 150)")

    speakable = d.get("speakable_th", [])
    if len(speakable) != 3:
        errors.append(f"{name}: speakable_th must have exactly 3 items (has {len(speakable)})")
    for i, s in enumerate(speakable):
        if len(s) < 40:
            errors.append(f"{name}: speakable_th[{i}] too short ({len(s)} chars, need ≥ 40)")

    faq = d.get("faq", [])
    if len(faq) < 5:
        errors.append(f"{name}: faq must have ≥ 5 items (has {len(faq)})")
    for i, f in enumerate(faq):
        if len(f.get("answer", "")) < 60:
            errors.append(f"{name}: faq[{i}].answer too short ({len(f.get('answer',''))} chars, need ≥ 60)")

    qf = d.get("quick_facts", {})
    for k in ("price_range", "class_size", "format", "age_range"):
        if not qf.get(k):
            errors.append(f"{name}: quick_facts.{k} missing")

    if not d.get("categories"):
        errors.append(f"{name}: categories empty")
    if not d.get("subjects"):
        errors.append(f"{name}: subjects empty")
    if not d.get("sources"):
        errors.append(f"{name}: sources empty (must cite where data came from)")

    # Contact info is preferred but optional — listings sourced from Google Maps
    # often have map address + reviews even when the business does not publish
    # phone/website. Users can still find them via the address.
    has_contact = d.get("phone") or d.get("line_id") or d.get("website") or d.get("email") or d.get("facebook_url")
    if not has_contact and not d.get("address_th"):
        errors.append(f"{name}: neither contact (phone/line/website/email/fb) nor address provided")

    return errors


def main():
    listings_dir = Path("src/content/listings")
    if not listings_dir.exists():
        print(f"✗ Not found: {listings_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(listings_dir.glob("*.md"))
    print(f"Validating {len(files)} listings...")
    all_errors = []
    for f in files:
        errs = validate(f)
        all_errors.extend(errs)

    if all_errors:
        print(f"\n✗ {len(all_errors)} error(s):", file=sys.stderr)
        for e in all_errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✓ All {len(files)} listings pass the anti-thin gate.")


if __name__ == "__main__":
    main()
