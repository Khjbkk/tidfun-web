// Run the same bot on your own computer (no Cloudflare): node local/server.mjs
// Reads .env, keeps chat state in data/state.json, serves public/ and runs follow-ups every 10 min.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import worker from '../src/index.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function loadEnvFile(file) {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (!m) continue;
    let v = m[2].replace(/\s+#.*$/, '');
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    out[m[1]] = v;
  }
  return out;
}

// Minimal Workers-KV look-alike persisted to a JSON file.
function fileKV(file) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  let data = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {};
  let timer;
  const flush = () => { clearTimeout(timer); timer = setTimeout(() => fs.writeFileSync(file, JSON.stringify(data)), 200); };
  return {
    async get(k, type) { const v = data[k]; if (!v) return null; return type === 'json' ? JSON.parse(v.value) : v.value; },
    async put(k, value, opts = {}) { data[k] = { value, metadata: opts.metadata }; flush(); },
    async list({ prefix }) {
      return { keys: Object.entries(data).filter(([k]) => k.startsWith(prefix)).map(([name, v]) => ({ name, metadata: v.metadata })), list_complete: true };
    },
  };
}

const env = { ...loadEnvFile(path.join(root, '.env')), ...process.env };
env.STATE = fileKV(path.join(root, 'data', 'state.json'));
const PORT = Number(env.PORT || 8787);

const MIME = { '.png': 'image/png', '.pdf': 'application/pdf', '.jpg': 'image/jpeg' };

function serveStatic(urlPath, res) {
  const file = path.normalize(path.join(root, 'public', decodeURIComponent(urlPath)));
  if (!file.startsWith(path.join(root, 'public')) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return false;
  res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
  return true;
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    if (req.method === 'GET' && serveStatic(url.pathname, res)) return;
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const body = chunks.length ? Buffer.concat(chunks) : undefined;
    const request = new Request(url, { method: req.method, headers: req.headers, body: ['GET', 'HEAD'].includes(req.method) ? undefined : body });
    const waits = [];
    const response = await worker.fetch(request, env, { waitUntil: (p) => waits.push(p) });
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
    await Promise.allSettled(waits);
  } catch (e) {
    console.error(e);
    if (!res.headersSent) res.writeHead(500);
    res.end('error');
  }
});

server.listen(PORT, () => {
  console.log(`Bot running on http://localhost:${PORT}  (webhook: /webhook, health: /health)`);
  if (!env.PAGE_ACCESS_TOKEN) console.warn('⚠️  PAGE_ACCESS_TOKEN is missing in .env');
  if (!env.PUBLIC_URL) console.warn('⚠️  PUBLIC_URL is empty: set it to your tunnel URL so QR images and PDF links work');
});

// Follow-ups / upsell every 10 minutes (same as the Cloudflare cron).
setInterval(() => {
  worker.scheduled({}, env, { waitUntil: (p) => p.catch((e) => console.error('cron', e)) });
}, 10 * 60_000);
