#!/usr/bin/env bash
# IndexNow submission — pushes all URLs from sitemap to Bing/Yandex/Seznam IndexNow API
# Run after Bing Webmaster Tools verifies the key file at:
#   https://xn--l3cbnp4hpa.com/b1324706905a1c9a05eaa36d03773959.txt
#
# Usage: bash tools/submit_indexnow.sh
set -euo pipefail

HOST="xn--l3cbnp4hpa.com"
KEY="b1324706905a1c9a05eaa36d03773959"
KEY_LOCATION="https://${HOST}/${KEY}.txt"
SITEMAP="https://${HOST}/sitemap-0.xml"

echo "Fetching URLs from ${SITEMAP}..."
URLS=$(curl -s "${SITEMAP}" | grep -oE 'https://[^<]+' | sort -u)
URL_COUNT=$(echo "${URLS}" | wc -l | tr -d ' ')
echo "Found ${URL_COUNT} URLs"

URL_JSON=$(echo "${URLS}" | python3 -c 'import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')

PAYLOAD=$(python3 -c "
import json
print(json.dumps({
    'host': '${HOST}',
    'key': '${KEY}',
    'keyLocation': '${KEY_LOCATION}',
    'urlList': ${URL_JSON}
}))
")

echo "Submitting to api.indexnow.org..."
curl -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "${PAYLOAD}" \
  -w "\nHTTP %{http_code}\n"
echo "Done. Expected codes: 200 OK | 202 Accepted | 400 Bad Request | 403 Forbidden (key not verified yet) | 422 Unprocessable | 429 Too Many."
