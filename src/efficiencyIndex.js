/**
 * Efficiency Index calculator.
 *
 * Formula: totalPointsEarned / (totalFocusSeconds / 60)
 * Display: `.NNN` — no leading zero, always 3 decimal places.
 */

export class EfficiencyIndex {
  constructor() {
    this._totalPoints = 0;
    this._totalFocusSeconds = 0;
    this._buffMultiplier = 1.0;
  }

  get totalPoints() {
    return this._totalPoints;
  }

  get totalFocusSeconds() {
    return this._totalFocusSeconds;
  }

  get buffMultiplier() {
    return this._buffMultiplier;
  }

  /** Raw index value without buff multiplier. */
  get rawValue() {
    const minutes = this._totalFocusSeconds / 60;
    if (minutes <= 0) return 0;
    return this._totalPoints / minutes;
  }

  /** Index value with buff multiplier applied. */
  get value() {
    return this.rawValue * this._buffMultiplier;
  }

  /**
   * Format the index as `.NNN` (sports-style, no leading zero).
   * @returns {string}
   */
  format() {
    const val = this.value;
    if (!isFinite(val)) return '.000';
    return val.toFixed(3).replace(/^0\./, '.');
  }

  /**
   * Add points from a completed task.
   * @param {number} points
   */
  addPoints(points) {
    if (points < 0) throw new Error('Points cannot be negative');
    this._totalPoints += points;
  }

  /**
   * Add elapsed focus time.
   * @param {number} seconds
   */
  addFocusTime(seconds) {
    if (seconds < 0) throw new Error('Focus time cannot be negative');
    this._totalFocusSeconds += seconds;
  }

  /**
   * Set the buff multiplier.
   * @param {number} multiplier - Must be >= 1.0
   */
  setBuffMultiplier(multiplier) {
    if (multiplier < 1.0) throw new Error('Buff multiplier cannot be less than 1.0');
    this._buffMultiplier = multiplier;
  }

  /** Reset for a new day. */
  reset() {
    this._totalPoints = 0;
    this._totalFocusSeconds = 0;
    this._buffMultiplier = 1.0;
  }
}
