#!/usr/bin/env python3
"""
大宗商品供应链与地缘政治综合分析脚本
用法: python3 commodity_intel.py <商品名> <期货代码> [主力合约]

示例:
  python3 commodity_intel.py "甲醇" "MA"
  python3 commodity_intel.py "红枣" "CJ"
  python3 commodity_intel.py "生猪" "LH"
  python3 commodity_intel.py "螺纹钢" "RB"
  python3 commodity_intel.py "原油" "SC"
  python3 commodity_intel.py "PTA" "TA" "TA2609"
"""

import sys
import json
import subprocess
import re
from datetime import datetime, timedelta
from collections import defaultdict

COMMODITY_NAME = ""
FUTURES_CODE = ""
MAIN_CONTRACT = ""

EXCHANGE_MAP = {
    "CZCE": {"name": "郑商所", "full": "郑州商品交易所",
             "contract_func": "futures_contract_info_czce",
             "warehouse_func": "futures_warehouse_receipt_czce"},
    "DCE": {"name": "大商所", "full": "大连商品交易所",
            "contract_func": "futures_contract_info_dce",
            "warehouse_func": "futures_warehouse_receipt_dce"},
    "SHFE": {"name": "上期所", "full": "上海期货交易所",
             "contract_func": "futures_contract_info_shfe",
             "warehouse_func": "futures_warehouse_receipt_shfe"},
    "GFEX": {"name": "广期所", "full": "广州期货交易所",
             "contract_func": "futures_contract_info_gfex",
             "warehouse_func": "futures_warehouse_receipt_gfex"},
    "INE": {"name": "能源中心", "full": "上海国际能源交易中心",
            "contract_func": "futures_contract_info_ine",
            "warehouse_func": None},
}

CODE_EXCHANGE = {
    "MA": "CZCE", "TA": "CZCE", "SR": "CZCE", "CF": "CZCE",
    "SA": "CZCE", "CJ": "CZCE", "UR": "CZCE", "SF": "CZCE",
    "SM": "CZCE", "AP": "CZCE", "PK": "CZCE", "ZC": "CZCE",
    "RM": "CZCE", "OI": "CZCE", "PF": "CZCE", "SH": "CZCE",
    "LH": "DCE", "M": "DCE", "Y": "DCE", "P": "DCE",
    "I": "DCE", "JM": "DCE", "J": "DCE", "JD": "DCE",
    "RB": "SHFE", "HC": "SHFE", "CU": "SHFE",
    "AL": "SHFE", "ZN": "SHFE", "PB": "SHFE", "NI": "SHFE",
    "SN": "SHFE", "AU": "SHFE", "AG": "SHFE", "RU": "SHFE",
    "BU": "SHFE", "FU": "SHFE", "SP": "SHFE", "SS": "SHFE",
    "BC": "SHFE", "LU": "INE", "SC": "INE", "NR": "INE",
    "LC": "GFEX", "SI": "GFEX",
}


def print_header(title):
    sep = "═" * 70
    print(f"\n{sep}")
    print(f"  📊 {title}")
    print(f"{sep}")


def print_section(title, content=""):
    if content:
        print(f"\n🔹 {title}")
        print(content)
    else:
        print(f"\n🔹 {title}")


# ─── WEB SEARCH ─────────────────────────────────────────────────

