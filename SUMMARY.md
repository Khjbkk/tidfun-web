# SUMMARY — Thai dating ebook ("แฟนฝรั่ง ไม่ต้องรอดวง")

ทุกไฟล์อยู่ใน `thai-dating-ebook/` · สถานะปัจจุบันและรายละเอียดเต็มอยู่ด้านล่าง (สำเนาของ `thai-dating-ebook/SESSION_HANDOFF.md`)

## สถานะสินค้าโดยย่อ
- ✅ ebook 129฿, Chat Cards (+49฿), ของแจกฟรี 10 ประโยค — PDF เสร็จ
- ✅ เพจ "คุยกับฝรั่งเป็น" (Page ID 1339142735957300) สร้างแล้ว
- ✅ แอด Meta (บัญชี education) เผยแพร่แล้ว 200฿/วัน — รอ Meta ตรวจ, รูป AI ยังไม่ได้เช็กตัวสะกดไทย
- ✅ สคริปต์ตอบลูกค้า (บัญชี SCB บริษัท ซิโอร่า) พร้อมใช้
- 🟡 Messenger bot เขียนเสร็จ เทสต์ผ่าน 12/12 — ยังไม่ deploy, ต้องสร้าง Meta App + ผ่าน App Review
- 🟡 PDF ยังไม่ได้อัปขึ้น Drive / ลิงก์ไฟล์ในสคริปต์ยังเป็น placeholder

## ไฟล์ในโฟลเดอร์
| path | คืออะไร |
|---|---|
| `thai-dating-ebook/SESSION_HANDOFF.md` | สรุปทั้งหมด: IDs, ลิงก์, การตัดสินใจ, งานค้าง |
| `thai-dating-ebook/launch_kit/` | PDF สินค้า, รีเสิร์ช/แผนขาย, สคริปต์ตอบแชท, แอด, คลิป, ไลฟ์, affiliate, tracker, รูปแอด, ชุดตั้งเพจ |
| `thai-dating-ebook/messenger-bot/` | โค้ดบอท Messenger (Node.js / Cloudflare Worker) + คู่มือ |
| `thai-dating-ebook/source/` | ต้นฉบับ HTML/Python สำหรับแก้และเรนเดอร์ PDF/รูปใหม่ |

---

# สรุปงาน: ebook "แฟนฝรั่ง ไม่ต้องรอดวง" + เพจ "คุยกับฝรั่งเป็น"
อัปเดต: 19 ต.ค. 2026 · ใช้ไฟล์นี้เป็นบริบทให้ Claude Code บนเครื่อง (วางไว้ในโฟลเดอร์งานแล้วบอก Claude ว่า "อ่าน SESSION_HANDOFF.md ก่อน")

---

## 1. สินค้าและข้อเสนอ
| รายการ | ราคา | ไฟล์ |
|---|---|---|
| ebook "แฟนฝรั่ง ไม่ต้องรอดวง" (PDF A5 32 หน้า) | **129฿** | `launch_kit/แฟนฝรั่ง-ไม่ต้องรอดวง-ebook.pdf` |
| Order bump: Chat Cards 100 ประโยค (การ์ดมือถือ 102 หน้า) | +49฿ (รวม 178฿) | `launch_kit/chat_cards.pdf` |
| Upsell: รีวิวโปรไฟล์ + Bio 1:1 (ส่ง feedback ใน 48 ชม.) | 490฿ | บริการทำมือ |
| ของแจกฟรี: 10 ประโยคเปิดแชท (คนคอมเมนต์ "ประโยค") | ฟรี | `launch_kit/lead_magnet.pdf` |
| โปรพิเศษ (ไลฟ์ / retarget) | 99฿ | — |
| โค้ด affiliate | ลด 10฿ (119฿), ค่าคอม 50฿/ชุด | — |

**Positioning:** "คุยกับต่างชาติได้มั่นใจ คัดคนจริงจัง และไม่โดนหลอก" — ห้ามใช้ "จับฝรั่ง/หาผัวรวย", ห้ามการันตีผล, รับประกันคืนเงิน 7 วัน
**เป้า:** ขั้นต่ำ 50 ชุด/วัน · ปิดการขายใน **Facebook Messenger เท่านั้น** (ไม่ใช้ LINE)

