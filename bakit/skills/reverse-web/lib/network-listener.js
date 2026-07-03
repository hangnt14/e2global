/**
 * network-listener.js
 * Passive network capture using page.on('response') — non-blocking listener.
 * Does NOT use page.route() which would intercept and block requests.
 * Rate limit detection signals via callback (not throw) since async event
 * listeners cannot propagate exceptions to the crawl engine's try/catch.
 */

import fs from 'fs';
import { sanitizeHeaders } from './guardrails.js';
import { scanObject } from './sensitive-scanner.js';

const MAX_BODY_KEYS = 20;
const MAX_BODY_SIZE = 512 * 1024; // 512KB — skip body parse for large responses

/**
 * Attach a passive response listener to the page.
 * @param {import('playwright').Page} page
 * @param {string} outputPath - path to network.ndjson
 * @param {object} options
 * @param {function} options.onRateLimit - called with status code when 429/403 detected
 */
export function attachNetworkListener(page, outputPath, options = {}) {
  const { onRateLimit } = options;

  page.on('response', async (response) => {
    try {
      const status = response.status();
      const url = response.url();
      const request = response.request();
      const method = request.method();
      const contentType = response.headers()['content-type'] || '';

      // C1: signal rate limit via callback instead of throwing
      // (async event listeners cannot propagate exceptions to crawl engine)
      if (status === 429 || status === 403) {
        if (onRateLimit) onRateLimit(status);
        return;
      }

      // G2: sanitize headers (allowlist)
      const safeHeaders = sanitizeHeaders(response.headers());

      // Capture response body shape for JSON responses only
      let bodyShape = null;
      if (contentType.includes('application/json') && status < 400) {
        try {
          // Check content-length before buffering large responses
          const contentLength = parseInt(response.headers()['content-length'] || '0', 10);
          if (!contentLength || contentLength < MAX_BODY_SIZE) {
            const body = await response.json();
            const scanned = scanObject(body);
            if (typeof scanned === 'object' && scanned !== null && !Array.isArray(scanned)) {
              const keys = Object.keys(scanned).slice(0, MAX_BODY_KEYS);
              bodyShape = Object.fromEntries(keys.map((k) => [k, typeof scanned[k]]));
            } else if (Array.isArray(scanned) && scanned.length > 0) {
              const first = scanned[0];
              if (typeof first === 'object' && first !== null) {
                const keys = Object.keys(first).slice(0, MAX_BODY_KEYS);
                bodyShape = { _array: true, _itemShape: Object.fromEntries(keys.map((k) => [k, typeof first[k]])) };
              } else {
                bodyShape = { _array: true, _itemType: typeof first };
              }
            }
          }
        } catch { /* body parse failed — skip */ }
      }

      const entry = {
        method,
        url,
        status,
        contentType: safeHeaders['content-type'] || contentType.split(';')[0].trim(),
        bodyShape,
        timestamp: new Date().toISOString(),
      };

      // H4: use async append to avoid blocking event loop
      fs.appendFile(outputPath, JSON.stringify(entry) + '\n', 'utf8', () => {});
    } catch {
      // Silently skip — never crash the crawl from a listener error
    }
  });
}
