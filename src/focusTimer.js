/**
 * Focus Timer — manages Focus/Pause state transitions.
 *
 * States: idle → focus ↔ pause
 * While in focus mode, the denominator of the Efficiency Index grows.
 * Pausing freezes the index — a safe and encouraged action.
 */

export const TimerState = Object.freeze({
  IDLE: 'idle',
  FOCUS: 'focus',
  PAUSE: 'pause',
});

export class FocusTimer {
  /**
   * @param {function} [now] - Clock function returning current time in ms. Defaults to Date.now.
   */
  constructor(now = Date.now) {
    this._now = now;
    this._state = TimerState.IDLE;
    this._focusStart = null;
    this._totalFocusMs = 0;
    this._sessionCount = 0;
  }

  get state() {
    return this._state;
  }

  get isFocused() {
    return this._state === TimerState.FOCUS;
  }

  get isPaused() {
    return this._state === TimerState.PAUSE;
  }

  get isIdle() {
    return this._state === TimerState.IDLE;
  }

  get sessionCount() {
    return this._sessionCount;
  }

  /** Total accumulated focus time in ms (not including current running segment). */
  get totalFocusMs() {
    return this._totalFocusMs;
  }

  /** Total focus time in ms including the currently running segment. */
  get elapsedFocusMs() {
    if (this._state === TimerState.FOCUS && this._focusStart !== null) {
      return this._totalFocusMs + (this._now() - this._focusStart);
    }
    return this._totalFocusMs;
  }

  /** Total focus time in seconds including current segment. */
  get elapsedFocusSeconds() {
    return this.elapsedFocusMs / 1000;
  }

  /** Total focus time in minutes including current segment. */
  get elapsedFocusMinutes() {
    return this.elapsedFocusMs / 60000;
  }

  /**
   * Start or resume a focus session.
   * @throws If already in focus mode.
   */
  startFocus() {
    if (this._state === TimerState.FOCUS) {
      throw new Error('Already in focus mode.');
    }
    this._focusStart = this._now();
    this._state = TimerState.FOCUS;
    this._sessionCount++;
  }

  /**
   * Pause the current focus session.
   * @returns {number} Duration of the just-ended focus segment in ms.
   * @throws If not in focus mode.
   */
  pause() {
    if (this._state !== TimerState.FOCUS) {
      throw new Error('Cannot pause: not in focus mode.');
    }
    const now = this._now();
    const segmentMs = now - this._focusStart;
    this._totalFocusMs += segmentMs;
    this._focusStart = null;
    this._state = TimerState.PAUSE;
    return segmentMs;
  }

  /**
   * Stop the timer entirely and return total focus time.
   * @returns {number} Total focus time in ms.
   * @throws If timer is idle.
   */
  stop() {
    if (this._state === TimerState.IDLE) {
      throw new Error('Timer is not running.');
    }
    if (this._state === TimerState.FOCUS) {
      const now = this._now();
      this._totalFocusMs += now - this._focusStart;
    }
    const total = this._totalFocusMs;
    this._state = TimerState.IDLE;
    this._focusStart = null;
    return total;
  }

  /** Reset for a new day. */
  reset() {
    this._state = TimerState.IDLE;
    this._focusStart = null;
    this._totalFocusMs = 0;
    this._sessionCount = 0;
  }
}
