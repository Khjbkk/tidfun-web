// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

import cloudflare from '@astrojs/cloudflare';

// tidfun.org — primary canonical (ASCII). Brand "ติดฝัน" lives in content.
// ติดฝัน.com (xn--l3cbnp4hpa.com) is 301-redirected to tidfun.org via Cloudflare Bulk Redirect.
const SITE_URL = process.env.SITE_URL || 'https://tidfun.org';

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