def web_search_json(query, max_results=5):
    """Search the web via curl and return structured results."""
    try:
        encoded = subprocess.check_output(
            ["python3", "-c", f"import urllib.parse; print(urllib.parse.quote('''{query}'''))"],
            text=True
        ).strip()

        url = f"https://lite.duckduckgo.com/lite?q={encoded}"
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "15",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
             url],
            capture_output=True, text=True, timeout=20
        )

        html = result.stdout
        if not html:
            return {"error": "No data returned", "results": []}

        results = []
        rows = re.findall(
            r'<a[^>]*class="result-link"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        snippets = re.findall(
            r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
            html, re.DOTALL
        )

        for i, (url_, title_) in enumerate(rows[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ""
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            title_clean = re.sub(r'<[^>]+>', '', title_).strip()
            results.append({
                "title": title_clean,
                "url": url_,
                "snippet": snippet
            })

        if not results:
            url2 = f"https://html.duckduckgo.com/html?q={encoded}"
            result2 = subprocess.run(
                ["curl", "-s", "-L", "--max-time", "15",
                 "-H", "User-Agent: Mozilla/5.0",
                 url2],
                capture_output=True, text=True, timeout=20
            )
            html2 = result2.stdout
            links = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                html2, re.DOTALL
            )
            snippets2 = re.findall(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                html2, re.DOTALL
            )
            for i, (url_, title_) in enumerate(links[:max_results]):
                snippet = snippets2[i] if i < len(snippets2) else ""
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                title_clean = re.sub(r'<[^>]+>', '', title_).strip()
                results.append({
                    "title": title_clean,
                    "url": url_,
                    "snippet": snippet
                })

        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}


# ─── FUTURES DATA ────────────────────────────────────────────────

def get_futures_data(code, contract="0"):
    """Get futures OHLCV daily data using akshare."""
    try:
        import akshare as ak
        symbol = f"{code}{contract}"
        df = ak.futures_zh_daily_sina(symbol=symbol)
        return df
    except Exception as e:
        return {"error": str(e)}


def get_contract_structure(code, exchange):
    """Get multi-contract prices via individual queries (detailed OHLC)."""
    results = {}
    try:
        import akshare as ak

        # Build contract months to try based on current date
        from datetime import datetime
        now = datetime.now()
        yr = now.year % 100
        next_yr = (now.year + 1) % 100
        month = now.month

        # Standard delivery months (specific to each commodity, but
        # we probe broadly: this month through 3 next seasons)
        candidate_months = set()

        # 1, 3, 5, 7, 9, 11 + current month + next month
        for m in [1, 3, 5, 7, 9, 11]:
            if m >= month:
                candidate_months.add((yr, m))
            else:
                candidate_months.add((next_yr, m))

        # Also add current month and next month
        if month < 12:
            candidate_months.add((yr, month))
            candidate_months.add((yr, month + 1))
        else:
            candidate_months.add((yr, 12))
            candidate_months.add((next_yr, 1))

        # Deduplicate and sort
        sorted_months = sorted(candidate_months)

        for y, m in sorted_months:
            sym = f"{code}{y}{m:02d}"
            try:
                df = ak.futures_zh_daily_sina(symbol=sym)
                if df is not None and len(df) > 0:
                    last = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else None
                    chg = ((last['close'] - prev['close']) / prev['close'] * 100) if prev is not None else 0
                    hold_val = last.get('hold', 0)
                    results[sym] = {
                        "price": f"{last['close']:.0f}",
                        "open": f"{last['open']:.0f}",
                        "high": f"{last['high']:.0f}",
                        "low": f"{last['low']:.0f}",
                        "change": f"{chg:+.2f}%",
                        "volume": f"{last['volume']:.0f}",
                        "hold": f"{hold_val:.0f}",
                    }
            except Exception:
                continue

    except Exception as e:
        return {"error": str(e)}
    return results


def get_warehouse_receipts(code, exchange):
    """Get exchange warehouse receipt data."""
    try:
        import akshare as ak
        exchange_info = EXCHANGE_MAP.get(exchange, {})
        func_name = exchange_info.get("warehouse_func")
        if not func_name:
            return {"note": f"{exchange_info.get('name', exchange)} 不支持仓单查询"}

        func = getattr(ak, func_name)
        result = func()

        if isinstance(result, dict) and code in result:
            df = result[code]
            return df.tail(20)
        elif isinstance(result, dict):
            return {"note": f"未找到 {code} 的仓单数据，可用品种: {list(result.keys())[:10]}"}
        else:
            return result.tail(20) if hasattr(result, 'tail') else result
    except Exception as e:
        return {"error": str(e)}


# ─── PRICE DATA ANALYSIS ─────────────────────────────────────────