## 2. รีเสิร์ชโดยย่อ
- คู่ไทย-ต่างชาติจดทะเบียน ~4,800 คู่ (2565) เพิ่มเท่าตัวจากปีก่อน, ~89% หญิงไทย-ชายต่างชาติ, กรุงเทพฯ มากสุด (5,872 คู่ ปี 2566) — ตัวเลขจากบทความบริษัทจัดหาคู่อ้างกรมการปกครอง ใช้อย่างระวัง
- คดีหลอกรักจาก ThaiCupid เสียหาย 21.9 ล้านบาท (ข่าว ธ.ค. 2025)
- Meta Ad Library: ไม่พบคู่แข่งขาย ebook/คอร์สหัวข้อนี้ในไทย
- TikTok/IG: คลิป "อยากมีผัวฝรั่ง ฟังก่อน 5 สิ่งนี้" 1.7M วิว (242× ค่าเฉลี่ยช่อง), "เรื่องที่ฝรั่งไม่เข้าใจคนไทย" 865K วิว
- **Avatar:** "เมย์" สาวออฟฟิศ 27–36 ในเมือง (~60%) · "นิด" แม่เลี้ยงเดี่ยว 33–45 ต่างจังหวัด (~30%) · LGBTQ+/ชาย (~10%)
- **Pain หลัก:** กลัวโดนหลอก, ภาษาไม่มั่นใจ, เจอแต่คนไม่จริงจัง, แมตช์แล้วแชทเงียบ, กลัวถูกตัดสิน, ช่องว่างวัฒนธรรม, ไม่รู้เริ่มยังไง

## 3. เพจ Facebook
| | |
|---|---|
| ชื่อเพจ | **คุยกับฝรั่งเป็น** |
| Page ID | **1339142735957300** |
| Profile URL | https://www.facebook.com/profile.php?id=61595225504485 |
| Business | Sukit Utisvannakul's Business (285027155468468) |
| ลิงก์แชท | `https://m.me/1339142735957300` · affiliate: `https://m.me/1339142735957300?ref=โค้ด` |
| หมวดเพจที่แนะนำ | Education + Personal Coach (เลี่ยง Dating Service) |
| username ที่อยากได้ | `chatfarangpen` (ตั้งไม่ได้ตอนนี้ — ลองใหม่หลังเพจมีกิจกรรม) |

## 4. บัญชีรับเงิน
**ไทยพาณิชย์ (SCB) 264-296793-7 · บริษัท ซิโอร่า จำกัด**
- เลขบัญชีธนาคาร **ทำ QR พร้อมเพย์ไม่ได้** (สคริปต์ make_qr.py จะปฏิเสธ) — ถ้าต้องการ QR ใช้เลขผู้เสียภาษีบริษัท 13 หลัก (ถ้าผูกพร้อมเพย์) หรือสร้าง QR ในแอป SCB Business

## 5. โฆษณา Meta (เปิดใช้งานแล้ว)
| | ค่า |
|---|---|
| บัญชีโฆษณา | **education — 2885254735145531** (THB) |
| แคมเปญ | `TF-EBOOK-MSG-PURCHASE` — **120250954133610262** · Sales · งบ **200฿/วัน** (CBO) |
| Ad set | `TH-F-25-45-BROAD-MSG` — **120250954134260262** · ทั้งประเทศ หญิง 25+ (Advantage+ Audience) · Messenger · Optimize: Messaging purchase · Attribution 1-day click |
| แอด 1 | `TF-A1-AI-HiCafe-v2` — 120250955218550262 (มุมภาษา "หยุดทักฝรั่งว่า Hi") |
| แอด 2 | `TF-B1-AI-ScamWarning-v2` — 120250955220410262 (มุมกันโกง) |
| แอด 3 | `TF-A2-AI-CoffeeDate-v2` — 120250955220560262 (ภาษาไม่เก่งก็คุยได้) |
| ข้อความต้อนรับแชท | ไทย + ปุ่ม 📘 ในเล่มมีอะไรบ้าง / 💳 ซื้อเลย 129฿ / ❓ ภาษาไม่เก่ง ใช้ได้ไหม (แอด B1 ใช้ 🛡️ วิธีเช็กว่าเขาตัวจริงไหม) |
| สถานะล่าสุด | เผยแพร่แล้ว รอ Meta ตรวจ (IN_PROCESS) |
| แอดชุดแรก (v1) 3 ตัว | ค้างในฉบับร่าง ไม่ได้เผยแพร่ — ลบทิ้งได้ |
| Ads Manager | https://www.facebook.com/adsmanager/manage/ads?act=2885254735145531 |

