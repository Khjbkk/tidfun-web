# ติดฝัน (TidFun) — Directory ติวเตอร์-สถาบันกวดวิชา

Directory แห่งสถาบันกวดวิชาและติวเตอร์ทั่วประเทศไทย เตรียมสอบเข้า ป.1 ม.1 ม.4 และมหาวิทยาลัย ดำเนินงานโดย **บริษัท ซิโอร่า จำกัด**

**Production:** https://xn--l3cbnp4hpa.com (ติดฝัน.com — Thai IDN)

## Stack

- Astro 5 (Static Site Generation)
- Cloudflare Pages (hosting)
- Cloudflare Workers (adapter)
- Tailwind CSS v4
- TypeScript strict + Zod schemas for anti-thin content gates

## Architecture

Built following the Bigfoot Blueprint directory model.

```
src/
├── content/
│   ├── listings/         # Markdown listings (L1-L5 enriched schema)
│   └── pillars/          # Long-form SEO articles (planned)
├── data/
│   ├── categories.json   # por1, mor1, mor4, uni
│   ├── cities.json       # Bangkok, Chiangmai, etc.
│   ├── schools.json      # Target schools for /for-school/ pages
│   └── subjects.json     # math, science, english, etc.
├── pages/
│   ├── index.astro       # Home (search + categories + Trojan Horse)
│   ├── listing/[slug]    # Individual listing pages
│   ├── category/[slug]   # 4 category pages
│   ├── for-school/[slug] # 7 target-school pages
│   ├── city/[city]       # 8 city pages
│   ├── subject/[slug]    # 13 subject pages
│   ├── search.astro      # Client-side filter
│   └── tool/find-my-tutor # 5-step quiz → search
└── content.config.ts     # Zod schemas with anti-thin gates
```

## Data Pipeline (WAT framework)

```
tools/source_listings.py   # Apify / Google Places / Outscraper wrapper
tools/enrich_listing.py    # OpenAI L3 enrichment (description, speakable, FAQ)
tools/validate_listings.py # Anti-thin gate validator (pre-commit)
tools/submit_indexnow.sh   # Push new URLs to Bing/Yandex IndexNow
```

Requires environment variables (do NOT commit):

- `OPENAI_API_KEY` — for enrichment (platform.openai.com/api-keys)
- `GOOGLE_PLACES_KEY` — for Google Maps scrape (console.cloud.google.com)
- `APIFY_TOKEN` — for Facebook / multi-source scrape (console.apify.com)

## Development

```sh
npm install
npm run dev          # Astro dev server at localhost:4321
npm run build        # Static build + pagefind index
npm run preview      # Local preview via wrangler
```

## Deploy

Connected to Cloudflare Pages — push to `main` triggers deploy.

```sh
npm run deploy       # Manual wrangler deploy (fallback)
```

## Operator

ดำเนินงานโดย **บริษัท ซิโอร่า จำกัด** ภายใต้พระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล (PDPA)

Previous SheetSmith codebase preserved at branch `archive/sheetsmith`.
