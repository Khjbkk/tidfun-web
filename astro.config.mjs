// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

import cloudflare from '@astrojs/cloudflare';

// ติดฝัน.com (Thai IDN) — Punycode: xn--l3cbnp4hpa.com
const SITE_URL = process.env.SITE_URL || 'https://xn--l3cbnp4hpa.com';

export default defineConfig({
  site: SITE_URL,

  integrations: [
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
      lastmod: new Date(),
    }),
  ],

  vite: {
    plugins: [tailwindcss()],
  },

  markdown: {
    shikiConfig: { theme: 'github-light' },
  },

  adapter: cloudflare(),
});
