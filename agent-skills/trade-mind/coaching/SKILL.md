---
name: coaching
title: Trading Coaching
description: Convert behavior analysis and risk analysis into a structured coaching plan — corrective actions, measurable targets, and weekly goals.
---

# Trading Coaching Skill

## Purpose

Convert analysis output into actionable coaching recommendations. This is the bridge between "what went wrong" and "what to do next."

## Inputs

Requires both:
- **Behavior analysis** (from behavior-analysis skill or provided inline)
- **Risk analysis** (from risk-analysis skill or provided inline)

If either input is absent, flag it and proceed with available data.

## Process

1. **Identify the biggest mistake**
   - Out of all detected behaviors, select the one with the highest combined severity × frequency × impact score.
   - Explain why this is the priority target.

2. **Identify root cause**
   - Trace the mistake to its origin: is it lack of process, emotional trigger, knowledge gap, or environment?
   - Be specific — "entered breakouts without a volume confirmation filter" not "bad entries."

3. **Define one corrective action**
   - One action only. A single, concrete, enforceable rule or procedure.
   - Example: "Before any long entry, wait for the 5-minute candle to close above the 20 EMA AND volume > 1.5× 20-period average volume."

4. **Define a measurable target**
   - A quantifiable milestone that confirms the behavior is improving.
   - Example: "Reduce chasing-high trades from 4/week to ≤1/week within 2 weeks."

## Rules

- Never provide stock recommendations.
- Never provide market forecasts.
- Never provide entry / exit prices.
- Focus on behavior improvement only.
- If the user asks for market predictions, politely decline and redirect to process.

## Output

```json
{
  "session_id": "ISO8601-timestamp",
  "key_findings": [
    "3 of 5 losing trades were FOMO entries during hour 22:00–23:00",
    "Average loss on revenge trades is 2.8× larger than normal losing trades"
  ],
  "root_causes": {
    "primary": "Trading without a written plan — entries are reactive to price movement",
    "contributing": [
      "Late-night sessions correlate with higher emotional trading",
      "No pre-trade checklist"
    ]
  },
  "action_plan": {
    "priority_action": "Implement a mandatory 3-step pre-trade checklist: (1) mark key levels, (2) confirm setup pattern, (3) calculate R-multiple before entry",
    "measurable_target": "Zero trades entered without completing checklist for 14 consecutive sessions",
    "timeline": "2 weeks",
    "review_frequency": "Daily self-review first week, every-other-day second week"
  },
  "weekly_goals": [
    {
      "week": 1,
      "goal": "Log every entry reason in a journal. Target: 100% entries journaled.",
      "success_criteria": "Every trade timestamped with a 1-sentence entry rationale"
    },
    {
      "week": 2,
      "goal": "Reduce FOMO entries by 50%. Only enter when pre-defined levels are reached.",
      "success_criteria": "Max 2 FOMO-tagged trades for the week"
    }
  ]
}
```

## Follow-up

After the coaching session, offer to:
- Schedule a weekly review (set up a cron job).
- Save coaching history to profile memory for trend tracking.
