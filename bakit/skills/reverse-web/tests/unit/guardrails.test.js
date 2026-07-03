import { describe, it, expect } from 'vitest';
import {
  assertConsent,
  sanitizeHeaders,
  checkPageLimit,
  checkRateLimit,
  validateOutputPath,
  GuardrailViolation,
} from '../../lib/guardrails.js';

describe('guardrails', () => {
  describe('assertConsent (G1)', () => {
    it('throws GuardrailViolation with code G1 when consent is false', () => {
      expect(() => assertConsent({ consent: false })).toThrow(GuardrailViolation);
      try { assertConsent({ consent: false }); }
      catch (err) { expect(err.code).toBe('G1'); }
    });

    it('does not throw when consent is true', () => {
      expect(() => assertConsent({ consent: true })).not.toThrow();
    });
  });

  describe('sanitizeHeaders (G2)', () => {
    it('strips auth headers and keeps only safe headers', () => {
      const result = sanitizeHeaders({
        authorization: 'Bearer secret',
        'content-type': 'application/json',
        'x-api-key': 'key123',
        'x-custom-header': 'value',
        accept: 'application/json',
        'user-agent': 'test',
      });
      expect(result.authorization).toBeUndefined();
      expect(result['x-api-key']).toBeUndefined();
      expect(result['x-custom-header']).toBeUndefined();
      expect(result['content-type']).toBe('application/json');
      expect(result.accept).toBe('application/json');
      expect(result['user-agent']).toBe('test');
    });

    it('returns empty object when all headers are unsafe', () => {
      const result = sanitizeHeaders({ authorization: 'x', 'x-session': 'y' });
      expect(Object.keys(result)).toHaveLength(0);
    });
  });

  describe('checkPageLimit (G3)', () => {
    it('throws GuardrailViolation with code G3 at limit', () => {
      expect(() => checkPageLimit(30, 30)).toThrow(GuardrailViolation);
      try { checkPageLimit(30, 30); }
      catch (err) { expect(err.code).toBe('G3'); }
    });

    it('does not throw below limit', () => {
      expect(() => checkPageLimit(29, 30)).not.toThrow();
    });

    it('does not throw at zero', () => {
      expect(() => checkPageLimit(0, 30)).not.toThrow();
    });
  });

  describe('checkRateLimit (G5)', () => {
    it('throws with code G5_429 on 429', () => {
      expect(() => checkRateLimit(429)).toThrow(GuardrailViolation);
      try { checkRateLimit(429); }
      catch (err) { expect(err.code).toBe('G5_429'); }
    });

    it('throws with code G5_403 on 403', () => {
      expect(() => checkRateLimit(403)).toThrow(GuardrailViolation);
      try { checkRateLimit(403); }
      catch (err) { expect(err.code).toBe('G5_403'); }
    });

    it('does not throw on 200', () => {
      expect(() => checkRateLimit(200)).not.toThrow();
    });

    it('does not throw on 301', () => {
      expect(() => checkRateLimit(301)).not.toThrow();
    });

    it('does not throw on 404', () => {
      expect(() => checkRateLimit(404)).not.toThrow();
    });
  });

  describe('validateOutputPath (G6)', () => {
    it('throws with code G6 for absolute path', () => {
      expect(() => validateOutputPath('/etc/evidence', '/project')).toThrow(GuardrailViolation);
      try { validateOutputPath('/etc/evidence', '/project'); }
      catch (err) { expect(err.code).toBe('G6'); }
    });

    it('throws with code G6 for path traversal', () => {
      expect(() => validateOutputPath('../outside', process.cwd())).toThrow(GuardrailViolation);
    });

    it('does not throw for relative path within project', () => {
      expect(() => validateOutputPath('./evidence', process.cwd())).not.toThrow();
    });

    it('does not throw for nested relative path', () => {
      expect(() => validateOutputPath('./output/evidence', process.cwd())).not.toThrow();
    });
  });
});
