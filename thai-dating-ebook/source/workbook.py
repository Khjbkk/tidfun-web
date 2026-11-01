"""Build the 30-day challenge workbook HTML (A4, printable / fill on tablet)."""
import os

D = os.path.dirname(os.path.abspath(__file__))

DAYS = [
    ("เขียนเป้าหมายใน 1 ประโยค", "ฉันมองหา..."),
    ("เลือก 2 แอป + ยืนยันตัวตน", "บท 2"),
    ("ถ่ายรูปใบที่ 1–2 (หน้าชัด + เต็มตัว)", "บท 3"),
    ("ถ่ายรูปใบที่ 3–5 (กิจกรรม/เพื่อน/ที่เที่ยว)", "บท 3"),
    ("เขียน Bio 3 บรรทัด + ให้เพื่อนอ่าน", "หน้า 4"),
    ("เปิดโปรไฟล์ ปัดขวาเฉพาะคนที่มี Bio", ""),
    ("ปัดแบบเลือก 20 คน · จดว่าใครน่าสนใจ", ""),
    ("ทักแมตช์ใหม่ 3 คน (สังเกต + ถาม)", "บท 4"),
    ("ทักอีก 3 คน · ใช้ประโยคจากคลังวันละ 1", "หน้า 9"),
    ("ฝึกกฎ 1 ต่อ 1 ทุกข้อความ", ""),
    ("จดประโยคที่ได้ผลดีที่สุดวันนี้", "หน้า 9"),
    ("ถาม 3 คำถามกรองกับทุกคนที่คุย > 3 วัน", "บท 5"),
    ("ให้คะแนนสัญญาณแดง/เขียวรายคน", "หน้า 7"),
    ("Unmatch คนที่มีแดง 3 ข้อ (ไม่ต้องอธิบาย)", ""),
    ("อ่านบท 6 + ค้นรูปย้อนกลับทุกคน", "หน้า 8"),
    ("เช็กลิสต์ 'เขาตัวจริงไหม' รายคน", "หน้า 8"),
    ("ชวนวิดีโอคอลคนที่ผ่านการกรอง 1 คน", "บท 4"),
    ("วิดีโอคอลคนที่ 2", ""),
    ("ทบทวน: ใครเลี่ยงคอล? → ตัดออก", ""),
    ("เลือกคุยต่อไม่เกิน 2–3 คน", "หน้า 6"),
    ("ปรับรูป/Bio จากสิ่งที่เรียนรู้", ""),
    ("ชวนเจอ (คาเฟ่ · กลางวัน)", "บท 4"),
    ("กรอกแผนเดทปลอดภัย", "หน้า 10"),
    ("ส่งข้อมูลเดทให้เพื่อน 1 คน", "หน้า 10"),
    ("ไปเดทแรก 💛", "บท 7"),
    ("ส่งข้อความหลังเดท", "บท 7"),
    ("ทบทวนเดท: รู้สึกปลอดภัย/เป็นตัวเองไหม", ""),
    ("ฝึกพูดความรู้สึกแบบไม่เกรงใจ 1 ครั้ง", "บท 8"),
    ("สรุป 3 สิ่งที่ได้เรียนรู้", "หน้า 12"),
    ("ตั้งเป้า 30 วันถัดไป 🎉", "หน้า 12"),
]

