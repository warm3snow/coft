# 晶泰控股 (02228.HK / XTALPi) — 2026年6月 Worked Example

Worked example of a HK stock analysis using the Sina+Bing+EastMoney fallback (akshare not installed).

## Stock data (2026-06-09)

| Key | Value |
|-----|-------|
| Name | 晶泰控股 (XtalPi Holdings) |
| Code | 02228.HK |
| Price (close) | 6.91 HKD |
| Daily change | -2.54% |
| PE | ~206x |
| 52w high | 15.12 |
| 52w low | 5.02 |
| Market cap | ~297亿 HKD |
| Shares | 43.03亿 |
| Dividend | 0% |
| Cash on hand (2025年报) | 70.7亿 RMB |

## Data Sources Used

1. **Real-time price**: `curl -sL 'https://hq.sinajs.cn/list=hk02228' -H 'Referer: https://finance.sina.com.cn'` → parsed GBK response via iconv
2. **Company overview**: `browser_navigate(url='https://stock.finance.sina.com.cn/hkstock/quotes/02228.html')` → extracted PE, market cap, 52w range from accessibility tree
3. **News / financial reports**: `browser_navigate(url='https://www.bing.com/news/search?q=晶泰控股+XtalPi+02228&setlang=zh-Hans')` → multiple scrolls to reveal financial report headlines and 2025 annual results
4. **EastMoney alternative** (when Bing blocked): `https://so.eastmoney.com/news/s?keyword=晶泰控股+02228&pageindex=1` → 10,000+ results

## Key Financial Insights from News

- Revenue 8.03亿 RMB (+201.2%) — first profitable year (net profit 1.35亿 RMB)
- 28.66亿 HKD zero-coupon CB issued Jan 2026, maturing 2027 (potential dilution ~9%)
- 70亿+ RMB cash — very strong balance sheet
- Partnerships: Jinko Energy (solar), Mirxes (gastric cancer screening), Xellar Biosystems (3D bio-intelligence)
- South-bound (北向) funds held 19.77亿 shares as of May 2026

## Pitfall: Stock Code Recycling

Stock code 02228 on Sina's page shows legacy announcements ("取消上市地位", 2020/2021 reports) from a **prior code holder** that was delisted. HKEX recycles codes. Always verify the company name matches before using legacy data.

## Pitfall: Bing CAPTCHA Blocking

Bing frequently blocks headless browser access with CAPTCHA challenges (observed 2026-06-09). Fallback path: close the Bing tab, navigate directly to EastMoney news search with the same keywords. EastMoney does not block and returns results instantly.

## Three Lives Framework Applied

```
第一条命(尚未盈利): AI4S研发模式本身
  → 2018-2024持续亏损, 直到2025年才首次盈利
  → 但营收增速200%+, 模式已证明可行
  → 市场给PE 206x, 是在定价"Growth at a Reasonable Price"

第二条命(核心): AI药物发现+自动化实验室
  → 8亿营收(+201%), 首次盈利
  → 赛道头部地位明确
  → CB融资28.66亿说明机构看好

第三条命(未来): 跨行业AI应用(光伏、新材料)
  → 与晶科能源的合作是Key Catalyst
  → 还处于早期
  → 打开了估值天花板
```

Unlike Maoyan whose "Life 1" is dying, XtalPi's "Life 1" just turned profitable. The difference between a turnaround and a value trap.

## Investment Decision Applied (User down 50%)

### Entry deduction
- User says "亏50%" → entry ~13.8 (near 52w high of 15.12)

### Three options presented

| Option | Trigger | Suits |
|--------|---------|-------|
| A. Hold/add at dips | If 6-7 → add 1st batch, 5-6 → 2nd batch | Long-term AI4S believers, patient capital |
| B. Stop-loss/switch | Cut and reallocate to value stocks (Tencent, CNOOC) | Opportunity-cost-focused investors |
| C. Partial sell | Sell 1/3, keep rest for catalyst | Unsure, wants compromise |

### Structural vs Cyclical
- **Both**: AI4S sector is structurally promising but valuation was overly cyclical (IPO hype peak 15.12)
- The 50% decline is valuation normalization, not business deterioration
- Revenue 200%+ growth + first profitable year = business is actually getting stronger

### Key Catalysts to Watch
- 2026 mid-year results (Aug): can revenue maintain 100%+ growth?
- CB conversion (2027): 9% dilution headwind, watch for conversion patterns
- AI drug pipeline progress: any real drug approval would be transformative
