#!/usr/bin/env python3
"""
A股股票数据采集脚本 — 获取估值分析所需的基础财务和行情数据

Usage:
    python3 stock_analysis.py <stock_code> [stock_name]

Examples:
    python3 stock_analysis.py 688707 振华新材
    python3 stock_analysis.py 000858 五粮液
    python3 stock_analysis.py 600519
    python3 stock_analysis.py 002594 比亚迪
    python3 stock_analysis.py 300750 宁德时代

输出说明:
  - 公司概况: 基本信息、主营业务、上市日期、实控人
  - 财务指标: 近8个报告期的净利润、营收、毛利率、净利率、ROE、资产负债率等
  - 实时行情: 当前价格、涨跌幅、成交量
  - 近期日线: 近30个交易日的收盘价、涨跌幅、成交量
  - 主营构成: 各业务板块的收入占比

依赖: pip install akshare pandas
"""

import sys
import akshare as ak
import pandas as pd
import warnings
import time
import requests

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 220)
pd.set_option('display.max_colwidth', 100)

# ── Fallback data sources for outside-China users ──
SINA_HEADERS = {'Referer': 'https://finance.sina.com.cn'}

def fetch_tencent_quote(code: str) -> dict:
    """Fetch PE/PB/market cap via Tencent Finance API (works from outside China).
    Returns dict with keys: pe, pb, price, mkt_cap_total, mkt_cap_float, turnover_rate, name
    or empty dict on failure.
    """
    prefix = 'sh' if code.startswith(('6', '9')) else 'sz'
    try:
        url = f"https://qt.gtimg.cn/q={prefix}{code}"
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        data = resp.text.split('=')[1].strip().strip('"').split('~')
        if len(data) < 47:
            return {}
        return {
            'name': data[1],
            'price': data[3],
            'pe': data[39],
            'pb': data[46],
            'mkt_cap_total': data[45],
            'mkt_cap_float': data[44],
            'turnover_rate': data[37],
            'high': data[41],
            'low': data[42],
            'open': data[5],
            'prev_close': data[4],
            'amplitude': data[43],
        }
    except Exception as e:
        return {}

def fetch_sina_price(code: str) -> dict:
    """Fetch real-time price via Sina batch API (works from outside China)."""
    prefix = 'sh' if code.startswith(('6', '9')) else 'sz'
    try:
        url = f"https://hq.sinajs.cn/list={prefix}{code}"
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        values = resp.text.split('=')[1].strip().strip('"').split(',')
        if len(values) < 10:
            return {}
        return {
            'name': values[0],
            'open': values[1],
            'prev_close': values[2],
            'price': values[3],
            'high': values[4],
            'low': values[5],
            'volume': values[8],
            'amount': values[9],
        }
    except Exception as e:
        return {}


def fmt(val) -> str:
    """Format values for display, handling various types."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if isinstance(val, float):
        if abs(val) >= 1e8:
            return f"{val/1e8:.2f}亿"
        if abs(val) >= 1e4:
            return f"{val/1e4:.2f}万"
        return f"{val:.2f}"
    return str(val)


def _to_float(val):
    """Safely convert string to float, return None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def section(title: str):
    """Print a section header."""
    print()
    print("=" * 80)
    print(f"【{title}】")
    print("=" * 80)


