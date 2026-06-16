---
name: hong-kong-stock-analysis
title: Hong Kong Stock Analysis using akshare
description: Analyze Hong Kong-listed stocks using akshare library — price data, financial statements, valuation metrics, dividend records, company profiles. Covers all HKEX stocks (Tencent, Meituan, Alibaba, etc.).
---

# Hong Kong Stock Analysis (港股分析)

Use this skill when the user asks about **Hong Kong-listed stocks** — price analysis, financial health, valuation, dividend yield, or fundamental research for any HKEX stock (e.g. 01896 猫眼娱乐, 0700 腾讯, 9988 阿里巴巴, 3690 美团).

## Prerequisites

- `akshare` must be installed (`uv pip install akshare -q` or `pip install akshare -q`)
- Run analysis via `python3 -c "..."` in `terminal()` — akshare is synchronous and works well in short Python snippets.
- Set `pd.set_option('display.max_rows', 200)` and `pd.set_option('display.width', 300)` for readable output.

## Core Workflow

### 1. Get Daily Price Data

```python
import akshare as ak
import pandas as pd
pd.set_option('display.max_rows', 200)
pd.set_option('display.width', 300)

df = ak.stock_hk_daily(symbol='01896', adjust='qfq')
```

Key notes:
- `symbol` is the HK stock code (without `.HK` suffix) — e.g. `'01896'` for 猫眼, `'00700'` for 腾讯
- `adjust='qfq'` applies forward-adjusted prices (for dividend/split adjustments)
- Returns columns: `date, open, high, low, close, volume, amount`
- **Important**: The `date` column is **datetime64**, not string. Filter by year with `df[df['date'].dt.year == 2026]`.

#### Useful analysis patterns:

```python
# Annual performance
for yr in [2021, 2022, 2023, 2024, 2025]:
    d = df[df['date'].dt.year == yr]
    if not d.empty:
        chg = (d.iloc[-1]['close'] - d.iloc[0]['close']) / d.iloc[0]['close'] * 100
        print(f'{yr}: {d.iloc[0]["close"]:.2f}→{d.iloc[-1]["close"]:.2f} ({chg:+.2f}%), high={d["high"].max():.2f}, low={d["low"].min():.2f}')

# Moving averages
recent = df.tail(60)
print(f'MA5: {recent.tail(5)["close"].mean():.3f}')
print(f'MA20: {recent.tail(20)["close"].mean():.3f}')
print(f'MA60: {recent["close"].mean():.3f}')

# 52-week range
year = df.tail(250)
print(f'52w高: {year["high"].max():.2f}')
print(f'52w低: {year["low"].min():.2f}')
print(f'距52w高: {(year["high"].max()-df.iloc[-1]["close"])/year["high"].max()*100:.1f}%')

# All-time high
ath = df['high'].max()
ath_date = df[df['high'] == ath].iloc[0]['date']
print(f'历史最高: {ath:.2f} ({ath_date.strftime("%Y-%m-%d")})')
print(f'从ATH跌幅: {(df.iloc[-1]["close"]-ath)/ath*100:.1f}%')
```

### 2. Get Company Profile & Business Description

```python
df = ak.stock_hk_company_profile_em(symbol='01896')
print(df['公司介绍'].values[0])
```

Also available: `stock_hk_security_profile_em`, `stock_individual_basic_info_hk_xq` (snowball).

### 3. Get Financial Indicators (核心财务数据)

```python
df = ak.stock_financial_hk_analysis_indicator_em(symbol='01896')
# Returns: REVENUE, NET_PROFIT, EPS, BPS, ROE, ROA, GROSS_MARGIN, 
#          DEBT_RATIO, OCF_PER_SHARE, etc. for each fiscal year
```

