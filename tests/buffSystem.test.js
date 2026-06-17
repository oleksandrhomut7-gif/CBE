import { describe, it, expect, beforeEach } from 'vitest';
import { BuffSystem, DEFAULT_TEMPLATES } from '../src/buffSystem.js';

function createClock(start = 0) {
  let now = start;
  const clock = () => now;
  clock.advance = (ms) => { now += ms; };
  clock.advanceMinutes = (m) => { now += m * 60000; };
  return clock;
}

describe('BuffSystem', () => {
  let clock;
  let system;

  beforeEach(() => {
    clock = createClock();
    system = new BuffSystem(clock);
  });

  describe('activation', () => {
    it('activates a buff by template name', () => {
      const buff = system.activateBuff('Water');
      expect(buff.name).toBe('Water');
      expect(buff.bonusPercent).toBe(5);
      expect(buff.id).toBeDefined();
      expect(system.activeBuffs).toHaveLength(1);
    });

    it('throws for nonexistent template', () => {
      expect(() => system.activateBuff('Nonexistent')).toThrow('No buff template');
    });

    it('activates multiple different buffs', () => {
      system.activateBuff('Water');
      clock.advanceMinutes(20);
      system.activateBuff('Stretch');
      expect(system.activeBuffs).toHaveLength(2);
    });
  });

  describe('bonus calculation', () => {
    it('returns 0 bonus with no buffs', () => {
      expect(system.totalBonusPercent).toBe(0);
      expect(system.totalMultiplier).toBeCloseTo(1.0);
    });

    it('single buff gives its bonus', () => {
      system.activateBuff('Water');
      expect(system.totalBonusPercent).toBe(5);
      expect(system.totalMultiplier).toBeCloseTo(1.05);
    });

    it('multiple buffs stack additively', () => {
      system.activateBuff('Water');
      clock.advanceMinutes(20);
      system.activateBuff('Stretch');
      expect(system.totalBonusPercent).toBe(10);
      expect(system.totalMultiplier).toBeCloseTo(1.10);
    });
  });

  describe('expiration', () => {
    it('buff expires after its duration', () => {
      system.activateBuff('Water'); // 30 min duration
      clock.advanceMinutes(31);
      expect(system.activeBuffs).toHaveLength(0);
      expect(system.totalBonusPercent).toBe(0);
    });

    it('buff still active before expiration', () => {
      system.activateBuff('Water');
      clock.advanceMinutes(29);
      expect(system.activeBuffs).toHaveLength(1);
    });

    it('partial expiration of multiple buffs', () => {
      system.activateBuff('Eye Rest'); // 20 min
      clock.advanceMinutes(21);
      system.activateBuff('Stretch'); // 25 min, fresh
      expect(system.activeBuffs).toHaveLength(1);
      expect(system.activeBuffs[0].name).toBe('Stretch');
    });
  });

  describe('cooldown', () => {
    it('prevents reactivation during cooldown', () => {
      system.activateBuff('Water'); // cooldown: 15 min
      clock.advanceMinutes(5);
      expect(() => system.activateBuff('Water')).toThrow('on cooldown');
    });

    it('allows activation after cooldown expires', () => {
      system.activateBuff('Water');
      clock.advanceMinutes(16);
      const buff = system.activateBuff('Water');
      expect(buff.name).toBe('Water');
    });

    it('isOnCooldown returns true during cooldown', () => {
      system.activateBuff('Water');
      expect(system.isOnCooldown('Water')).toBe(true);
      clock.advanceMinutes(16);
      expect(system.isOnCooldown('Water')).toBe(false);
    });

    it('reports remaining cooldown minutes', () => {
      system.activateBuff('Water'); // cooldown: 15 min
      clock.advanceMinutes(10);
      expect(system.cooldownRemainingMinutes('Water')).toBeCloseTo(5);
    });

    it('returns 0 remaining when not activated', () => {
      expect(system.cooldownRemainingMinutes('Water')).toBe(0);
    });

    it('throws for nonexistent template on cooldown check', () => {
      expect(() => system.isOnCooldown('Nonexistent')).toThrow('No buff template');
    });
  });

  describe('templates', () => {
    it('has default templates', () => {
      const names = system.templates.map(t => t.name);
      expect(names).toContain('Water');
      expect(names).toContain('Eye Rest');
      expect(names).toContain('Stretch');
    });

    it('adds custom template', () => {
      system.addTemplate({
        name: 'Meditation',
        bonusPercent: 8,
        durationMinutes: 45,
        cooldownMinutes: 0,
      });
      const buff = system.activateBuff('Meditation');
      expect(buff.bonusPercent).toBe(8);
    });

    it('template with no cooldown allows repeated activation', () => {
      system.addTemplate({
        name: 'NoCooldown',
        bonusPercent: 3,
        durationMinutes: 10,
        cooldownMinutes: 0,
      });
      system.activateBuff('NoCooldown');
      system.activateBuff('NoCooldown');
      expect(system.activeBuffs).toHaveLength(2);
    });

    it('rejects template with invalid name', () => {
      expect(() => system.addTemplate({ name: '', bonusPercent: 5, durationMinutes: 10, cooldownMinutes: 0 }))
        .toThrow('non-empty name');
    });
  });

  describe('reset()', () => {
    it('clears all buffs and cooldowns', () => {
      system.activateBuff('Water');
      system.reset();
      expect(system.activeBuffs).toHaveLength(0);
      expect(system.totalBonusPercent).toBe(0);
      expect(system.isOnCooldown('Water')).toBe(false);
    });
  });
});
