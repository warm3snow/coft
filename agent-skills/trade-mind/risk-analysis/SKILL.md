---
name: risk-analysis
title: Risk Analysis
description: Evaluate trading risk — position concentration, leverage, drawdown, volatility exposure, correlation risk. Risk comes before return.
---

# Risk Analysis Skill

## Purpose

Evaluate trading risk from structured trade data. Risk assessment is independent of behavior analysis — it evaluates portfolio-level exposure, not individual action patterns.

## Risk dimensions to analyze

| Dimension | Method |
|-----------|--------|
| Position concentration | % of equity in single positions; Herfindahl-Hirschman Index across symbols |
| Leverage | Notional exposure / account equity; peak and average across trades |
| Drawdown | Peak-to-trough equity decline; duration of max drawdown |
| Volatility exposure | Position size relative to ATR; % of trades with entry during high-VIX regimes |
| Correlation risk | Net long/short bias; sector concentration; overlapping positions in correlated symbols |

## Priority

Risk comes before return.

Identify risks that could cause significant capital loss (≥15% drawdown) before evaluating profitability.

## Evaluation rules

- Flag any single position > 5% of equity as a concentration risk.
- Flag any period where leverage > 3× for more than 5 consecutive trades.
- Flag drawdown exceeding 20% as critical regardless of subsequent recovery.
- If correlation data is unavailable, flag as "unable to assess — recommend symbol correlation review."

## Risk rating

| Score | Label | Condition |
|-------|-------|-----------|
| 0–2  | Low   | No flagged risk items |
| 3–5  | Medium | 1–2 flagged items |
| 6–8  | High  | 3–4 flagged items |
| 9–10 | Critical | ≥5 flagged items OR any single item rated critical |

## Output schema

```json
{
  "risk_score": 0,
  "risk_level": "low",
  "major_risks": [
    {
      "risk_type": "concentration",
      "description": "BTC position represents 42% of account equity",
      "severity": "critical",
      "action": "Reduce BTC exposure to max 15% of equity"
    }
  ],
  "minor_risks": [],
  "risk_actions": [
    "Set maximum position size to 5% of equity",
    "Diversify across at least 4 uncorrelated instruments"
  ]
}
```