CSS = """
<link rel="stylesheet" href="fonts.css">
<style>
@page { size: A4; margin: 14mm; }
@page :first { margin: 0; }
:root { --navy:#23395b; --rose:#d94f70; --ink:#2b2230; --mute:#7a707e; --line:#d9cfdc; --soft:#fbf6f9; }
* { box-sizing:border-box; }
body { margin:0; font-family:'Sarabun',sans-serif; color:var(--ink); font-size:11pt; line-height:1.5; background:#fff; }
h1,h2,h3 { font-family:'Prompt',sans-serif; color:var(--navy); margin:0; }
h2 { font-size:18pt; margin-bottom:2mm; }
h3 { font-size:12pt; color:var(--rose); margin:4mm 0 2mm; }
.page { page-break-before:always; }
.sub { color:var(--mute); margin-bottom:5mm; }
.kick { font-family:'Prompt'; color:var(--rose); font-size:9pt; letter-spacing:.1em; font-weight:600; }
.line { border-bottom:0.4mm dotted var(--line); height:9mm; }
.box { border:0.4mm solid var(--line); border-radius:3mm; padding:3mm 4mm; margin-bottom:3mm; break-inside:avoid; }
.tick { display:inline-block; width:5mm; height:5mm; border:0.5mm solid var(--rose); border-radius:1mm; vertical-align:middle; margin-right:2mm; }
table { width:100%; border-collapse:collapse; font-size:10pt; }
th { background:var(--navy); color:#fff; font-family:'Prompt'; font-weight:600; padding:2mm; text-align:left; }
td { border:0.3mm solid var(--line); padding:2mm; height:10mm; vertical-align:top; }
.daytbl td { height:15mm; }
.daytbl td.d { width:14mm; font-family:'Prompt'; font-weight:700; color:var(--rose); text-align:center; vertical-align:middle; }
.daytbl td.t { width:10mm; text-align:center; vertical-align:middle; }
.small { font-size:8.5pt; color:var(--mute); }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:4mm; }
.photo { border:0.5mm dashed var(--rose); border-radius:3mm; height:42mm; padding:3mm; font-size:9.5pt; color:var(--mute); }
.cover { width:210mm; height:297mm; background:linear-gradient(160deg,#23395b 0%,#4b3a6e 55%,#d94f70 100%); color:#fff; padding:28mm 20mm; position:relative; }
.cover h1 { color:#fff; font-size:44pt; line-height:1.1; margin:12mm 0 6mm; }
.cover h1 span { color:#ffd3de; }
.cover .t { font-family:'Prompt'; background:rgba(255,255,255,.18); display:inline-block; padding:2mm 6mm; border-radius:10mm; }
.cover .s { font-size:15pt; max-width:150mm; line-height:1.6; }
.cover .name { position:absolute; bottom:24mm; left:20mm; right:20mm; border-top:0.4mm solid rgba(255,255,255,.4); padding-top:6mm; font-size:13pt; }
.cover .name .l { display:inline-block; width:110mm; border-bottom:0.4mm solid rgba(255,255,255,.7); height:8mm; }
.trk { display:grid; grid-template-columns:repeat(10,1fr); gap:2mm; }
.trk div { border:0.5mm solid var(--rose); border-radius:2mm; height:16mm; font-family:'Prompt'; font-size:9pt; color:var(--rose); padding:1mm 2mm; }
</style>"""


def lines(n):
    return "".join('<div class="line"></div>' for _ in range(n))


