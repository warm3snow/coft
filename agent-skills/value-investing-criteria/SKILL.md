---
name: value-investing-criteria
title: Value Investing Analysis - Buffett and Duan Yongping Frameworks
description: Evaluate stocks against Warren Buffett's economic moat theory and Duan Yongping's (段永平) investment philosophy. Structured criteria for assessing business quality, management, and price.
---

# Value Investing Analysis - Buffett and Duan Yongping Frameworks

Use this skill when the user asks whether a stock fits **Warren Buffett's** or **Duan Yongping's (段永平)** investment philosophy. Apply structured criteria to evaluate business quality, competitive advantages (护城河), management quality, and valuation safety margin.

## Duan Yongping (段永平) Framework

Duan Yongping's core philosophy: **"Good business, Good company, Good price" (好生意、好公司、好价格)**.

### 1. Good Business (好生意)

Evaluate the business model itself:

| Criteria | What to Ask | Signal |
|----------|-------------|--------|
| **Excellent Business Model** | Is this business easy to make money? | High gross margin + high net margin + light assets |
| **Moat (壁垒)** | Why can't competitors beat it? | Brand premium / network effects / switching costs / scale advantage / patents |
| **Understandability** | Can I explain how it makes money in 5 minutes? | Simple, clear business |
| **Sustainability** | Will it exist in 10 years? Better or worse? | Long-term demand certainty |
| **Low Cyclicality** | Can it survive a recession? | Staples/addictive/necessity > discretionary/cyclical |

**Duan Yongping's favorite business models:** Apple (ecosystem lock-in), Moutai (unreplicable brand), Tencent (network effects). He avoids: strong cyclicality, fast-iterating hardware, pure channel/platform plays.

### 2. Good Company (好公司)

Evaluate management and culture:

| Criteria | What to Ask |
|----------|-------------|
| **Integrity** | Does management tell the truth? Any history of harming minority shareholders? |
| **Culture** | Is there a culture of "doing the right thing" (本分) and rational decision-making (平常心)? |
| **Capital Allocation** | Rational distribution of profits (buybacks/dividends/wise M&A)? No盲目多元化? |
| **Ownership Structure** | Are major shareholders' interests aligned with minority holders? |
| **Stop-Doing List** | Does management avoid: (1) businesses they don't understand (2) leverage (3) deceiving users? |

### 3. Good Price (好价格)

| Criteria | Assessment |
|----------|------------|
| **Reasonable Valuation** | Is PE in reasonable range? Duan's rule: "The better the business, the less price matters" |
| **Margin of Safety** | Is there enough safety margin for uncertainty? |
| **Long-term Return** | If it didn't rise for 5 years, would you still hold it? |

### Duan Yongping's Stop-Doing List (不为清单)

- Do not invest in businesses you don't understand
- Do not invest on margin / leverage
- Do not blindly diversify
- Do not short sell
- Do not trade frequently (think in years, not days)
- Do not invest in companies with dishonest management
- Do not invest in businesses with poor business models (no matter how cheap)

## Warren Buffett Framework

### Five Types of Economic Moat (护城河)

| Moat Type | Meaning | Examples | How to Assess |
|-----------|---------|----------|---------------|
| **Brand Moat** | Consumers pay premium for the brand | Moutai, Coca-Cola, Hermes | Is gross margin consistently above peers? Does brand affect purchase decisions? |
| **Switching Costs** | High cost to change providers | Banking systems, SAP, WeChat | How high is user migration cost? Data/relationship/habit lock-in? |
| **Network Effects** | More users = more value | Tencent, Meituan, Taobao | Is there a two-sided network? Does user growth increase the product's value? |
| **Cost Advantage** | Can produce/deliver at lower cost | Walmart, Southwest Airlines | Does it have unique production/logistics/scale cost advantages? |
| **Scale Advantage** | Scale itself creates barrier | TSMC, AWS | Does it require massive capital to catch up? |

### Buffett's Core Screening Criteria

```
[ ] Predictable earnings — net profit not too volatile over 10 years
[ ] High ROE (>15%, stable long-term) — best businesses have ROE >20%
[ ] Sustainable competitive advantage — moat is wide and not eroding
[ ] Conservative capital structure — low debt ratio, preferably no interest-bearing debt
[ ] Rational management — shareholder-oriented, wise capital allocation
[ ] Reasonable purchase price — buy great companies at fair prices, not mediocre companies at cheap prices
```

### Buffett's Indicator Cheat Sheet

