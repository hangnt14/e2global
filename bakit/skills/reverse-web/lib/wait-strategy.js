/**
 * wait-strategy.js
 * Page stability detection using domcontentloaded + MutationObserver.
 * Does NOT use networkidle — fails on SPAs with persistent connections.
 */

/**
 * Wait for page to be visually stable:
 * 1. Wait for domcontentloaded
 * 2. Wait for no DOM mutations for quietMs (default 1000ms)
 * 3. Race against stabilityTimeout — proceed anyway if timeout fires
 *
 * @param {import('playwright').Page} page
 * @param {object} options
 * @param {number} options.stabilityTimeout - max ms to wait for stability (default 5000)
 * @param {number} options.quietMs - ms of no mutations to consider stable (default 1000)
 */
export async function waitForStability(page, options = {}) {
  const { stabilityTimeout = 5000, quietMs = 1000 } = options;

  // Step 1: wait for domcontentloaded (already fired if page.goto used it)
  try {
    await page.waitForLoadState('domcontentloaded', { timeout: stabilityTimeout });
  } catch {
    // Timeout on domcontentloaded — proceed anyway
    return;
  }

  // Step 2: wait for DOM mutation quiet period via MutationObserver
  try {
    await Promise.race([
      page.evaluate((quietMs) => {
        return new Promise((resolve) => {
          let timer = setTimeout(resolve, quietMs);
          const observer = new MutationObserver(() => {
            clearTimeout(timer);
            timer = setTimeout(resolve, quietMs);
          });
          observer.observe(document.body || document.documentElement, {
            childList: true,
            subtree: true,
            attributes: true,
          });
          // Clean up observer when done
          setTimeout(() => {
            observer.disconnect();
            resolve();
          }, quietMs * 10); // safety ceiling
        });
      }, quietMs),
      new Promise((resolve) => setTimeout(resolve, stabilityTimeout)),
    ]);
  } catch {
    // page.evaluate can fail on navigation — proceed anyway
  }
}
