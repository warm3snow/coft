---
name: behavior-analysis
title: Behavior Analysis
description: Identify recurring trading mistakes from trade records — chasing highs, averaging down, overtrading, revenge trading, FOMO, oversized positions, and other behavioral patterns.
---

# Behavior Analysis Skill

## Purpose

Identify recurring trading mistakes from structured trade data.

## Behavioral patterns to detect

| Pattern | Detection heuristic |
|---------|---------------------|
| Chasing highs | Entry near candle high / RSI > 70 zone, followed by quick reversal |
| Averaging down | Same symbol re-entered at lower price while still holding a losing position |
| Overtrading | Trade frequency > 3× the trader's own median for the period |
| Revenge trading | A trade entered within 15 minutes of a significant loss on prior trade |
| Emotional trading | Unusual position size spike (> 2× average) after a large win or loss |
| Oversized positions | Any single trade risking > 5% of account equity |
| No stop loss | Trade with exit > 3× average move without a recorded stop |
| Premature profit taking | Position closed < 30 min after entry with profit < 0.5× ATR |
| Holding losers too long | Position held for > 5× the trader's median holding time while in drawdown |
| FOMO | Trade entered during a parabolic move (> 3σ from 20-period MA) on low conviction |

## Analysis rules

- **Do not analyze market direction.** Analyze trader behavior only.
- Detection is evidence-based — every tagged pattern must cite the specific trade(s) that triggered it.
- Severity is rated against the trader's own historical behavior, not an absolute standard.

## Per-detected-behavior output

For each detected behavior, provide:

| Field | Description |
|-------|-------------|
| Evidence | List of trade IDs and data points that support this tag |
| Severity | Low / Medium / High |
| Frequency | Number of occurrences in this batch |
| Impact | Estimated P&L impact (absolute $ or % of total losses) |

## Output schema

```json
{
  "behavior_tags": [
    {
      "behavior": "chasing_highs",
      "evidence": ["trade_001", "trade_015"],
      "severity": "high",
      "frequency": 2,
      "impact_pnl": -425.0,
      "description": "Entered at candle highs during momentum spikes, both reversed >3%"
    }
  ],
  "root_causes": [
    "Fear of missing out on breakouts",
    "No pre-defined entry criteria before session"
  ],
  "severity_score": 7.5,
  "summary": "3 distinct behavior patterns detected. Overtrading is the most costly, contributing 62% of total losses this period."
}
```
