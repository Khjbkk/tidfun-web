# Messenger Bot — คุยกับฝรั่งเป็น (Cloudflare Worker)

บอทขาย ebook "แฟนฝรั่ง ไม่ต้องรอดวง" ใน Messenger ของเพจ **คุยกับฝรั่งเป็น** (Page ID `1339142735957300`)

```
ลูกค้าทัก (แอด / m.me / คอมเมนต์ "ประโยค")
  → ต้อนรับ + ปุ่ม [ในเล่มมีอะไร] [ซื้อเลย 129฿] [ถามก่อน]
  → เสนอ Chat Cards +49฿  → QR PromptPay ตามยอด (129 / 178)
  → ลูกค้าส่งรูปสลิป → บอทตอบ "กำลังตรวจ"
  → แอดมินพิมพ์ #ok ในแชทนั้น (Business Suite Inbox)
  → บอทส่งปุ่มดาวน์โหลดเล่ม (+การ์ด) + ส่ง Purchase กลับ Meta (ให้แอดหาคนซื้อ)
  → 23 ชม. ต่อมา: ขอรีวิว + เสนอรีวิวโปรไฟล์ 1:1 490฿
ยังไม่โอน → ตามอัตโนมัติ 1 ชม. / 3 ชม. / 22 ชม. (ภายในกรอบ 24 ชม. ของ Messenger)
```

## คำสั่งแอดมิน (พิมพ์ในแชทลูกค้าผ่าน Meta Business Suite)
| พิมพ์ | ผล |
|---|---|
| `#ok` | สลิปถูกต้อง → บอทส่งไฟล์ + ยิง Purchase event (ใช้กับ upsell 490 ด้วย) |
| `#no` | สลิปไม่ผ่าน → บอทขอสลิปใหม่ |
| `#99` | ให้ราคาพิเศษ 99฿ กับลูกค้าคนนี้ |
| `#bot` | ให้บอทกลับมาตอบต่อทันที |
| พิมพ์ข้อความอื่นเอง | บอทเงียบให้ 30 นาทีในแชทนั้น (แอดมินคุยเอง) |

ลูกค้าพิมพ์ "แอดมิน / คืนเงิน / โดนหลอก / ร้องเรียน" → บอทหยุด 12 ชม. ให้คนตอบ
ลูกค้าพิมพ์โค้ด affiliate (ตั้งใน `AFFILIATE_CODES`) → ลด 10฿ + บันทึกว่ามาจากใคร
ลิงก์ `m.me/1339142735957300?ref=MAY` → บันทึก ref = MAY ให้อัตโนมัติ

---

## ติดตั้ง (ครั้งเดียว ~30–45 นาที)

### 1) สร้าง Meta App
1. https://developers.facebook.com/apps → **Create app** → ประเภท **Business** → ผูกกับ Business "Sukit Utisvannakul's Business"
2. เพิ่ม product **Messenger** → **Messenger API Settings**
3. หัวข้อ *Access tokens* → **Add or remove Pages** → เลือก "คุยกับฝรั่งเป็น" → **Generate token** → เก็บไว้ = `PAGE_ACCESS_TOKEN`
4. **App settings → Basic** → เก็บ **App ID** = `APP_ID` และ **App secret** = `APP_SECRET`

### 2) ทำ QR PromptPay (ไม่บังคับ)
บัญชีรับเงินตั้งไว้แล้ว: **ไทยพาณิชย์ 264-296793-7 บริษัท ซิโอร่า จำกัด** (บอทแจ้งเลขบัญชีให้โอน)
ถ้าบริษัทมีพร้อมเพย์ (เลขผู้เสียภาษี 13 หลัก) ทำ QR ได้ตามนี้ แล้วตั้ง `QR_ENABLED=true` — **เลขบัญชีธนาคารใช้ทำ QR พร้อมเพย์ไม่ได้** สคริปต์จะปฏิเสธ
```bash
pip install qrcode pillow
python3 scripts/make_qr.py 0812345678     # ใส่เบอร์/เลขบัตรที่ผูก PromptPay ของคุณ
```
ได้ไฟล์ `public/qr/99.png 119 129 148 168 178 490` — **สแกนจ่ายจริงด้วยแอปธนาคาร 1 ครั้ง** เช็กชื่อบัญชีและยอดก่อนเปิดใช้

