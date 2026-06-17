/**
 * Task Manager — 3-Column Lifecycle.
 *
 * Zones: Backpack (plan) → Now (focus) → Done (completed)
 * Enforces single-task rule on Now and capacity limit on Backpack.
 */

import { randomUUID } from 'crypto';

/** Valid point values for tasks. */
export const TASK_POINTS = { SMALL: 10, MEDIUM: 50, LARGE: 100 };

/** Default daily capacity for the Backpack zone. */
export const DEFAULT_CAPACITY = 300;

/**
 * Create a new task object.
 * @param {string} title
 * @param {number} points - Must be 10, 50, or 100.
 * @returns {object}
 */
export function createTask(title, points) {
  const validPoints = [TASK_POINTS.SMALL, TASK_POINTS.MEDIUM, TASK_POINTS.LARGE];
  if (!validPoints.includes(points)) {
    throw new Error(`Invalid points value: ${points}. Must be one of ${validPoints.join(', ')}`);
  }
  if (!title || typeof title !== 'string') {
    throw new Error('Title must be a non-empty string');
  }
  return {
    id: randomUUID(),
    title,
    points,
    status: 'backpack',
    timerStart: null,
    timerElapsedSeconds: 0,
    completedAt: null,
  };
}

export class TaskManager {
  /**
   * @param {number} [capacity=DEFAULT_CAPACITY] - Max points in Backpack.
   */
  constructor(capacity = DEFAULT_CAPACITY) {
    this._capacity = capacity;
    this._backpack = [];
    this._now = null;
    this._done = [];
  }

  get capacity() {
    return this._capacity;
  }

  get backpack() {
    return [...this._backpack];
  }

  get nowTask() {
    return this._now;
  }

  get done() {
    return [...this._done];
  }

  /** Total points currently in the backpack. */
  get backpackPointsUsed() {
    return this._backpack.reduce((sum, t) => sum + t.points, 0);
  }

  /** Points remaining before capacity is reached. */
  get backpackPointsRemaining() {
    return this._capacity - this.backpackPointsUsed;
  }

  /** Total points earned from completed tasks. */
  get totalPointsEarned() {
    return this._done.reduce((sum, t) => sum + t.points, 0);
  }

  /**
   * Add a task to the Backpack.
   * @param {object} task - Created via createTask().
   */
  addToBackpack(task) {
    if (this.backpackPointsUsed + task.points > this._capacity) {
      throw new Error(
        `Cannot add task (${task.points} pts): would exceed capacity of ${this._capacity} pts ` +
        `(${this.backpackPointsUsed} pts used)`
      );
    }
    task.status = 'backpack';
    this._backpack.push(task);
  }

  /**
   * Move a task from Backpack to Now (active focus).
   * @param {string} taskId
   * @param {number} [timestamp] - Optional ISO timestamp or epoch ms for timer start.
   * @returns {object} The task moved to Now.
   */
  moveToNow(taskId, timestamp = Date.now()) {
    if (this._now !== null) {
      throw new Error('Now zone is occupied. Complete or return the current task first.');
    }
    const idx = this._backpack.findIndex(t => t.id === taskId);
    if (idx === -1) {
      throw new Error(`Task '${taskId}' not found in Backpack.`);
    }
    const [task] = this._backpack.splice(idx, 1);
    task.status = 'now';
    task.timerStart = timestamp;
    this._now = task;
    return task;
  }

  /**
   * Complete the current Now task and move it to Done.
   * @param {number} [timestamp] - Optional timestamp for completion.
   * @returns {object} The completed task.
   */
  completeNowTask(timestamp = Date.now()) {
    if (this._now === null) {
      throw new Error('No task in Now zone to complete.');
    }
    const task = this._now;
    if (task.timerStart !== null) {
      task.timerElapsedSeconds += (timestamp - task.timerStart) / 1000;
    }
    task.timerStart = null;
    task.status = 'done';
    task.completedAt = timestamp;
    this._now = null;
    this._done.push(task);
    return task;
  }

  /**
   * Return the current Now task back to the Backpack.
   * @param {number} [timestamp] - Optional timestamp.
   * @returns {object} The returned task.
   */
  returnToBackpack(timestamp = Date.now()) {
    if (this._now === null) {
      throw new Error('No task in Now zone to return.');
    }
    const task = this._now;
    if (task.timerStart !== null) {
      task.timerElapsedSeconds += (timestamp - task.timerStart) / 1000;
    }
    task.timerStart = null;
    task.status = 'backpack';
    this._now = null;
    this._backpack.push(task);
    return task;
  }

  /**
   * Remove a task from the Backpack entirely.
   * @param {string} taskId
   * @returns {object} The removed task.
   */
  removeFromBackpack(taskId) {
    const idx = this._backpack.findIndex(t => t.id === taskId);
    if (idx === -1) {
      throw new Error(`Task '${taskId}' not found in Backpack.`);
    }
    return this._backpack.splice(idx, 1)[0];
  }
}