**รูปแอด AI (OpenArt, Nano Banana 2.1):**
- A1: https://cdn.openart.ai/openart-ai/production/2026-10/create-image/QiwCymtNqDxX503AYTiK/image_1792376596179_eaa8ec60_1792376597347_4c88f176.png
- B1: https://cdn.openart.ai/openart-ai/production/2026-10/create-image/QiwCymtNqDxX503AYTiK/image_1792376597172_5fccd9ee_1792376597320_df33e691.png
- A2: https://cdn.openart.ai/openart-ai/production/2026-10/create-image/QiwCymtNqDxX503AYTiK/image_1792376595249_63e572ae_1792376596124_1db51345.png
- ⚠️ ยังไม่มีใครเช็กว่าตัวหนังสือไทยในรูปสะกดถูก
- รูปแอดแบบไม่ใช้ AI (HTML) อีก 12 ไฟล์: `launch_kit/ads/`

**กฎปรับแอด (เช็ก 09:00 ทุกวัน):** CPA ≤ 90฿ → เพิ่มงบ +20% · 90–120฿ → สลับครีเอทีฟแย่สุด · >120฿ สองวันติด → หยุด ad set · Cost/แชท > 35฿ → เปลี่ยน hook · แชท→ซื้อ < 20% → แก้บอท/สคริปต์ ไม่ใช่เพิ่มงบ · Frequency > 3 → เปลี่ยนครีเอทีฟ
**กฎ 18:00:** ยอด < 35 ชุด → retarget โปร 99฿ · เพิ่มงบ ad set ที่ CPA < 90฿ อีก 30% · ไลฟ์ด่วน 30 นาที · ขอ affiliate 3 คนลงสตอรี่

## 6. Google Drive
โฟลเดอร์ "แฟนฝรั่ง ไม่ต้องรอดวง — Launch Kit": https://drive.google.com/drive/folders/1_ey8biPMVWpVU4N8MXWqG3scA29j7tu_
- เช็กลิสต์เปิดตัว: https://docs.google.com/document/d/13hSYQbv2AhF-tX4OkAy6TyWUoVxTpUR_kmorMk3CB8k/edit
- สคริปต์บอท + SOP: https://docs.google.com/document/d/1uDB-MzAQUyWM8PfEoRXIvwzzXJeeiElyrWK-EdA9eOI/edit
- ข้อความแอด + ตั้งแคมเปญ: https://docs.google.com/document/d/1DoC1A0hCXFKQN645kK3ZXG-fUsyQKi3xy9BAHnyY5mQ/edit
- สคริปต์คลิป 30 วัน: https://docs.google.com/document/d/1hmo7hIKjbjnKVnnnonK-3hzAmOE9U1vM5Li4bRser-Q/edit
- สคริปต์ไลฟ์: https://docs.google.com/document/d/1TLMdAhNxDNYKli_U9Dd_sJPHmuFFl2MWslxPVR4SIBM/edit
- Affiliate kit: https://docs.google.com/document/d/1vw2pTvw04VQ3luKEPlL8qnE3W8Wl-5GC6rRta4UJQnE/edit
- ตารางยอดรายวัน (Sheets): https://docs.google.com/spreadsheets/d/1MXChXX3BbuUstg7114yC6mLR_JQYh9y6qMKNwWsK1f4/edit
- ⚠️ ไฟล์ใน Drive ยังเป็นลิงก์ `m.me/PAGE` / ไม่มีเลขบัญชี — **ใช้ไฟล์ในโฟลเดอร์นี้เป็นฉบับล่าสุด**
- ⚠️ PDF 3 ไฟล์ยังไม่ได้อัปขึ้น Drive (ไฟล์ใหญ่เกินเครื่องมือ) — ลากขึ้นเอง

## 7. Messenger bot (`messenger-bot/`)
Node.js — รันได้ 2 แบบ: บนเครื่อง (`./start.sh` / `start.bat`) หรือ Cloudflare Workers (`npx wrangler deploy`)
- Flow: ต้อนรับ → FAQ → เสนอ Chat Cards → แจ้งโอน SCB → รับสลิป → แอดมินพิมพ์ `#ok` → ส่งลิงก์ PDF + ยิง Purchase (Conversions API) → ตาม 1/3/22 ชม. → upsell 490฿ ที่ 23 ชม.
- คำสั่งแอดมินในแชท: `#ok` อนุมัติ · `#no` สลิปไม่ผ่าน · `#99` ราคาพิเศษ · `#bot` ให้บอทกลับมา · พิมพ์เอง = บอทเงียบ 30 นาที
- คอมเมนต์ "ประโยค" → private reply ส่ง 10 ประโยค
- PDF เสิร์ฟจากตัวบอทที่ `public/files/8c3b21350e868347/`
- เทสต์: `npm test` → ผ่าน 12/12 (จำลอง Graph API) — **ยังไม่ได้ทดสอบกับเพจจริง**
- ต้องมี: Meta App (Business) + Messenger product → PAGE_ACCESS_TOKEN, APP_ID, APP_SECRET; webhook fields `messages, messaging_postbacks, messaging_referrals, message_echoes, feed`
- ⚠️ ต้องผ่าน **App Review (`pages_messaging` Advanced Access)** ก่อน บอทถึงจะตอบลูกค้าทั่วไปได้ (ก่อนนั้นตอบได้แค่แอดมิน/tester)
- รายละเอียด: `messenger-bot/README.md`, `messenger-bot/RUN_ON_MY_COMPUTER.md`