def recent_days_analysis(df, n=15):
    """Show last N trading days with daily details and volume ratio."""
    try:
        if isinstance(df, dict) and "error" in df:
            return df
        import pandas as pd
        df['date'] = pd.to_datetime(df['date'])
        recent = df.tail(n)
        avg_vol_20 = df.tail(20)['volume'].mean() if len(df) >= 20 else df['volume'].mean()
        avg_hold_20 = df.tail(20)['hold'].mean() if len(df) >= 20 and 'hold' in df.columns else 0

        lines = []
        for _, r in recent.iterrows():
            vol_ratio = r['volume'] / avg_vol_20 if avg_vol_20 > 0 else 0
            hold_str = f" HLD={r['hold']:.0f}" if 'hold' in r else ""
            lines.append(
                f"{str(r['date'])[:10]}  O={r['open']:.0f} H={r['high']:.0f} "
                f"L={r['low']:.0f} C={r['close']:.0f} V={r['volume']:.0f}({vol_ratio:.2f}x){hold_str}"
            )
        return {
            "lines": lines,
            "avg_vol_20": f"{avg_vol_20:.0f}",
            "avg_hold_20": f"{avg_hold_20:.0f}" if avg_hold_20 else "N/A",
        }
    except Exception as e:
        return {"error": str(e)}


def period_segmentation(df):
    """Break price history into quarters/months and show performance."""
    try:
        if isinstance(df, dict) and "error" in df:
            return df
        import pandas as pd
        df['date'] = pd.to_datetime(df['date'])
        now = datetime.now()
        yr = now.year
        segments = []

        # Build smart segments: last 3 full quarters + current YTD months
        quarters = []
        for y in range(yr - 1, yr + 1):
            for q_start, q_label in [
                ((y, 1, 1), f"{y}年Q1"),
                ((y, 4, 1), f"{y}年Q2"),
                ((y, 7, 1), f"{y}年Q3"),
                ((y, 10, 1), f"{y}年Q4"),
            ]:
                if datetime(*q_start) <= now:
                    quarters.append((datetime(*q_start), q_label))

        # Also add individual months for current year
        for m in range(1, now.month + 1):
            label = f"{yr}年{m}月"
            m_start = datetime(yr, m, 1)
            m_end = datetime(yr, m + 1, 1) if m < 12 else datetime(yr + 1, 1, 1)
            segments.append((m_start, m_end, label))

        # Add quarters too
        for q_start, q_label in quarters:
            q_end_month = q_start.month + 3
            q_y = q_start.year
            if q_end_month > 12:
                q_end_month -= 12
                q_y += 1
            q_end = datetime(q_y, q_end_month, 1)
            # Only add if not already covered by months (avoid overlap with current year)
            if q_start.year < yr or q_start.month < 1:
                segments.append((q_start, q_end, q_label))

        # Only show segments with data
        results = []
        for start, end, label in segments:
            seg = df[(df['date'] >= start) & (df['date'] < end)]
            if len(seg) > 0:
                chg = (seg.iloc[-1]['close'] - seg.iloc[0]['close']) / seg.iloc[0]['close'] * 100
                results.append({
                    "label": label,
                    "start_price": f"{seg.iloc[0]['close']:.0f}",
                    "end_price": f"{seg.iloc[-1]['close']:.0f}",
                    "change": f"{chg:+.2f}%",
                    "high": f"{seg['high'].max():.0f}",
                    "low": f"{seg['low'].min():.0f}",
                    "avg_vol": f"{seg['volume'].mean():.0f}",
                })
        return results
    except Exception as e:
        return {"error": str(e)}


