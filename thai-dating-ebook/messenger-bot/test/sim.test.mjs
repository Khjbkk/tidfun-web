// End-to-end simulation against a fake Graph API and in-memory KV. Run: node --test test/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import worker from '../src/index.js';
import { runFollowups, load } from '../src/flow.js';

function memKV() {
  const m = new Map();
  return {
    async get(k, type) { const v = m.get(k); if (!v) return null; return type === 'json' ? JSON.parse(v.value) : v.value; },
    async put(k, value, opts = {}) { m.set(k, { value, metadata: opts.metadata }); },
    async list({ prefix }) { return { keys: [...m.entries()].filter(([k]) => k.startsWith(prefix)).map(([name, v]) => ({ name, metadata: v.metadata })), list_complete: true }; },
  };
}

const calls = [];
globalThis.fetch = async (url, init) => { calls.push({ url: String(url), body: JSON.parse(init.body) }); return new Response('{}', { status: 200 }); };

const env = {
  PAGE_ID: '1339142735957300', APP_ID: '999', APP_SECRET: 'shh', VERIFY_TOKEN: 'vt', PAGE_ACCESS_TOKEN: 'tok',
  DATASET_ID: '555', PROMPTPAY_ID: '081-234-5678', PROMPTPAY_NAME: 'ทดสอบ',
  QR_URLS: JSON.stringify({ 129: 'https://x/qr129.png', 178: 'https://x/qr178.png', 490: 'https://x/qr490.png' }),
  FILE_EBOOK_URL: 'https://x/ebook', FILE_CARDS_URL: 'https://x/cards', FILE_LEAD_URL: 'https://x/lead',
  AFFILIATE_CODES: 'MAY,NID', STATE: memKV(),
};

async function hook(entry) {
  const raw = JSON.stringify({ object: 'page', entry: [entry] });
  const sig = 'sha256=' + crypto.createHmac('sha256', env.APP_SECRET).update(raw).digest('hex');
  const waits = [];
  const res = await worker.fetch(new Request('https://bot/webhook', { method: 'POST', body: raw, headers: { 'x-hub-signature-256': sig } }), env, { waitUntil: (p) => waits.push(p) });
  await Promise.all(waits);
  return res;
}
const msg = (psid, message) => hook({ id: env.PAGE_ID, messaging: [{ sender: { id: psid }, recipient: { id: env.PAGE_ID }, message }] });
const sentTo = (psid) => calls.filter((c) => c.body.recipient && c.body.recipient.id === psid);
const texts = (psid) => sentTo(psid).map((c) => c.body.message && (c.body.message.text || JSON.stringify(c.body.message.attachment))).join('\n');

test('webhook verification', async () => {
  const ok = await worker.fetch(new Request('https://bot/webhook?hub.mode=subscribe&hub.verify_token=vt&hub.challenge=42'), env, {});
  assert.equal(await ok.text(), '42');
  const bad = await worker.fetch(new Request('https://bot/webhook?hub.mode=subscribe&hub.verify_token=no&hub.challenge=42'), env, {});
  assert.equal(bad.status, 403);
});

test('rejects bad signature', async () => {
  const res = await worker.fetch(new Request('https://bot/webhook', { method: 'POST', body: '{}', headers: { 'x-hub-signature-256': 'sha256=00' } }), env, { waitUntil() {} });
  assert.equal(res.status, 401);
});

test('full purchase with bump, admin approval, CAPI, upsell', async () => {
  const u = 'U1';
  await msg(u, { text: 'สวัสดีค่ะ' });
  assert.match(texts(u), /ยินดีต้อนรับ/);
  await msg(u, { text: '💳 ซื้อเลย 129฿', quick_reply: { payload: 'BUY' } });
  assert.match(texts(u), /Chat Cards 100/);
  await msg(u, { text: 'เอาด้วย', quick_reply: { payload: 'BUMP_YES' } });
  assert.match(texts(u), /ยอดชำระ 178฿/);
  assert.match(texts(u), /qr178/);
  await msg(u, { attachments: [{ type: 'image', payload: { url: 'https://slip' } }] });
  assert.match(texts(u), /ได้รับสลิปแล้ว/);
  assert.equal((await load(env, u)).stage, 'slip_review');

  // Admin types #ok in the Inbox -> echo event
  await hook({ id: env.PAGE_ID, messaging: [{ sender: { id: env.PAGE_ID }, recipient: { id: u }, message: { is_echo: true, text: '#ok' } }] });
  const s = await load(env, u);
  assert.equal(s.stage, 'paid');
  assert.match(texts(u), /ดาวน์โหลดเล่ม/);
  assert.match(texts(u), /ดาวน์โหลดการ์ด/);
  const capi = calls.find((c) => c.url.includes('/555/events'));
  assert.equal(capi.body.data[0].custom_data.value, 178);
  assert.equal(capi.body.data[0].user_data.page_scoped_user_id, u);

  const n = await runFollowups(env, Date.now() + 23 * 3600_000 + 1000);
  assert.ok(n >= 1);
  assert.match(texts(u), /รีวิวโปรไฟล์/);
});