def build():
    p = ['<!doctype html><html lang="th"><head><meta charset="utf-8"><title>สมุดชาเลนจ์ 30 วัน</title>', CSS, "</head><body>"]
    p.append("""<section class="cover"><div class="t">สมุดชาเลนจ์ · ใช้คู่กับคู่มือ "แฟนฝรั่ง ไม่ต้องรอดวง"</div>
<h1>ชาเลนจ์ 30 วัน<br><span>คุยกับฝรั่งเป็น</span></h1>
<div class="s">วันละ 1 ภารกิจ ติ๊กทุกวัน · จากโปรไฟล์ใหม่ ถึงเดทแรกที่ปลอดภัย<br>มีช่องให้เขียน ตารางคัดคน เช็กลิสต์กันหลอก และแผนเดท</div>
<div class="name">สมุดของ <span class="l"></span><br><br>เริ่มวันที่ ......../......../........ &nbsp;&nbsp; ครบ 30 วัน ......../......../........</div></section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 1</div><h2>ก่อนเริ่ม: สัญญากับตัวเอง</h2>
<div class="sub">พิมพ์ออกมา หรือเปิดในแท็บเล็ตแล้วเขียนทับได้เลย</div>
<h3>เป้าหมายของฉันใน 1 ประโยค</h3><div class="box">ฉันมองหา ..........................................................................................................................<br><br>ที่ ....................................................................................................................................</div>
<h3>สิ่งที่ฉันจะไม่ยอม (ขอบเขตของฉัน)</h3>{lines(4)}
<h3>กฎ 4 ข้อของชาเลนจ์นี้</h3>
<div class="box"><span class="tick"></span>ทำวันละ 1 ภารกิจ (20–30 นาที) พลาดได้ แต่ห้ามพลาด 2 วันติด<br><br>
<span class="tick"></span>ไม่โอนเงินให้คนที่ไม่เคยเจอตัวจริง ไม่ว่าเหตุผลอะไร<br><br>
<span class="tick"></span>วิดีโอคอลก่อนผูกพันทุกครั้ง<br><br>
<span class="tick"></span>เล่าให้เพื่อนสนิท 1 คนฟังเสมอ ชื่อเพื่อน: ...........................................</div>
<div style="margin-top:10mm">ลงชื่อ ..................................................... &nbsp; วันที่ ....................</div></section>""")

    rows = "".join(
        f'<tr><td class="d">วัน {i+1}</td><td>{t}<div class="small">{ref}</div></td><td></td><td class="t"><span class="tick"></span></td></tr>'
        for i, (t, ref) in enumerate(DAYS))
    rows = rows.split("</tr>")
    weeks = [("สัปดาห์ 1–2: หน้าร้าน + เริ่มแชท", 0, 10), ("สัปดาห์ 2–3: คัดคน + กันหลอก", 10, 20), ("สัปดาห์ 3–4: เดทจริง", 20, 30)]
    for n, (title, a, b) in enumerate(weeks):
        body = "</tr>".join(rows[a:b]) + "</tr>"
        p.append(f"""<section class="page"><div class="kick">หน้า {n+2} · ภารกิจรายวัน</div><h2>{title}</h2>
<table class="daytbl"><tr><th>วัน</th><th>ภารกิจ</th><th style="width:62mm">บันทึกสั้น ๆ</th><th>เสร็จ</th></tr>{body}</table></section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 5 · วัน 3–5</div><h2>สร้างโปรไฟล์</h2>
<h3>รูป 5 ใบ (ติ๊กเมื่อได้รูปที่ใช่)</h3><div class="grid2">
<div class="photo"><span class="tick"></span>1. หน้าชัด ยิ้มเห็นฟัน แสงธรรมชาติ</div>
<div class="photo"><span class="tick"></span>2. เต็มตัว ชุดที่ใส่จริงวันหยุด</div>
<div class="photo"><span class="tick"></span>3. ทำกิจกรรมที่ชอบ</div>
<div class="photo"><span class="tick"></span>4. กับเพื่อน/ครอบครัว (หาตัวเองเจอง่าย)</div></div>
<div class="photo" style="margin-top:4mm"><span class="tick"></span>5. ที่เที่ยว/ที่ทำงาน (ไม่เห็นชื่อบริษัท/ทะเบียนรถ)</div>
<h3>Bio 3 บรรทัด</h3>
<div class="box"><b>1) ฉันเป็นใคร</b>{lines(1)}<b>2) สิ่งพิเศษ/ตะขอ 1 อย่าง</b>{lines(1)}<b>3) สิ่งที่มองหา + คำชวนคุย</b>{lines(1)}</div>
<div class="small">เช็ก: มีตะขอให้เขาเปิดแชทไหม · บอกเป้าหมายด้วยน้ำเสียงบวกไหม · ไม่มีคำว่า "No players!"</div></section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 6 · วัน 8–20</div><h2>ตารางคนที่กำลังคุย</h2>
<div class="sub">จดทุกคนที่คุยเกิน 2 วัน · ช่องสุดท้าย: คุยต่อ / พักไว้ / ตัดออก</div>
<table><tr><th>ชื่อ/แอป</th><th>อยู่ไทย?</th><th>หาอะไร?</th><th>🟢</th><th>🔴</th><th>คอลแล้ว</th><th>สถานะ</th></tr>
{''.join('<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>' for _ in range(12))}</table></section>""")

    green = ["ถามเรื่องชีวิต งาน ครอบครัวฉัน", "จำสิ่งที่ฉันเล่าได้", "ชวนเจอที่สาธารณะ กลางวัน", "วิดีโอคอลได้ง่าย ๆ", "มีแผนชีวิตชัด", "เคารพเมื่อฉันบอกไม่"]
    red = ["ชมแต่รูปร่าง / ถามเรื่องเซ็กซ์เร็ว", "ถามซ้ำ เหมือนคุยหลายคน", "ชวนไปห้องตั้งแต่เดทแรก", "กล้องเสียตลอด", "พูดถึงเงิน/ลงทุน/ของขวัญติดด่าน", "กดดัน ตื๊อ โกรธเมื่อถูกปฏิเสธ"]
    card = lambda: f"""<div class="box"><b>ชื่อ:</b> ............................................. <b>แอป:</b> ..............................
<div class="grid2" style="margin-top:2mm"><div>{''.join(f'<span class="tick"></span>{g}<br>' for g in green)}</div><div>{''.join(f'<span class="tick"></span>{r}<br>' for r in red)}</div></div>
<div style="margin-top:2mm">🟢 ...... ข้อ &nbsp; 🔴 ...... ข้อ &nbsp;→ <span class="tick"></span>คุยต่อ <span class="tick"></span>ถามตรง ๆ <span class="tick"></span>Unmatch (แดง 3 ข้อ)</div></div>"""
    p.append(f"""<section class="page"><div class="kick">หน้า 7 · วัน 13</div><h2>ใบให้คะแนนรายคน</h2>
<div class="sub">แดง 1 = จดไว้ · แดง 2 = ถามตรง ๆ · แดง 3 = Unmatch ไม่ต้องอธิบาย</div>{card()}{card()}{card()}</section>""")

    shield = ["วิดีโอคอลแล้ว หน้าตรงกับรูป", "ค้นรูปใน Google Lens แล้ว ไม่ใช่รูปคนอื่น", "รู้ชื่อจริง ค้นเจอตัวตนที่มีประวัติยาว", "เรื่องเล่าตรงกันทุกครั้ง (งาน เมือง อายุ)", "ไม่เคยพูดถึงเงิน การลงทุน ของขวัญติดด่าน", "ยอมนัดเจอในที่สาธารณะ", "เพื่อนสนิทฟังแล้วไม่รู้สึกแปลก"]
    p.append(f"""<section class="page"><div class="kick">หน้า 8 · วัน 15–16</div><h2>เกราะกันหลอก: เขาตัวจริงไหม</h2>
<table><tr><th>ข้อเช็ก</th><th style="width:28mm">คนที่ 1</th><th style="width:28mm">คนที่ 2</th><th style="width:28mm">คนที่ 3</th></tr>
<tr><td><b>ชื่อ</b></td><td></td><td></td><td></td></tr>
{''.join(f'<tr><td>{s}</td><td></td><td></td><td></td></tr>' for s in shield)}</table>
<div class="box" style="margin-top:5mm;background:#fdeceb;border-color:#e8b4b0"><b>ถ้าเขาขอเงิน / ชวนลงทุน / ของติดศุลกากร:</b> หยุดคุยทันที · แคปทุกอย่าง · โทร <b>1441</b> · แจ้งความ <b>thaipoliceonline.go.th</b><br>
ประโยคตัดบท: <i>"I have a personal rule: I never send money to someone I haven't met in person."</i></div></section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 9 · ทุกวัน</div><h2>สมุดฝึกประโยค</h2>
<div class="sub">วันละ 1 ประโยคจากคลังในเล่ม/Chat Cards · ใช้จริงแล้วจดผล</div>
<table><tr><th style="width:12mm">วัน</th><th>ประโยคที่ใช้</th><th style="width:22mm">ใช้กับใคร</th><th style="width:30mm">ผล 😊😐🙁</th></tr>
{''.join(f'<tr><td>{i}</td><td></td><td></td><td></td></tr>' for i in range(1, 17))}</table></section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 10 · วัน 23–24</div><h2>แผนเดทแรกแบบปลอดภัย</h2>
<div class="box"><b>เจอกับ:</b> ................................................ <b>แอป:</b> ........................ <b>ลิงก์โปรไฟล์:</b> ................................<br><br>
<b>วัน/เวลา:</b> ................................ <b>สถานที่ (สาธารณะ):</b> ...................................................................</div>
<h3>เช็กลิสต์ก่อนออกจากบ้าน</h3>
<div class="box"><span class="tick"></span>เดินทางไป-กลับเอง ไม่ให้มารับที่บ้าน<br><br><span class="tick"></span>ส่งชื่อ รูป สถานที่ เวลา ให้เพื่อน: ............................ + แชร์ตำแหน่ง<br><br>
<span class="tick"></span>นัดให้เพื่อนโทรเช็กเวลา ........................<br><br><span class="tick"></span>มีเงินพอจ่ายส่วนตัว + ค่ากลับบ้าน<br><br><span class="tick"></span>ดื่มน้อย ไม่ทิ้งแก้วลับตา</div>
<h3>หัวข้อที่อยากคุย</h3>{lines(3)}
<h3>หลังเดท: รู้สึกยังไง</h3>{lines(3)}
<div><span class="tick"></span>อยากเจออีก &nbsp; <span class="tick"></span>ไม่แน่ใจ &nbsp; <span class="tick"></span>ไม่ไปต่อ (ส่งข้อความสุภาพในบท 7)</div></section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 11</div><h2>ตารางติ๊ก 30 วัน</h2>
<div class="sub">ระบายช่องทุกวันที่ทำภารกิจเสร็จ · ติดตู้เย็นหรือตั้งเป็นวอลเปเปอร์ได้</div>
<div class="trk">{''.join(f'<div>{i}</div>' for i in range(1, 31))}</div>
<h3>ทบทวนรายสัปดาห์</h3>
{''.join(f'<div class="box"><b>สัปดาห์ {w}</b> &nbsp; สิ่งที่ได้ผล:{lines(1)}สิ่งที่จะปรับ:{lines(1)}</div>' for w in range(1, 5))}</section>""")

    p.append(f"""<section class="page"><div class="kick">หน้า 12 · วัน 29–30</div><h2>ครบ 30 วันแล้ว 🎉</h2>
<h3>3 สิ่งที่ฉันได้เรียนรู้</h3>{lines(6)}
<h3>ตัวเลขของฉัน</h3><div class="box">แมตช์ ........ &nbsp; คนที่คุยเกิน 3 วัน ........ &nbsp; วิดีโอคอล ........ &nbsp; เดท ........ &nbsp; Unmatch คนไม่ใช่ ........</div>
<h3>ฉันภูมิใจในตัวเองที่...</h3>{lines(3)}
<h3>เป้า 30 วันถัดไป</h3>{lines(4)}
<div class="small" style="margin-top:8mm">สมุดนี้เป็นเครื่องมือฝึกทักษะการสื่อสารและความปลอดภัย ไม่รับประกันผลลัพธ์ทางความสัมพันธ์ · ตกเป็นเหยื่อมิจฉาชีพ โทร 1441</div></section>""")
    p.append("</body></html>")
    open(os.path.join(D, "workbook.html"), "w").write("".join(p))


if __name__ == "__main__":
    build()
