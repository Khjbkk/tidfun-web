#!/usr/bin/env bash
# Mac/Linux: ./start.sh  — starts the bot + a public HTTPS tunnel for the Meta webhook.
set -e
cd "$(dirname "$0")"
command -v node >/dev/null || { echo "ติดตั้ง Node.js 18+ ก่อน: https://nodejs.org"; exit 1; }
[ -f .env ] || { cp .env.example .env; echo "สร้าง .env แล้ว — เปิดไฟล์ .env ใส่ค่าให้ครบ แล้วรัน ./start.sh อีกครั้ง"; exit 0; }
PP=$(grep -E '^PROMPTPAY_QR_ID=' .env | cut -d= -f2 | cut -d'#' -f1 | tr -cd '0-9')
if [ -n "$PP" ] && [ ! -f public/qr/129.png ]; then
  python3 -m pip install -q qrcode pillow && python3 scripts/make_qr.py "$PP"
fi
node local/server.mjs &
BOT=$!
trap 'kill $BOT' EXIT
echo "กำลังเปิด tunnel… มองหาบรรทัด https://xxxx.trycloudflare.com แล้วนำไปใส่ PUBLIC_URL ใน .env และ Callback URL ใน Meta"
npx --yes cloudflared tunnel --url http://localhost:${PORT:-8787}
