import { describe, it, expect, beforeEach } from 'vitest';
import { FocusTimer, TimerState } from '../src/focusTimer.js';

function createClock(start = 0) {
  let now = start;
  const clock = () => now;
  clock.advance = (ms) => { now += ms; };
  clock.advanceSeconds = (s) => { now += s * 1000; };
  clock.advanceMinutes = (m) => { now += m * 60000; };
  return clock;
}

describe('FocusTimer', () => {
  let clock;
  let timer;

  beforeEach(() => {
    clock = createClock();
    timer = new FocusTimer(clock);
  });

  describe('state transitions', () => {
    it('starts in idle state', () => {
      expect(timer.state).toBe(TimerState.IDLE);
      expect(timer.isIdle).toBe(true);
      expect(timer.isFocused).toBe(false);
      expect(timer.isPaused).toBe(false);
    });

    it('transitions to focus on startFocus', () => {
      timer.startFocus();
      expect(timer.state).toBe(TimerState.FOCUS);
      expect(timer.isFocused).toBe(true);
    });

    it('transitions to pause on pause()', () => {
      timer.startFocus();
      timer.pause();
      expect(timer.state).toBe(TimerState.PAUSE);
      expect(timer.isPaused).toBe(true);
    });

    it('resumes from pause to focus', () => {
      timer.startFocus();
      timer.pause();
      timer.startFocus();
      expect(timer.isFocused).toBe(true);
    });

    it('stops from focus', () => {
      timer.startFocus();
      clock.advanceSeconds(60);
      const total = timer.stop();
      expect(timer.isIdle).toBe(true);
      expect(total).toBe(60000);
    });

    it('stops from pause', () => {
      timer.startFocus();
      clock.advanceSeconds(30);
      timer.pause();
      const total = timer.stop();
      expect(timer.isIdle).toBe(true);
      expect(total).toBe(30000);
    });
  });

  describe('error handling', () => {
    it('throws when starting focus while already focused', () => {
      timer.startFocus();
      expect(() => timer.startFocus()).toThrow('Already in focus mode');
    });

    it('throws when pausing while not focused', () => {
      expect(() => timer.pause()).toThrow('not in focus mode');
    });

    it('throws when pausing from pause state', () => {
      timer.startFocus();
      timer.pause();
      expect(() => timer.pause()).toThrow('not in focus mode');
    });

    it('throws when stopping while idle', () => {
      expect(() => timer.stop()).toThrow('not running');
    });
  });

  describe('time tracking', () => {
    it('tracks elapsed time during focus', () => {
      timer.startFocus();
      clock.advanceSeconds(120);
      expect(timer.elapsedFocusSeconds).toBeCloseTo(120);
      expect(timer.elapsedFocusMinutes).toBeCloseTo(2);
    });

    it('freezes time during pause', () => {
      timer.startFocus();
      clock.advanceSeconds(60);
      timer.pause();
      clock.advanceSeconds(9999); // time passes but not tracked
      expect(timer.elapsedFocusSeconds).toBeCloseTo(60);
    });

    it('accumulates across multiple focus sessions', () => {
      timer.startFocus();
      clock.advanceSeconds(60);
      timer.pause();

      timer.startFocus();
      clock.advanceSeconds(40);
      timer.pause();

      expect(timer.elapsedFocusSeconds).toBeCloseTo(100);
    });

    it('pause() returns segment duration', () => {
      timer.startFocus();
      clock.advanceSeconds(45);
      const duration = timer.pause();
      expect(duration).toBe(45000);
    });

    it('totalFocusMs tracks completed segments only', () => {
      timer.startFocus();
      clock.advanceSeconds(30);
      timer.pause();
      expect(timer.totalFocusMs).toBe(30000);
    });
  });

  describe('session count', () => {
    it('starts at 0', () => {
      expect(timer.sessionCount).toBe(0);
    });

    it('increments on each startFocus', () => {
      timer.startFocus();
      expect(timer.sessionCount).toBe(1);
      timer.pause();
      timer.startFocus();
      expect(timer.sessionCount).toBe(2);
    });
  });

  describe('reset()', () => {
    it('clears all state', () => {
      timer.startFocus();
      clock.advanceSeconds(100);
      timer.pause();

      timer.reset();

      expect(timer.isIdle).toBe(true);
      expect(timer.totalFocusMs).toBe(0);
      expect(timer.elapsedFocusSeconds).toBe(0);
      expect(timer.sessionCount).toBe(0);
    });
  });
});
