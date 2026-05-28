# 示例

## 0. 使用规则

- 先读 `standards.md`。
- 再按 `output-template.md` 输出。
- 只有在输出风格拿不准时再看这里。

## 1. 审阅指令

```text
按 guomi-app-data-security 对当前仓库做应用和数据安全方向审阅。

要求：
1. 仅基于你实际读取到的文件下结论。
2. 重点检查数据加密、鉴权与访问控制、通信安全、国密适配线索。
3. 所有结论必须附带文件路径、位置和判断依据。
4. 证据不足时标记为 manual_review。
5. 输出 Markdown 报告。
```

## 2. 最小合格输出

```markdown
# 应用和数据安全审阅报告

- Scope: `src/, config/, deployment/`
- Summary: `critical=0 high=1 medium=2 low=1 manual_review=2`
- Note: `本结论仅基于仓库静态内容，不替代正式密评认证`

## 总体评估
- 数据加密：发现 1 个中风险问题。
- 鉴权与访问控制：发现 1 个高风险问题，1 个人工复核项。
- 通信安全：发现 1 个中风险问题。
- 国密适配线索：需人工复核。

## 高风险问题
## 管理接口缺少明确鉴权保护
- Domain: `authentication_authorization`
- Severity: `high`
- Confidence: `medium`
- Status: `manual_review`
- Evidence: `src/admin/routes.py:12` + `@router.get('/admin/users')`
- Rationale: 当前已查看代码中未见明确鉴权保护。
- Remediation: 确认统一鉴权链路；若没有，应补充认证与角色校验。
```

## 3. Finding 示例

```text
Finding {
  id: "AUTH-001",
  domain: "authentication_authorization",
  title: "管理接口缺少明确鉴权保护",
  severity: "high",
  confidence: "medium",
  summary: "发现管理类接口暴露，但当前已查看代码中未见明确鉴权中间件或注解保护。",
  rationale: "接口路径显示为管理能力，且处理逻辑中未见权限判断。由于尚未确认是否由上层网关统一鉴权，因此保留部分不确定性。",
  evidence: [
    {
      file: "src/admin/routes.py",
      location: "12-38",
      excerpt: "@router.get('/admin/users')"
    }
  ],
  remediation: "确认该接口是否已由统一鉴权链路保护；若没有，应补充认证与角色校验。",
  status: "manual_review"
}
```

## 4. 禁止写法示例

- 误用：没有看到 TLS 配置，就直接写“系统未启用 TLS”。
  正确：写成“当前已查看仓库内容中未观察到 TLS 配置证据，需人工复核”。

- 误用：看到 `md5` 字符串就直接写“敏感数据使用弱算法”。
  正确：先确认其是否真实用于敏感数据保护，否则保守处理。

- 误用：把“最佳实践偏差”直接写成“密评不通过”。
  正确：区分规范性建议和明确风险结论。

- 误用：直接输出详细问题，不写摘要和高风险问题区。
  正确：按 `output-template.md` 的固定结构输出。
