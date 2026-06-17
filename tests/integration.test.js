import { describe, it, expect } from 'vitest';
import { EfficiencyIndex } from '../src/efficiencyIndex.js';
import { TaskManager, createTask, TASK_POINTS } from '../src/taskManager.js';
import { FocusTimer } from '../src/focusTimer.js';
import { BuffSystem } from '../src/buffSystem.js';

function createClock(start = 0) {
  let now = start;
  const clock = () => now;
  clock.advance = (ms) => { now += ms; };
  clock.advanceSeconds = (s) => { now += s * 1000; };
  clock.advanceMinutes = (m) => { now += m * 60000; };
  return clock;
}

describe('Integration — full day workflow', () => {
  it('plan → focus → complete cycle updates index', () => {
    const clock = createClock();
    const mgr = new TaskManager();
    const timer = new FocusTimer(clock);
    const index = new EfficiencyIndex();

    // Plan tasks
    const t1 = createTask('Review PRs', TASK_POINTS.MEDIUM);
    const t2 = createTask('Write feature', TASK_POINTS.LARGE);
    mgr.addToBackpack(t1);
    mgr.addToBackpack(t2);

    // Focus on t1
    mgr.moveToNow(t1.id, clock());
    timer.startFocus();
    clock.advanceMinutes(25);

    // Complete
    timer.pause();
    const completed = mgr.completeNowTask(clock());
    index.addPoints(completed.points);
    index.addFocusTime(timer.elapsedFocusSeconds);

    // 50 points / 25 minutes = 2.0
    expect(index.rawValue).toBeCloseTo(2.0);
    expect(index.format()).toBe('2.000');
  });

  it('buff increases efficiency index', () => {
    const clock = createClock();
    const mgr = new TaskManager();
    const timer = new FocusTimer(clock);
    const index = new EfficiencyIndex();
    const buffs = new BuffSystem(clock);

    const task = createTask('Quick fix', TASK_POINTS.SMALL);
    mgr.addToBackpack(task);
    mgr.moveToNow(task.id, clock());
    timer.startFocus();
    clock.advanceMinutes(10);
    timer.pause();
    mgr.completeNowTask(clock());

    index.addPoints(task.points);
    index.addFocusTime(timer.elapsedFocusSeconds);
    const rawBefore = index.rawValue;

    // Activate buff
    buffs.activateBuff('Water');
    index.setBuffMultiplier(buffs.totalMultiplier);

    expect(index.value).toBeGreaterThan(rawBefore);
    expect(index.value).toBeCloseTo(rawBefore * 1.05);
  });

  it('returning task and switching preserves state', () => {
    const clock = createClock();
    const mgr = new TaskManager();

    const t1 = createTask('Hard task', TASK_POINTS.LARGE);
    const t2 = createTask('Easy win', TASK_POINTS.SMALL);
    mgr.addToBackpack(t1);
    mgr.addToBackpack(t2);

    // Start hard task, decide to switch
    mgr.moveToNow(t1.id, clock());
    clock.advanceSeconds(30);
    mgr.returnToBackpack(clock());

    // t1 should have elapsed time
    expect(mgr.backpack.find(t => t.id === t1.id).timerElapsedSeconds).toBe(30);

    // Do easy task instead
    mgr.moveToNow(t2.id, clock());
    clock.advanceSeconds(60);
    mgr.completeNowTask(clock());

    expect(mgr.totalPointsEarned).toBe(10);
    expect(mgr.backpack).toHaveLength(1);
  });

  it('index decays over idle focus time', () => {
    const clock = createClock();
    const timer = new FocusTimer(clock);
    const index = new EfficiencyIndex();

    timer.startFocus();
    clock.advanceMinutes(10);
    timer.pause();

    index.addPoints(50);
    index.addFocusTime(timer.elapsedFocusSeconds);
    const val1 = index.value; // 50 / 10 = 5.0

    // More focus time without completions
    timer.startFocus();
    clock.advanceMinutes(20);
    timer.pause();
    index.addFocusTime(20 * 60); // add 20 more minutes
    const val2 = index.value; // 50 / 30 ≈ 1.67

    expect(val2).toBeLessThan(val1);
  });

  it('pause protects the index from decay', () => {
    const clock = createClock();
    const timer = new FocusTimer(clock);
    const index = new EfficiencyIndex();

    timer.startFocus();
    clock.advanceMinutes(10);
    timer.pause();

    index.addPoints(50);
    index.addFocusTime(timer.elapsedFocusSeconds);
    const valAtPause = index.value;

    // Long pause — time passes but timer is frozen
    clock.advanceMinutes(60);
    expect(index.value).toBe(valAtPause);
  });

  it('onboarding: demo tasks fit within capacity', () => {
    const mgr = new TaskManager();
    // Simulate onboarding demo tasks
    const demo1 = createTask('Try dragging this to Now', TASK_POINTS.SMALL);
    const demo2 = createTask('Complete a medium task', TASK_POINTS.MEDIUM);
    const demo3 = createTask('Tackle a big one', TASK_POINTS.LARGE);

    mgr.addToBackpack(demo1);
    mgr.addToBackpack(demo2);
    mgr.addToBackpack(demo3);

    expect(mgr.backpackPointsUsed).toBe(160);
    expect(mgr.backpackPointsRemaining).toBe(140);
  });
});