test('unpaid follow-ups stop at 3 and respect 24h window', async () => {
  const u = 'U2';
  await msg(u, { text: 'ซื้อ' });
  await msg(u, { text: 'x', quick_reply: { payload: 'BUMP_NO' } });
  assert.match(texts(u), /ยอดชำระ 129฿/);
  const t0 = (await load(env, u)).lastIn;
  await runFollowups(env, t0 + 3600_000 + 1);
  await runFollowups(env, t0 + 3 * 3600_000 + 1);
  await runFollowups(env, t0 + 22 * 3600_000 + 1);
  await runFollowups(env, t0 + 23 * 3600_000 + 1);
  const s = await load(env, u);
  assert.equal(s.followups, 3);
  assert.equal(s.next, 0);
});

test('affiliate code gives discount and keeps ref', async () => {
  const u = 'U3';
  await msg(u, { text: 'may' });
  assert.match(texts(u), /ใช้โค้ด MAY แล้ว/);
  await msg(u, { text: 'x', quick_reply: { payload: 'BUMP_NO' } });
  assert.match(texts(u), /ยอดชำระ 119฿/);
  assert.equal((await load(env, u)).ref, 'MAY');
});

test('m.me ref link is stored', async () => {
  const u = 'U4';
  await hook({ id: env.PAGE_ID, messaging: [{ sender: { id: u }, recipient: { id: env.PAGE_ID }, referral: { ref: 'nid', source: 'SHORTLINK' } }] });
  assert.equal((await load(env, u)).ref, 'NID');
  assert.match(texts(u), /ยินดีต้อนรับ/);
});

test('human admin reply pauses bot; #no rejects slip', async () => {
  const u = 'U5';
  await msg(u, { text: 'ซื้อ' });
  await msg(u, { text: 'x', quick_reply: { payload: 'BUMP_NO' } });
  await hook({ id: env.PAGE_ID, messaging: [{ sender: { id: env.PAGE_ID }, recipient: { id: u }, message: { is_echo: true, text: 'สวัสดีค่ะ แอดมินเองค่ะ' } }] });
  const before = sentTo(u).length;
  await msg(u, { text: 'อยากถามเรื่องภาษา' });
  assert.equal(sentTo(u).length, before, 'bot stays silent while admin is handling');
  await hook({ id: env.PAGE_ID, messaging: [{ sender: { id: env.PAGE_ID }, recipient: { id: u }, message: { is_echo: true, text: '#no' } }] });
  assert.match(texts(u), /ตรวจสลิปนี้ไม่ผ่าน/);
  assert.equal((await load(env, u)).stage, 'await_slip');
});

test('bot echoes from our own app are ignored', async () => {
  const u = 'U6';
  await msg(u, { text: 'ซื้อ' });
  await hook({ id: env.PAGE_ID, messaging: [{ sender: { id: env.PAGE_ID }, recipient: { id: u }, message: { is_echo: true, app_id: 999, text: 'anything' } }] });
  assert.ok(!(await load(env, u)).humanUntil);
});

test('comment keyword sends private reply', async () => {
  await hook({ id: env.PAGE_ID, changes: [{ field: 'feed', value: { item: 'comment', verb: 'add', comment_id: 'C1', message: 'ขอประโยคค่ะ', from: { id: 'X' } } }] });
  const pr = calls.find((c) => c.body.recipient && c.body.recipient.comment_id === 'C1');
  assert.match(pr.body.message.text, /10 ประโยค/);
  assert.ok(calls.some((c) => c.url.includes('/C1/comments')));
});

test('refund keyword hands over to human', async () => {
  const u = 'U7';
  await msg(u, { text: 'ขอคืนเงินค่ะ' });
  assert.match(texts(u), /แอดมินจะเข้ามาตอบ/);
  assert.ok((await load(env, u)).humanUntil > Date.now());
});

test('QR and PDF links derive from PUBLIC_URL when not set explicitly', async () => {
  const { fileUrl } = await import('../src/flow.js');
  const e = { ...env, FILE_EBOOK_URL: '', QR_URLS: '', PUBLIC_URL: 'https://bot.example/', FILES_PATH: 'files/abc', QR_ENABLED: 'true' };
  assert.equal(fileUrl(e, 'ebook'), 'https://bot.example/files/abc/fanfarang-ebook.pdf');
  const u = 'U8';
  const saved = { ...env }; Object.assign(env, e);
  await msg(u, { text: 'ซื้อ' });
  await msg(u, { text: 'x', quick_reply: { payload: 'BUMP_NO' } });
  Object.assign(env, saved);
  assert.match(texts(u), /bot\.example\/qr\/129\.png/);
});

test('bank-transfer only (no QR) shows account details', async () => {
  const u = 'U9';
  const saved = { ...env };
  Object.assign(env, { QR_URLS: '', PUBLIC_URL: '', PROMPTPAY_ID: 'ไทยพาณิชย์ (SCB) 264-296793-7', PROMPTPAY_NAME: 'บริษัท ซิโอร่า จำกัด' });
  await msg(u, { text: 'ซื้อ' });
  await msg(u, { text: 'x', quick_reply: { payload: 'BUMP_NO' } });
  Object.assign(env, saved);
  const out = texts(u);
  assert.match(out, /โอนเข้าบัญชี ไทยพาณิชย์ \(SCB\) 264-296793-7/);
  assert.match(out, /บริษัท ซิโอร่า จำกัด/);
  assert.doesNotMatch(out, /สแกน QR/);
});
