/**
 * Buff System — micro-habit rewards.
 *
 * Buffs are temporary percentage bonuses applied to the Efficiency Index.
 * They stack additively: two +5% buffs = +10% total.
 * Each buff has a duration and expires after that time.
 */

import { randomUUID } from 'crypto';

/**
 * @typedef {object} BuffTemplate
 * @property {string} name
 * @property {number} bonusPercent
 * @property {number} durationMinutes
 * @property {number} cooldownMinutes
 */

/** Default micro-habit templates. */
export const DEFAULT_TEMPLATES = [
  { name: 'Water', bonusPercent: 5, durationMinutes: 30, cooldownMinutes: 15 },
  { name: 'Eye Rest', bonusPercent: 5, durationMinutes: 20, cooldownMinutes: 20 },
  { name: 'Stretch', bonusPercent: 5, durationMinutes: 25, cooldownMinutes: 30 },
];

export class BuffSystem {
  /**
   * @param {function} [now] - Clock function returning current time in ms.
   * @param {BuffTemplate[]} [templates] - Buff templates.
   */
  constructor(now = Date.now, templates = DEFAULT_TEMPLATES) {
    this._now = now;
    this._templates = [...templates];
    this._activeBuffs = [];
    this._activationHistory = new Map();
  }

  get templates() {
    return [...this._templates];
  }

  /** Active (non-expired) buffs. */
  get activeBuffs() {
    this._cleanupExpired();
    return [...this._activeBuffs];
  }

  /** Total additive bonus percentage from all active buffs. */
  get totalBonusPercent() {
    this._cleanupExpired();
    return this._activeBuffs.reduce((sum, b) => sum + b.bonusPercent, 0);
  }

  /** Total multiplier to apply to the efficiency index. */
  get totalMultiplier() {
    return 1.0 + this.totalBonusPercent / 100;
  }

  /**
   * Add a custom buff template.
   * @param {BuffTemplate} template
   */
  addTemplate(template) {
    if (!template.name || typeof template.name !== 'string') {
      throw new Error('Template must have a non-empty name');
    }
    this._templates.push(template);
  }

  /**
   * Activate a buff by template name.
   * @param {string} name
   * @returns {object} The activated buff.
   */
  activateBuff(name) {
    const template = this._findTemplate(name);
    this._checkCooldown(template);

    const now = this._now();
    const buff = {
      id: randomUUID(),
      name: template.name,
      bonusPercent: template.bonusPercent,
      durationMinutes: template.durationMinutes,
      activatedAt: now,
    };
    this._activeBuffs.push(buff);
    this._activationHistory.set(template.name, now);
    return buff;
  }

  /**
   * Check if a buff template is on cooldown.
   * @param {string} name
   * @returns {boolean}
   */
  isOnCooldown(name) {
    const template = this._findTemplate(name);
    if (template.cooldownMinutes <= 0) return false;

    const lastActivation = this._activationHistory.get(template.name);
    if (lastActivation === undefined) return false;

    const elapsedMinutes = (this._now() - lastActivation) / 60000;
    return elapsedMinutes < template.cooldownMinutes;
  }

  /**
   * Get remaining cooldown time in minutes.
   * @param {string} name
   * @returns {number}
   */
  cooldownRemainingMinutes(name) {
    const template = this._findTemplate(name);
    if (template.cooldownMinutes <= 0) return 0;

    const lastActivation = this._activationHistory.get(template.name);
    if (lastActivation === undefined) return 0;

    const elapsedMinutes = (this._now() - lastActivation) / 60000;
    return Math.max(0, template.cooldownMinutes - elapsedMinutes);
  }

  /** Reset all buffs for a new day. */
  reset() {
    this._activeBuffs = [];
    this._activationHistory.clear();
  }

  /** @private */
  _cleanupExpired() {
    const now = this._now();
    this._activeBuffs = this._activeBuffs.filter(b => {
      const elapsedMinutes = (now - b.activatedAt) / 60000;
      return elapsedMinutes < b.durationMinutes;
    });
  }

  /** @private */
  _findTemplate(name) {
    const template = this._templates.find(t => t.name === name);
    if (!template) {
      throw new Error(`No buff template named '${name}'`);
    }
    return template;
  }

  /** @private */
  _checkCooldown(template) {
    if (this.isOnCooldown(template.name)) {
      const remaining = this.cooldownRemainingMinutes(template.name);
      throw new Error(
        `Buff '${template.name}' is on cooldown. ${remaining.toFixed(1)} minutes remaining.`
      );
    }
  }
}
