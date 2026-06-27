#!/usr/bin/env bash
# IndexNow submission — pushes all URLs from sitemap to Bing/Yandex/Seznam IndexNow API
# Run after Bing Webmaster Tools verifies the key file at:
#   https://tidfun.org/de1c54297c5185452acd6c9673d8f281.txt
#
# Usage: bash tools/submit_indexnow.sh
set -euo pipefail

HOST="tidfun.org"
KEY="de1c54297c5185452acd6c9673d8f281"
KEY_LOCATION="https://${HOST}/${KEY}.txt"
SITEMAP="https://${HOST}/sitemap-listings.xml"

echo "Fetching URLs from sitemaps..."
URLS=""
for sm in sitemap-listings.xml sitemap-discovery.xml sitemap-content.xml; do
  URLS+=$(curl -s "https://${HOST}/${sm}" | grep -oE 'https://[^<]+')
  URLS+=$'\n'
done
URLS=$(echo "${URLS}" | sort -u | grep -v "^$")
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
