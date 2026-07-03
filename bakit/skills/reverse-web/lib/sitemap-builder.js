/**
 * sitemap-builder.js
 * Incrementally builds sitemap.json during crawl.
 * Flushes to disk every 10 pages for crash safety.
 * In --continue mode, merges with existing sitemap.
 */

import fs from 'fs';
import path from 'path';

const FLUSH_INTERVAL = 10;

export class SitemapBuilder {
  constructor(outputPath, existingData = null) {
    this.outputPath = outputPath;
    this.pages = existingData?.pages ? [...existingData.pages] : [];
    this.edges = existingData?.edges ? [...existingData.edges] : [];
    this.pagesSinceFlush = 0;
    // Track existing URLs for deduplication
    this.existingUrls = new Set(this.pages.map((p) => p.url));
  }

  /**
   * Add a page to the sitemap.
   * @param {string} url
   * @param {string} title
   * @param {number} depth
   * @param {string} screenshotPath - relative path to screenshot
   */
  addPage(url, title, depth, screenshotPath = '') {
    if (this.existingUrls.has(url)) return;
    this.existingUrls.add(url);
    this.pages.push({ url, title, depth, screenshotPath, addedAt: new Date().toISOString() });
    this.pagesSinceFlush++;

    if (this.pagesSinceFlush >= FLUSH_INTERVAL) {
      this.flush();
      this.pagesSinceFlush = 0;
    }
  }

  /**
   * Add a navigation edge (from → to).
   * @param {string} from
   * @param {string} to
   */
  addEdge(from, to) {
    // Deduplicate edges
    const exists = this.edges.some((e) => e.from === from && e.to === to);
    if (!exists) {
      this.edges.push({ from, to });
    }
  }

  /**
   * Flush current state to disk.
   */
  flush() {
    const data = {
      pages: this.pages,
      edges: this.edges,
      updatedAt: new Date().toISOString(),
    };
    // Atomic write: write to temp then rename
    const tmpPath = this.outputPath + '.tmp';
    fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2), 'utf8');
    fs.renameSync(tmpPath, this.outputPath);
  }

  /**
   * Load existing sitemap from disk for --continue mode.
   * @param {string} sitemapPath
   * @returns {object|null} existing data or null
   */
  static loadExisting(sitemapPath) {
    try {
      if (fs.existsSync(sitemapPath)) {
        return JSON.parse(fs.readFileSync(sitemapPath, 'utf8'));
      }
    } catch {
      // Corrupt file — start fresh
    }
    return null;
  }

  /**
   * Get set of already-visited URLs (for --continue mode BFS skip).
   * @returns {Set<string>}
   */
  getVisitedUrls() {
    return new Set(this.pages.map((p) => p.url));
  }

  get pageCount() {
    return this.pages.length;
  }
}