def this_month_analysis(df):
    """Analyze current month's open/high/low/close/change."""
    try:
        if isinstance(df, dict) and "error" in df:
            return df
        import pandas as pd
        df['date'] = pd.to_datetime(df['date'])
        now = datetime.now()
        m_start = datetime(now.year, now.month, 1)
        mth = df[df['date'] >= m_start]
        if len(mth) == 0:
            return None
        open_ = mth.iloc[0]['open']
        high = mth['high'].max()
        low = mth['low'].min()
        close = mth.iloc[-1]['close']
        chg = (close - open_) / open_ * 100
        return {
            "month": f"{now.year}年{now.month}月",
            "open": f"{open_:.0f}",
            "high": f"{high:.0f}",
            "low": f"{low:.0f}",
            "close": f"{close:.0f}",
            "change": f"{chg:+.2f}%",
            "high_date": str(mth.loc[mth['high'].idxmax(), 'date'])[:10],
            "low_date": str(mth.loc[mth['low'].idxmin(), 'date'])[:10],
        }
    except Exception:
        return None


def crop_year_analysis(df):
    """Analyze the current crop year (Oct 1 - Sep 30)."""
    try:
        if isinstance(df, dict) and "error" in df:
            return df
        import pandas as pd
        df['date'] = pd.to_datetime(df['date'])
        now = datetime.now()
        if now.month >= 10:
            cy_start = datetime(now.year, 10, 1)
        else:
            cy_start = datetime(now.year - 1, 10, 1)

        cy = df[df['date'] >= cy_start]
        if len(cy) == 0:
            return None
        chg = (cy.iloc[-1]['close'] - cy.iloc[0]['close']) / cy.iloc[0]['close'] * 100
        return {
            "crop_year": f"{cy_start.year}/{(cy_start.year + 1) % 100}",
            "start_date": str(cy.iloc[0]['date'])[:10],
            "avg_price": f"{cy['close'].mean():.0f}",
            "high": f"{cy['high'].max():.0f}",
            "high_date": str(cy.loc[cy['high'].idxmax(), 'date'])[:10],
            "low": f"{cy['low'].min():.0f}",
            "low_date": str(cy.loc[cy['low'].idxmin(), 'date'])[:10],
            "change": f"{chg:+.2f}%",
            "current_hold": f"{cy.iloc[-1].get('hold', 0):.0f}",
        }
    except Exception:
        return None


def seasonal_analysis(df):
    """Analyze historical same-month performance."""
    try:
        if isinstance(df, dict) and "error" in df:
            return df
        import pandas as pd
        df['date'] = pd.to_datetime(df['date'])
        current_month = datetime.now().month
        current_year = datetime.now().year

        results = []
        for yr in range(max(2022, current_year - 4), current_year):
            month_data = df[(df['date'].dt.year == yr) &
                            (df['date'].dt.month == current_month)]
            if len(month_data) > 0:
                start_price = month_data.iloc[0]['close']
                end_price = month_data.iloc[-1]['close']
                change = (end_price - start_price) / start_price * 100
                high = month_data['high'].max()
                low = month_data['low'].min()
                amplitude = (high - low) / start_price * 100
                results.append({
                    "year": yr,
                    "start": f"{start_price:.0f}",
                    "end": f"{end_price:.0f}",
                    "change": f"{change:+.2f}%",
                    "amplitude": f"{amplitude:.1f}%",
                    "range": f"{low:.0f}~{high:.0f}"
                })
        return results
    except Exception as e:
        return {"error": str(e)}


def technical_analysis(df, main_contract):
    """Basic technical indicators: MAs, volume ratio, support/resistance."""
    try:
        if isinstance(df, dict) and "error" in df:
            return df
        if len(df) < 20:
            return {"note": "数据不足，至少需要20个交易日"}

        recent = df.tail(30)
        avg_vol_20 = df.tail(20)['volume'].mean()
        avg_vol_5 = df.tail(5)['volume'].mean()
        vol_ratio = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else 0

        if 'hold' in recent.columns:
            pos_trend = (recent.iloc[-1]['hold'] - recent.iloc[-5]['hold']) / recent.iloc[-5]['hold'] * 100
        else:
            pos_trend = 0

        price_chg_5 = (recent.iloc[-1]['close'] - recent.iloc[-5]['close']) / recent.iloc[-5]['close'] * 100
        price_chg_20 = (recent.iloc[-1]['close'] - recent.iloc[0]['close']) / recent.iloc[0]['close'] * 100

        high_20 = recent['high'].max()
        low_20 = recent['low'].min()
        current = recent.iloc[-1]['close']

        ma5 = recent['close'].tail(5).mean()
        ma20 = recent['close'].tail(20).mean() if len(recent) >= 20 else None
        ma10 = recent['close'].tail(10).mean() if len(recent) >= 10 else None

        return {
            "current_price": f"{current:.0f}",
            "ma5": f"{ma5:.0f}",
            "ma10": f"{ma10:.0f}" if ma10 else "N/A",
            "ma20": f"{ma20:.0f}" if ma20 else "N/A",
            "high_20d": f"{high_20:.0f}",
            "low_20d": f"{low_20:.0f}",
            "price_chg_5d": f"{price_chg_5:+.2f}%",
            "price_chg_20d": f"{price_chg_20:+.2f}%",
            "volume_ratio": f"{vol_ratio:.2f}x",
            "pos_trend_5d": f"{pos_trend:+.2f}%" if pos_trend != 0 else "N/A",
            "interpretation": []
        }
    except Exception as e:
        return {"error": str(e)}


