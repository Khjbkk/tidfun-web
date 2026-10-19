// Cloudflare Worker entry: Messenger webhook + cron follow-ups.
import { verifySignature } from './fb.js';
import { onMessagingEvent, onFeedChange, runFollowups } from './flow.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/health') return new Response('ok');
    if (url.pathname !== '/webhook') return new Response('not found', { status: 404 });

    if (request.method === 'GET') {
      const ok = url.searchParams.get('hub.mode') === 'subscribe'
        && url.searchParams.get('hub.verify_token') === env.VERIFY_TOKEN;
      return ok ? new Response(url.searchParams.get('hub.challenge')) : new Response('forbidden', { status: 403 });
    }

    if (request.method !== 'POST') return new Response('method not allowed', { status: 405 });
    const raw = await request.text();
    if (!(await verifySignature(env, raw, request.headers.get('x-hub-signature-256')))) {
      return new Response('bad signature', { status: 401 });
    }
    const body = JSON.parse(raw);
    if (body.object !== 'page') return new Response('ignored');

    // Reply 200 fast; process in the background so Meta does not retry.
    ctx.waitUntil((async () => {
      for (const entry of body.entry || []) {
        for (const ev of entry.messaging || []) {
          try { await onMessagingEvent(env, ev); } catch (e) { console.error('messaging', e); }
        }
        for (const ch of entry.changes || []) {
          try { await onFeedChange(env, ch); } catch (e) { console.error('feed', e); }
        }
      }
    })());
    return new Response('EVENT_RECEIVED');
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(runFollowups(env).then((n) => console.log('followups sent', n)));
  },
};
