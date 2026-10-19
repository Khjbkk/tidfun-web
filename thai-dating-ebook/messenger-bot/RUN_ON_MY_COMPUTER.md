# รัน bot บนเครื่องตัวเอง (ไม่ใช้ Cloudflare Workers)

## แบบให้ Claude Code บนเครื่องทำให้ (ง่ายสุด)
1. แตก `messenger-bot.zip` ไว้ในโฟลเดอร์ เช่น `~/chatfarang-bot`
2. เปิด Terminal ที่โฟลเดอร์นั้น พิมพ์ `claude` (Claude Code บนเครื่อง)
3. วางข้อความด้านล่างทั้งก้อน:

```
ในโฟลเดอร์นี้คือ Messenger bot (Node.js) ของเพจ "คุยกับฝรั่งเป็น" อ่าน README.md และ RUN_ON_MY_COMPUTER.md แล้วช่วยผมรันบนเครื่องนี้ให้ครบ:
1) เช็ก Node 18+ และ Python 3 ถ้าไม่มีให้บอกวิธีติดตั้ง
2) รัน npm test ต้องผ่านทั้งหมด
3) สร้าง .env จาก .env.example แล้วถามผมทีละค่า: PAGE_ACCESS_TOKEN, APP_ID, APP_SECRET (VERIFY_TOKEN ให้สุ่มให้เอง) ห้ามพิมพ์ค่า token กลับมาในแชท — บัญชีรับเงินตั้งไว้แล้ว: ไทยพาณิชย์ 264-296793-7 บริษัท ซิโอร่า จำกัด
4) ถามผมว่ามีพร้อมเพย์ของบริษัท (เลขผู้เสียภาษี 13 หลัก) ไหม ถ้ามี ใส่ PROMPTPAY_QR_ID แล้วรัน python3 scripts/make_qr.py <เลข 13 หลัก> ตั้ง QR_ENABLED=true แล้วเปิด public/qr/129.png ให้ผมสแกนเช็ก ถ้าไม่มี ข้ามได้ (บอทจะแจ้งเลขบัญชีให้โอนแทน)
5) รัน npm start แล้วเปิด tunnel ด้วย npm run tunnel เอา URL https ที่ได้ไปใส่ PUBLIC_URL ใน .env แล้วรีสตาร์ท bot
6) บอกผมว่าต้องไปใส่ Callback URL / Verify token / fields อะไรในหน้า Meta Messenger webhook และรัน npm run profile ให้
7) ทดสอบ: ให้ผมทักเพจจากบัญชีแอดมิน แล้วดู log ว่าบอทตอบ
```

## แบบทำเอง
```bash
cd chatfarang-bot
npm test                     # ต้องขึ้น pass 11
cp .env.example .env         # แล้วเปิดแก้ใส่ค่า
# (ไม่บังคับ) QR: ใช้ได้เฉพาะพร้อมเพย์ — เลขผู้เสียภาษีบริษัท 13 หลัก หรือเบอร์มือถือ ไม่ใช่เลขบัญชีธนาคาร
# python3 -m pip install qrcode pillow && python3 scripts/make_qr.py <เลข13หลัก>  แล้วตั้ง QR_ENABLED=true
./start.sh                   # Mac/Linux  (Windows: ดับเบิลคลิก start.bat)
```
`start.sh` จะเปิด bot ที่ `http://localhost:8787` และเปิด tunnel ให้ได้ URL `https://xxxx.trycloudflare.com`
1. เอา URL นั้นใส่ `PUBLIC_URL=` ใน `.env` แล้วรัน `./start.sh` ใหม่
2. Meta → Messenger API Settings → Webhooks → Callback URL = `https://xxxx.trycloudflare.com/webhook`, Verify token = ค่า `VERIFY_TOKEN` ใน `.env`
3. Subscribe fields: `messages`, `messaging_postbacks`, `messaging_referrals`, `message_echoes`, `feed`
4. `PAGE_ACCESS_TOKEN=... npm run profile` (ตั้งปุ่ม Get Started / เมนู)

## ข้อควรรู้เมื่อรันบนเครื่อง
- **เครื่องต้องเปิดและต่อเน็ตตลอด** ถ้าปิดเครื่อง/หลับ บอทหยุดตอบ (Meta จะส่งซ้ำได้ไม่กี่ครั้งแล้วทิ้ง) — ตั้งเครื่องไม่ให้ sleep
- **URL ของ quick tunnel เปลี่ยนทุกครั้งที่รันใหม่** → ต้องไปแก้ Callback URL ใน Meta และ `PUBLIC_URL` ทุกครั้ง ถ้าจะใช้ยาว ให้สร้าง *named tunnel* ของ Cloudflare (ฟรี ต้องมีโดเมน) หรือย้ายไป Cloudflare Workers ตาม README
- ข้อมูลลูกค้าเก็บใน `data/state.json` — สำรองไฟล์นี้ไว้ อย่าแชร์
- App Review (`pages_messaging`) ยังจำเป็นเหมือนเดิม ก่อนผ่านบอทตอบได้แค่แอดมิน/tester
