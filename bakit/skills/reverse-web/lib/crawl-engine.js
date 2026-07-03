/**
 * crawl-engine.js
 * BFS crawler orchestrator. Coordinates Playwright, guardrails,
 * DOM extraction, network capture, sitemap building, and evidence index.
 */

import fs from 'fs';
import path from 'path';
import { chromium } from 'playwright';
import { assertConsent, validateOutputPath, checkPageLimit, GuardrailViolation } from './guardrails.js';
import { attachNetworkListener } from './network-listener.js';
import { extractDOM } from './dom-extractor.js';
import { waitForStability } from './wait-strategy.js';
import { SitemapBuilder } from './sitemap-builder.js';
import { fetchAndParse, isAllowed } from './robots-parser.js';
import { buildEvidenceIndex } from './evidence-index-builder.js';

/**
 * Normalize a URL for deduplication: remove trailing slash, sort query params.
 * @param {string} url
 * @returns {string}
 */
function normalizeUrl(url) {
  try {
    const u = new URL(url);
    u.hash = '';
    // Sort query params for deduplication
    u.searchParams.sort();
    return u.toString().replace(/\/$/, '');
  } catch {
    return url;
  }
}

/**
 * Convert a URL to a filesystem-safe slug.
 * @param {string} url
 * @returns {string}
 */