### 3) Deploy ขึ้น Cloudflare
```bash
npm install
npx wrangler login
npx wrangler kv namespace create STATE        # เอา id ที่ได้ไปใส่ใน wrangler.toml (REPLACE_WITH_KV_ID)
npx wrangler secret put PAGE_ACCESS_TOKEN
npx wrangler secret put APP_SECRET
npx wrangler secret put APP_ID
npx wrangler secret put VERIFY_TOKEN          # ตั้งเองเป็นข้อความสุ่มยาว ๆ
npx wrangler deploy                           # ได้ URL เช่น https://chatfarang-messenger-bot.<you>.workers.dev
```
แล้วแก้ใน `wrangler.toml`:
- `PUBLIC_URL` = URL ที่ได้จาก deploy
- `PROMPTPAY_ID` / `PROMPTPAY_NAME` = ตั้งเป็นบัญชี SCB บริษัท ซิโอร่า แล้ว
- `AFFILIATE_CODES` = โค้ด affiliate คั่นด้วยจุลภาค (ถ้ามี)

แล้ว `npx wrangler deploy` อีกครั้ง → เปิด `https://.../health` ต้องขึ้น `ok`

### 4) ผูก Webhook
Messenger API Settings → **Configure webhooks**
- Callback URL: `https://<worker-url>/webhook`
- Verify token: ค่าเดียวกับ `VERIFY_TOKEN`
- Subscribe fields ของเพจ: `messages`, `messaging_postbacks`, `messaging_referrals`, `message_echoes`, `feed`

### 5) ตั้งปุ่ม Get Started / เมนู / ice breakers
```bash
PAGE_ACCESS_TOKEN=EAAG... npm run profile
```

### 6) ปิดระบบตอบอัตโนมัติเดิมของเพจ
Business Suite → Inbox → Automations → ปิด *Instant reply* และ *FAQ* (ไม่งั้นจะตอบซ้อนกับบอท)
ถ้าในแอด Click-to-Messenger มี "Message template" ของ Ads Manager จะยังโชว์อยู่ — ไม่ชนกัน บอทรับปุ่มจากแอดได้ทุกปุ่ม

### 7) (แนะนำ) ส่งยอดซื้อกลับ Meta ให้แอดฉลาดขึ้น
Events Manager → สร้าง/เลือก Dataset → เชื่อมกับเพจ "คุยกับฝรั่งเป็น" → คัดลอก Dataset ID
```bash
npx wrangler secret put DATASET_ID
npx wrangler secret put CAPI_TOKEN     # Generate access token ในหน้า Dataset settings (Conversions API)
```
ทุกครั้งที่แอดมินพิมพ์ `#ok` บอทจะยิง `Purchase` (action_source = business_messaging) พร้อมยอดเงิน

---

## ⚠️ ข้อจำกัดสำคัญ: App Review
ก่อนผ่าน App Review บอทจะตอบได้เฉพาะคนที่มีบทบาทในแอป/เพจ (แอดมิน, tester) เท่านั้น
ต้องยื่น **App Review → ขอ Advanced Access ของ `pages_messaging`** (และ `pages_manage_engagement` ถ้าจะให้บอทตอบคอมเมนต์สาธารณะ) + ยืนยันธุรกิจ (Business Verification) — ปกติใช้เวลาหลายวัน
**ระหว่างรอ:** แอดยังวิ่งอยู่ → ให้แอดมินตอบแชทเองตาม `messenger_bot_script.md` หรือเปิด Instant reply ของ Business Suite ไว้ก่อน แล้วค่อยปิดเมื่อบอทผ่าน review

---

## ทดสอบ
```bash
npm test          # จำลองลูกค้าซื้อครบ flow กับ Graph API ปลอม (11 เคส)
npx wrangler tail # ดู log สด ตอนทดสอบกับเพจจริง
```

## โครงไฟล์
| ไฟล์ | หน้าที่ |
|---|---|
| `src/index.js` | Webhook (ตรวจลายเซ็น) + cron ทุก 10 นาที |
| `src/flow.js` | ลำดับการขาย, คีย์เวิร์ด, คำสั่งแอดมิน, ตามลูกค้า, upsell |
| `src/messages.js` | ข้อความทั้งหมด (แก้ภาษาได้ที่นี่ที่เดียว) |
| `src/fb.js` | Send API, Private reply คอมเมนต์, Conversions API |
| `scripts/make_qr.py` | สร้าง QR PromptPay ทุกยอด |
| `scripts/setup-profile.mjs` | ตั้ง Get Started / เมนู / ice breakers |
| `public/files/8c3b.../` | PDF เล่ม, Chat Cards, 10 ประโยค (ลิงก์เดาไม่ได้) |
