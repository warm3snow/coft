"""
多标的对比实验：验证趋势策略在不同标的上的表现差异

标的选择：
- 510300 沪深300ETF：A股宽基，均值回归倾向强
- 159915 创业板ETF：成长风格，趋势性较强
- 518880 黄金ETF：商品类，长趋势持续性好
- 513100 纳指ETF：美股映射，长期牛市+强趋势

运行：python compare_symbols.py
"""
import os
import subprocess
import json
import time
import pandas as pd
import backtrader as bt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 复用 main.py 中的策略类
from main import TrendFollowing, BuyHold, DailyValue


SYMBOLS = {
    "510300": "沪深300ETF",
    "159915": "创业板ETF",
    "518880": "黄金ETF",
    "513100": "纳指ETF",
}

CACHE_DIR = os.path.dirname(__file__)


def fetch_symbol(symbol):
    """获取单个标的数据，带本地缓存。"""
    csv_path = os.path.join(CACHE_DIR, f"{symbol}_daily.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path, index_col="datetime", parse_dates=True)

    market_id = 1 if symbol.startswith(("5", "6")) else 0
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&ut=7eea3edcaed734bea9cbfc24409ed989"
        f"&klt=101&fqt=1"
        f"&secid={market_id}.{symbol}"
        f"&beg=20100101&end=20251231"
    )

    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "--retry", "5",
         "--retry-delay", "3", "--retry-all-errors", url],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ConnectionError(f"{symbol} 数据获取失败")

    data_json = json.loads(result.stdout)
    klines = data_json["data"]["klines"]

    rows = []
    for kline in klines:
        parts = kline.split(",")
        rows.append({
            "datetime": parts[0],
            "open": float(parts[1]),
            "close": float(parts[2]),
            "high": float(parts[3]),
            "low": float(parts[4]),
            "volume": int(parts[5]),
        })

    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]
    df.to_csv(csv_path)
    return df


def run_strategy(strat_cls, df):
    """运行单个策略，返回指标字典。"""
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strat_cls)
    cerebro.adddata(bt.feeds.PandasData(dataname=df))
    cerebro.broker.setcash(100_000)
    cerebro.broker.setcommission(commission=0.00025)
    cerebro.broker.set_slippage_perc(perc=0.0005)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe",
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.02)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="rets")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(DailyValue, _name="daily_value")

    strat = cerebro.run()[0]

    trade_analysis = strat.analyzers.trades.get_analysis()
    total_trades = trade_analysis.get("total", {}).get("closed", 0)
    won = trade_analysis.get("won", {}).get("total", 0)

    return {
        "final": cerebro.broker.getvalue(),
        "cagr": strat.analyzers.rets.get_analysis().get("rnorm100", 0),
        "max_dd": strat.analyzers.dd.get_analysis()["max"]["drawdown"],
        "sharpe": strat.analyzers.sharpe.get_analysis().get("sharperatio", None),
        "trades": total_trades,
        "win_rate": (won / total_trades * 100) if total_trades > 0 else 0,
        "strat": strat,
    }


def main():
    strategies = {
        "Buy & Hold": BuyHold,
        "TrendFollowing": TrendFollowing,
    }

    # 收集所有结果
    all_results = {}

    for sym, name in SYMBOLS.items():
        print(f"\n{'='*60}")
        print(f"  标的: {sym} {name}")
        print(f"{'='*60}")

        try:
            df = fetch_symbol(sym)
            print(f"  数据: {len(df)} bars, {df.index[0].date()} ~ {df.index[-1].date()}")
        except Exception as e:
            print(f"  跳过: {e}")
            continue

        time.sleep(1)  # 避免请求太快

        all_results[sym] = {}
        for strat_name, strat_cls in strategies.items():
            result = run_strategy(strat_cls, df)
            all_results[sym][strat_name] = result

    # 打印汇总表
    print("\n\n")
    print("=" * 90)
    print("  多标的对比实验结果")
    print("=" * 90)
    print(f"{'标的':<12} {'策略':<22} {'CAGR':>7} {'MaxDD':>7} {'Sharpe':>8} {'Trades':>7} {'Win%':>6}")
    print("-" * 90)

    for sym, name in SYMBOLS.items():
        if sym not in all_results:
            continue
        for strat_name, result in all_results[sym].items():
            sharpe_str = f"{result['sharpe']:.3f}" if result['sharpe'] else "N/A"
            print(f"{name:<12} {strat_name:<22} {result['cagr']:>6.1f}% "
                  f"{result['max_dd']:>6.1f}% {sharpe_str:>8} "
                  f"{result['trades']:>7} {result['win_rate']:>5.1f}%")
        print("-" * 90)

    # 绘制多标的对比图
    plot_multi_symbol(all_results)


def plot_multi_symbol(all_results):
    """绘制多标的 x 多策略的净值对比图（每个标的一行子图）。"""
    n_symbols = len(all_results)
    fig, axes = plt.subplots(n_symbols, 2, figsize=(16, 4 * n_symbols), squeeze=False)
    fig.suptitle("Multi-Symbol Comparison: Trend Following Strategy\nBuy & Hold vs TrendFollowing (Trailing TP/SL)",
                 fontsize=13, y=0.98)

    colors = {"Buy & Hold": "gray", "TrendFollowing": "steelblue"}

    for row, (sym, strat_results) in enumerate(all_results.items()):
        ax_nav = axes[row, 0]
        ax_dd = axes[row, 1]
        name = SYMBOLS[sym]

        for strat_name, result in strat_results.items():
            analysis = result["strat"].analyzers.daily_value.get_analysis()
            dates = pd.to_datetime(analysis["dates"])
            values = pd.Series(analysis["values"], index=dates)
            nav = values / values.iloc[0]
            color = colors.get(strat_name, "black")

            ax_nav.plot(dates, nav, label=strat_name, color=color, lw=1.0,
                        alpha=0.6 if strat_name == "Buy & Hold" else 0.9)

            cummax = nav.cummax()
            dd = (nav - cummax) / cummax * 100
            ax_dd.fill_between(dates, dd, 0, alpha=0.2, color=color, label=strat_name)

        ax_nav.set_title(f"{sym} {name}", fontsize=11, loc="left")
        ax_nav.axhline(y=1.0, color="black", linestyle="--", alpha=0.2)
        ax_nav.set_ylabel("NAV")
        ax_nav.legend(loc="upper left", fontsize=8)
        ax_nav.grid(True, alpha=0.2)

        ax_dd.set_title(f"{sym} {name} - Drawdown", fontsize=11, loc="left")
        ax_dd.set_ylabel("DD (%)")
        ax_dd.legend(loc="lower left", fontsize=8)
        ax_dd.grid(True, alpha=0.2)

    plt.tight_layout()
    output_path = os.path.join(CACHE_DIR, "multi_symbol_comparison.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\n图表已保存至: {output_path}")
    plt.close()


if __name__ == "__main__":
    main()
