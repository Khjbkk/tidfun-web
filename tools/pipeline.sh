#!/usr/bin/env bash
# pipeline.sh — Bigfoot §3 STEP 3-6 full automated pipeline.
#
# Source (Apify) → Enrich (OpenAI) → Validate → Build → Commit → Push
#
# Requires .env with APIFY_TOKEN + OPENAI_API_KEY.
#
# Usage:
#   bash tools/pipeline.sh               # default: BKK + 3 cities, ~$5 + ~$1.50
#   bash tools/pipeline.sh --skip-source # if you already have .tmp/gmaps_merged.csv
#   bash tools/pipeline.sh --dry-run     # build + validate without committing
set -euo pipefail

cd "$(dirname "$0")/.."

# Load .env
if [ -f .env ]; then
  set -a; source .env; set +a
fi
: "${APIFY_TOKEN:?APIFY_TOKEN not set — add to .env}"
: "${OPENAI_API_KEY:?OPENAI_API_KEY not set — add to .env}"

# Auto-bootstrap project venv with pyyaml (works around PEP 668 externally-managed environment)
if [ ! -d .venv ]; then
  echo "═══ First run: creating .venv with pyyaml ═══"
  python3 -m venv .venv
  .venv/bin/pip install --quiet pyyaml
fi
# Prepend venv to PATH so 'python3' in this script + children resolves to .venv/bin/python3
export PATH=".venv/bin:${PATH}"
echo "Using Python: $(which python3) ($(python3 --version 2>&1))"

SKIP_SOURCE=0
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --skip-source) SKIP_SOURCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
  esac
done

mkdir -p .tmp

if [ "$SKIP_SOURCE" = "0" ]; then
  echo "═══ Phase 1: Source (Apify Google Maps) ═══"
  # Phase 1 expansion — 6 new regional cities + 2 BKK keyword variants
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Nakhon Ratchasima, Thailand" --limit 8 --out .tmp/korat.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Ubon Ratchathani, Thailand" --limit 8 --out .tmp/ubon.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Udon Thani, Thailand" --limit 8 --out .tmp/udon.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Phuket, Thailand" --limit 8 --out .tmp/phuket.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Songkhla, Thailand" --limit 8 --out .tmp/songkhla.csv
  python3 tools/source_listings.py --query "ติวเตอร์ ม.4" --location "Bangkok, Thailand" --limit 10 --out .tmp/bkk_mor4.csv
  python3 tools/source_listings.py --query "ติวเตอร์ มหาวิทยาลัย" --location "Bangkok, Thailand" --limit 10 --out .tmp/bkk_uni.csv

  echo "═══ Merge CSVs ═══"
  head -1 .tmp/korat.csv > .tmp/gmaps_merged.csv
  for f in .tmp/korat.csv .tmp/ubon.csv .tmp/udon.csv .tmp/phuket.csv .tmp/songkhla.csv .tmp/bkk_mor4.csv .tmp/bkk_uni.csv; do
    tail -n +2 "$f" >> .tmp/gmaps_merged.csv
  done
  echo "  $(wc -l < .tmp/gmaps_merged.csv) rows (incl. header)"
fi

echo
echo "═══ Phase 2: Enrich (OpenAI gpt-4o) ═══"
python3 tools/enrich_listing.py \
  --input .tmp/gmaps_merged.csv \
  --model gpt-4o \
  --skip-existing \
  --out src/content/listings/

echo
echo "═══ Phase 3: Validate (anti-thin gate) ═══"
python3 tools/validate_listings.py

echo
echo "═══ Phase 4: Build ═══"
PATH=/usr/local/bin:$PATH npx astro build 2>&1 | tail -5

if [ "$DRY_RUN" = "1" ]; then
  echo
  echo "═══ Dry run complete — not committing ═══"
  echo "Review src/content/listings/ then re-run without --dry-run"
  exit 0
fi

NEW_COUNT=$(git status --porcelain src/content/listings/ | grep -c "^??")
if [ "$NEW_COUNT" = "0" ]; then
  echo "No new listings to commit."
  exit 0
fi

echo
echo "═══ Phase 5: Commit + Push ═══"
git add src/content/listings/
git commit -m "Add ${NEW_COUNT} enriched listings (Apify → OpenAI pipeline)

Sourced from Google Maps via Apify, enriched to L3 via OpenAI gpt-4o
per Bigfoot §3 STEP 3-5. All listings pass the Zod anti-thin gate.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
"
git pull --rebase origin main
git push origin main

echo
echo "✓ Pipeline complete. Cloudflare rebuild in 1-3 min."
