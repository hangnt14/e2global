/**
 * robots-parser.js
 * Fetches and parses robots.txt to filter disallowed URLs before crawling.
 * On fetch failure (404, timeout, network error) → treats as "allow all".
 */

/**
 * Fetch and parse robots.txt for a given origin.
 * @param {string} origin - e.g. "https://example.com"
 * @returns {Promise<{disallow: string[]}>} parsed rules
 */
export async function fetchAndParse(origin) {
  try {
    const url = `${origin}/robots.txt`;
    const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!response.ok) return { disallow: [] };

    const text = await response.text();
    return parseRobotsTxt(text);
  } catch {
    // Network error, timeout, or parse failure — allow all
    return { disallow: [] };
  }
}

/**
 * Parse robots.txt text into disallow rules.
 * Only processes rules for User-agent: * (all bots).
 * @param {string} text
 * @returns {{disallow: string[]}}
 */
export function parseRobotsTxt(text) {
  const disallow = [];
  let inAllAgents = false;

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;

    const [field, ...rest] = line.split(':');
    const key = field.trim().toLowerCase();
    const value = rest.join(':').trim();

    if (key === 'user-agent') {
      inAllAgents = value === '*';
    } else if (key === 'disallow' && inAllAgents && value) {
      disallow.push(value);
    }
  }

  return { disallow };
}

/**
 * Check if a URL is allowed by the parsed robots rules.
 * @param {string} url - full URL to check
 * @param {{disallow: string[]}} rules
 * @returns {boolean} true if allowed, false if disallowed
 */
export function isAllowed(url, rules) {
  if (!rules.disallow.length) return true;

  try {
    const { pathname } = new URL(url);
    for (const pattern of rules.disallow) {
      if (pathname.startsWith(pattern)) return false;
    }
  } catch {
    // Invalid URL — allow
  }
  return true;
}
