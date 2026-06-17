# Stillwork

> A focus-density task manager. One task. One moment. Your personal efficiency index.

---

## Philosophy

Stillwork is not a checklist app. It does not reward you for accumulating completed tasks — it measures the **density of your focus** in real time.

The core principle is simple: **one task at a time, in a calm and uncluttered space**. The app does not push, remind, or punish. It only reflects reality back to you — honestly and quietly.

---

## Quick Start

```bash
npm install
npm test              # run all tests
npm run test:coverage # run tests with coverage report
```

---

## Architecture

```
src/
  efficiencyIndex.js  — CBE formula: points / focus_minutes, displayed as .NNN
  taskManager.js      — 3-column lifecycle (Backpack → Now → Done)
  focusTimer.js       — Focus/Pause state machine with time tracking
  buffSystem.js       — Micro-habit rewards with cooldowns and expiration
  index.js            — Public API barrel export

tests/
  efficiencyIndex.test.js
  taskManager.test.js
  focusTimer.test.js
  buffSystem.test.js
  integration.test.js
```

---

## The Efficiency Index

```
Efficiency Index = Total points of completed tasks / Total active focus time (minutes)
```

Displayed without a leading zero, with exactly three decimal places:

```
.413     .650     .091
```

---

## Workspace — 3-Column Lifecycle

| Zone | Name | Rule |
|------|------|------|
| 1 | **Backpack** | Daily plan. Capacity limit (default 300 pts). |
| 2 | **Now** | Active focus. Single-task only. Timer auto-starts. |
| 3 | **Done** | Completed. Points added to index. |

Task point values: Small (10), Medium (50), Large (100).

---

## Focus States

| State | Effect |
|-------|--------|
| **Focus** | Timer runs. Index is live. |
| **Pause** | Timer stops. Index frozen. Safe rest. |

---

## Buffs

Micro-habit rewards (water, eye rest, stretch) grant temporary `+5%` bonuses to the efficiency index. Buffs stack additively and expire after their duration.

---

## License

MIT
