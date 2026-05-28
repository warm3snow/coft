# 输出模板

## 1. Finding 结构

每个 Finding 应包含：

```text
Finding {
  id
  domain
  title
  severity
  confidence
  summary
  rationale
  evidence[]
  remediation
  status
}
```

其中 `evidence[]` 至少包含：

- 文件路径
- 行号或片段位置
- 原始证据摘要
- 触发的检查点

`status` 建议取值：

- `confirmed`
- `suspected`
- `manual_review`
- `suppressed`

## 2. Markdown 报告模板

建议结构：

1. 报告摘要
2. 总体评估
3. 高风险问题
4. 详细问题清单
5. 人工复核项
6. 附录

### 2.1 报告摘要

至少包含：

- 扫描对象
- 扫描范围说明
- 问题总数
- 各风险等级数量
- 说明“本结论仅基于仓库静态内容”

### 2.2 详细问题清单

每条问题至少包含：

- 标题
- 风险域
- 风险等级
- 置信度
- 证据
- 判断依据
- 整改建议

## 3. HTML 报告要求

HTML 内容结构应与 Markdown 一致，允许增强但不能改变语义。

建议增强：

- 风险分布摘要区
- Finding 折叠展示
- 证据高亮
- 风险域筛选

## 4. 输出禁忌

不得输出：

- 没有证据的强结论
- 引用了未读文件的判断
- 把推测表述成事实
- 把“未观察到”表述成“确定不存在”
