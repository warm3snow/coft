# 新浪搜索：中文商品新闻可靠入口

## 为什么用新浪搜索

当百度/Bing/Google/DDG 均因 CAPTCHA/反爬机制被拦截时，`search.sina.com.cn` 的中文新闻搜索**不触发验证码**，是目前环境下获取中国农产品/期货现货新闻最可靠的渠道。

## 基础URL模式

```
https://search.sina.com.cn/search?q={关键词}&tp=news&sort=time
```

| 参数 | 值 | 作用 |
|------|-----|------|
| `q` | URL编码关键词 | 搜索词 |
| `tp` | `news` | 限制为新闻（排除综合/图集/视频杂项） |
| `sort` | `time` | 按时间排序，优先看到最新信息 |

## 常用搜索模式

### 产区天气/产量
```
https://search.sina.com.cn/search?q=红枣+新疆+坐果+产量+2026&tp=news&sort=time
https://search.sina.com.cn/search?q=红枣+减产+天气+新疆&tp=news&sort=time
https://search.sina.com.cn/search?q=苹果+陕西+坐果+套袋+2026&tp=news&sort=time
```

### 政策/行业
```
https://search.sina.com.cn/search?q=棉花+新疆+种植面积+2026&tp=news&sort=time
https://search.sina.com.cn/search?q=甲醇+开工率+库存+2026&tp=news&sort=time
```

## 注意事项

1. **搜索结果页导航** — 页面底部有分页按钮，ref ID 为 `e65`(第1页)到 `e76`(最后一页)，可点击翻页查看更多
2. **文章正文查看** — 在新浪搜索结果页点击文章链接后，通常需要 scroll down 一到两次才能看到文章正文（正文在 iframe 之后），可能需要 browser_scroll 配合 browser_snapshot 查看
3. **新闻时效性** — 搜索结果默认按时间排序，最新新闻在前；特定关键词可能只返回少量结果，此时改成 `sort=rel`（按相关度）可能会找到更多
4. **新浪新闻 vs 新浪财经** — 新闻搜索主要覆盖 general news；期货价格类数据仍在 `finance.sina.com.cn/futures/` 页面获取

## 浏览器操作流程

```python
# Step 1: 导航到搜索页
browser_navigate("https://search.sina.com.cn/search?q=红枣+盛花期+新疆&tp=news&sort=time")

# Step 2: 从搜索结果列表中找相关条目
browser_snapshot(full=True)  # 查看搜索结果标题

# Step 3: 点击感兴趣的文章（ref ID通常为 e54 左右，因页面而异）
browser_click(ref="e54")

# Step 4: 等待加载后，滚动查看正文
browser_scroll(direction="down")
browser_snapshot(full=True)  # 查看文章正文内容
```

## 已验证的工作范例

- 2026-06-02 "8.8万亩红枣树盛花期到了！要丰收全看这时候" — 新浪新闻转载看看新闻KNEWS，详细介绍新疆泽普县红枣花期情况
- 2026-05-28 "【农产品早评】红枣：天气影响权重加大，关注产区坐果情况" — 行业晨报
- 2026-03-30 "期货工具持续赋能 新疆红枣产业升级换代提速" — 期货日报/郑商所发布
