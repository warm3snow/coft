"""
趋势跟踪策略：SMA 双均线 + ATR 移动止盈止损
标的：沪深 300 ETF（510300）、贵州茅台（600519）
数据：东方财富后复权日线，2012-12 ~ 2025-12
对照：Buy & Hold 同标的

用法：
    pip install backtrader matplotlib pandas
    python main.py
"""
import os
import pandas as pd
import backtrader as bt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---- 趋势跟踪策略：SMA 金叉 + ADX 过滤 + ATR 移动止盈止损 ----
class TrendFollowing(bt.Strategy):
    """
    趋势跟踪策略，核心逻辑：

    入场条件：
      - SMA 快线上穿慢线（金叉）
      - ADX > 阈值，确认市场处于趋势状态

    仓位管理：
      - 基于 ATR 计算单笔风险，控制仓位使单笔最大亏损 = 账户 * risk_per_trade

    移动止损（Trailing Stop）：
      - 初始止损 = 入场价 - atr_stop_mult * ATR
      - 持仓期间止损线 = max(当前止损, 最新收盘价 - atr_stop_mult * ATR)
      - 止损线只升不降，锁住浮盈

    移动止盈（收紧止损）：
      - 当浮盈 > profit_threshold * ATR 时，将止损倍数从 atr_stop_mult 收紧为 atr_tight_mult
      - 加速锁利，避免大幅回吐利润

    出场条件：
      - 价格跌破移动止损线
      - 或 SMA 死叉信号
    """
    params = dict(
        fast=20,                # 快线周期
        slow=60,                # 慢线周期
        atr_period=14,          # ATR 周期
        atr_stop_mult=2.5,      # 初始止损 ATR 倍数
        atr_tight_mult=1.2,     # 止盈收紧后的 ATR 倍数
        profit_threshold=3.0,   # 浮盈达到多少倍 ATR 后收紧止损
        risk_per_trade=0.05,    # 单笔风险 5%
        max_position_pct=0.9,   # 最大仓位占比 90%
        adx_period=14,
        adx_threshold=18,       # 降低 ADX 门槛，捕获更多趋势
    )

    def __init__(self):
        sma_f = bt.ind.SMA(self.data.close, period=self.p.fast)
        sma_s = bt.ind.SMA(self.data.close, period=self.p.slow)
        self.crossover = bt.ind.CrossOver(sma_f, sma_s)
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        self.adx = bt.ind.ADX(self.data, period=self.p.adx_period)
        self.stop_price = None
        self.entry_price = None

    def next(self):
        if not self.position:
            # 入场条件：金叉 + ADX 确认趋势
            if self.crossover > 0 and self.adx[0] > self.p.adx_threshold:
                stop = self.data.close[0] - self.p.atr_stop_mult * self.atr[0]
                risk = self.data.close[0] - stop
                if risk <= 0:
                    return
                # 基于风险预算计算仓位
                size = int(
                    (self.broker.getvalue() * self.p.risk_per_trade) / risk
                )
                # 限制最大仓位
                max_size = int(
                    self.broker.getvalue() * self.p.max_position_pct
                    / self.data.close[0]
                )
                size = min(size, max_size)
                if size > 0:
                    self.buy(size=size)
                    self.stop_price = stop
                    self.entry_price = self.data.close[0]
        else:
            # 计算浮盈（以 ATR 为单位）
            profit_in_atr = (self.data.close[0] - self.entry_price) / self.atr[0]

            # 根据浮盈动态调整止损倍数
            if profit_in_atr > self.p.profit_threshold:
                # 浮盈较大，收紧止损
                current_mult = self.p.atr_tight_mult
            else:
                current_mult = self.p.atr_stop_mult

            # 移动止损：只升不降
            new_stop = self.data.close[0] - current_mult * self.atr[0]
            self.stop_price = max(self.stop_price, new_stop)

            # 出场：死叉或触及移动止损
            if self.crossover < 0 or self.data.close[0] < self.stop_price:
                self.close()
                self.stop_price = None
                self.entry_price = None


