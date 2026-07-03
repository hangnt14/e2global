import { describe, it, expect } from 'vitest';
import { parseRobotsTxt, isAllowed } from '../../lib/robots-parser.js';

describe('robots-parser', () => {
  describe('parseRobotsTxt', () => {
    it('extracts Disallow rules for User-agent: *', () => {
      const txt = `
User-agent: *
Disallow: /admin
Disallow: /private
`;
      const rules = parseRobotsTxt(txt);
      expect(rules.disallow).toContain('/admin');
      expect(rules.disallow).toContain('/private');
    });

    it('ignores rules for specific user agents', () => {
      const txt = `
User-agent: Googlebot
Disallow: /google-only

User-agent: *
Disallow: /admin
`;
      const rules = parseRobotsTxt(txt);
      expect(rules.disallow).toContain('/admin');
      expect(rules.disallow).not.toContain('/google-only');
    });

    it('returns empty disallow for empty robots.txt', () => {
      const rules = parseRobotsTxt('');
      expect(rules.disallow).toHaveLength(0);
    });

    it('ignores comments', () => {
      const txt = `
# This is a comment
User-agent: *
# Another comment
Disallow: /admin
`;
      const rules = parseRobotsTxt(txt);
      expect(rules.disallow).toContain('/admin');
      expect(rules.disallow).toHaveLength(1);
    });

    it('handles Allow directives without crashing', () => {
      const txt = `
User-agent: *
Disallow: /admin
Allow: /admin/public
`;
      const rules = parseRobotsTxt(txt);
      expect(rules.disallow).toContain('/admin');
    });
  });

  describe('isAllowed', () => {
    const rules = { disallow: ['/admin', '/private/'] };

    it('returns false for disallowed path', () => {
      expect(isAllowed('https://example.com/admin', rules)).toBe(false);
      expect(isAllowed('https://example.com/admin/users', rules)).toBe(false);
    });

    it('returns true for allowed path', () => {
      expect(isAllowed('https://example.com/public', rules)).toBe(true);
      expect(isAllowed('https://example.com/', rules)).toBe(true);
    });

    it('returns true when no disallow rules', () => {
      expect(isAllowed('https://example.com/admin', { disallow: [] })).toBe(true);
    });

    it('returns true for invalid URL', () => {
      expect(isAllowed('not-a-url', rules)).toBe(true);
    });
  });
});