| Metric | Excellent | Good | Average | Poor |
|--------|-----------|------|---------|------|
| ROE (5yr avg) | >20% | 15-20% | 10-15% | <10% |
| Gross Margin | >60% | 40-60% | 20-40% | <20% |
| Net Margin | >20% | 10-20% | 5-10% | <5% |
| Debt Ratio | <20% | 20-35% | 35-50% | >50% |
| Revenue (5yr CAGR) | >15% | 10-15% | 5-10% | <5% |
| FCF / Net Profit | >1.0 | 0.8-1.0 | 0.5-0.8 | <0.5 |

### Buffett's Evaluation Checklist

```
Gate 1: Can I understand this business?
  → If NO, skip

Gate 2: Does it have a sustainable competitive advantage?
  → What type of moat? Getting wider or narrower?
  → How quickly could competitors replicate it?

Gate 3: Is management excellent and rational?
  → Do they respect shareholders? Any related-party transactions?
  → Do they expand within their circle of competence?

Gate 4: Is the price reasonable?
  → PE vs historical range and peers
  → At current price, is the long-term return satisfactory?
  - If the stock market closed for 5 years, would you still hold it?
```

## Analysis Workflows

### Single Stock Deep Dive

Run the data collection script:

```bash
python3 ~/.hermes/skills/data-science/value-investing-criteria/scripts/stock_analysis.py <code> <名称>
```

**⚠️ Note the Python version**: If `python3` points to 3.14+ but akshare is installed under 3.11 (common on macOS with Homebrew), use:
```bash
/usr/local/bin/python3.11 ~/.hermes/skills/.../stock_analysis.py <code> <名称>
```

Then use the script output to fill in the **Analysis Template** below. See `references/interpreting-script-output.md` for guidance on mapping each script column to the framework criteria.

### Batch Index Screening (for indexes like 上证50/沪深300)

When evaluating an entire index (50-300 stocks), use a **two-phase approach** instead of running the script per-stock:

**Phase 1 — First-Pass Filter (all stocks):**
```python
# 1. Get financials for all stocks via 同花顺 (works from outside China)
fin = ak.stock_financial_abstract_ths(symbol=code)

# 2. Filter annual reports only
annual = fin[~fin['报告期'].astype(str).str.contains('-03-31|-06-30|-09-30', regex=False)]

# 3. Check Buffett/Duan Yongping gates:
#    - Gross margin >40%  (pricing power)
#    - Net margin >10%    (good business)
#    - ROE (annual) >15%  (capital efficiency)
#    - Debt ratio <50%    (conservative)
#    - Revenue growth positive most years

# 4. Get PE/PB from Tencent API (works from outside China):
import requests
url = f"https://qt.gtimg.cn/q=sh{code}"  # or sz for Shenzhen
resp = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'})
values = resp.text.split('=')[1].strip().strip('"').split('~')
pe = values[39]   # 动态市盈率 at index 39
pb = values[46]   # 市净率 at index 46
mkt_cap = values[45]  # 总市值 at index 45
```

**Phase 2 — Deep Dive (passing candidates only):**
Run `stock_analysis.py` (or direct akshare calls with 同花顺) for detailed multi-year financial history on the ~10-15 candidates that passed Phase 1.

**Phase 3 — Framework Application:**
Apply the Buffett 4 gates and Duan Yongping 3 tests to each deep-dived stock. Present as a ranked table with key metrics and verdict.

### 1. Business Quality
- [ ] Gross margin ___% | Net margin ___% | ROE ___%
- [ ] Moat type: ___________
- [ ] Is moat getting wider or narrower?
- [ ] Channel business vs platform/ecosystem business?

### 2. Financial Health
- [ ] Debt ratio ___% | Operating cash flow healthy?
- [ ] Are revenue and net profit predictable?
- [ ] Cyclical volatility? How much?

### 3. Management Assessment
- [ ] Integrity evaluation
- [ ] Capital allocation history (dividends/buybacks/M&A quality)
- [ ] Corporate culture description

### 4. Valuation
- [ ] PE ___x | PB ___x | Dividend yield ___%
- [ ] Historical valuation percentile
- [ ] Margin of safety assessment

### 5. Final Verdict
- [ ] Meets Duan Yongping criteria? (Yes/No)
- [ ] Meets Buffett criteria? (Yes/No)
- [ ] Fits as Graham-style cigar butt? (Yes/No)
- [ ] Core reason: ___________

## Common Patterns

### Graham "Cigar Butt" Characteristics (vs Buffett's Quality)
- PB < 1 (trading below net asset value)
- Lots of cash + almost no interest-bearing debt
- Very low PE (< 10)
- Consistent dividend record
- Risk: value trap - cheap for a reason (declining industry, bad management, disappearing moat)

