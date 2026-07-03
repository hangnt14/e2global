/**
 * sensitive-scanner.js
 * Recursive object walker that redacts sensitive string values.
 * Numbers, booleans, null are never touched — prevents JSON corruption.
 */

// Patterns to detect sensitive values in strings
const PATTERNS = [
  // Credit card (Visa, Mastercard, Amex, etc.)
  /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g,
  // JWT tokens (header.payload.signature)
  /eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,
  // Bearer tokens
  /Bearer\s+[A-Za-z0-9._~+/=:-]+/g,
  // JSON-style password/secret fields: "password": "value"
  /"(password|passwd|pwd|secret|api_key|apikey|access_token|refresh_token|private_key)"\s*:\s*"[^"]*"/gi,
  // Key=value style credentials
  /(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*\S+/gi,
];

/**
 * Scan a single string value and redact any sensitive patterns.
 * @param {string} str
 * @returns {string} redacted string
 */
export function scanValue(str) {
  let result = str;
  for (const pattern of PATTERNS) {
    // Reset lastIndex for global patterns
    pattern.lastIndex = 0;
    result = result.replace(pattern, '[REDACTED]');
  }
  return result;
}

/**
 * Recursively walk an object/array and redact sensitive string values.
 * Numbers, booleans, null are returned unchanged.
 * @param {*} obj
 * @returns {*} sanitized copy
 */
export function scanObject(obj) {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === 'string') return scanValue(obj);
  // Numbers and booleans are never redacted — prevents JSON corruption
  if (typeof obj === 'number' || typeof obj === 'boolean') return obj;
  if (Array.isArray(obj)) return obj.map(scanObject);
  if (typeof obj === 'object') {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = scanObject(value);
    }
    return result;
  }
  return obj;
}

export { PATTERNS };
