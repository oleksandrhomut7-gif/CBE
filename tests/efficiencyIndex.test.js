import { describe, it, expect, beforeEach } from 'vitest';
import { EfficiencyIndex } from '../src/efficiencyIndex.js';

describe('EfficiencyIndex', () => {
  let idx;

  beforeEach(() => {
    idx = new EfficiencyIndex();
  });

  describe('calculation', () => {
    it('returns 0 when no activity', () => {
      expect(idx.value).toBe(0);
      expect(idx.rawValue).toBe(0);
    });

    it('returns 0 when points exist but no focus time', () => {
      idx.addPoints(100);
      expect(idx.value).toBe(0);
    });

    it('calculates points / minutes correctly', () => {
      idx.addPoints(50);
      idx.addFocusTime(120); // 2 minutes
      expect(idx.rawValue).toBeCloseTo(25); // 50 / 2
    });

    it('accumulates multiple point additions', () => {
      idx.addPoints(10);
      idx.addPoints(50);
      idx.addPoints(100);
      idx.addFocusTime(60); // 1 minute
      expect(idx.rawValue).toBeCloseTo(160); // 160 / 1
    });

    it('index decreases as focus time grows without completions', () => {
      idx.addPoints(50);
      idx.addFocusTime(60);
      const val1 = idx.rawValue;
      idx.addFocusTime(60);
      const val2 = idx.rawValue;
      expect(val2).toBeLessThan(val1);
    });
  });

  describe('buff multiplier', () => {
    it('defaults to 1.0', () => {
      expect(idx.buffMultiplier).toBe(1.0);
    });

    it('applies multiplier to value', () => {
      idx.addPoints(50);
      idx.addFocusTime(120); // raw = 25
      idx.setBuffMultiplier(1.10);
      expect(idx.value).toBeCloseTo(27.5);
    });

    it('does not affect rawValue', () => {
      idx.addPoints(50);
      idx.addFocusTime(120);
      idx.setBuffMultiplier(1.10);
      expect(idx.rawValue).toBeCloseTo(25);
    });

    it('throws if multiplier < 1.0', () => {
      expect(() => idx.setBuffMultiplier(0.9)).toThrow('cannot be less than 1.0');
    });
  });

  describe('format()', () => {
    it('formats zero as .000', () => {
      expect(idx.format()).toBe('.000');
    });

    it('formats typical sub-1 value', () => {
      idx.addPoints(413);
      idx.addFocusTime(60000); // 1000 minutes
      expect(idx.format()).toBe('.413');
    });

    it('formats .650', () => {
      idx.addPoints(650);
      idx.addFocusTime(60000);
      expect(idx.format()).toBe('.650');
    });

    it('formats values >= 1 without leading zero', () => {
      idx.addPoints(100);
      idx.addFocusTime(60); // 1 minute → 100.0
      // 100.000 → should not have leading zero issue
      expect(idx.format()).toBe('100.000');
    });

    it('always has 3 decimal places', () => {
      idx.addPoints(1);
      idx.addFocusTime(180); // 3 minutes → 0.333...
      expect(idx.format()).toBe('.333');
    });
  });

  describe('validation', () => {
    it('throws on negative points', () => {
      expect(() => idx.addPoints(-1)).toThrow('cannot be negative');
    });

    it('throws on negative focus time', () => {
      expect(() => idx.addFocusTime(-1)).toThrow('cannot be negative');
    });

    it('allows zero points', () => {
      idx.addPoints(0);
      expect(idx.totalPoints).toBe(0);
    });

    it('allows zero focus time', () => {
      idx.addFocusTime(0);
      expect(idx.totalFocusSeconds).toBe(0);
    });
  });

  describe('reset()', () => {
    it('clears all state', () => {
      idx.addPoints(100);
      idx.addFocusTime(300);
      idx.setBuffMultiplier(1.1);
      idx.reset();

      expect(idx.totalPoints).toBe(0);
      expect(idx.totalFocusSeconds).toBe(0);
      expect(idx.buffMultiplier).toBe(1.0);
      expect(idx.value).toBe(0);
    });
  });
});