def interpret_volume_price(tech, recent_df):
    """Decode volume/price/position relationships."""
    interpretations = []
    try:
        close_5d = recent_df.tail(5)['close'].values
        vol_5d = recent_df.tail(5)['volume'].values
        hold_5d = recent_df.tail(5)['hold'].values if 'hold' in recent_df.columns else None

        price_up = close_5d[-1] > close_5d[0]
        vol_up = vol_5d.mean() > recent_df.tail(20)['volume'].mean() if len(recent_df) >= 20 else True

        if price_up and vol_up:
            interpretations.append("📈 放量上涨 — 多头动能充足，趋势可能延续")
        elif price_up and not vol_up:
            interpretations.append("📈 缩量上涨 — 涨势有待确认，注意回调风险")
        elif not price_up and vol_up:
            interpretations.append("📉 放量下跌 — 空头压力大，注意止损")
        elif not price_up and not vol_up:
            interpretations.append("📉 缩量下跌 — 下跌动能减弱，关注企稳信号")

        if hold_5d is not None:
            hold_trend = (hold_5d[-1] - hold_5d[0]) / hold_5d[0] * 100
            if abs(hold_trend) > 2:
                if hold_trend > 0:
                    interpretations.append(f"🧾 持仓增加 {hold_trend:+.1f}% — 资金流入，趋势有持续性")
                else:
                    interpretations.append(f"🧾 持仓减少 {hold_trend:+.1f}% — 资金流出，趋势可能反转")
    except Exception:
        pass
    return interpretations


# ─── WEB SEARCH WRAPPERS ─────────────────────────────────────────

def get_spot_price_data(code, commodity_name):
    query = f"{commodity_name} 现货价格 最新"
    return web_search_json(query, max_results=5)


def get_global_supply_chain(commodity_name):
    queries = [
        f"{commodity_name} 全球产能 主要生产国 产量",
        f"{commodity_name} 全球消费 需求 进口国",
        f"{commodity_name} global production capacity supply chain",
    ]
    all_results = []
    for q in queries:
        data = web_search_json(q, max_results=3)
        all_results.extend(data.get("results", []))
    return all_results


def get_geopolitical_news(commodity_name):
    queries = [
        f"{commodity_name} 地缘政治 制裁 关税 2026年",
        f"{commodity_name} 出口限制 贸易政策 2026",
        f"{commodity_name} 新闻 最新政策",
    ]
    all_results = []
    for q in queries:
        data = web_search_json(q, max_results=3)
        all_results.extend(data.get("results", []))
    return all_results


def get_global_supply_demand(commodity_name):
    query = f"{commodity_name} 全球供需平衡 库存 2025 2026"
    return web_search_json(query, max_results=5)


def get_international_prices(commodity_name, code):
    query = f"{commodity_name} {code} international price FOB CFR latest"
    return web_search_json(query, max_results=5)


# ─── MAIN ────────────────────────────────────────────────────────

