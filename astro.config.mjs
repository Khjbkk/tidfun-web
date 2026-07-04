// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

import cloudflare from '@astrojs/cloudflare';

// tidfun.org — primary canonical (ASCII). Brand "ติดฝัน" lives in content.
// ติดฝัน.com (xn--l3cbnp4hpa.com) is 301-redirected to tidfun.org via Cloudflare Bulk Redirect.
const SITE_URL = process.env.SITE_URL || 'https://tidfun.org';

// @astrojs/sitemap intentionally NOT registered — the source of truth is
// src/pages/sitemap-*.xml.ts (custom sitemap-tidfun.xml + 3 sub-sitemaps).
// Running both produced two sitemap trees with the same URLs in slightly
// different formats, which Google reported as "Alternate page with proper
// canonical tag".

export default defineConfig({
  site: SITE_URL,
  trailingSlash: 'always',

  vite: {
    plugins: [tailwindcss()],
  },

  markdown: {
    shikiConfig: { theme: 'github-light' },
  },

  adapter: cloudflare(),
});