Key columns:
- `OPERATE_INCOME`: 营业总收入
- `HOLDER_PROFIT`: 净利润 (归母)
- `BASIC_EPS`: 基本每股收益
- `BPS`: 每股净资产
- `ROE_AVG`: 平均ROE (%)
- `ROA`: 总资产回报率 (%)
- `GROSS_PROFIT_RATIO`: 毛利率 (%)
- `NET_PROFIT_RATIO`: 净利率 (%)
- `DEBT_ASSET_RATIO`: 资产负债率 (%)
- `PER_NETCASH_OPERATE`: 每股经营现金流
- `OPERATE_INCOME_YOY`: 营收同比增速 (%)
- `HOLDER_PROFIT_YOY`: 净利润同比增速 (%)

### 4. Get Valuation Snapshot

```python
df = ak.stock_hk_financial_indicator_em(symbol='01896')
# Returns single row with: PE, PB, dividend yield, market cap, P/S, ROE, etc.
```

Key fields:
- `市盈率`: PE (TTM)
- `市净率`: PB
- `基本每股收益(元)`: EPS
- `每股净资产(元)`: BPS
- `每股股息TTM(港元)`: DPS
- `股息率TTM(%)`: Dividend yield
- `派息比率(%)`: Payout ratio
- `总市值(港元)`: Market cap
- `股东权益回报率(%)`: ROE

### 5. Get Valuation Comparison (行业对比)

```python
df = ak.stock_hk_valuation_comparison_em(symbol='01896')
# Shows PE, PB, PS, PC rankings within HK stocks
```

### 6. Get Dividend History

```python
df = ak.stock_hk_dividend_payout_em(symbol='01896')
# Returns: 分红方案, 除净日, 发放日, 财政年度
```

### 7. Get Financial Reports (利润表/资产负债表/现金流量表)

```python
df = ak.stock_financial_hk_report_em(symbol='01896')  # May be sparse
```

For deeper financial data, try:
- `stock_profit_sheet_by_yearly_em` for profit sheet
- `stock_financial_analysis_indicator` for general financial analysis

## Fallback: When akshare is Not Available

If `akshare` is not installed (ModuleNotFoundError), use **Sina Finance API + browser-based news gathering** as a fallback:

### 1. Real-time Quote (Sina API)

```bash
curl -sL 'https://hq.sinajs.cn/list=hk02228' \
  -H 'Referer: https://finance.sina.com.cn' \
  -H 'User-Agent: Mozilla/5.0'
```

Returns: `var hq_str_hk02228="XTALPI,晶泰控股,7.150,7.090,7.150,6.740,6.900,-0.190,-2.680,6.89000,6.90000,585167405,84512173,0.000,0.000,15.120,5.020,2026/06/09,14:52"`

Fields in order: name, open, prev_close, high, low, price, change, change%, bid, ask, volume, turnover, N/A, N/A, 52w_high, 52w_low, date, time

The response is GBK-encoded — pipe through `iconv -f gbk -t utf-8` if Chinese characters show garbled.

### 2. Company Overview & Fundamentals (Sina Browser Page)

Navigate `browser_navigate(url='https://stock.finance.sina.com.cn/hkstock/quotes/02228.html')` and extract from the snapshot:

- **Price panel**: current price, change%, PE, 52-week high/low, market cap, total shares, dividend yield
- **Recent announcements**: "实时公告" section (may contain legacy announcements from prior code holders)
- **Navigation links**: "公司介绍", "财务摘要", "综合损益", "资产负债" link to detail pages

The accessibility-tree snapshot provides structured data in list items — extract key-value pairs by reading the StaticText nodes.

### 3. Financial News & Reports (Bing News via Browser)

Navigate to Bing News search:

```
browser_navigate(url='https://www.bing.com/news/search?q=<company_name>+<stock_code>&setlang=zh-Hans')
```

Scroll to reveal results: `browser_scroll(direction='down')` + `browser_snapshot()`. Each result card contains:
- Headline (link with heading)
- Source name and date
- Summary snippet with key financial data

### 4. Price History (Alternative Data Sources)

