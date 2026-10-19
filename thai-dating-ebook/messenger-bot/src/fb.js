// Thin wrappers around the Messenger Send API, Conversions API and webhook signature check.

const graph = (env) => `https://graph.facebook.com/${env.GRAPH_VERSION || 'v24.0'}`;

export async function verifySignature(env, rawBody, header) {
  if (!env.APP_SECRET) return true; // allow local testing without a secret
  if (!header || !header.startsWith('sha256=')) return false;
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(env.APP_SECRET),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(rawBody));
  const hex = [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('');
  const given = header.slice(7);
  if (given.length !== hex.length) return false;
  let diff = 0;
  for (let i = 0; i < hex.length; i++) diff |= hex.charCodeAt(i) ^ given.charCodeAt(i);
  return diff === 0;
}

async function post(env, path, body, token) {
  try {
    const res = await fetch(`${graph(env)}${path}?access_token=${encodeURIComponent(token || env.PAGE_ACCESS_TOKEN)}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) console.error('graph error', path, res.status, await res.text());
    return res;
  } catch (e) {
    // Network failure must not stop the flow from saving the customer's state.
    console.error('graph unreachable', path, e.message);
    return null;
  }
}

const withQuickReplies = (text, replies) => (replies && replies.length
  ? { text, quick_replies: replies.map((r) => ({ content_type: 'text', title: r.title, payload: r.payload })) }
  : { text });

export async function sendText(env, psid, text, replies) {
  return post(env, '/me/messages', { recipient: { id: psid }, messaging_type: 'RESPONSE', message: withQuickReplies(text, replies) });
}

// Send several bubbles; quick replies attach to the last one only.
export async function sendTexts(env, psid, texts, replies) {
  for (let i = 0; i < texts.length; i++) {
    await sendText(env, psid, texts[i], i === texts.length - 1 ? replies : undefined);
  }
}

export async function sendImage(env, psid, url) {
  return post(env, '/me/messages', {
    recipient: { id: psid }, messaging_type: 'RESPONSE',
    message: { attachment: { type: 'image', payload: { url, is_reusable: true } } },
  });
}

export async function sendButton(env, psid, text, title, url) {
  return post(env, '/me/messages', {
    recipient: { id: psid }, messaging_type: 'RESPONSE',
    message: { attachment: { type: 'template', payload: { template_type: 'button', text, buttons: [{ type: 'web_url', url, title }] } } },
  });
}

// Private reply to a Page comment (opens a Messenger thread with the commenter).
export async function privateReply(env, commentId, text, replies) {
  return post(env, '/me/messages', { recipient: { comment_id: commentId }, message: withQuickReplies(text, replies) });
}

export async function publicCommentReply(env, commentId, text) {
  return post(env, `/${commentId}/comments`, { message: text });
}

// Conversions API for business messaging: tells Meta which chat bought, so the
// "purchase through messaging" ad set can optimise for buyers.
export async function sendPurchaseEvent(env, psid, value) {
  if (!env.DATASET_ID) return;
  return post(env, `/${env.DATASET_ID}/events`, {
    data: [{
      event_name: 'Purchase',
      event_time: Math.floor(Date.now() / 1000),
      action_source: 'business_messaging',
      messaging_channel: 'messenger',
      user_data: { page_id: env.PAGE_ID, page_scoped_user_id: psid },
      custom_data: { currency: 'THB', value },
    }],
  }, env.CAPI_TOKEN || env.PAGE_ACCESS_TOKEN);
}

export async function setMessengerProfile(env, profile) {
  return post(env, '/me/messenger_profile', profile);
}