class BuyHold(bt.Strategy):
    def next(self):
        if not self.position:
            size = int(self.broker.getcash() * 0.95 / self.data.close[0])
            if size > 0:
                self.buy(size=size)


# ---- 数据获取：东方财富 API ----
def _fetch_from_eastmoney(symbol="510300", start_date="20121201", end_date="20251231",
                          adjust="qfq"):
    """
    调用东方财富 API 获取日线数据。
    支持 ETF 和个股。
    """
    import subprocess
    import json

    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    # 沪市=1，深市=0
    market_id = 1 if symbol.startswith(("5", "6")) else 0

    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&ut=7eea3edcaed734bea9cbfc24409ed989"
        f"&klt=101"
        f"&fqt={adjust_dict[adjust]}"
        f"&secid={market_id}.{symbol}"
        f"&beg={start_date}"
        f"&end={end_date}"
    )

    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "--retry", "5",
         "--retry-delay", "5", "--retry-all-errors", url],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ConnectionError(
            f"curl 请求失败 (code {result.returncode}): {result.stderr}\n"
            "提示：东方财富 API 当前不可用。\n"
            "解决方案：稍后重试，或手动准备 CSV 数据文件。"
        )

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
    return df.set_index("datetime")[["open", "high", "low", "close", "volume"]]


def fetch(symbol="510300", start_date="20121201", end_date="20251231"):
    """从东方财富获取数据，成功后缓存为本地 CSV；已有缓存则直接加载。"""
    csv_path = os.path.join(os.path.dirname(__file__), f"{symbol}_daily.csv")

    if os.path.exists(csv_path):
        print(f"  从本地缓存加载: {csv_path}")
        df = pd.read_csv(csv_path, index_col="datetime", parse_dates=True)
        return df

    # 使用后复权数据，避免前复权产生负数价格
    print(f"  从东方财富 API 获取 {symbol} 后复权数据...")
    df = _fetch_from_eastmoney(symbol=symbol, start_date=start_date,
                               end_date=end_date, adjust="hfq")
    df.to_csv(csv_path)
    print(f"  数据已缓存至: {csv_path}")
    return df


# ---- 自定义 Analyzer：记录每日净值 ----
class DailyValue(bt.Analyzer):
    """记录每根 bar 的组合总价值，用于绘图。"""

    def start(self):
        self.values = []
        self.dates = []

    def next(self):
        self.values.append(self.strategy.broker.getvalue())
        self.dates.append(self.data.datetime.date(0))

    def get_analysis(self):
        return {"dates": self.dates, "values": self.values}


# ---- 回测引擎 ----
def run(strat_cls, df, name, cash=100_000, commission=0.00025, stamp_tax=0.0):
    """
    运行单次回测。
    stamp_tax: 印花税率（个股卖出收取，ETF 为 0）
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strat_cls)
    cerebro.adddata(bt.feeds.PandasData(dataname=df))
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.broker.set_slippage_perc(perc=0.0005)  # 5 bp 滑点

    # 个股印花税通过额外佣金近似模拟
    if stamp_tax > 0:
        cerebro.broker.setcommission(commission=commission + stamp_tax / 2)

    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        _name="sharpe",
        timeframe=bt.TimeFrame.Days,
        riskfreerate=0.02,
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="rets")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(DailyValue, _name="daily_value")
    results = cerebro.run()
    strat = results[0]

    # 提取指标
    final_value = cerebro.broker.getvalue()
    cagr = strat.analyzers.rets.get_analysis().get("rnorm100", 0)
    max_dd = strat.analyzers.dd.get_analysis()["max"]["drawdown"]
    sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio", None)

    # 交易统计
    trade_analysis = strat.analyzers.trades.get_analysis()
    total_trades = trade_analysis.get("total", {}).get("closed", 0)
    won = trade_analysis.get("won", {}).get("total", 0)
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0

    print(f"\n{'='*60}")
    print(f"  策略: {name}")
    print(f"{'='*60}")
    print(f"  最终资产:   ¥{final_value:,.2f}")
    print(f"  年化收益:   {cagr:.2f}%")
    print(f"  最大回撤:   {max_dd:.2f}%")
    print(f"  夏普比率:   {sharpe:.4f}" if sharpe else "  夏普比率:   N/A")
    print(f"  交易次数:   {total_trades}")
    print(f"  胜率:       {win_rate:.1f}%")
    print(f"{'='*60}")

    return cerebro, strat


# ---- 绘图：净值对比 + 回撤 ----
def plot_comparison(results, title, output_filename):
    """绘制多策略净值和回撤对比图。results: [(name, strat), ...]"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    fig.suptitle(title, fontsize=13)

    colors = ["gray", "steelblue", "darkorange", "green"]

    for i, (name, strat) in enumerate(results):
        analysis = strat.analyzers.daily_value.get_analysis()
        dates = pd.to_datetime(analysis["dates"])
        values = pd.Series(analysis["values"], index=dates)
        nav = values / values.iloc[0]

        color = colors[i % len(colors)]
        ax1.plot(dates, nav, label=name, color=color, lw=1.2,
                 alpha=0.6 if i == 0 else 0.9)

        # 回撤
        cummax = nav.cummax()
        dd = (nav - cummax) / cummax * 100
        ax2.fill_between(dates, dd, 0, alpha=0.2 + i * 0.1, color=color,
                         label=f"{name} DD")

    ax1.axhline(y=1.0, color="black", linestyle="--", alpha=0.3)
    ax1.set_ylabel("Normalized NAV")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Date")
    ax2.legend(loc="lower left")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), output_filename)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\n图表已保存至: {output_path}")
    plt.close()


