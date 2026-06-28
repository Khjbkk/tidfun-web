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
  echo "═══ Phase 1: Source (Apify Google Maps) — Top-up to 500+ ═══"
  # 5 small top-up queries to push from 466 → 500+
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Trang, Thailand" --limit 8 --out .tmp/trang.csv
  python3 tools/source_listings.py --query "ติว IELTS" --location "Chiang Mai, Thailand" --limit 8 --out .tmp/cm_ielts.csv
  python3 tools/source_listings.py --query "ติวเตอร์" --location "Pathum Thani, Thailand" --limit 8 --out .tmp/pt_tutor.csv
  python3 tools/source_listings.py --query "ติว ม.4 วิทยาศาสตร์" --location "Bangkok, Thailand" --limit 8 --out .tmp/bkk_sci.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Yala, Thailand" --limit 8 --out .tmp/yala.csv

  echo "═══ Merge CSVs ═══"
  head -1 .tmp/trang.csv > .tmp/gmaps_merged.csv
  for f in .tmp/trang.csv .tmp/cm_ielts.csv .tmp/pt_tutor.csv .tmp/bkk_sci.csv .tmp/yala.csv; do
    tail -n +2 "$f" >> .tmp/gmaps_merged.csv
  done
  echo "  $(wc -l < .tmp/gmaps_merged.csv) rows (incl. header)"
fi

# Legacy long-form scale block — kept for future use but skipped in top-up mode
if false; then
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Chiang Rai, Thailand" --limit 8 --out .tmp/cr.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Lampang, Thailand" --limit 8 --out .tmp/lp.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Buri Ram, Thailand" --limit 8 --out .tmp/br.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Loei, Thailand" --limit 8 --out .tmp/le.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Krabi, Thailand" --limit 8 --out .tmp/kb.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Ayutthaya, Thailand" --limit 8 --out .tmp/ay.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Lopburi, Thailand" --limit 8 --out .tmp/lb.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Nakhon Pathom, Thailand" --limit 8 --out .tmp/np.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Phetchaburi, Thailand" --limit 8 --out .tmp/pb.csv
  python3 tools/source_listings.py --query "สถาบันกวดวิชา" --location "Suphanburi, Thailand" --limit 8 --out .tmp/sup.csv

  # 5 existing-city deepen × 8 = ~40
  python3 tools/source_listings.py --query "ติวเตอร์ ม.4" --location "Chiang Mai, Thailand" --limit 8 --out .tmp/cm_mor4.csv
  python3 tools/source_listings.py --query "ติวเตอร์" --location "Phitsanulok, Thailand" --limit 8 --out .tmp/pl_tutor.csv
  python3 tools/source_listings.py --query "ติวเตอร์" --location "Pattaya, Thailand" --limit 8 --out .tmp/pty_tutor.csv
  python3 tools/source_listings.py --query "ติวเตอร์" --location "Songkhla, Thailand" --limit 8 --out .tmp/sk_tutor.csv
  python3 tools/source_listings.py --query "ติวเตอร์ มหาวิทยาลัย" --location "Chiang Mai, Thailand" --limit 8 --out .tmp/cm_uni.csv

  # 10 subject + specialty niches × 8 = ~80
  python3 tools/source_listings.py --query "ติว GAT PAT" --location "Bangkok, Thailand" --limit 8 --out .tmp/gatpat.csv
  python3 tools/source_listings.py --query "ติวสอบเข้าแพทย์" --location "Bangkok, Thailand" --limit 8 --out .tmp/medic.csv
  python3 tools/source_listings.py --query "ติวพยาบาล" --location "Bangkok, Thailand" --limit 8 --out .tmp/nurse.csv
  python3 tools/source_listings.py --query "ติวภาษาจีน" --location "Bangkok, Thailand" --limit 8 --out .tmp/chinese.csv
  python3 tools/source_listings.py --query "ติวภาษาญี่ปุ่น" --location "Bangkok, Thailand" --limit 8 --out .tmp/japanese.csv
  python3 tools/source_listings.py --query "ติว GED" --location "Bangkok, Thailand" --limit 8 --out .tmp/ged.csv
  python3 tools/source_listings.py --query "ติวเขียนแบบ สถาปัตย์" --location "Bangkok, Thailand" --limit 8 --out .tmp/arch.csv
  python3 tools/source_listings.py --query "ติวสอบเข้านายร้อย" --location "Bangkok, Thailand" --limit 8 --out .tmp/cadet.csv
  python3 tools/source_listings.py --query "ติวอนุบาล" --location "Bangkok, Thailand" --limit 8 --out .tmp/prek.csv
  python3 tools/source_listings.py --query "ติว A-Level" --location "Bangkok, Thailand" --limit 8 --out .tmp/alevel.csv

  echo "═══ Merge CSVs ═══"
  head -1 .tmp/cr.csv > .tmp/gmaps_merged.csv
  for f in .tmp/cr.csv .tmp/lp.csv .tmp/br.csv .tmp/le.csv .tmp/kb.csv .tmp/ay.csv .tmp/lb.csv .tmp/np.csv .tmp/pb.csv .tmp/sup.csv \
           .tmp/cm_mor4.csv .tmp/pl_tutor.csv .tmp/pty_tutor.csv .tmp/sk_tutor.csv .tmp/cm_uni.csv \
           .tmp/gatpat.csv .tmp/medic.csv .tmp/nurse.csv .tmp/chinese.csv .tmp/japanese.csv .tmp/ged.csv .tmp/arch.csv .tmp/cadet.csv .tmp/prek.csv .tmp/alevel.csv; do
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
# Stash any other working-tree changes (e.g. package-lock churn) so the
# rebase doesn't abort with "cannot pull with rebase: unstaged changes"
STASHED=0
if ! git diff-index --quiet HEAD --; then
  git stash push -u -m "pipeline-autostash"
  STASHED=1
fi
git pull --rebase origin main
git push origin main
if [ "$STASHED" = "1" ]; then
  git stash pop || true
fi

echo
echo "✓ Pipeline complete. Cloudflare rebuild in 1-3 min."
