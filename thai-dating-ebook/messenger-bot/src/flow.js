// Sales state machine: welcome -> bump -> pay -> slip -> admin #ok -> deliver -> upsell.
import { M, QR } from './messages.js';
import { sendText, sendTexts, sendImage, sendButton, privateReply, publicCommentReply, sendPurchaseEvent } from './fb.js';

const HOUR = 3600_000;
const MIN = 60_000;
const WINDOW = 24 * HOUR; // Messenger standard messaging window

const num = (v, d) => (v === undefined || v === '' ? d : Number(v));
const price = (env) => num(env.PRICE, 129);
const bumpPrice = (env) => num(env.BUMP_PRICE, 49);
const upsellPrice = (env) => num(env.UPSELL_PRICE, 490);
const codes = (env) => (env.AFFILIATE_CODES || '').split(',').map((s) => s.trim().toUpperCase()).filter(Boolean);
// QR image per amount: explicit QR_URLS entry, else the PNG this Worker serves from public/qr/.
const qrFor = (env, amount) => {
  let url;
  try { url = JSON.parse(env.QR_URLS || '{}')[String(amount)]; } catch { url = undefined; }
  if (!url && env.PUBLIC_URL && env.QR_ENABLED === 'true') url = `${env.PUBLIC_URL.replace(/\/$/, '')}/qr/${amount}.png`;
  return url || undefined;
};

// PDF links: explicit FILE_*_URL, else the copy this Worker serves under public/<FILES_PATH>/.
const FILES = { ebook: ['FILE_EBOOK_URL', 'fanfarang-ebook.pdf'], cards: ['FILE_CARDS_URL', 'chat-cards.pdf'], lead: ['FILE_LEAD_URL', '10-sentences.pdf'] };
export const fileUrl = (env, key) => {
  const [v, name] = FILES[key];
  if (env[v]) return env[v];
  if (env.PUBLIC_URL && env.FILES_PATH) return `${env.PUBLIC_URL.replace(/\/$/, '')}/${env.FILES_PATH}/${name}`;
  return undefined;
};

// ---------- state (Workers KV) ----------
export async function load(env, psid) {
  const s = await env.STATE.get(`u:${psid}`, 'json');
  return s || { id: psid, stage: 'new', created: Date.now() };
}

export async function save(env, s) {
  // `next` in metadata lets the cron find due follow-ups without reading every value.
  await env.STATE.put(`u:${s.id}`, JSON.stringify(s), { metadata: { next: s.next || 0 } });
}

const basePrice = (env, s) => (s.offer99 ? 99 : s.codeDiscount ? price(env) - s.codeDiscount : price(env));