| Source | URL Pattern | Notes |
|--------|-----------|-------|
| Sina real-time | `https://hq.sinajs.cn/list=hk02228` | Current quote only, GBK encoding |
| Sina finance page | `https://stock.finance.sina.com.cn/hkstock/quotes/02228.html` | Full overview with financial links |
| Bing News | `https://www.bing.com/news/search?q=<name>+<code>&setlang=zh-Hans` | Recent news, financial reports, analyst coverage |
| EastMoney News | `https://so.eastmoney.com/news/s?keyword=<name>+<code>&pageindex=1&searchrange=all` | Best fallback when Bing CAPTCHA-blocks; 10,000+ results; less bot-detection aggressive |

### Limitations of the Fallback

- No easy access to multi-year historical daily OHLCV data
- No standardized financial statement tables (revenue, profit, ROE, etc.)
- Must extract financial data from news snippets and company announcements
- Browser-based — slower than direct API calls
- Stock code 02228 may have legacy announcements from a prior code-holder (HKEX recycles codes); filter by relevance

Install akshare (`uv pip install akshare -q`) for deep analysis when it's available in the environment.

## Extended Analysis: Beyond the Numbers

After collecting price, financial, and valuation data, extend the analysis in two directions before delivering recommendations.

### Industry & Competitive Analysis

**1. Structural vs Cyclical Decline**

Before recommending action, determine whether the stock's price decline reflects:

| Type | Signal | Implication |
|------|--------|-------------|
| **Cyclical** | Industry-wide downturn, macro-driven, temporary | Hold / add on weakness |
| **Structural** | Business model being disrupted, moat eroding, market share loss permanent | Consider exit regardless of price |
| **Both** | Cyclical downturn accelerating structural shifts | Most dangerous — requires deepest analysis |

**2. Competitor Staging Methodology**

When a disruptor threatens the company's core business, characterize the competitor's strategy evolution:

- **Phase 1 — Adjacent**: Competitor uses the company's product as supply/content source (e.g., Douyin as movie trailer distribution)
- **Phase 2 — Transaction**: Competitor captures the transaction directly (e.g., Douyin selling movie tickets via live-streaming)
- **Phase 3 — Full Stack**: Competitor builds complete competing infrastructure (e.g., Douyin with full movie-ticketing UX including seat selection, refunds, membership)

The deeper into Phase 3, the more structural the threat.

**3. Market Share Triangulation**

Estimate competitor market share even without official data:
- From annual report disclosures of the company and its peers
- From news articles citing analyst estimates or internal data
- From South-bound (北向) / institutional holding changes
- Always caveat as estimates and test sensitivity (±10-15%)

**4. The "Three Lives" (三条命) Framework for Companies in Transition**

Evaluate a company through three concurrent business "lives":

```
第一条命 (Dying/Breaking):   The legacy business being disrupted
  → Is it profitable, stable, declining? How fast?
  → Can it be defended or only delayed?

第二条命 (Transitional/Core): The current profitable business
  → Is it growing or stagnating?
  → Is the transition toward it complete?

第三条命 (Future/Embryonic): The next growth engine being built
  → Is it real or lab-stage?
  → How much investment does it need? When might it pay off?
```

Each "life" has a different valuation. The current stock price is the weighted sum. This framework helps separate market emotions about "Life 1" from the actual value of "Life 2+3."

### Investment Decision Framework (Position Management)

When the user asks "what should I do with this stock" (holding a position, often at a loss), use this structured approach.

**1. Entry Point Recovery**

First, deduce the user's approximate entry cost from:
- "跌了N%" → cost = current_price / (1 - N/100)
- 52-week high/low context → which part of the range they likely entered
- Historical news buzz periods (IPO, breakout peaks, analyst initiations)

**2. The Three-Option Framework**

Present three clear options with who each fits:

| Option | Description | Best For |
|--------|-------------|----------|
| **A. Hold / Add** (等待/补仓) | Hold existing position, add at price triggers | Long-term believers, patient capital |
| **B. Stop-Loss / Switch** (止损换股) | Cut position, reallocate to better risk/reward | Opportunity-cost-focused, funds needed soon |
| **C. Partial Risk-Management** (分批减仓) | Sell 1/3 now, hold 1/3 for catalyst, keep 1/3 for dividend | User unsure, wants compromise |

