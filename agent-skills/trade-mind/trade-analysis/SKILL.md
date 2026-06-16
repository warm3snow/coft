---
name: trade-analysis
title: Trade Analysis
description: Parse raw trade records and convert them into structured trading data — win rate, avg profit/loss, profit factor, holding time, and full trade table.
---

# Trade Analysis Skill

## Purpose

Analyze raw trade records and convert them into structured trading data.

## Input

Supported input sources:
- Trade history / order history / position history
- Broker exports / CSV files
- Screenshots (via OCR when structured data unavailable)

## Tasks

### Extract per-trade

For each trade, extract:
- Symbol
- Direction (Long / Short)
- Entry time
- Exit time
- Entry price
- Exit price
- Position size
- Profit and Loss (absolute and %)

### Calculate aggregate metrics

From the extracted trade set, compute:
- **Win rate** — % of profitable trades
- **Average profit** — mean profit across winning trades
- **Average loss** — mean loss across losing trades
- **Profit factor** — gross profit / gross loss
- **Average holding time** — mean duration from entry to exit
- **Max consecutive wins / losses**
- **Largest winning / losing trade**

## Handling ambiguity

- If entry/exit times are missing, flag the trade as incomplete and note the gap.
- If position size is implicit (e.g., 1 contract = standard lot), document the assumption.
- If data contains partial fills, merge them into a single trade entry.

## Output schema

Return structured JSON:

```json
{
  "summary": {
    "total_trades": 0,
    "win_rate": 0.0,
    "avg_profit": 0.0,
    "avg_loss": 0.0,
    "profit_factor": 0.0,
    "avg_holding_hours": 0.0,
    "max_consecutive_wins": 0,
    "max_consecutive_losses": 0,
    "largest_win": 0.0,
    "largest_loss": 0.0
  },
  "trades": [
    {
      "symbol": "string",
      "direction": "Long|Short",
      "entry_time": "ISO8601",
      "exit_time": "ISO8601",
      "entry_price": 0.0,
      "exit_price": 0.0,
      "position_size": 0,
      "pnl": 0.0,
      "pnl_pct": 0.0
    }
  ]
}
```

## Quality checks

- All monetary values must be in the same denomination (default: USD).
- Validate that win_rate + loss_rate ≤ 1.0 (breakeven trades allowed).
- Report any data quality issues (missing fields, suspicious outliers) together with the output.