### Warning Signs: "Looks cheap but fails Buffett standard"
- ROE < 10% -> business itself has low return
- Net profit volatile -> unpredictable, not a good business
- High debt -> fragile
- Strong cyclicality -> can't hold long-term
- Industry being disrupted -> moat narrowing

## When to Use This Skill

- User asks "Does this stock meet Buffett's criteria?"
- User asks "Would Duan Yongping buy this stock?"
- User asks about value investing analysis for any stock
- Comparing a stock against Buffett/Duan Yongping investment philosophy

## Data Collection Script

This skill includes a reusable A-share stock data collection script at `scripts/stock_analysis.py`.

### Usage

```bash
# Basic usage — provide stock code
python3 scripts/stock_analysis.py 688707

# With optional stock name for display
python3 scripts/stock_analysis.py 000858 五粮液
python3 scripts/stock_analysis.py 600519 贵州茅台
python3 scripts/stock_analysis.py 002594 比亚迪
python3 scripts/stock_analysis.py 300750 宁德时代
```

### What It Fetches

| Section | Data | Source |
|---------|------|--------|
| 公司概况 | Company name, industry, listing date, registered capital, main business | `stock_profile_cninfo` |
| 财务历史 | Full financial history (all report periods since listing): net profit, revenue, gross margin, net margin, ROE, debt ratio, EPS, book value, operating cash flow, inventory turnover | `stock_financial_abstract_ths` |
| 实时行情 | Current price, change %, volume, turnover, PE, PB, market cap | `stock_zh_a_spot_em` |
| 近期日线 | Last 30 trading days of OHLCV data | `stock_zh_a_hist` |
| 主营构成 | Revenue breakdown by product/business segment | `stock_zygc_em` / `stock_financial_abstract_ths` (按产品) |
| 分红记录 | Dividend payout history | `stock_hk_dividend_payout_em` |

### Workflow

1. Run the script first to collect raw data
2. Use the collected data to fill in the **Analysis Template** above
3. Apply Buffett's/Duan Yongping's frameworks to evaluate the stock

### Installation

The script requires `akshare` and `pandas`:
```bash
pip install akshare pandas
```

## 🐍 Python Version Note (macOS Homebrew)

On macOS with Homebrew-managed Python, the bare `python3` command may point to **Python 3.14+** (installed by Homebrew) while `pip3` and akshare are installed under the **system Python 3.11** at `/usr/local/bin/python3.11`. This manifests as:

```bash
$ python3 -c "import akshare"   # ❌ ModuleNotFoundError
$ /usr/local/bin/python3.11 -c "import akshare"  # ✅ OK
```

**Always use explicit paths** when akshare is involved:
```bash
# ❌ Wrong — may silently use the wrong Python
python3 scripts/stock_analysis.py 600519

# ✅ Correct — forces the Python version with akshare installed
/usr/local/bin/python3.11 scripts/stock_analysis.py 600519

# ✅ Also correct for inline scripts
/usr/local/bin/python3.11 << 'PYEOF'
import akshare ...
PYEOF
```

To check the version mismatch:
```bash
python3 --version        # May show 3.14.x
pip3 show akshare       # akshare location indicates which Python it's under
which python3           # /usr/local/bin/python3 vs system python3
```

- **Network connectivity (critical for outside-China users)**: All 东方财富 (EM suffix) APIs — `stock_zh_a_spot_em`, `stock_individual_info_em`, `stock_zygc_em`, `stock_zh_a_hist` — are frequently blocked with `RemoteDisconnected` from outside mainland China. **These are listed as sources in the script but will very likely fail.** Use these fallbacks instead:
  - **财务历史数据**: 同花顺 `stock_financial_abstract_ths` — **works reliably** from outside China. This is the primary financial data source.
  - **实时价格**: Sina batch API `hq.sinajs.cn` — works (curl with Referer header).
  - **PE/PB/估值/市值**: Tencent Finance API `qt.gtimg.cn` — works. Returns 47+ fields in `~`-delimited format. Key indices: PE动态=[39], PB=[46], 总市值=[45], 流通市值=[44].
  - **日线行情**: Sina `stock_zh_a_hist` via `stock_zh_a_hist_sina` (not EM) may work. Otherwise use manual Sina fetch.
  - See `references/api-sources.md` for exact API patterns and response parsing.
- **Python version**: On macOS with Homebrew, `python3` may point to 3.14+ while akshare is installed under 3.11. Use `/usr/local/bin/python3.11` explicitly in that case.
- **STAR Market / ChiNext stocks** (codes starting with 688/300): Work the same way as main board stocks.

## When NOT to Use This Skill

- Technical trading analysis
- Quantitative/factor analysis
- Short-term price forecasting