**3. Downside Scenario Analysis (最坏情况)**

Compute a worst-case floor valuation:

```python
# Mental math template:
worst_case_earnings = current_earnings * disruption_factor  # e.g., 0.5-0.7
worst_case_pe = 8  # Conservative PE for HK value stocks
floor_market_cap = worst_case_earnings * worst_case_pe
floor_price = floor_market_cap / total_shares
downside_from_current = (floor_price - current_price) / current_price
```

Caveat this as "拍脑袋" (guesstimate) — clearly frame it as directional, not precise.

**4. Key Catalysts Checklist**

Identify forward-looking events that will change the thesis:

```
[ ] Upcoming earnings — revenue/profit growth trajectory
[ ] Competitive moves — new entrants, regulatory changes
[ ] Dividend changes — increases signal confidence, cuts signal trouble
[ ] Major shareholder moves — insider buying/selling
[ ] Industry catalysts — seasonality, new product cycles, macro triggers
```

**5. Final Framework Application**

Apply the "old stock vs new stock" test:
- **Old stock**: You'd buy it today at this price if you didn't already own it? → Hold
- **New stock**: You wouldn't buy it fresh today? → The sunk-cost fallacy is speaking → Consider exit

---

## Multi-Agent Trade Orchestration Pipeline

For deep dives where the user wants a comprehensive investment thesis (not just data), use this parallel pipeline to produce a synthesized final decision. **The orchestrator does NOT do data collection** — it defines the scope, dispatches subagents, resolves contradictions, and synthesizes.

### Pipeline Overview

```
Step 1 — Task Definition
   Identify the thesis question (buy/hold/sell? what price?)
   Determine analysis dimensions (usually 3: industry, valuation/argumentation, technical)
   → Output: todo list + subagent task specifications

Step 2 — Parallel Dispatch
   Dispatch 2-3 subagents via delegate_task(tasks=[...]):
   
   a) Macro / Industry / Competitive
      - Industry structure & trends
      - Competitor threat staging (Phase 1/2/3)
      - Policy & regulatory landscape
      - "Three Lives" framework application
   
   b) Bull vs Bear Argumentation
      - Both sides with hard data (not opinions)
      - Normalized earnings vs headline earnings
      - Conflict Map: facts both sides agree on but interpret differently
   
   c) Technical Analysis
      - Moving average alignment
      - RSI / Bollinger Bands / volume analysis
      - Support & resistance levels
      - Pattern recognition (W-bottom, descending channel, etc.)
   
   → Each subagent returns a structured analysis + writes to a file

Step 3 — Collection & Risk Review
   Collect all subagent outputs
   Identify contradictions between bull/bear/technical views
   → Output: Conflict Map with resolution direction

Step 4 — Scenario Analysis
   Base case (50% prob): most likely outcome
   Bull case (20% prob): what needs to go right
   Bear case (30% prob): worst-case downside
   → Output: 3 scenarios with price targets and probability

Step 5 — Final Synthesis
   Weighted multi-factor score → decision recommendation
   "Old stock vs New stock" test applied
   3-Option Framework (hold/add, stop-loss/switch, partial risk-management)
   Key monitoring triggers (catalyst checklist)
   → Output: synthesized report with clear recommendation
```

### When to Use This Pipeline

Use it when the user asks for an in-depth investment opinion, "分析走势", "怎么看这个股票", or "未来走势" on a specific stock they hold or are considering. Single-agent data gathering is fine for price checks, simple questions, or just providing data.

### Pipeline Pitfalls

1. **No conversation memory in subagents** — Pass all relevant constraints (language, format, specific data points) in the `context` field. If the user writes in Chinese, include `"respond in Chinese"` in context, or subagents default to English.

2. **Subagents are self-reporting** — Always verify key claims (file creation, price levels) after they return. A subagent that says "file written" may be wrong.

