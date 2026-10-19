// One-time: Get Started button, greeting, ice breakers and persistent menu.
// Usage: PAGE_ACCESS_TOKEN=... node scripts/setup-profile.mjs
const token = process.env.PAGE_ACCESS_TOKEN;
if (!token) { console.error('Set PAGE_ACCESS_TOKEN'); process.exit(1); }
const v = process.env.GRAPH_VERSION || 'v24.0';
const body = {
  get_started: { payload: 'GET_STARTED' },
  greeting: [{ locale: 'default', text: 'สวัสดีค่ะ {{user_first_name}} 💛 คุยกับต่างชาติได้มั่นใจ คัดคนจริงจัง ไม่โดนหลอก กด "เริ่มต้นใช้งาน" ได้เลยค่ะ' }],
  ice_breakers: [{ locale: 'default', call_to_actions: [
    { question: '📘 ในเล่มมีอะไรบ้าง', payload: 'INFO' },
    { question: '💳 ซื้อเลย 129฿', payload: 'BUY' },
    { question: '❓ ภาษาไม่เก่ง ใช้ได้ไหม', payload: 'FAQ_LANG' },
    { question: '🛡️ เช็กว่าเขาตัวจริงยังไง', payload: 'FAQ_SCAM' },
  ] }],
  persistent_menu: [{ locale: 'default', composer_input_disabled: false, call_to_actions: [
    { type: 'postback', title: '💳 ซื้อเล่ม 129฿', payload: 'BUY' },
    { type: 'postback', title: '📘 ในเล่มมีอะไร', payload: 'INFO' },
    { type: 'postback', title: '🙋 คุยกับแอดมิน', payload: 'HUMAN' },
  ] }],
};
const res = await fetch(`https://graph.facebook.com/${v}/me/messenger_profile?access_token=${token}`, {
  method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
});
console.log(res.status, await res.text());