def main():
    global COMMODITY_NAME, FUTURES_CODE, MAIN_CONTRACT

    if len(sys.argv) < 3:
        print("用法: python3 commodity_intel.py <商品名> <期货代码> [主力合约]")
        print("示例: python3 commodity_intel.py 甲醇 MA")
        sys.exit(1)

    COMMODITY_NAME = sys.argv[1]
    FUTURES_CODE = sys.argv[2].upper()
    MAIN_CONTRACT = sys.argv[3] if len(sys.argv) > 3 else f"{FUTURES_CODE}0"

    exchange = CODE_EXCHANGE.get(FUTURES_CODE, "CZCE")
    exchange_info = EXCHANGE_MAP.get(exchange, {"name": exchange, "full": exchange})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print_header(f"{COMMODITY_NAME}（{FUTURES_CODE}）供应链与行情综合报告")
    print(f"📅 报告时间: {now}")
    print(f"🏛️ 交易所: {exchange_info['full']}（{exchange_info['name']}）")
    print(f"🔗 主力合约: {MAIN_CONTRACT}")

    # Load main continuous contract
    main_df = get_futures_data(FUTURES_CODE, MAIN_CONTRACT.replace(FUTURES_CODE, ""))
    if isinstance(main_df, dict) and "error" in main_df:
        main_df = get_futures_data(FUTURES_CODE, "0")

    # ════════════════════════════════════════════════════════════
    # PART 1: Multi-contract price structure (detailed)
    # ════════════════════════════════════════════════════════════
    print_header("📈 第一阶段：各合约报价详情")

    contract_data = get_contract_structure(FUTURES_CODE, exchange)
    if isinstance(contract_data, dict) and "error" not in contract_data and contract_data:
        print(f"\n  {'合约':<12} {'最新价':<10} {'开盘':<8} {'最高':<8} {'最低':<8} {'涨跌幅':<10} {'成交量':<12} {'持仓量':<12}")
        print(f"  {'-'*88}")
        for sym, info in sorted(contract_data.items()):
            print(f"  {sym:<12} {str(info.get('price','N/A')):<10} {str(info.get('open','N/A')):<8} "
                  f"{str(info.get('high','N/A')):<8} {str(info.get('low','N/A')):<8} "
                  f"{str(info.get('change','N/A')):<10} {str(info.get('volume','N/A')):<12} "
                  f"{str(info.get('hold','N/A')):<12}")

        # Price structure determination
        prices_sorted = {}
        for sym, info in contract_data.items():
            try:
                prices_sorted[sym] = float(info.get('price', 0))
            except (ValueError, TypeError):
                pass

        if prices_sorted:
            sorted_syms = sorted(prices_sorted.keys())
            sorted_prices = [prices_sorted[s] for s in sorted_syms]

            is_backwardation = all(sorted_prices[i] >= sorted_prices[i+1]
                                   for i in range(len(sorted_prices)-1))
            is_contango = all(sorted_prices[i] <= sorted_prices[i+1]
                              for i in range(len(sorted_prices)-1))

            if is_backwardation and len(sorted_prices) >= 2:
                spread = sorted_prices[0] - sorted_prices[-1]
                print(f"\n  市场结构: 📊 Backwardation（反向市场）")
                print(f"  近月高于远月 {spread:.0f} 点 — 现货偏紧预期")
            elif is_contango and len(sorted_prices) >= 2:
                spread = sorted_prices[-1] - sorted_prices[0]
                print(f"\n  市场结构: 📈 Contango（正向市场）")
                print(f"  远月高于近月 {spread:.0f} 点 — 远月升水/供应宽松预期")
            else:
                print(f"\n  市场结构: 🔄 混合结构 — 各月合约未呈现单调排列")
    else:
        print("  ⚠️ 合约数据暂不可用")

    # ════════════════════════════════════════════════════════════
    # PART 2: This month & crop year overview
    # ════════════════════════════════════════════════════════════
    print_header("📊 第二阶段：月度与年度走势概览")

    if not isinstance(main_df, dict) or "error" not in main_df:
        # This month
        mth = this_month_analysis(main_df)
        if mth:
            print(f"\n  📅 {mth['month']}走势:")
            print(f"     开盘={mth['open']}  最高={mth['high']}({mth['high_date']})  "
                  f"最低={mth['low']}({mth['low_date']})  收盘={mth['close']}  涨跌={mth['change']}")

        # Crop year (Oct 1 - Sep 30)
        cy = crop_year_analysis(main_df)
        if cy:
            print(f"\n  🌾 {cy['crop_year']}产季 ({cy['start_date']}至今):")
            print(f"     均价={cy['avg_price']}  最高={cy['high']}({cy['high_date']})  "
                  f"最低={cy['low']}({cy['low_date']})  涨跌={cy['change']}  当前持仓={cy['current_hold']}")

        # Period segmentation (quarterly/monthly breakdown)
        segs = period_segmentation(main_df)
        if isinstance(segs, list) and len(segs) >= 3:
            print(f"\n  📆 分段表现:")
            print(f"  {'时间段':<16} {'起始价':<10} {'结束价':<10} {'涨跌幅':<12} {'最高':<10} {'最低':<10}")
            print(f"  {'-'*68}")
            for s in segs:
                print(f"  {s['label']:<16} {s['start_price']:<10} {s['end_price']:<10} "
                      f"{s['change']:<12} {s['high']:<10} {s['low']:<10}")

        # Seasonal (same month historical)
        seas = seasonal_analysis(main_df)
        if isinstance(seas, list) and seas:
            print(f"\n  📆 {datetime.now().month}月历史同期走势:")
            print(f"  {'年份':<8} {'月初价':<10} {'月末价':<10} {'涨跌幅':<12} {'振幅':<10} {'区间':<16}")
            print(f"  {'-'*66}")
            for s in seas:
                print(f"  {s['year']:<8} {s['start']:<10} {s['end']:<10} {s['change']:<12} "
                      f"{s['amplitude']:<10} {s['range']:<16}")

    # ════════════════════════════════════════════════════════════
    # PART 3: Recent daily detail
    # ════════════════════════════════════════════════════════════
    print_header("📉 第三阶段：近期每日行情细节")

    if not isinstance(main_df, dict) or "error" not in main_df:
        recent = recent_days_analysis(main_df, n=15)
        if isinstance(recent, dict) and "error" not in recent:
            print(f"  20日均量: {recent['avg_vol_20']}  |  20日均仓: {recent['avg_hold_20']}")
            print()
            for line in recent['lines']:
                print(f"  {line}")

    # ════════════════════════════════════════════════════════════
    # PART 4: Technical analysis
    # ════════════════════════════════════════════════════════════
    print_header("📉 第四阶段：技术面分析")

    if not isinstance(main_df, dict) or "error" not in main_df:
        tech = technical_analysis(main_df, MAIN_CONTRACT)
        if isinstance(tech, dict) and "error" not in tech:
            print(f"\n  📍 当前价格: {tech['current_price']}")
            print(f"  📐 MA5: {tech['ma5']} | MA10: {tech['ma10']} | MA20: {tech['ma20']}")
            print(f"  ⬆️ 5日涨幅: {tech['price_chg_5d']} | 20日涨幅: {tech['price_chg_20d']}")
            print(f"  📊 量比(5日/20日): {tech['volume_ratio']}")
            print(f"  📦 持仓变化(5日): {tech['pos_trend_5d']}")
            print(f"  🔝 20日高点: {tech['high_20d']} | 20日低点: {tech['low_20d']}")

            if not isinstance(main_df, dict):
                interps = interpret_volume_price(tech, main_df)
                if interps:
                    print(f"\n  📋 量价解读:")
                    for interp in interps:
                        print(f"     {interp}")
        else:
            print(f"  ⚠️ 技术分析数据不足")

    # ════════════════════════════════════════════════════════════
    # PART 5: Warehouse receipts
    # ════════════════════════════════════════════════════════════
    print_header("🏭 第五阶段：仓单数据")

    wr = get_warehouse_receipts(FUTURES_CODE, exchange)
    if isinstance(wr, dict) and "error" in wr:
        # Some products (e.g. LH生猪, SC原油) are cash-settled or non-warehouse
        err_msg = wr['error']
        if 'Expecting value' in err_msg or 'No JSON' in err_msg:
            print(f"  ℹ️  {COMMODITY_NAME}（{FUTURES_CODE}）为现金交割/非仓单品种，无仓单数据")
        else:
            print(f"  ❌ {err_msg}")
    elif isinstance(wr, dict) and "note" in wr:
        print(f"  ℹ️  {wr['note']}")
    else:
        try:
            if hasattr(wr, 'to_string'):
                print(f"\n  {wr.tail(10).to_string()}")
            elif hasattr(wr, 'to_dict'):
                print(f"\n  {str(wr)[:500]}")
            else:
                print(f"\n  {str(wr)[:500]}")
        except Exception:
            print(f"  ℹ️  仓单数据获取成功")
            print(f"  {str(wr)[:300]}")

    # ════════════════════════════════════════════════════════════
    # PARTS 6-10: Web search (supply chain, geopolitics, etc.)
    # ════════════════════════════════════════════════════════════

    print_header("🌍 第六阶段：全球供应链地图")
    print(f"  🔍 正在搜索 {COMMODITY_NAME} 全球供应链信息...")
    supply_chain = get_global_supply_chain(COMMODITY_NAME)
    if supply_chain:
        for r in supply_chain[:6]:
            print(f"\n  📰 {r['title']}")
            if r.get('snippet'):
                print(f"     {r['snippet'][:300]}")
    else:
        print("  ⚠️ 未能获取全球供应链信息（搜索引擎验证拦截）")

    print_header("🌐 第七阶段：地缘政治影响")
    print(f"  🔍 正在搜索影响 {COMMODITY_NAME} 的地缘政治因素...")
    geopolitics = get_geopolitical_news(COMMODITY_NAME)
    if geopolitics:
        for r in geopolitics[:5]:
            print(f"\n  📰 {r['title']}")
            if r.get('snippet'):
                print(f"     {r['snippet'][:300]}")
    else:
        print("  ⚠️ 未能获取地缘政治相关信息（搜索引擎验证拦截）")

    print_header("📋 第八阶段：全球供求与库存")
    print(f"  🔍 正在搜索 {COMMODITY_NAME} 全球供需平衡数据...")
    supply_demand = get_global_supply_demand(COMMODITY_NAME)
    supply_demand_results = supply_demand.get("results", [])
    if supply_demand_results:
        for r in supply_demand_results[:5]:
            print(f"\n  📰 {r['title']}")
            if r.get('snippet'):
                print(f"     {r['snippet'][:300]}")
    else:
        print("  ⚠️ 未能获取全球供需数据（搜索引擎验证拦截）")

    print_header("💰 第九阶段：现货与国际价格")
    spot_data = get_spot_price_data(FUTURES_CODE, COMMODITY_NAME)
    if spot_data.get("results"):
        for r in spot_data["results"][:5]:
            print(f"\n  📰 {r['title']}")
            if r.get('snippet'):
                print(f"     {r['snippet'][:200]}")
    else:
        print("  ⚠️ 未获取到现货价格信息")

    print_header("💵 第十阶段：国际市场价格")
    international = get_international_prices(COMMODITY_NAME, FUTURES_CODE)
    if international.get("results"):
        for r in international["results"][:5]:
            print(f"\n  📰 {r['title']}")
            if r.get('snippet'):
                print(f"     {r['snippet'][:200]}")
    else:
        print("  ⚠️ 未获取到国际市场价格信息")

    # ════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════
    print_header("📋 数据采集完成")
    print(f"  ✅ 以上为 {COMMODITY_NAME}（{FUTURES_CODE}）的综合数据")
    print(f"  🕐 报告时间: {now}")
    print(f"  💡 提示: 请结合以上数据生成完整的分析报告和操作建议")
    print(f"  ⚠️ 免责声明: 本数据仅供研究参考，不构成投资建议")
    print()


if __name__ == "__main__":
    main()
