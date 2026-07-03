import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { SitemapBuilder } from '../../lib/sitemap-builder.js';

describe('sitemap-builder', () => {
  let tmpDir;
  let sitemapPath;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sitemap-test-'));
    sitemapPath = path.join(tmpDir, 'sitemap.json');
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('flushes to disk every 10 pages (crash safety)', () => {
    const builder = new SitemapBuilder(sitemapPath);
    for (let i = 0; i < 10; i++) {
      builder.addPage(`https://example.com/page-${i}`, `Page ${i}`, 1);
    }
    // After 10 pages, flush should have fired
    expect(fs.existsSync(sitemapPath)).toBe(true);
    const data = JSON.parse(fs.readFileSync(sitemapPath, 'utf8'));
    expect(data.pages).toHaveLength(10);
  });

  it('does not flush before 10 pages', () => {
    const builder = new SitemapBuilder(sitemapPath);
    for (let i = 0; i < 9; i++) {
      builder.addPage(`https://example.com/page-${i}`, `Page ${i}`, 1);
    }
    expect(fs.existsSync(sitemapPath)).toBe(false);
  });

  it('records edges correctly', () => {
    const builder = new SitemapBuilder(sitemapPath);
    builder.addEdge('https://example.com/', 'https://example.com/about');
    builder.addEdge('https://example.com/', 'https://example.com/login');
    builder.flush();
    const data = JSON.parse(fs.readFileSync(sitemapPath, 'utf8'));
    expect(data.edges).toHaveLength(2);
    expect(data.edges[0].from).toBe('https://example.com/');
    expect(data.edges[0].to).toBe('https://example.com/about');
  });

  it('deduplicates pages — same URL added twice → one entry', () => {
    const builder = new SitemapBuilder(sitemapPath);
    builder.addPage('https://example.com/', 'Home', 0);
    builder.addPage('https://example.com/', 'Home', 0);
    builder.flush();
    const data = JSON.parse(fs.readFileSync(sitemapPath, 'utf8'));
    expect(data.pages).toHaveLength(1);
  });

  it('deduplicates edges', () => {
    const builder = new SitemapBuilder(sitemapPath);
    builder.addEdge('https://example.com/', 'https://example.com/about');
    builder.addEdge('https://example.com/', 'https://example.com/about');
    builder.flush();
    const data = JSON.parse(fs.readFileSync(sitemapPath, 'utf8'));
    expect(data.edges).toHaveLength(1);
  });

  it('loads existing sitemap for --continue mode', () => {
    // Write an existing sitemap
    const existing = {
      pages: [{ url: 'https://example.com/', title: 'Home', depth: 0 }],
      edges: [],
    };
    fs.writeFileSync(sitemapPath, JSON.stringify(existing), 'utf8');

    const loaded = SitemapBuilder.loadExisting(sitemapPath);
    expect(loaded.pages).toHaveLength(1);
    expect(loaded.pages[0].url).toBe('https://example.com/');
  });

  it('returns null for missing sitemap', () => {
    const result = SitemapBuilder.loadExisting('/nonexistent/path.json');
    expect(result).toBeNull();
  });

  it('getVisitedUrls returns set of existing page URLs', () => {
    const existing = {
      pages: [
        { url: 'https://example.com/', title: 'Home', depth: 0 },
        { url: 'https://example.com/about', title: 'About', depth: 1 },
      ],
      edges: [],
    };
    const builder = new SitemapBuilder(sitemapPath, existing);
    const visited = builder.getVisitedUrls();
    expect(visited.has('https://example.com/')).toBe(true);
    expect(visited.has('https://example.com/about')).toBe(true);
    expect(visited.has('https://example.com/other')).toBe(false);
  });

  it('writes atomically via tmp + rename', () => {
    const builder = new SitemapBuilder(sitemapPath);
    builder.addPage('https://example.com/', 'Home', 0);
    builder.flush();
    // tmp file should not exist after flush
    expect(fs.existsSync(sitemapPath + '.tmp')).toBe(false);
    expect(fs.existsSync(sitemapPath)).toBe(true);
  });
});
