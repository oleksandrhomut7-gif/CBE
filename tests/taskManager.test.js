import { describe, it, expect, beforeEach } from 'vitest';
import { TaskManager, createTask, TASK_POINTS, DEFAULT_CAPACITY } from '../src/taskManager.js';

describe('createTask', () => {
  it('creates a task with valid points', () => {
    const task = createTask('Test task', TASK_POINTS.SMALL);
    expect(task.title).toBe('Test task');
    expect(task.points).toBe(10);
    expect(task.status).toBe('backpack');
    expect(task.id).toBeDefined();
    expect(task.timerStart).toBeNull();
    expect(task.timerElapsedSeconds).toBe(0);
    expect(task.completedAt).toBeNull();
  });

  it('rejects invalid point values', () => {
    expect(() => createTask('Bad', 25)).toThrow('Invalid points value');
  });

  it('rejects empty title', () => {
    expect(() => createTask('', TASK_POINTS.SMALL)).toThrow('non-empty string');
  });

  it('rejects non-string title', () => {
    expect(() => createTask(null, TASK_POINTS.SMALL)).toThrow('non-empty string');
  });

  it('generates unique IDs', () => {
    const t1 = createTask('a', 10);
    const t2 = createTask('b', 10);
    expect(t1.id).not.toBe(t2.id);
  });
});

describe('TaskManager', () => {
  let mgr;

  beforeEach(() => {
    mgr = new TaskManager();
  });

  describe('backpack operations', () => {
    it('adds a task to backpack', () => {
      const task = createTask('Read docs', TASK_POINTS.SMALL);
      mgr.addToBackpack(task);
      expect(mgr.backpack).toHaveLength(1);
      expect(mgr.backpack[0].id).toBe(task.id);
    });

    it('tracks backpack points', () => {
      mgr.addToBackpack(createTask('a', 10));
      mgr.addToBackpack(createTask('b', 50));
      expect(mgr.backpackPointsUsed).toBe(60);
      expect(mgr.backpackPointsRemaining).toBe(DEFAULT_CAPACITY - 60);
    });

    it('rejects task that exceeds capacity', () => {
      const mgr50 = new TaskManager(50);
      mgr50.addToBackpack(createTask('a', 50));
      expect(() => mgr50.addToBackpack(createTask('b', 10))).toThrow('exceed capacity');
    });

    it('allows exactly at capacity', () => {
      const mgr100 = new TaskManager(100);
      mgr100.addToBackpack(createTask('a', 100));
      expect(mgr100.backpackPointsUsed).toBe(100);
      expect(mgr100.backpackPointsRemaining).toBe(0);
    });

    it('removes task from backpack', () => {
      const task = createTask('x', 10);
      mgr.addToBackpack(task);
      const removed = mgr.removeFromBackpack(task.id);
      expect(removed.id).toBe(task.id);
      expect(mgr.backpack).toHaveLength(0);
    });

    it('throws when removing nonexistent task', () => {
      expect(() => mgr.removeFromBackpack('bad-id')).toThrow('not found');
    });
  });

  describe('Now zone operations', () => {
    it('moves task to Now zone', () => {
      const task = createTask('Focus', TASK_POINTS.LARGE);
      mgr.addToBackpack(task);
      const moved = mgr.moveToNow(task.id, 1000);
      expect(moved.status).toBe('now');
      expect(moved.timerStart).toBe(1000);
      expect(mgr.nowTask).not.toBeNull();
      expect(mgr.backpack).toHaveLength(0);
    });

    it('enforces single-task rule', () => {
      const t1 = createTask('first', 10);
      const t2 = createTask('second', 10);
      mgr.addToBackpack(t1);
      mgr.addToBackpack(t2);
      mgr.moveToNow(t1.id);
      expect(() => mgr.moveToNow(t2.id)).toThrow('occupied');
    });

    it('throws if task not in backpack', () => {
      expect(() => mgr.moveToNow('nonexistent')).toThrow('not found');
    });

    it('nowTask is null initially', () => {
      expect(mgr.nowTask).toBeNull();
    });
  });

  describe('completing tasks', () => {
    it('completes the Now task', () => {
      const task = createTask('Finish', TASK_POINTS.MEDIUM);
      mgr.addToBackpack(task);
      mgr.moveToNow(task.id, 1000);
      const completed = mgr.completeNowTask(61000); // 60s later

      expect(completed.status).toBe('done');
      expect(completed.timerElapsedSeconds).toBe(60);
      expect(completed.completedAt).toBe(61000);
      expect(mgr.nowTask).toBeNull();
      expect(mgr.done).toHaveLength(1);
    });

    it('throws when completing empty Now', () => {
      expect(() => mgr.completeNowTask()).toThrow('No task in Now');
    });

    it('accumulates totalPointsEarned', () => {
      for (let i = 0; i < 3; i++) {
        const t = createTask(`t-${i}`, 10);
        mgr.addToBackpack(t);
        mgr.moveToNow(t.id, i * 1000);
        mgr.completeNowTask((i + 1) * 1000);
      }
      expect(mgr.totalPointsEarned).toBe(30);
      expect(mgr.done).toHaveLength(3);
    });
  });

  describe('returning tasks', () => {
    it('returns Now task to Backpack', () => {
      const task = createTask('Return me', TASK_POINTS.LARGE);
      mgr.addToBackpack(task);
      mgr.moveToNow(task.id, 1000);
      const returned = mgr.returnToBackpack(11000); // 10s later

      expect(returned.status).toBe('backpack');
      expect(returned.timerElapsedSeconds).toBe(10);
      expect(returned.timerStart).toBeNull();
      expect(mgr.nowTask).toBeNull();
      expect(mgr.backpack).toHaveLength(1);
    });

    it('throws when returning from empty Now', () => {
      expect(() => mgr.returnToBackpack()).toThrow('No task in Now');
    });
  });

  describe('full lifecycle', () => {
    it('supports complete day workflow', () => {
      const t1 = createTask('Architecture', TASK_POINTS.LARGE);
      const t2 = createTask('README', TASK_POINTS.SMALL);
      const t3 = createTask('Deploy', TASK_POINTS.MEDIUM);

      mgr.addToBackpack(t1);
      mgr.addToBackpack(t2);
      mgr.addToBackpack(t3);
      expect(mgr.backpackPointsUsed).toBe(160);

      // Work on t1
      mgr.moveToNow(t1.id, 0);
      mgr.completeNowTask(60000);
      expect(mgr.totalPointsEarned).toBe(100);

      // Try t3, return it
      mgr.moveToNow(t3.id, 60000);
      mgr.returnToBackpack(90000);
      expect(mgr.nowTask).toBeNull();
      expect(mgr.backpack).toHaveLength(2);

      // Complete t2
      mgr.moveToNow(t2.id, 90000);
      mgr.completeNowTask(120000);
      expect(mgr.totalPointsEarned).toBe(110);
    });
  });
});
