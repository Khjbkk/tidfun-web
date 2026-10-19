import os, html
from sentences import S, LEAD
D = os.path.dirname(os.path.abspath(__file__))
CSS = """
<link rel="stylesheet" href="../fonts.css">
<style>
@page { size: 1080px 1920px; margin:0; }
* { box-sizing:border-box; margin:0; }
body { font-family:'Sarabun',sans-serif; color:#2b2230; }
.card { width:1080px; height:1920px; padding:120px 90px; position:relative; page-break-after:always;
  background:linear-gradient(160deg,#23395b 0%,#4b3a6e 55%,#d94f70 100%); color:#fff; display:flex; flex-direction:column; justify-content:center; }
.card.light { background:#fff7f9; color:#2b2230; }
.cat { font-family:'Prompt'; font-size:34px; letter-spacing:.1em; opacity:.85; margin-bottom:40px; }
.light .cat { color:#d94f70; opacity:1; }
.num { position:absolute; top:90px; right:90px; font-family:'Prompt'; font-size:40px; opacity:.6; }
.en { font-family:'Prompt'; font-weight:600; font-size:66px; line-height:1.35; margin-bottom:60px; }
.th { font-size:46px; line-height:1.6; opacity:.92; }
.light .th { color:#6d6470; }
.foot { position:absolute; bottom:90px; left:90px; right:90px; font-family:'Prompt'; font-size:30px; opacity:.7; border-top:2px solid rgba(255,255,255,.35); padding-top:30px; }
.light .foot { border-color:#e6d6dc; color:#9a8a92; }
.cover .t1 { font-family:'Prompt'; font-size:52px; opacity:.9; }
.cover h1 { font-family:'Prompt'; font-size:120px; line-height:1.1; margin:40px 0; }
.cover .sub { font-size:44px; line-height:1.5; }
.tip { font-size:40px; line-height:1.6; }
.tip h2 { font-family:'Prompt'; font-size:70px; margin-bottom:40px; }
.tip li { margin-bottom:24px; }
</style>"""

def card(i, cat, en, th, light, foot):
    return f'<section class="card {"light" if light else ""}"><div class="num">{i}</div><div class="cat">{cat}</div><div class="en">{html.escape(en)}</div><div class="th">{th}</div><div class="foot">{foot}</div></section>'

def build(name, items, title, sub, foot, extra_tip):
    out = ['<!doctype html><html lang="th"><head><meta charset="utf-8">', CSS, '</head><body>']
    out.append(f'<section class="card cover"><div class="t1">{sub}</div><h1>{title}</h1><div class="sub">เซฟลงมือถือ · เปิดดูตอนแชท · ก๊อปวางได้ทันที</div><div class="foot">{foot}</div></section>')
    out.append(f'<section class="card light tip"><h2>วิธีใช้</h2><ul><li>เลือกประโยคตามสถานการณ์ แล้วแก้คำใน [ ] ให้เป็นเรื่องของคุณ</li><li>ทุกข้อความ: 1 เรื่องของคุณ + 1 คำถามกลับ</li><li>อย่าก๊อปทั้งบทสนทนา เขาอยากคุยกับ "คุณ"</li><li>ถ้าเขาขอเงิน/ชวนลงทุน ใช้การ์ดหมวด "ขอบเขต" แล้วเลิกคุย</li></ul>{extra_tip}<div class="foot">{foot}</div></section>')
    for i,(cat,en,th) in enumerate(items,1):
        out.append(card(i, cat, en, th, i%2==0, foot))
    out.append('</body></html>')
    open(os.path.join(D, name), 'w').write(''.join(out))

build('chat_cards.html', S, 'Chat Cards<br>100 ประโยค', 'แฟนฝรั่ง ไม่ต้องรอดวง · โบนัส',
      'Chat Cards · แฟนฝรั่ง ไม่ต้องรอดวง', '')
build('lead_magnet.html', LEAD, '10 ประโยค<br>เปิดแชท', 'ของขวัญฟรี · แฟนฝรั่ง ไม่ต้องรอดวง',
      'ฟรี · อีก 90 ประโยค + คู่มือ 30 วัน ทักแชทเพจ 129฿',
      '<p style="margin-top:40px">💛 ชอบไหม? ในเล่มเต็มมีอีก 90 ประโยค + วิธีคัดคนจริงจัง + เกราะกันมิจฉาชีพ ทักแชทเพจได้เลย 129฿</p>')
print("ok")
