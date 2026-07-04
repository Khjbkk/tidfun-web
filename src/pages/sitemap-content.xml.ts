import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import bestOf from '../data/best_of.json';

export const GET: APIRoute = async ({ site }) => {
  const pillars = await getCollection('pillars');
  const listings = await getCollection('listings');

  const now = new Date().toISOString();
  // Site-level lastmod = most-recently-updated listing (fresh content signal)
  const siteLatest = listings.reduce<Date>((acc, l) => {
    const d = (l.data.date_updated || l.data.date_listed) as Date;
    return d > acc ? d : acc;
  }, new Date(0)).toISOString();

  const urls: { loc: string; lastmod: string; priority: number }[] = [
    { loc: `${site}`, lastmod: siteLatest, priority: 1.0 },
    // /search/ is noindex,nofollow — must not appear in sitemap. Its previous
    // listing (without trailing slash, no less) caused Google to flag it as
    // "Alternate page with proper canonical" against the canonical /search/.
    { loc: `${site}tool/find-my-tutor/`, lastmod: now, priority: 0.9 },
    { loc: `${site}about/`, lastmod: now, priority: 0.5 },
    { loc: `${site}privacy/`, lastmod: now, priority: 0.3 },
    { loc: `${site}terms/`, lastmod: now, priority: 0.3 },
    { loc: `${site}contact/`, lastmod: now, priority: 0.5 },
    { loc: `${site}claim/`, lastmod: now, priority: 0.6 },
    { loc: `${site}editorial-standards/`, lastmod: now, priority: 0.4 },
  ];

  pillars.forEach(p => urls.push({
    loc: `${site}pillars/${p.id}/`,
    lastmod: (p.data.updatedDate || p.data.publishDate).toISOString(),
    priority: 0.9,
  }));

  bestOf.forEach(b => urls.push({
    loc: `${site}best-of/${b.id}/`,
    lastmod: siteLatest,
    priority: 0.8,
  }));

  // VS pages — must match the filter in src/pages/vs/[combo].astro
  const MAX_VS_PER_LISTING = 6;
  const counts = new Map<string, number>();
  for (let i = 0; i < listings.length; i++) {
    for (let j = i + 1; j < listings.length; j++) {
      const a = listings[i];
      const b = listings[j];
      const shared = a.data.categories.find(c => b.data.categories.includes(c));
      if (!shared) continue;
      const sameCity = a.data.city === b.data.city;
      const sharedSchool = a.data.target_schools.some(s => b.data.target_schools.includes(s));
      if (!sameCity && !sharedSchool) continue;
      if (a.data.type !== b.data.type) continue;
      if ((counts.get(a.id) || 0) >= MAX_VS_PER_LISTING) continue;
      if ((counts.get(b.id) || 0) >= MAX_VS_PER_LISTING) continue;
      counts.set(a.id, (counts.get(a.id) || 0) + 1);
      counts.set(b.id, (counts.get(b.id) || 0) + 1);
      const [first, second] = a.id < b.id ? [a, b] : [b, a];
      urls.push({
        loc: `${site}vs/${first.id}-vs-${second.id}/`,
        lastmod: now,
        priority: 0.6,
      });
    }
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url><loc>${u.loc}</loc><lastmod>${u.lastmod}</lastmod><priority>${u.priority}</priority></url>`).join('\n')}
</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
