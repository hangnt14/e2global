import { describe, it, expect } from 'vitest';
import { scanValue, scanObject } from '../../lib/sensitive-scanner.js';

describe('sensitive-scanner', () => {
  describe('scanValue', () => {
    it('redacts credit card numbers', () => {
      expect(scanValue('card: 4111-1111-1111-1111')).toContain('[REDACTED]');
      expect(scanValue('4111111111111111')).toContain('[REDACTED]');
      expect(scanValue('4111 1111 1111 1111')).toContain('[REDACTED]');
    });

    it('redacts JWT tokens', () => {
      const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123';
      expect(scanValue(jwt)).toContain('[REDACTED]');
    });

    it('redacts Bearer tokens', () => {
      expect(scanValue('Bearer eyJhbGciOiJIUzI1NiJ9.abc.def')).toContain('[REDACTED]');
    });

    it('leaves normal text unchanged', () => {
      expect(scanValue('hello world')).toBe('hello world');
      expect(scanValue('user@example.com')).toBe('user@example.com');
      expect(scanValue('')).toBe('');
    });

    it('leaves short numbers unchanged (not credit card pattern)', () => {
      expect(scanValue('12345')).toBe('12345');
      expect(scanValue('order-1234')).toBe('order-1234');
    });
  });

  describe('scanObject', () => {
    it('redacts string values matching patterns', () => {
      const result = scanObject({ token: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc' });
      expect(result.token).toContain('[REDACTED]');
    });

    it('leaves numbers unchanged — prevents JSON corruption', () => {
      const result = scanObject({ count: 4111111111111111 });
      expect(result.count).toBe(4111111111111111);
    });

    it('leaves booleans unchanged', () => {
      const result = scanObject({ active: true, deleted: false });
      expect(result.active).toBe(true);
      expect(result.deleted).toBe(false);
    });

    it('leaves null unchanged', () => {
      const result = scanObject({ value: null });
      expect(result.value).toBeNull();
    });

    it('recurses into nested objects', () => {
      const result = scanObject({ nested: { token: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc' } });
      expect(result.nested.token).toContain('[REDACTED]');
    });

    it('recurses into arrays', () => {
      const result = scanObject({ items: ['safe text', 'Bearer eyJhbGciOiJIUzI1NiJ9.abc.def'] });
      expect(result.items[0]).toBe('safe text');
      expect(result.items[1]).toContain('[REDACTED]');
    });

    it('handles deeply nested structures', () => {
      const result = scanObject({ a: { b: { c: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc' } } });
      expect(result.a.b.c).toContain('[REDACTED]');
    });

    it('handles empty object', () => {
      expect(scanObject({})).toEqual({});
    });

    it('handles empty array', () => {
      expect(scanObject([])).toEqual([]);
    });

    it('returns primitives directly', () => {
      expect(scanObject('hello')).toBe('hello');
      expect(scanObject(42)).toBe(42);
      expect(scanObject(null)).toBeNull();
    });
  });
});
