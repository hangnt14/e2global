/**
 * guardrails.js
 * Code-enforced guardrails for the reverse-web crawl script.
 * All functions throw GuardrailViolation — never call process.exit directly.
 * The CLI entry point (scripts/crawl.js) catches and exits.
 */

export class GuardrailViolation extends Error {
  constructor(message, code) {
    super(message);
    this.name = 'GuardrailViolation';
    this.code = code;
  }
}

// G1: Consent — must pass --consent flag
export function assertConsent(flags) {
  if (!flags.consent) {
    throw new GuardrailViolation(
      'Consent required. Re-run with --consent to confirm you have permission to crawl this site.',
      'G1'
    );
  }
}

// G2: Credential allowlist — only persist safe headers, strip everything else
const SAFE_HEADERS = new Set([
  'content-type',
  'accept',
  'user-agent',
  'content-length',
  'cache-control',
  'content-encoding',
  'transfer-encoding',
]);

export function sanitizeHeaders(headers) {
  const safe = {};
  for (const [key, value] of Object.entries(headers)) {
    if (SAFE_HEADERS.has(key.toLowerCase())) {
      safe[key.toLowerCase()] = value;
    }
  }
  return safe;
}

// G3: Page limit — hard stop per run
export function checkPageLimit(count, max) {
  if (count >= max) {
    throw new GuardrailViolation(
      `Page limit reached (${max}). Use --continue to crawl more pages in a subsequent run, or increase --max-pages.`,
      'G3'
    );
  }
}

// G5: Rate limit — immediate stop on 429 or 403
export function checkRateLimit(status) {
  if (status === 429) {
    throw new GuardrailViolation(
      'Rate limited (HTTP 429). The site is throttling requests. Wait before retrying.',
      'G5_429'
    );
  }
  if (status === 403) {
    throw new GuardrailViolation(
      'Access forbidden (HTTP 403). The site is blocking the crawler.',
      'G5_403'
    );
  }
}

// G6: Path containment — output must stay within project dir
import path from 'path';

export function validateOutputPath(outputDir, projectDir) {
  const resolved = path.resolve(outputDir);
  const project = path.resolve(projectDir);

  if (!resolved.startsWith(project + path.sep) && resolved !== project) {
    throw new GuardrailViolation(
      `Output path "${outputDir}" is outside the project directory. Use a relative path within the project.`,
      'G6'
    );
  }
}
