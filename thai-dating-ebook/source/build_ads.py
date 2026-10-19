import os
D = os.path.dirname(os.path.abspath(__file__))
ADS = [
 ("A1","ภาษา","หยุดทักฝรั่งว่า<br>\"Hi\"","ทักแบบนี้แทน แล้วเขาจะตอบกลับ","\"Okay, important question:<br>have you tried som tam yet? 🌶️\"","60+ ประโยคก๊อปวาง · ทักแชทรับเลย 129฿"),
 ("A2","ภาษา","ภาษาอังกฤษไม่เก่ง<br>ก็คุยกับฝรั่งได้","ประโยคเดียวที่ทำให้เขาใจเย็นกับคุณ","\"Sorry, my English isn't perfect.<br>Can you say that in a simpler way?\"","คู่มือ 30 วัน + 60 ประโยค · ทักแชท 129฿"),
 ("A3","ภาษา","แมตช์แล้ว<br>แชทเงียบทุกที?","เพราะข้อความแรกของคุณไม่มี \"ตะขอ\"","สูตร: สังเกต 1 อย่าง + ถาม 1 คำถาม","เทมเพลต Bio 6 แบบ + ประโยคเปิดแชท · ทักแชท 129฿"),
 ("B1","กันโกง","ถ้าเขาพูดประโยคนี้<br>= มิจฉาชีพ 99%","\"I sent you a gift, but customs need a fee\"","คนไทยเสียหาย 21.9 ล้านบาท จากแชทแบบนี้","เช็กลิสต์กันหลอกรัก + วิธีคัดคนจริงจัง · ทักแชท 129฿"),
 ("B2","กันโกง","ถามฝรั่ง 3 คำถามนี้<br>รู้เลยว่าจริงจังหรือแค่มาเที่ยว","1) Are you living in Thailand, or just visiting?","2) What are you looking for here?<br>3) ... อยู่ในเล่ม","คู่มือเดทกับต่างชาติแบบปลอดภัย · ทักแชท 129฿"),
 ("B3","กันโกง","อยากมีแฟนต่างชาติ<br>แต่กลัวโดนหลอก?","กฎเหล็ก 7 ข้อ ที่คนโดนหลอกไม่เคยรู้","ข้อ 1: ไม่โอนเงินให้คนที่ไม่เคยเจอตัวจริง","เล่มนี้เน้นปลอดภัย ไม่ขายฝัน · ทักแชท 129฿"),
]
CSS = """<link rel="stylesheet" href="../fonts.css"><style>
*{box-sizing:border-box;margin:0}
body{font-family:'Sarabun',sans-serif;color:#fff}
.ad{position:relative;overflow:hidden;background:linear-gradient(160deg,#23395b 0%,#4b3a6e 55%,#d94f70 100%);padding:80px;display:flex;flex-direction:column;justify-content:space-between}
.sq{width:1080px;height:1080px}.st{width:1080px;height:1920px;padding:200px 90px}
.tag{font-family:'Prompt';font-size:30px;background:rgba(255,255,255,.18);display:inline-block;padding:10px 28px;border-radius:40px;align-self:flex-start;max-width:720px}
h1{font-family:'Prompt';font-weight:700;font-size:86px;line-height:1.15;margin:30px 0 20px}
.st h1{font-size:104px}
.sub{font-family:'Prompt';font-size:40px;color:#ffd3de;line-height:1.4}
.quote{background:rgba(255,255,255,.14);border-left:10px solid #ffd3de;padding:34px 40px;font-family:'Prompt';font-weight:600;font-size:44px;line-height:1.4;border-radius:0 24px 24px 0;margin:40px 0}
.st .quote{font-size:52px}
.cta{background:#fff;color:#23395b;font-family:'Prompt';font-weight:700;font-size:38px;padding:28px 40px;border-radius:24px;text-align:center}
.st .cta{font-size:44px}
.book{position:absolute;right:60px;top:70px;width:200px;height:270px;font-size:28px;background:linear-gradient(160deg,#2b4a78,#d94f70);border-radius:16px;box-shadow:0 30px 60px rgba(0,0,0,.4);transform:rotate(-8deg);opacity:.95;padding:30px;font-family:'Prompt';font-weight:700;line-height:1.2}
.sq .book{width:150px;height:200px;font-size:22px;right:50px;top:50px;padding:18px}
.sq h1{font-size:78px;margin-top:40px}
</style>"""
for code,angle,h1,sub,quote,cta in ADS:
    for fmt in ("sq","st"):
        html=f'<!doctype html><html lang="th"><head><meta charset="utf-8">{CSS}</head><body style="width:1080px;height:{1080 if fmt=="sq" else 1920}px"><div class="ad {fmt}"><div class="tag">{"สำหรับคนที่อยากมีแฟนต่างชาติแบบจริงจัง" if angle=="ภาษา" else "เตือนภัย · อ่านก่อนคุยกับใคร"}</div><div><h1>{h1}</h1><div class="sub">{sub}</div><div class="quote">{quote}</div></div><div class="cta">💬 {cta}</div><div class="book">แฟนฝรั่ง<br>ไม่ต้องรอดวง</div></div></body></html>'
        open(os.path.join(D,f"ad_{code}_{fmt}.html"),"w").write(html)
print("ok")
