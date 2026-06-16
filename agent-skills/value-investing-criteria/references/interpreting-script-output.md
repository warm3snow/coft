# Interpreting stock_analysis.py Output for Value Investing

This reference maps the raw output of `scripts/stock_analysis.py` to the Buffett/Duan Yongping evaluation criteria. Use it after running the script to answer "is this a good business?"

## Quick Reference: Script Fields → Framework Criteria

| Script Column | Framework Criterion | What to Look For |
|---------------|-------------------|------------------|
| `销售毛利率` | Moat (pricing power) | **Excellent:** >60%, stable for years. **Warning:** <20% or negative = commodity business with no pricing power |
| `销售净利率` | Business quality | **Excellent:** >20%. **Average:** 5-10%. **Poor:** <5% or negative |
| `净资产收益率` (ROE) | Capital efficiency | **Excellent:** >20% sustained. **Good:** 15-20%. **Poor:** <10% or wildly volatile |
| `资产负债率` | Financial safety | **Conservative:** <20%. **Average:** 20-35%. **Risky:** >50% |
| `营业总收入同比增长率` | Predictability | **Stable:** 5-15% every year. **Warning:** Negative or wildly swinging = cyclical |
| `净利润同比增长率` | Earnings stability | **Ideal:** Positive every year. **Red flag:** Alternating positive/negative = no moat |
| `每股经营现金流` | Earnings quality | Should be ≥ EPS (net profit). Persistent negative OCF while reporting profit = accounting risk |
| `存货周转天数` | Demand health | Stable or slowly increasing = normal. **Spiking 3x+** = demand collapse (red flag) |
| `应收账款周转天数` | Customer payment | Increasing = customers are delaying payment (weak bargaining position). Decreasing = strong |
| `流动比率 / 速动比率` | Liquidity | Current ratio >1.5, quick ratio >1.0 = healthy. Below 1.0 = liquidity risk |

## Reading the "Full Financial History" Output

The script outputs raw panel data. Here's how to extract the signal:

### Step 1: Find the annual periods

Annual reports are rows where `报告期` is a plain year (e.g. `2022`, `2023`) or ends in `12-31`. Skip quarterly/half-year rows for the big picture.

### Step 2: Trace the 5-year trajectory

Look for these patterns in the annual rows (read bottom → top for chronological):

```
# GOOD BUSINESS PATTERN (茅台-like)
2021: 营收+16%, 净利+12%, 毛利率>91%, ROE>29%
2022: 营收+17%, 净利+20%, 毛利率>91%, ROE>30%
2023: 营收+18%, 净利+19%, 毛利率>91%, ROE>34%
2024: 营收+16%, 净利+15%, 毛利率>91%, ROE>36%
2025: 营收-1%,  净利-5%,  毛利率>91%, ROE>33%
→ Signs: margins stable through cycles, ROE always >25%, revenue nearly always up

# BAD BUSINESS PATTERN (振华新材-like)
2021: 营收+432%, 净利+343%, 毛利率15%,  ROE 22%
2022: 营收+153%, 净利+208%, 毛利率14%,  ROE 36%   ← peak year
2023: 营收-51%,  净利-92%,  毛利率6.8%, ROE 2.6%  ← collapse
2024: 营收-71%,  净利转负,  毛利率-13%, ROE -11%  ← crisis
2025: 营收-27%,  净利仍亏,  毛利率-13%, ROE -10%  ← still bleeding
→ Signs: boom-bust cycle, margins disappear in downturn, negative profits
```

### Step 3: Check the warning indicators

From the script output, these are the specific values that kill the Buffett/Duan Yongping thesis:

| Finding | Verdict | Reasoning |
|---------|---------|-----------|
| Gross margin < 0% (negative) | ❌ Insta-skip | Selling below cost — business model broken |
| Gross margin < 20% | ⚠️ Weak moat | No pricing power, commodity-like |
| ROE volatile: 36% → -10% | ❌ Not predictable | Earnings aren't durable |
| Revenue down 90% from peak | ❌ Extreme cyclicality | Duan Yongping explicitly avoids this |
| Debt ratio > 50% | ⚠️ Fragile | Can't survive a prolonged downturn |
| OCF negative for 2+ years | ❌ Self-funding broken | Burning cash, need capital |
| Inventory days 50→330 | ❌ Demand vanished | Products not moving |

## The Script + Framework Workflow

```
1. Run:  python3 scripts/stock_analysis.py 688707

2. Scan the "完整财务历史" table:
   [ ] Gross margin trend → stable? declining? negative?
   [ ] ROE trend → consistently >15%? volatile?
   [ ] Revenue growth → each year positive? or boom-bust?
   [ ] Debt ratio → under 35%?
   [ ] OCF per share → positive?

3. Quick score:
   All 5 pass → strong candidate for Buffett/Duan Yongping
   3-4 pass → investigate further (moat depth, management)
   0-2 pass → likely a value trap or cyclical commodity play
```

## Example: 振华新材 (688707) Scorecard (2026-06)

| Criterion | Value | Pass? | Note |
|-----------|-------|-------|------|
| Gross margin | -13% to -20% | ❌ | Selling below cost for 3 years |
| Net margin | -27% to -52% | ❌ | Deeply loss-making |
| ROE | -11% (trending down) | ❌ | Destroying shareholder value |
| Revenue stability | 139亿→14亿 (-90%) | ❌ | Extreme cyclical collapse |
| Debt ratio | 39% | ⚠️ | Manageable, but decreasing via losses |
| OCF per share | -0.40 (2026Q1) | ❌ | Cash burn resumed |
| Moat type | None | ❌ | Commodity cathode materials |
| **Overall** | **Fails all criteria** | **❌** | **Value trap, skip** |