## 8. ไฟล์ทั้งหมดในแพ็กนี้
| โฟลเดอร์/ไฟล์ | เนื้อหา |
|---|---|
| `launch_kit/แฟนฝรั่ง-ไม่ต้องรอดวง-ebook.pdf` | สินค้าหลัก |
| `launch_kit/research-avatar-แผนขาย.pdf` | รีเสิร์ช + avatar + แผนขาย (129฿/Messenger) |
| `launch_kit/chat_cards.pdf`, `lead_magnet.pdf` | bump + ของแจกฟรี |
| `launch_kit/สคริปต์ตอบลูกค้า-ก๊อปวาง.md` | **ใช้ตอบแชทตอนนี้** (ใส่บัญชี SCB แล้ว) |
| `launch_kit/messenger_bot_script.md` | สคริปต์บอทฉบับเต็ม + SOP แอดมิน |
| `launch_kit/ad_copy_and_campaign_setup.md` | ข้อความแอด 7 ชุด + โครงแคมเปญ |
| `launch_kit/30_video_scripts.md`, `live_script.md`, `affiliate_kit.md` | คอนเทนต์ + ไลฟ์ + affiliate |
| `launch_kit/daily_tracker.xlsx` | ตารางยอด + กฎตัดสินใจ + ทะเบียน affiliate |
| `launch_kit/00_LAUNCH_CHECKLIST.md` | เช็กลิสต์ 14 ข้อ |
| `launch_kit/ads/*.png` | รูปแอด 12 ไฟล์ (1:1, 9:16) |
| `launch_kit/page/` | รูปโปรไฟล์ / รูปปก / ขั้นตอนตั้งเพจ / About / โพสต์แรก |
| `messenger-bot/` | โค้ดบอท |
| `source/` | ไฟล์ต้นฉบับ HTML/Python สำหรับแก้และเรนเดอร์ PDF/รูปใหม่ (ใช้ Chromium + ฟอนต์ Prompt/Sarabun) |

## 9. สิ่งที่ยังค้าง (เรียงตามความด่วน)
1. **ตอบแชทลูกค้าจากแอดตอนนี้** ใน Business Suite ด้วย `สคริปต์ตอบลูกค้า-ก๊อปวาง.md` (ยังไม่มีบอท) → ติดป้าย "ซื้อแล้ว" ทุกแชทที่ปิดการขาย
2. อัป PDF 3 ไฟล์ขึ้น Drive → ใส่ลิงก์ [ลิงก์เล่ม] [ลิงก์การ์ด] [ลิงก์10ประโยค] ในสคริปต์
3. เช็กตัวหนังสือไทยในรูปแอด AI ใน Ads Manager — ตัวไหนผิดให้ปิด
4. ลบแอด v1 ที่ค้างในฉบับร่าง
5. ตั้งเพจ: รูปโปรไฟล์/ปก, About, โพสต์แรก (ใน `launch_kit/page/PAGE_SETUP.md`)
6. สร้าง Meta App → รันบอท (บนเครื่องหรือ Cloudflare) → ยื่น App Review
7. (ถ้าต้องการ QR) หาเลขพร้อมเพย์บริษัท 13 หลัก หรือทำ QR จากแอป SCB
8. หลังแอดวิ่ง 24–48 ชม.: ดึงผล CPA / ต้นทุนต่อแชท แล้วปรับตามกฎข้อ 5
9. เริ่มคอนเทนต์ TikTok/Reels วันละ 2–3 คลิป + ทัก affiliate 30 คน + นัดไลฟ์แรก

## 10. ข้อควรระวัง
- ตามลูกค้าใน Messenger ได้แค่ภายใน 24 ชม. หลังลูกค้าทักล่าสุด
- โฆษณาหมวดหาคู่ถูกตรวจเข้ม — วางมุม "ภาษา" และ "ความปลอดภัย" เสมอ
- บัญชีรับเงินเป็นชื่อบริษัท ซิโอร่า (ไม่ตรงชื่อเพจ) — ยืนยันว่าตั้งใจใช้บัญชีนี้
- อย่าแชร์ `.env`, token, และ `data/state.json` (ข้อมูลลูกค้า)