# ---- 单标的回测流程 ----
def backtest_symbol(symbol, symbol_name, cash, commission, stamp_tax):
    """对单个标的运行 Buy&Hold 和 TrendFollowing 策略对比。"""
    print(f"\n{'#'*60}")
    print(f"  标的: {symbol_name} ({symbol})")
    print(f"  区间: 2012-12 ~ 2025-12")
    print(f"  初始资金: ¥{cash:,.0f}")
    print(f"  手续费: 万{commission*10000:.1f} | 印花税: {stamp_tax*1000:.1f}‰")
    print(f"{'#'*60}")

    df = fetch(symbol=symbol)
    print(f"  数据量: {len(df)} 条，范围: {df.index[0].date()} ~ {df.index[-1].date()}")

    _, strat_bh = run(BuyHold, df, f"Buy & Hold ({symbol_name})",
                      cash=cash, commission=commission, stamp_tax=stamp_tax)
    _, strat_trend = run(TrendFollowing, df,
                         f"TrendFollowing ({symbol_name})",
                         cash=cash, commission=commission, stamp_tax=stamp_tax)

    return [
        ("Buy & Hold", strat_bh),
        ("TrendFollowing (Trailing TP/SL)", strat_trend),
    ]


def main():
    print("=" * 60)
    print("  趋势跟踪策略回测：移动止盈止损")
    print("  SMA 20/60 + ADX 趋势过滤 + ATR 移动止盈止损")
    print("=" * 60)

    # ---- 沪深 300 ETF (510300) ----
    results_csi300 = backtest_symbol(
        symbol="510300",
        symbol_name="沪深300ETF",
        cash=100_000,
        commission=0.00025,  # ETF 万 2.5
        stamp_tax=0.0,       # ETF 无印花税
    )
    plot_comparison(
        results_csi300,
        title="Trend Following Strategy: CSI 300 ETF (510300)\n2012-12 ~ 2025-12 | Trailing Stop + Take Profit",
        output_filename="trend_csi300.png",
    )

    # ---- 贵州茅台 (600519) ----
    results_moutai = backtest_symbol(
        symbol="600519",
        symbol_name="贵州茅台",
        cash=500_000,         # 茅台股价高，需要更多资金
        commission=0.00025,   # 万 2.5
        stamp_tax=0.001,      # 印花税千 1（卖出）
    )
    plot_comparison(
        results_moutai,
        title="Trend Following Strategy: Kweichow Moutai (600519)\n2012-12 ~ 2025-12 | Trailing Stop + Take Profit",
        output_filename="trend_moutai.png",
    )

    print("\n\n" + "=" * 60)
    print("  全部回测完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
