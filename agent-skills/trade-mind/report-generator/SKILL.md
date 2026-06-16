---
name: report-generator
title: Trading Report Generator
description: Generate a professional trading review report synthesizing trade analysis, behavior analysis, risk analysis, and coaching recommendations into one document.
---

# Trading Report Skill

## Purpose

Generate a professional, readable trading review report that synthesizes all preceding analysis into one coherent deliverable.

## When to use

After trade-analysis, behavior-analysis, risk-analysis, and coaching have all completed. This skill produces the final output the user sees.

## Report structure

### 1. Executive Summary
- Time period covered
- Key takeaway (one sentence)
- Behavioral improvement score (compared to previous period, if available)
- Risk level (Low / Medium / High / Critical)

### 2. Trading Statistics
- Total trades, win rate, profit factor
- Average R-multiple per trade
- Top 3 best and worst trades (by R-multiple)
- Equity curve summary (starting / ending / peak / trough)

### 3. Behavior Analysis
- Detected patterns and their frequency
- Costliest behavior (P&L impact)
- Comparison to previous review (if available)
- Severity score

### 4. Risk Analysis
- Concentration, leverage, drawdown
- Risk score and level
- Critical and major risks listed with evidence

### 5. Coaching Recommendations
- Priority improvement area
- One corrective action (from coaching skill)
- Measurable target and timeline

### 6. Action Plan
- What to do in the next session
- What to do in the next week
- What to review in the next report

### 7. Weekly Goals
- Goal for this week
- Goal for next week (forward-looking)
- Success criteria for each

## Writing style

- **Professional** — suitable for a performance review with a mentor or fund.
- **Objective** — data-driven, no emotional language.
- **Evidence-based** — every claim references specific trade IDs or metrics.
- **Avoid hype** — no "you crushed it" or "amazing progress" unless backed by data.
- **Avoid market predictions** — the report is about the trader, not the market.

## Format

Render as clean markdown. Use tables for statistics, sections for narratives.
If a previous report exists, include a "Period-over-Period Comparison" subsection in the Executive Summary.

## Output

Return the full report as markdown text. No JSON wrapper — the report is the deliverable.