3. **Max 3 concurrent subagents** — Configured via `delegation.max_concurrent_children`. For this user: 3.

4. **Total token cost is high** — Each subagent consumes its own context budget. ~300-500K input tokens per pipeline run is normal. Use this for high-value queries only.

5. **Language consistency** — Always pass the user's language in context for every subagent to avoid mixed-language output.

6. **Intermediate files** — Subagents may write to project directories. Clean up or note file locations in the final response.

7. **Score weighting calibration** — The multi-factor score is a directional tool, not a precise measure. Weight dimensions by what matters most for the specific stock (e.g., competitive threat weight > technicals for a structural-decline story).

---

## Key Pitfalls

1. **Stock code format**: Hong Kong stock codes are 5 digits with leading zeros (e.g., `'00700'` for Tencent, not `'700'`). Use `'01896'`, not `'1896'`.

2. **Date column type**: `stock_hk_daily()` returns `date` as **datetime64**. Use `.dt.year` for year filtering, not `.str.startswith()`.

3. **Multiple akshare sources**: Different akshare functions may return slightly different data for the same stock. Cross-reference if precision matters.

4. **Missing financial data**: Not all HK stocks have complete financial data in akshare. If a function returns empty, try an alternative function from `[f for f in dir(ak) if 'hk' in f.lower()]`.

5. **Adjustment method**: `adjust='qfq'` is forward-adjusted. For unadjusted prices, omit the parameter. Always use qfq for dividend-adjusted analysis.

6. **PE interpretation**: HK stock PE tends to be lower than A-shares. PE < 10 is common for value stocks. PB < 1 (破净) is a significant signal.

7. **HKD vs CNY**: Financial data may be reported in HKD or CNY. Check the `CURRENCY` column in financial indicators.

8. **Bing CAPTCHA blocking**: Bing frequently throws CAPTCHA challenges when accessed via headless browser. When blocked, switch to EastMoney News search (`https://so.eastmoney.com/news/s?keyword=<name>+<code>&pageindex=1&searchrange=all`) as the primary news source. It's less bot-detection aggressive and returns 10,000+ results.

9. **Structural vs Cyclical confusion**: A stock can be down 50% and look "cheap" but still be a value trap. Always distinguish: is the decline from a cyclical industry downturn (hold/add) or from a structural business model disruption (consider exit regardless of price)? The "Three Lives" framework helps separate these.

10. **Sunk cost fallacy in position advice**: When a user asks about a stock they already hold at a loss, apply the "old stock vs new stock" test before recommending: "If you had cash today, would you buy this stock at this price?" If no → the position is held for emotional reasons, not rational conviction.

## When to Use This Skill

- User asks about any HKEX-listed stock (price, fundamentals, valuation)
- User says "分析这只港股" or names a specific HK stock
- Comparing valuation metrics across HK stocks
- Dividend/income analysis for HK-listed companies

## Reference Files

- `references/maoyan-01896-analysis.md` — Full worked example: 猫眼娱乐 2026年6月 analysis showing yearly performance, financial indicators, valuation metrics, Buffett/Duan Yongping framework, competitive analysis (抖音三步走/threat staging), "three lives" framework, position management decision tree, and worst-case downside scenario.
- `references/maoyan-01896-orchestration-pipeline-2026-06.md` — Full Multi-Agent Trade Orchestration Pipeline worked example: task definition, parallel subagent specs (industry/bull-bear/technical), conflict resolution, weighted scoring, scenario analysis, three-option recommendation, and candidate stock screening logic.
- `references/xtalpi-02228-analysis.md` — Worked example using Sina+Bing+EastMoney fallback when akshare is unavailable; covers CB dilution analysis, stock code recycling pitfall, Bing CAPTCHA blocking fallback, "three lives" framework for an early-stage high-growth company, and 3-option recommendation for a user down 50%.

## When NOT to Use This Skill

- A-share stocks (use 沪深 stock functions instead)
- US-listed Chinese stocks (use US stock functions)
- Futures/commodities (use chinese-futures-analysis skill)