def try_fetch(fn, label, retries=2):
    """Try fetching data with retries. Returns DataFrame or None."""
    for attempt in range(retries):
        try:
            result = fn()
            return result
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            print(f"⚠️  {label}: {type(e).__name__}: {e}")
            return None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 stock_analysis.py <股票代码> [股票名称]")
        print("示例: python3 stock_analysis.py 688707 振华新材")
        sys.exit(1)

    code = sys.argv[1].strip()
    name = sys.argv[2].strip() if len(sys.argv) > 2 else ""
    display_name = f"{name} ({code})" if name else code

    # =========================================================
    # 1. 公司简介
    # =========================================================
    section(f"{display_name} 公司概况")
    profile = try_fetch(lambda: ak.stock_profile_cninfo(symbol=code), "公司简介")
    if profile is not None and not profile.empty:
        row = profile.iloc[0] if len(profile) == 1 else profile.T
        # Show key fields
        key_fields = [
            '公司名称', 'A股简称', '主营业务', '所属行业',
            '法人代表', '注册资金', '成立日期', '上市日期',
            '官方网站', '注册地址', '入选指数'
        ]
        if isinstance(row, pd.Series):
            for f in key_fields:
                if f in row.index:
                    print(f"{f}: {row[f]}")
        else:
            print(row.to_string())

    # =========================================================
    # 2. 完整财务历史
    # =========================================================
    section("完整财务历史（近9年）")
    fin = try_fetch(lambda: ak.stock_financial_abstract_ths(symbol=code), "财务指标")
    if fin is not None and not fin.empty:
        # Show full history
        print(f"共 {len(fin)} 个报告期")
        print(fin.to_string())

    # =========================================================
    # 3. 实时行情 + 估值 (via Tencent API — works from outside China)
    # =========================================================
    section("实时行情与估值")
    # Primary: Tencent Finance API (PE/PB/market cap + price)
    q = fetch_tencent_quote(code)
    if q:
        print(f"名称:     {q['name']}")
        print(f"代码:     {code}")
        print(f"最新价:   {q['price']} 元")
        # Try Sina for change % and volume (Tencent has limited intraday data)
        sp = fetch_sina_price(code)
        if sp:
            try:
                change_pct = (float(sp['price']) - float(sp['prev_close'])) / float(sp['prev_close']) * 100
                print(f"涨跌幅:   {change_pct:.2f}%")
            except (ValueError, ZeroDivisionError):
                pass
            print(f"今开:     {sp['open']} 元")
            print(f"昨收:     {sp['prev_close']} 元")
            print(f"成交量:   {sp['volume']} 手")
            print(f"成交额:   {sp['amount']}")
        print(f"最高:     {q['high']} 元")
        print(f"最低:     {q['low']} 元")
        print(f"换手率:   {q['turnover_rate']}%")
        print(f"振幅:     {q['amplitude']}%")
        print(f"市盈率(动): {q['pe']}")
        print(f"市净率:   {q['pb']}")
        print(f"总市值:   {fmt(_to_float(q['mkt_cap_total']) * 1e4)}")  # Tencent returns 万元
        print(f"流通市值: {fmt(_to_float(q['mkt_cap_float']) * 1e4)}")
        print(f"（数据来源: 腾讯财经API + Sina报价）")
    else:
        # Fallback: Sina price only (no PE/PB)
        sp = fetch_sina_price(code)
        if sp:
            print(f"名称:     {sp['name']}")
            print(f"最新价:   {sp['price']} 元 (Sina报价，无PE/PB估值)")
            print(f"今开:     {sp['open']} 元")
            print(f"昨收:     {sp['prev_close']} 元")
            print(f"最高:     {sp['high']} 元")
            print(f"最低:     {sp['low']} 元")
            print(f"成交量:   {sp['volume']} 手")
            print(f"成交额:   {sp['amount']}")
        else:
            print("⚠️  Tencent API和Sina API均失败，无法获取实时行情")
            print("建议手动查询或稍后重试")

    # =========================================================
    # 4. 近期日线行情
    # =========================================================
    section("近期行情（近30个交易日）")
    from datetime import datetime, timedelta
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
    hist = try_fetch(
        lambda: ak.stock_zh_a_hist(symbol=code, period="daily",
                                   start_date=start, end_date=end, adjust="qfq"),
        "日线行情"
    )
    if hist is not None and not hist.empty:
        hist = hist.sort_values('日期', ascending=False)
        print(hist.head(30).to_string())
    else:
        # Fallback: try Sina K-line API
        print("（东方财富日线API不可用，尝试Sina K-line备用）")
        try:
            prefix = 'sh' if code.startswith(('6', '9')) else 'sz'
            # Sina K-line: 日线 = 'd', 周线 = 'w', 月线 = 'm'
            url = f"https://quotes.money.163.com/service/chddata.html?code={prefix}{code}&start={start}&end={end}"
            resp = requests.get(url, headers=SINA_HEADERS, timeout=15)
            if resp.status_code == 200 and len(resp.text) > 200:
                lines = resp.text.strip().split('\n')
                # CSV format: date,open,high,low,close,volume,amount,...
                recent = lines[-31:-1] if len(lines) > 31 else lines[-30:]
                print(f"日期        开盘    最高    最低    收盘    成交量")
                for line in reversed(recent):
                    cols = line.split(',')
                    if len(cols) >= 6:
                        print(f"{cols[0]:12s} {cols[3]:>7s} {cols[4]:>7s} {cols[5]:>7s} {cols[2]:>7s} {cols[6]:>12s}")
            else:
                print("⚠️  Sina K-line备用数据源也未返回有效数据")
        except Exception as e2:
            print(f"⚠️  Sina K-line备用失败: {e2}")

    # =========================================================
    # 5. 主营构成
    # =========================================================
    section("主营构成（按产品/行业）")
    # Try multiple akshare functions for business breakdown
    biz = try_fetch(lambda: ak.stock_zygc_em(symbol=code), "主营构成")
    if biz is not None and not biz.empty:
        print(biz.to_string())
    else:
        # Fallback: use financial abstract data for product revenue breakdown
        fin_detail = try_fetch(
            lambda: ak.stock_financial_abstract_ths(symbol=code, indicator='按产品'),
            "主营构成(按产品)"
        )
        if fin_detail is not None and not fin_detail.empty:
            print(fin_detail.tail(10).to_string())

    # =========================================================
    # 6. 分红记录
    # =========================================================
    section("分红记录")
    # Try multiple dividend functions
    div = try_fetch(lambda: ak.stock_hk_dividend_payout_em(symbol=code), "分红记录")
    if div is not None and not div.empty:
        print(div.tail(8).to_string())
    else:
        print("暂无分红数据（A股分红接口可能受限）")

    print()
    print("=" * 80)
    print("数据采集完成。以上数据可用于估值分析（参见 value-investing-criteria 框架）")


if __name__ == "__main__":
    main()
