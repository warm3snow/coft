# Chinese Stock Data API Sources

## Source Reliability Map (from outside mainland China)

| Source | Domain | Works? | Data Type | Notes |
|--------|--------|--------|-----------|-------|
| 同花顺 (iFinD) | `stock_financial_abstract_ths` | ✅ Reliable | Financial history | Primary source for annual/quarterly financials |
| 同花顺 | `stock_profile_cninfo` | ✅ Reliable | Company profile | Basic info, industry, listing date |
| Sina Finance | `hq.sinajs.cn` | ✅ Reliable | Real-time quotes | Batch endpoint, fast |
| Tencent Finance | `qt.gtimg.cn` | ✅ Reliable | Complete quote + PE/PB/MCap | 47+ fields per stock |
| 东方财富 (EM) | `*.em` suffixes | ❌ Blocked | All EM endpoints | Connection reset from non-CN IPs |
| Sina K-line | `stock_zh_a_hist` | ⚠️ Unstable | Daily K-line data | May work with retries |

## Quick Reference: Endpoints That Work

### 1. 同花顺 — Financial Data (primary)
```python
import akshare as ak

# Full financial history (all report periods since listing)
fin = ak.stock_financial_abstract_ths(symbol="600519")  # Works ✓

# Company profile
profile = ak.stock_profile_cninfo(symbol="600519")  # Works ✓

# Revenue breakdown by product (may need fallback)
biz = ak.stock_zygc_em(symbol="600519")  # Likely blocked
# Alternative: 
fin_detail = ak.stock_financial_abstract_ths(symbol="600519", indicator='按产品')
```

### 2. Tencent Finance API — PE/PB/Market Cap (recommended)
```python
import requests
import json

code = "600519"
url = f"https://qt.gtimg.cn/q=sh{code}"  # 'sh' for Shanghai, 'sz' for Shenzhen
headers = {'Referer': 'https://finance.sina.com.cn'}

resp = requests.get(url, headers=headers, timeout=10)
# Response format: v_sh600519="...~...~..." (47+ fields delimited by ~)
data = resp.text.split('=')[1].strip().strip('"').split('~')

name     = data[1]   # 名称
code_t   = data[2]   # 代码
price    = data[3]   # 最新价
prev_close = data[4] # 昨收
open_p   = data[5]   # 今开
volume   = data[6]   # 成交量(手)
turnover = data[37]  # 换手率
pe       = data[39]  # 动态市盈率
amplitude = data[43] # 振幅
mkt_cap_float = data[44]  # 流通市值
mkt_cap_total = data[45]  # 总市值
pb       = data[46]  # 市净率
```

### 3. Sina Batch API — Real-time Prices
```python
import requests

# Shanghai prefix: sh, Shenzhen prefix: sz
codes_param = ','.join(['sh600519', 'sh600809', 'sh600887'])
url = f"https://hq.sinajs.cn/list={codes_param}"
headers = {'Referer': 'https://finance.sina.com.cn'}

resp = requests.get(url, headers=headers, timeout=15)
for line in resp.text.strip().split('\n'):
    values = line.split('=')[1].strip().strip('"').split(',')
    name    = values[0]
    price   = values[3]
    high    = values[4]
    low     = values[5]
    vol     = values[8]
    amount  = values[9]
```

### 4. Index Constituents — Get Stock List
```python
import akshare as ak

# 上证50 = 000016, 沪深300 = 000300, 中证500 = 000905, 科创50 = 000688
index_stocks = ak.index_stock_cons(symbol="000016")
# Returns: 品种代码, 品种名称, 纳入日期
```

## Response Field Reference

### Tencent API Field Index (47+ field format)
```
Index  Field
─────  ─────
0      market (sh/sz)
1      name
2      code
3      current_price
4      previous_close
5      open_price
6      volume (shares)
7      ... (bid/ask)
37     turnover_rate (%)
38     ... 
39     PE_dynamic (动态市盈率)
40     ... 
41     high
42     low
43     amplitude (%)
44     float_market_cap (流通市值)
45     total_market_cap (总市值)
46     PB (市净率)
```

### Sina API Field Index
```
Index  Field
─────  ─────
0      name
1      open
2      previous_close
3      current_price
4      high
5      low
6      ... 
8      volume
9      amount (成交额)
```

## Common Data Collection Pattern (robust)

```python
import akshare as ak
import requests
import time

def get_financials(code):
    """Primary: 同花顺 (reliable from outside China)."""
    return ak.stock_financial_abstract_ths(symbol=code)

def get_pe_pb(code):
    """PE/PB via Tencent (reliable from outside China)."""
    prefix = 'sh' if code.startswith(('6','9')) else 'sz'
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    resp = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'}, timeout=10)
    v = resp.text.split('=')[1].strip().strip('"').split('~')
    return {'pe': v[39], 'pb': v[46], 'mkt_cap': v[45]}

def get_price(code):
    """Price via Sina (reliable from outside China)."""
    prefix = 'sh' if code.startswith(('6','9')) else 'sz'
    url = f"https://hq.sinajs.cn/list={prefix}{code}"
    resp = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'}, timeout=10)
    v = resp.text.split('=')[1].strip().strip('"').split(',')
    return {'price': v[3], 'high': v[4], 'low': v[5]}
```
