# coft

> Complex Systems of Trading — 量化交易、AI 工程、Agent & Skills 实践合集

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## 简介

coft 是一个面向技术人的量化交易与 AI 工程实践仓库。每个子项目都是一个**可独立运行**的最小完整示例，配套公众号文章讲解核心概念。

目标：**clone 即用，代码即文档**。

## 目录结构

```
coft/
├── quant/                   # 量化交易实践
│   └── backtrader-sma-atr/  # Backtrader SMA双均线 + ATR止损策略
├── ai-engineering/          # AI 工程化实践
├── agent-skills/            # Agent & Skills 实践
├── LICENSE                  # Apache 2.0
└── README.md
```

## 快速开始

每个子项目目录内都有独立的 `README.md` 和 `requirements.txt`，进入对应目录按说明运行即可。

例如运行 Backtrader 均线策略回测：

```bash
cd quant/backtrader-sma-atr
pip install -r requirements.txt
python sma_atr_strategy.py
```

## 项目列表

### 量化交易 (quant/)

| 项目 | 说明 | 文章 |
|------|------|------|
| [backtrader-sma-atr](quant/backtrader-sma-atr/) | SMA 双均线 + ATR 止损，含手续费/滑点/风控 | 用 Backtrader 拆解量化交易 |

### AI 工程 (ai-engineering/)

*持续更新中...*

### Agent & Skills (agent-skills/)

*持续更新中...*

## 环境要求

- Python 3.9+
- 各子项目的具体依赖见对应 `requirements.txt`

## 许可证

[Apache License 2.0](LICENSE)

## 关注公众号

更多量化、AI 工程、复杂系统文章，关注公众号获取。