function urlToSlug(url) {
  try {
    const u = new URL(url);
    const slug = (u.pathname + u.search)
      .replace(/[^a-zA-Z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 60);
    return slug || 'root';
  } catch {
    return 'page';
  }
}

/**
 * Main crawl function.
 * @param {string} startUrl
 * @param {object} options
 */
export async function crawl(startUrl, options = {}) {
  const {
    consent = false,
    maxPages = 30,
    maxDepth = 3,
    delay = 1000,
    timeout = 15000,
    stabilityTimeout = 5000,
    output = './evidence',
    ignoreRobots = false,
    continueMode = false,
  } = options;

  // G1: consent check
  assertConsent({ consent });

  // G6: path containment
  validateOutputPath(output, process.cwd());

  // Validate start URL early with user-friendly error
  let origin;
  try {
    origin = new URL(startUrl).origin;
  } catch {
    throw new Error(`Invalid URL: "${startUrl}". Provide a full URL including protocol (e.g. https://example.com)`);
  }

  const evidenceDir = path.resolve(output);
  const screenshotsDir = path.join(evidenceDir, 'screenshots');
  const domDir = path.join(evidenceDir, 'dom');
  const networkPath = path.join(evidenceDir, 'network.ndjson');
  const sitemapPath = path.join(evidenceDir, 'sitemap.json');
  const manifestPath = path.join(evidenceDir, 'manifest.json');

  // Create directory structure
  fs.mkdirSync(screenshotsDir, { recursive: true });
  fs.mkdirSync(domDir, { recursive: true });

  // Load existing sitemap for --continue mode
  let existingData = null;
  if (continueMode) {
    existingData = SitemapBuilder.loadExisting(sitemapPath);
  }

  const sitemap = new SitemapBuilder(sitemapPath, existingData);
  const visitedUrls = continueMode ? sitemap.getVisitedUrls() : new Set();

  // Parse origin for robots.txt and same-origin filtering (already validated above)

  // G7: fetch robots.txt
  let robotsRules = { disallow: [] };
  if (!ignoreRobots) {
    robotsRules = await fetchAndParse(origin);
  }

  // Write initial manifest
  const crawlStart = new Date().toISOString();
  const writeManifest = (status, stoppedReason = null) => {
    const manifest = {
      url: startUrl,
      origin,
      timestamp: crawlStart,
      completedAt: new Date().toISOString(),
      config: { maxPages, maxDepth, delay, timeout, ignoreRobots, continueMode },
      pagesVisited: sitemap.pageCount,
      status,
      stoppedReason,
      continued: continueMode,
    };
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');
  };

  let browser;
  let pageCounter = 0; // always per-run count; --continue adds to existing pages via sitemap
  let rateLimitHit = null; // signal from network listener (C1 fix)

  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (compatible; BA-kit-reverse-web/1.0)',
    });
    const page = await context.newPage();

    // Attach passive network listener — signals rate limit via shared flag (C1 fix)
    attachNetworkListener(page, networkPath, {
      onRateLimit: (status) => { rateLimitHit = status; },
    });

    // BFS queue: [{url, depth}]
    const queue = [{ url: normalizeUrl(startUrl), depth: 0 }];
    // Seed queued from visitedUrls in --continue mode (M2 fix)
    const queued = new Set([...visitedUrls, normalizeUrl(startUrl)]);

    while (queue.length > 0) {
      const { url, depth } = queue.shift();

      // Skip already-visited (continue mode)
      if (visitedUrls.has(url)) continue;

      // G7: robots check
      if (!ignoreRobots && !isAllowed(url, robotsRules)) {
        console.log(`  [robots] Skipping: ${url}`);
        continue;
      }

      // G3: page limit check
      checkPageLimit(pageCounter, maxPages);

      // C1: check rate limit signal from network listener
      if (rateLimitHit) {
        throw new GuardrailViolation(
          `Rate limited (HTTP ${rateLimitHit}). The site is throttling requests.`,
          `G5_${rateLimitHit}`
        );
      }

      console.log(`  [${pageCounter + 1}/${maxPages}] Crawling: ${url}`);

      // Navigate
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout });
      } catch (err) {
        console.warn(`  [warn] Navigation failed for ${url}: ${err.message}`);
        continue;
      }

      // Wait for stability
      await waitForStability(page, { stabilityTimeout, quietMs: 1000 });

      // Screenshot
      const slug = urlToSlug(url);
      const screenshotFile = `${String(pageCounter + 1).padStart(3, '0')}-${slug}.png`;
      const screenshotPath = path.join(screenshotsDir, screenshotFile);
      try {
        await page.screenshot({ path: screenshotPath, fullPage: true });
      } catch (err) {
        console.warn(`  [warn] Screenshot failed for ${url}: ${err.message}`);
      }

      // DOM extraction
      let domSnapshot = null;
      try {
        domSnapshot = await extractDOM(page);
        const domFile = `${String(pageCounter + 1).padStart(3, '0')}-${slug}.json`;
        fs.writeFileSync(path.join(domDir, domFile), JSON.stringify(domSnapshot, null, 2), 'utf8');
      } catch (err) {
        console.warn(`  [warn] DOM extraction failed for ${url}: ${err.message}`);
      }

      // Add to sitemap
      const relativeScreenshot = path.join('screenshots', screenshotFile);
      sitemap.addPage(url, domSnapshot?.title || '', depth, relativeScreenshot);
      visitedUrls.add(url);
      pageCounter++;

      // Extract same-origin links and enqueue
      if (depth < maxDepth && domSnapshot?.links) {
        for (const link of domSnapshot.links) {
          try {
            const linkUrl = normalizeUrl(link.href);
            const linkOrigin = new URL(linkUrl).origin;
            if (linkOrigin !== origin) continue;
            if (visitedUrls.has(linkUrl) || queued.has(linkUrl)) continue;
            sitemap.addEdge(url, linkUrl);
            queue.push({ url: linkUrl, depth: depth + 1 });
            queued.add(linkUrl);
          } catch { /* invalid URL — skip */ }
        }
      }

      // Delay between requests
      if (queue.length > 0 && delay > 0) {
        await new Promise((r) => setTimeout(r, delay));
      }
    }

    // Final flush and manifest
    sitemap.flush();
    writeManifest('complete');
    console.log(`\n✓ Crawl complete: ${pageCounter} pages captured`);

  } catch (err) {
    // Flush whatever we have
    try { sitemap.flush(); } catch { /* ignore */ }

    if (err instanceof GuardrailViolation) {
      writeManifest('stopped', err.code);
      throw err; // re-throw for CLI to handle
    }

    writeManifest('error', err.message);
    throw err;
  } finally {
    if (browser) {
      try { await browser.close(); } catch { /* ignore */ }
    }
    // C8: generate evidence index in finally so it runs even on early stop
    try {
      await buildEvidenceIndex(evidenceDir, startUrl, crawlStart);
      console.log(`✓ Evidence index written: ${path.join(output, 'evidence-index.md')}`);
    } catch (err) {
      console.warn(`[warn] Evidence index generation failed: ${err.message}`);
    }
  }
}