// ---------- intents ----------
const KEYWORDS = [
  [/คืนเงิน|โดนหลอก|ร้องเรียน|แอดมิน|admin|คุยกับคน/i, 'HUMAN'],
  [/^#?99$|ราคาพิเศษ 99/, 'OFFER99'],
  [/ประโยค/, 'LEAD'],
  [/ซื้อ|สั่ง|buy|โอน|จ่าย|ชำระ|เอาเล่ม|รับเล่ม/i, 'BUY'],
  [/ในเล่ม|มีอะไร|เนื้อหา|สารบัญ|ราคา|เท่าไหร่|กี่บาท/, 'INFO'],
  [/ภาษา|อังกฤษ|english/i, 'FAQ_LANG'],
  [/ตัวจริง|มิจฉา|หลอก|scam/i, 'FAQ_SCAM'],
  [/การันตี|รับประกัน|ได้แฟน/, 'FAQ_GUARANTEE'],
  [/คืน|refund/i, 'FAQ_REFUND'],
  [/แม่เลี้ยงเดี่ยว|อายุ|40|แก่/, 'FAQ_WHO'],
  [/ใครรู้|ความลับ|ส่วนตัว/, 'FAQ_PRIVACY'],
  [/ถาม|สงสัย|faq/i, 'FAQ'],
];

export function intentFromText(env, text) {
  const t = (text || '').trim();
  const upper = t.toUpperCase();
  if (codes(env).includes(upper)) return { intent: 'CODE', code: upper };
  for (const [re, intent] of KEYWORDS) if (re.test(t)) return { intent };
  return { intent: 'UNKNOWN' };
}

// ---------- actions ----------
async function welcome(env, s, name) {
  await sendTexts(env, s.id, M.welcome(name));
  await sendText(env, s.id, M.welcomeAsk, [QR.INFO, { ...QR.BUY, title: `💳 ซื้อเลย ${basePrice(env, s)}฿` }, QR.FAQ]);
  s.stage = s.stage === 'new' ? 'browsing' : s.stage;
}

async function info(env, s) {
  await sendTexts(env, s.id, M.info(basePrice(env, s)), [{ ...QR.BUY, title: `💳 ซื้อเลย ${basePrice(env, s)}฿` }, QR.FAQ]);
}

async function faqMenu(env, s) {
  await sendText(env, s.id, M.faqMenu, [QR.FAQ_LANG, QR.FAQ_GUARANTEE, QR.FAQ_PRIVACY, QR.FAQ_REFUND, QR.FAQ_WHO, QR.FAQ_SCAM, QR.HUMAN]);
}

async function faqAnswer(env, s, key) {
  await sendText(env, s.id, M.faq[key], [{ ...QR.BUY, title: `💳 ซื้อเลย ${basePrice(env, s)}฿` }, QR.FAQ]);
}

async function offerBump(env, s) {
  s.stage = 'await_bump';
  const p = basePrice(env, s);
  if (env.CARD_SAMPLE_URL) await sendImage(env, s.id, env.CARD_SAMPLE_URL);
  await sendTexts(env, s.id, M.bumpOffer(p), [
    { ...QR.BUMP_YES, title: `✅ เอาด้วย รวม ${p + bumpPrice(env)}฿` },
    { ...QR.BUMP_NO, title: `เอาแค่เล่ม ${p}฿` },
  ]);
}

async function askPayment(env, s, bump) {
  s.bump = bump;
  s.amount = basePrice(env, s) + (bump ? bumpPrice(env) : 0);
  s.stage = 'await_slip';
  s.followups = 0;
  s.next = Date.now() + HOUR;
  const qr = qrFor(env, s.amount);
  const [t1, t2] = M.pay(s.amount, env.PROMPTPAY_NAME, env.PROMPTPAY_ID, !!qr);
  await sendText(env, s.id, t1);
  if (qr) await sendImage(env, s.id, qr);
  await sendText(env, s.id, t2);
}

async function receiveSlip(env, s) {
  if (s.stage === 'upsell_slip') {
    s.stage = 'upsell_review';
    s.next = 0;
    await sendText(env, s.id, M.upsellReceived);
    return;
  }
  s.stage = 'slip_review';
  s.slipAt = Date.now();
  s.next = 0;
  if (env.AUTO_APPROVE_SLIPS === 'true') return deliver(env, s);
  await sendText(env, s.id, M.slipReceived);
}

export async function deliver(env, s) {
  await sendTexts(env, s.id, M.delivered(s.bump));
  await sendButton(env, s.id, '📘 แฟนฝรั่ง ไม่ต้องรอดวง (PDF)', 'ดาวน์โหลดเล่ม', fileUrl(env, 'ebook'));
  if (s.bump && fileUrl(env, 'cards')) await sendButton(env, s.id, '🃏 Chat Cards 100 ประโยค (PDF)', 'ดาวน์โหลดการ์ด', fileUrl(env, 'cards'));
  await sendText(env, s.id, M.howToStart);
  s.stage = 'paid';
  s.paidAt = Date.now();
  s.paidAmount = s.amount;
  s.next = Date.now() + 23 * HOUR; // upsell just inside the 24h window
  await sendPurchaseEvent(env, s.id, s.amount);
}

async function sendLead(env, s) {
  s.lead = true;
  await sendTexts(env, s.id, M.lead(fileUrl(env, 'lead')), [{ ...QR.BUY, title: `💳 รับเล่มเต็ม ${basePrice(env, s)}฿` }, QR.INFO]);
}

async function goHuman(env, s) {
  s.humanUntil = Date.now() + 12 * HOUR;
  await sendText(env, s.id, M.human);
}

async function upsellPay(env, s) {
  s.stage = 'upsell_slip';
  s.amount = upsellPrice(env);
  s.next = 0;
  const qr = qrFor(env, s.amount);
  const [t1, t2] = M.upsellPay(env.PROMPTPAY_ID, env.PROMPTPAY_NAME, !!qr);
  await sendText(env, s.id, t1);
  if (qr) await sendImage(env, s.id, qr);
  await sendText(env, s.id, t2);
}

// ---------- dispatcher for one intent ----------
async function handleIntent(env, s, intent, extra = {}) {
  switch (intent) {
    case 'GET_STARTED': return welcome(env, s, extra.name);
    case 'INFO': return info(env, s);
    case 'FAQ': return faqMenu(env, s);
    case 'BUY': return offerBump(env, s);
    case 'BUMP_YES': return askPayment(env, s, true);
    case 'BUMP_NO': return askPayment(env, s, false);
    case 'LEAD': return sendLead(env, s);
    case 'HUMAN': return goHuman(env, s);
    case 'UPSELL_YES': return upsellPay(env, s);
    case 'UPSELL_NO': s.next = 0; return sendText(env, s.id, M.upsellNo);
    case 'OFFER99':
      if (env.ALLOW_99 === 'true') { s.offer99 = true; await sendText(env, s.id, M.offer99Applied); return offerBump(env, s); }
      return sendText(env, s.id, M.fallback, [QR.INFO, QR.BUY, QR.HUMAN]);
    case 'CODE': {
      s.ref = s.ref || extra.code;
      s.codeDiscount = num(env.CODE_DISCOUNT, 10);
      await sendText(env, s.id, M.codeApplied(extra.code, basePrice(env, s)));
      return offerBump(env, s);
    }
    default:
      if (intent && intent.startsWith('FAQ_')) return faqAnswer(env, s, intent);
      if (s.stage === 'await_slip') return sendText(env, s.id, M.remindSlip, [QR.HUMAN]);
      return sendText(env, s.id, M.fallback, [QR.INFO, { ...QR.BUY, title: `💳 ซื้อเลย ${basePrice(env, s)}฿` }, QR.HUMAN]);
  }
}

// ---------- entry points ----------
export async function onMessagingEvent(env, ev) {
  const pageId = String(env.PAGE_ID || '');

  // Echo = a message sent by the Page (bot or human admin in the Inbox).
  if (ev.message && ev.message.is_echo) {
    const customer = ev.recipient.id;
    const text = (ev.message.text || '').trim().toLowerCase();
    const fromOurApp = env.APP_ID && String(ev.message.app_id || '') === String(env.APP_ID);
    if (fromOurApp) return;
    const s = await load(env, customer);
    if (text === '#ok') {
      if (s.stage === 'upsell_review' || s.stage === 'upsell_slip') { s.stage = 'upsell_paid'; await sendPurchaseEvent(env, customer, upsellPrice(env)); }
      else await deliver(env, s);
      s.humanUntil = 0;
    } else if (text === '#no') {
      s.stage = 'await_slip'; s.humanUntil = 0;
      await sendText(env, customer, M.slipRejected, [QR.HUMAN]);
    } else if (text === '#bot') {
      s.humanUntil = 0;
    } else if (text === '#99') {
      s.offer99 = true; s.humanUntil = 0;
      await sendText(env, customer, M.offer99Applied); await offerBump(env, s);
    } else {
      // A human admin replied manually: let them handle the chat for 30 minutes.
      s.humanUntil = Date.now() + 30 * MIN;
    }
    return save(env, s);
  }

  const psid = ev.sender && ev.sender.id;
  if (!psid || psid === pageId) return;
  const s = await load(env, psid);
  s.lastIn = Date.now();

  const ref = (ev.referral && ev.referral.ref) || (ev.postback && ev.postback.referral && ev.postback.referral.ref);
  if (ref && !s.ref) s.ref = String(ref).toUpperCase();

  // Paused for a human, except for slips and explicit buttons the customer taps.
  const paused = s.humanUntil && s.humanUntil > Date.now();

  if (ev.message && ev.message.attachments && ev.message.attachments.some((a) => a.type === 'image') && !ev.message.sticker_id) {
    if (['await_slip', 'await_bump', 'browsing', 'slip_review', 'upsell_slip', 'new'].includes(s.stage)) {
      if (!s.amount) s.amount = basePrice(env, s);
      await receiveSlip(env, s);
    }
    return save(env, s);
  }

  let intent; let extra = {};
  if (ev.postback) intent = ev.postback.payload;
  else if (ev.message && ev.message.quick_reply) intent = ev.message.quick_reply.payload;
  else if (ev.referral) intent = s.stage === 'new' ? 'GET_STARTED' : null;
  else if (ev.message && ev.message.text) ({ intent, ...extra } = intentFromText(env, ev.message.text));

  if (!intent) return save(env, s);
  if (paused && !(ev.postback || (ev.message && ev.message.quick_reply)) && intent !== 'HUMAN') return save(env, s);
  if (s.stage === 'new' && !['GET_STARTED', 'LEAD', 'CODE', 'OFFER99', 'HUMAN'].includes(intent)) {
    await welcome(env, s);
    if (intent === 'UNKNOWN') return save(env, s);
  }
  await handleIntent(env, s, intent, extra);
  return save(env, s);
}

// Comment containing the keyword -> private reply with the lead magnet.
export async function onFeedChange(env, change) {
  const v = change.value || {};
  if (change.field !== 'feed' || v.item !== 'comment' || v.verb !== 'add') return;
  if (!v.from || String(v.from.id) === String(env.PAGE_ID)) return;
  const kw = env.COMMENT_KEYWORD || 'ประโยค';
  if (!(v.message || '').includes(kw)) return;
  const [t1, url, t3] = M.lead(fileUrl(env, 'lead'));
  await privateReply(env, v.comment_id, `${t1}\n${url}\n\n${t3}`, [QR.BUY, QR.INFO]);
  if (env.PUBLIC_COMMENT_REPLY !== 'false') await publicCommentReply(env, v.comment_id, M.commentPublicReply);
}

// Cron: follow-ups for unpaid chats and the post-purchase upsell, all inside 24h.
export async function runFollowups(env, now = Date.now()) {
  let cursor; let sent = 0;
  do {
    const page = await env.STATE.list({ prefix: 'u:', cursor });
    for (const k of page.keys) {
      const next = (k.metadata && k.metadata.next) || 0;
      if (!next || next > now) continue;
      const s = await env.STATE.get(k.name, 'json');
      if (!s) continue;
      const inWindow = s.lastIn && now - s.lastIn < WINDOW - 10 * MIN;
      const paused = s.humanUntil && s.humanUntil > now;
      if (!inWindow) { s.next = 0; await save(env, s); continue; }
      if (paused) { s.next = s.humanUntil + MIN; await save(env, s); continue; }

      if (s.stage === 'await_slip') {
        s.followups = (s.followups || 0) + 1;
        if (s.followups === 1) { await sendText(env, s.id, M.followup1, [QR.HUMAN]); s.next = s.lastIn + 3 * HOUR; }
        else if (s.followups === 2) { await sendText(env, s.id, M.followup2); s.next = s.lastIn + 22 * HOUR; }
        else { await sendText(env, s.id, M.followup3, [QR.HUMAN]); s.next = 0; }
        sent++;
      } else if (s.stage === 'paid' && !s.upsellSent) {
        await sendTexts(env, s.id, M.upsell, [QR.UPSELL_YES, QR.UPSELL_NO]);
        s.upsellSent = true; s.next = 0; sent++;
      } else {
        s.next = 0;
      }
      await save(env, s);
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return sent;
}
