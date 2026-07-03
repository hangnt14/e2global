/**
 * evidence-index-builder.js
 * Generates evidence-index.md — the agent-facing index file.
 * Session AI reads this FIRST during synthesis to get a full picture
 * without reading 30+ individual DOM/screenshot files.
 */

import fs from 'fs';
import path from 'path';
import { createReadStream } from 'fs';
import { createInterface } from 'readline';

/**
 * H2: Sanitize a value for safe inclusion in a markdown table cell.
 * Strips pipe characters, newlines, and trims to max length.
 * @param {string} val
 * @param {number} maxLen
 * @returns {string}
 */
function mdSafe(val, maxLen = 80) {
  if (val === null || val === undefined) return '';
  return String(val)
    .replace(/[|\r\n]/g, ' ')
    .trim()
    .slice(0, maxLen);
}

/**
 * Build evidence-index.md from crawl output.
 * @param {string} evidenceDir - path to evidence/ folder
 * @param {string} sourceUrl - original crawl URL
 * @param {string} timestamp - crawl timestamp ISO string
 */
export async function buildEvidenceIndex(evidenceDir, sourceUrl, timestamp) {
  const sitemapPath = path.join(evidenceDir, 'sitemap.json');
  const networkPath = path.join(evidenceDir, 'network.ndjson');
  const domDir = path.join(evidenceDir, 'dom');

  // Load sitemap
  let sitemap = { pages: [], edges: [] };
  try {
    sitemap = JSON.parse(fs.readFileSync(sitemapPath, 'utf8'));
  } catch { /* no sitemap yet */ }

  // Load DOM snapshots
  const domData = {};
  if (fs.existsSync(domDir)) {
    for (const file of fs.readdirSync(domDir)) {
      if (!file.endsWith('.json')) continue;
      try {
        const dom = JSON.parse(fs.readFileSync(path.join(domDir, file), 'utf8'));
        domData[dom.url] = dom;
      } catch { /* skip corrupt file */ }
    }
  }

  // Load network entries
  const networkEntries = await readNdjson(networkPath);

  // Deduplicate endpoints by method + URL pattern (strip IDs)
  const endpointMap = new Map();
  for (const entry of networkEntries) {
    try {
      const u = new URL(entry.url);
      // Normalize path: replace numeric segments with :id
      const pattern = u.pathname.replace(/\/\d+/g, '/:id');
      const key = `${entry.method}:${pattern}`;
      if (!endpointMap.has(key)) {
        endpointMap.set(key, {
          method: entry.method,
          urlPattern: pattern,
          status: entry.status,
          contentType: entry.contentType,
          bodyShape: entry.bodyShape,
        });
      }
    } catch { /* skip invalid URL */ }
  }

  // Count screenshots
  const screenshotsDir = path.join(evidenceDir, 'screenshots');
  const screenshotCount = fs.existsSync(screenshotsDir)
    ? fs.readdirSync(screenshotsDir).filter((f) => f.endsWith('.png')).length
    : 0;

  // Build markdown
  const lines = [];
  lines.push('# Evidence Index');
  lines.push('');
  lines.push(`Source: ${sourceUrl}`);
  lines.push(`Crawled: ${timestamp}`);
  lines.push(`Pages: ${sitemap.pages.length} | Screenshots: ${screenshotCount} | API endpoints: ${endpointMap.size}`);
  lines.push('');

  // Pages table
  lines.push('## Pages');
  lines.push('');
  lines.push('| # | URL | Title | Has Forms | Has Tables | Screenshot |');
  lines.push('|---|-----|-------|-----------|------------|------------|');
  for (let i = 0; i < sitemap.pages.length; i++) {
    const page = sitemap.pages[i];
    const dom = domData[page.url];
    const hasForms = dom?.forms?.length > 0 ? `Yes (${dom.forms.length})` : 'No';
    const hasTables = dom?.tables?.length > 0 ? `Yes (${dom.tables.length})` : 'No';
    const screenshot = mdSafe(page.screenshotPath || '');
    const urlPath = mdSafe((() => { try { return new URL(page.url).pathname; } catch { return page.url; } })());
    const title = mdSafe(page.title || '');
    lines.push(`| ${i + 1} | ${urlPath} | ${title} | ${hasForms} | ${hasTables} | ${screenshot} |`);
  }
  lines.push('');

  // API endpoints table
  lines.push('## API Endpoints Observed');
  lines.push('');
  if (endpointMap.size > 0) {
    lines.push('| Method | URL Pattern | Status | Response Shape |');
    lines.push('|--------|-------------|--------|----------------|');
    for (const ep of endpointMap.values()) {
      const shape = ep.bodyShape ? mdSafe(JSON.stringify(ep.bodyShape)) : '-';
      lines.push(`| ${mdSafe(ep.method)} | ${mdSafe(ep.urlPattern)} | ${ep.status} | ${shape} |`);
    }
  } else {
    lines.push('_No API endpoints captured._');
  }
  lines.push('');

  // Forms table
  const allForms = [];
  for (const page of sitemap.pages) {
    const dom = domData[page.url];
    if (dom?.forms?.length) {
      const urlPath = (() => { try { return new URL(page.url).pathname; } catch { return page.url; } })();
      for (const form of dom.forms) {
        const fields = form.inputs
          .map((i) => `${i.name} (${i.type}${i.required ? ', required' : ''})`)
          .join(', ');
        allForms.push({ page: urlPath, action: form.action, method: form.method, fields });
      }
    }
  }

  lines.push('## Forms Detected');
  lines.push('');
  if (allForms.length > 0) {
    lines.push('| Page | Action | Method | Fields |');
    lines.push('|------|--------|--------|--------|');
    for (const f of allForms) {
      lines.push(`| ${mdSafe(f.page)} | ${mdSafe(f.action)} | ${mdSafe(f.method)} | ${mdSafe(f.fields)} |`);
    }
  } else {
    lines.push('_No forms detected._');
  }
  lines.push('');

  // Navigation structure
  lines.push('## Navigation Structure');
  lines.push('');
  const byDepth = {};
  for (const page of sitemap.pages) {
    const d = page.depth ?? 0;
    if (!byDepth[d]) byDepth[d] = [];
    const urlPath = (() => { try { return new URL(page.url).pathname; } catch { return page.url; } })();
    byDepth[d].push(urlPath);
  }
  for (const [depth, urls] of Object.entries(byDepth).sort((a, b) => a[0] - b[0])) {
    const label = depth === '0' ? 'Entry' : `Depth ${depth}`;
    lines.push(`${label}: ${urls.join(', ')}`);
  }
  lines.push('');

  const outputPath = path.join(evidenceDir, 'evidence-index.md');
  // M6: atomic write via tmp + rename (consistent with sitemap-builder)
  const tmpPath = outputPath + '.tmp';
  fs.writeFileSync(tmpPath, lines.join('\n'), 'utf8');
  fs.renameSync(tmpPath, outputPath);
  return outputPath;
}

/**
 * Read an NDJSON file line by line.
 * @param {string} filePath
 * @returns {Promise<object[]>}
 */
async function readNdjson(filePath) {
  const entries = [];
  if (!fs.existsSync(filePath)) return entries;
  const rl = createInterface({ input: createReadStream(filePath), crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    try { entries.push(JSON.parse(line)); } catch { /* skip corrupt line */ }
  }
  return entries;
}
