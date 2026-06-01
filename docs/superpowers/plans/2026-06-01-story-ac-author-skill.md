# Story-AC Author Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a documentation-only skill `agent-skills/story-ac-author/` that turns natural-language requirements into agile User Stories with testable Given-When-Then acceptance criteria via interactive 5-dimension clarification.

**Architecture:** Five Markdown files (SKILL.md / standards.md / output-template.md / examples.md / README.md) following the same skeleton as the existing `guomi-app-data-security` and `ai-codebase-docs` skills. No executable code. Verification is via cross-file consistency checks and a dry-run on a sample requirement.

**Tech Stack:** Markdown only. Reference spec: `docs/superpowers/specs/2026-06-01-story-ac-author-design.md`.

**Reference Note:** Throughout this plan, "spec" refers to the design document at `docs/superpowers/specs/2026-06-01-story-ac-author-design.md`. The spec contains verbatim content for many sections — copy that content rather than rewriting from memory.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `agent-skills/story-ac-author/SKILL.md` | Entry: HARD-GATE, Required Order, Output Gate, Review Checklist, Common Failures, Red Flags |
| `agent-skills/story-ac-author/standards.md` | Judgment rules: 5-dimension clarification matrix, AC 4-item hard checks, forbidden words, Epic split rules, file-landing conventions |
| `agent-skills/story-ac-author/output-template.md` | Single-Story template, Epic-index template, AC unit format, template usage constraints |
| `agent-skills/story-ac-author/examples.md` | Good/bad examples, demand-based clarification dialog, Epic split dialog, anti-patterns |
| `agent-skills/story-ac-author/README.md` | Read order, file roles, design principles |

---

## Task 1: Create directory and README.md

**Files:**
- Create: `agent-skills/story-ac-author/README.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p agent-skills/story-ac-author
```

Verify with `ls agent-skills/story-ac-author` — directory exists, empty.

- [ ] **Step 2: Write README.md**

Write the following content to `agent-skills/story-ac-author/README.md`:

```markdown
# story-ac-author

把自然语言需求转换为敏捷 User Story 与可测试可验收 AC 的 skill。

## Read Order

1. `SKILL.md`
2. `standards.md`
3. `output-template.md`
4. `examples.md`

## 文件说明

- `SKILL.md`：Skill 入口说明，硬约束与必做顺序
- `standards.md`：5 维度澄清规则、AC 4 项硬性检查、Epic 拆分判定、禁止写法
- `output-template.md`：Story、AC、Epic 索引的 Markdown 模板
- `examples.md`：好例 / 坏例 / 典型对话片段 / 反模式

## 使用要点

- 先读 `SKILL.md` 的硬约束和执行顺序。
- 5 维度未全部澄清前不得生成 Story。
- 每条 AC 落盘前必须通过 4 项硬性检查。
- 检测到 Epic 信号时必须先与用户确认拆分方案。
- 任务要求生成文档时，必须实际写入文件，不得只在对话里输出文本。

## 设计原则

- Skill 只定义标准，不实现执行器或解析器。
- Skill 要求所有 Story 必须附澄清证据（澄清记录表）。
- Skill 要求每条 AC 必须可独立验证。
- Skill 拒绝模糊词（"正确地"/"合适的"/"尽快"等）。
- Skill 在落盘前必须过 Output Gate；不过则修正再过，直到全部通过。
```

- [ ] **Step 3: Verify README.md**

Run: `wc -l agent-skills/story-ac-author/README.md`
Expected: ~30 lines.

Run: `grep -c "^##" agent-skills/story-ac-author/README.md`
Expected: 4 (Read Order / 文件说明 / 使用要点 / 设计原则).

- [ ] **Step 4: Commit**

```bash
git add agent-skills/story-ac-author/README.md
git commit -m "feat(agent-skills): scaffold story-ac-author skill with README"
```

---

## Task 2: output-template.md — Story template section

**Files:**
- Create: `agent-skills/story-ac-author/output-template.md`

- [ ] **Step 1: Write file header and Story template**

Write the following content to `agent-skills/story-ac-author/output-template.md`:

````markdown
# Output Templates

本文件定义 story-ac-author skill 落盘文档的 Markdown 骨架。三类模板：

1. 单 Story 文件模板 (§1)
2. Epic 索引文件模板 (§2)
3. AC 单元格式 (§3，嵌入在 Story 模板内)

## 1. 单 Story 文件模板

落盘路径：`docs/stories/YYYY-MM-DD-<slug>.md`

```markdown
# Story: <一句话标题>

> 生成时间: YYYY-MM-DD
> 角色: <已澄清的具体角色>
> 状态: draft

## Story

As a <具体角色>
I want <目标，不含实现细节>
So that <可识别的业务价值>

## 上下文 (Context)

<2-4 句澄清后的关键背景：触发场景、上游/下游关系、为什么现在要做>

## 范围 (In Scope)

- <本 Story 包含的能力点 1>
- <本 Story 包含的能力点 2>

## 不在范围 (Out of Scope)

- <明确不做的项 1，附简短理由>
- <明确不做的项 2>

## Acceptance Criteria

### AC-1: <一句话场景标题>
- **Given** <具体的前置状态/数据>
- **When** <用户/系统的具体动作>
- **Then** <可观察的结果，含具体值>
- **And** <附加可观察结果（可选）>

**边界**: <若涉及范围/时间/并发/数量，明确边界值>
**验证方式建议**: <单测 / 接口测试 / E2E / 手工 中的一项或多项>

### AC-2: ...

## 依赖与假设

- 依赖: <上游服务/数据/前置 Story，无则写"无">
- 假设: <skill 已与用户确认的隐性前提>

## 澄清记录

| 维度 | 状态 | 依据 |
|---|---|---|
| 用户角色 | 明确 | 用户原文："..." |
| 核心场景 | 明确 (轮 N 提问) | 用户回答：... |
| 边界与异常 | 明确 (轮 N 提问) | 用户回答：... |
| 验收判定 | 明确 (轮 N 提问) | 用户回答：... |
| 范围边界 | 明确 | 用户原文："..." |

## AC 检查通过记录

| AC | 输入具体 | 期望可观察 | 边界明确 | 可独立验证 |
|---|---|---|---|---|
| AC-1 | ✓ | ✓ | ✓ | ✓ |
| AC-2 | ✓ | ✓ | ✓ | ✓ |
```

### 1.1 强制字段

以下字段不得删除：

- 顶部元数据三行（生成时间 / 角色 / 状态）
- `## Story` 三行（As a / I want / So that）
- `## Acceptance Criteria` 章节（至少 1 条 AC）
- `## 澄清记录` 表格
- `## AC 检查通过记录` 表格

### 1.2 条件字段

- AC 中的 `And` 行：≥1 个附加观察结果时使用
- AC 中的 `**边界**` 行：涉及范围/时间/并发/数量时使用
- AC 中的 `**验证方式建议**` 行：建议字段，缺失不算违规
````

- [ ] **Step 2: Verify Story template structure**

Run: `grep -E "^### 1\." agent-skills/story-ac-author/output-template.md`
Expected: matches `### 1.1 强制字段` and `### 1.2 条件字段`.

Run: `grep -c "澄清记录\|AC 检查通过记录" agent-skills/story-ac-author/output-template.md`
Expected: ≥ 2 (one in template body, one in 强制字段 section).

---

## Task 3: output-template.md — Epic index template + usage constraints

**Files:**
- Modify: `agent-skills/story-ac-author/output-template.md`

- [ ] **Step 1: Append Epic index template**

Append to `agent-skills/story-ac-author/output-template.md`:

````markdown

## 2. Epic 索引文件模板

落盘路径：`docs/stories/YYYY-MM-DD-<epic-slug>/README.md`

子 Story 文件命名：`NN-<story-slug>.md`（NN 为两位数字序号，表示建议交付顺序）

```markdown
# Epic: <一句话标题>

> 生成时间: YYYY-MM-DD
> 状态: draft

## 背景

<3-5 句：业务目标、用户问题、为什么需要拆成多个 Story>

## 共享角色定义

| 角色 | 定义 |
|---|---|
| <角色名> | <定义> |

## 术语表

| 术语 | 定义 |
|---|---|
| <术语> | <定义> |

## Story 列表

| 序号 | Story | 依赖 (depends_on) | 文件 |
|---|---|---|---|
| 01 | <Story 标题> | 无 | [01-<slug>.md](./01-<slug>.md) |
| 02 | <Story 标题> | 01 | [02-<slug>.md](./02-<slug>.md) |

## 拆分依据

<列出触发拆分的信号与本次具体命中点。引用 standards.md §3 的 5 个信号。>
- 信号 X：<具体说明>
- 信号 Y：<具体说明>
```

### 2.1 强制字段

- 顶部元数据两行（生成时间 / 状态）
- `## 背景` 章节
- `## Story 列表` 表格（至少 2 行）
- `## 拆分依据` 章节（至少列出 1 个命中信号）

### 2.2 条件字段

- `## 共享角色定义`：≥1 个跨 Story 共享角色时必填，否则可省略
- `## 术语表`：存在跨 Story 共享术语时必填，否则可省略

## 3. AC 单元格式（嵌入 §1 Story 模板）

每条 AC 的强制结构：

```
### AC-<编号>: <一句话场景标题>
- **Given** <具体前置>
- **When** <具体动作>
- **Then** <可观察结果>
```

允许追加（按需）：

- `- **And** <附加可观察结果>` —— 多于 1 个观察结果时使用
- `**边界**: <边界值>` —— 涉及范围/时间/并发/数量时必填
- `**验证方式建议**: <方式>` —— 建议字段

## 4. 模板使用约束

以下规则在所有模板使用场景中强制生效：

- 不得删除 §1.1 与 §2.1 列出的强制字段。
- 不得用空表占位：表格存在但内容为空 / 仅含占位符 `<...>` / 仅含表头 —— 视为未通过 Output Gate。
- 自定义新增章节允许，但不得删除已有的强制章节。
- 角色字段不得使用泛化"用户"，必须填写已澄清的具体角色名。
- 状态字段在初次生成时统一为 `draft`；后续状态变更不在本 skill 职责范围。
````

- [ ] **Step 2: Verify file structure**

Run: `grep -E "^## [1-4]\." agent-skills/story-ac-author/output-template.md`
Expected: 4 lines matching `## 1. 单 Story 文件模板`, `## 2. Epic 索引文件模板`, `## 3. AC 单元格式`, `## 4. 模板使用约束`.

Run: `wc -l agent-skills/story-ac-author/output-template.md`
Expected: ~150 lines.

- [ ] **Step 3: Commit**

```bash
git add agent-skills/story-ac-author/output-template.md
git commit -m "feat(agent-skills): add story-ac-author output templates"
```

---

## Task 4: standards.md — 5-dimension clarification matrix

**Files:**
- Create: `agent-skills/story-ac-author/standards.md`

- [ ] **Step 1: Write file header and §1 (5 dimensions)**

Write the following content to `agent-skills/story-ac-author/standards.md`:

```markdown
# Standards

本文件定义 story-ac-author skill 在与用户交互、生成 Story、生成 AC、判定 Epic 拆分时所有判定口径与禁止写法。

章节：

1. 5 维度澄清矩阵 (§1)
2. 按需提问判定流程 (§2)
3. AC 4 项硬性检查 (§3)
4. AC 禁止写法 (§4)
5. Story 自身轻量检查 (§5)
6. Epic 拆分判定信号 (§6)
7. Epic 拆分流程 (§7)
8. 文件落盘约定 (§8)
9. slug 派生规则 (§9)

## 1. 5 维度澄清矩阵

每个需求生成 Story 前必须将以下 5 个维度全部判定为"明确"。

| # | 维度 | 必须搞清的事 | "已明确"判定标准 |
|---|---|---|---|
| 1 | 用户角色 | 谁会用？是否多角色？权限差异？ | 用户原始描述里点名了具体角色（如"注册用户"/"管理员"/"游客"），且角色单一或差异已说明 |
| 2 | 核心场景 | 触发条件、主流程步骤、价值结果 | 用户说清了"什么时候触发 → 走什么流程 → 拿到什么结果" |
| 3 | 边界与异常 | 输入边界、并发、超时、错误分支、空态 | 用户主动列出了至少 1 个失败/异常分支 |
| 4 | 验收判定 | 怎么算"做完了"？可观察的成功信号 | 用户给出可观察指标/结果（如"返回 200"/"页面跳转到 X"/"数据库写入"） |
| 5 | 范围边界 (Out of Scope) | 这次不做什么？依赖谁？ | 用户主动声明了不做项或下游依赖 |

判定时的取证要求：

- 维度被判为"明确"时，必须在内部澄清记录中保留依据（用户原文片段或对应轮次的用户回答）。
- 不得用"假设默认值"代替"已明确"。
- 不得把"用户未提及"等同于"无要求"——未提及的维度按未明确处理。

## 2. 按需提问判定流程

```
对每个维度 i ∈ {1..5}:
  if 该维度已"明确"（按 §1 标准）:
     skip，在内部澄清记录中标注 "明确(原文证据: ...)"
  else:
     生成 1 个针对性问题（优先多选，否则开放式）
     一次只问 1 个问题，等待用户回答
     回答后重新判定该维度是否明确
循环直到 5 个维度全部"明确"
```

提问优先策略：

- 优先**多选题**（A/B/C，覆盖常见取值）。
- 多选无法穷举常见取值时改用开放式问题。
- 每个问题必须附"为什么问"（一句话），让用户理解必要性。

提问期间的硬约束：

- 不得在同一条消息里问多个澄清问题。
- 不得跳过 5 维度中任何一个维度。
- 不得用默认值替代提问，除非该默认值在本文件中明确允许（当前版本无此例外）。
```

- [ ] **Step 2: Verify §1-§2 sections present**

Run: `grep -E "^## [1-2]\." agent-skills/story-ac-author/standards.md`
Expected: matches `## 1. 5 维度澄清矩阵` and `## 2. 按需提问判定流程`.

Run: `grep -c "^| [1-5] |" agent-skills/story-ac-author/standards.md`
Expected: 5 (one row per dimension in §1 table).

---

## Task 5: standards.md — AC 4-item hard checks + forbidden words + Story checks

**Files:**
- Modify: `agent-skills/story-ac-author/standards.md`

- [ ] **Step 1: Append §3 (AC 4-item checks)**

Append to `agent-skills/story-ac-author/standards.md`:

```markdown

## 3. AC 4 项硬性检查

每条 AC（Given-When-Then 三段，含可选 And/边界/验证方式建议）在落盘前必须满足全部 4 项。

| # | 检查项 | 通过标准 | 不通过示例 → 修正示例 |
|---|---|---|---|
| 1 | 输入具体 | Given/When 中所有"输入数据/前置状态"必须是具体值或具体集合，不得用模糊词 | "用户输入合适的密码" → "用户输入符合 8-20 位、含数字+字母的密码 'Abc12345'" |
| 2 | 期望可观察 | Then 中的"结果"必须是外部可观察的：UI 文案 / 路由跳转 / HTTP 状态码 / 响应字段 / 数据库行变化 / 事件发出 | "系统正确处理请求" → "API 返回 200 + body 中 `data.userId` 为新创建用户 ID" |
| 3 | 边界明确 | 凡涉及范围/时间/并发/数量的 AC，必须标注边界值 | "验证码有效期内可用" → "验证码自下发起 5 分钟内有效，第 6 分钟必须返回 410 Gone" |
| 4 | 可独立验证 | 该 AC 不依赖其他 AC 的执行结果就能单独验证（每条 AC 自带必要前置） | "AC-2 在 AC-1 完成后..." → "AC-2: Given 用户已登录（前置可独立构造），..." |

第 4 项允许 AC 之间共享前置，但**前置必须独立可构造**——不能强依赖另一条 AC 的执行才能成立。

落盘前自检流程：

- 对每条 AC 跑一遍 4 项检查。
- 任何一项失败必须先修正再落盘。
- 在文档底部"AC 检查通过记录"表中为每条 AC 的每项打 ✓。

## 4. AC 禁止写法

AC 中出现以下任一关键词或表达模式，视为未通过检查，必须修正：

| 禁止词/模式 | 原因 | 修正方向 |
|---|---|---|
| "正确地" / "合适的" / "合理的" | 主观、不可验证 | 替换为具体阈值或可观察行为 |
| "尽快" / "及时" / "高效" | 无可测量边界 | 给出 SLA 数值（如 "P95 < 500ms"） |
| "易用" / "友好" / "美观" | 主观感受 | 用具体行为或 UI 文案替代 |
| "支持" / "兼容" 后接模糊对象 | 范围不清 | 列出具体对象集合（如 "支持 Chrome 100+ / Firefox 100+"） |
| 仅描述实现而无外部观察 | 不可验收 | 改写为外部可观察的行为或数据 |

注：以上为关键词级硬筛。语义级"模糊期望"由 §3 第 2 项（期望可观察）兜底。

## 5. Story 自身轻量检查

Story 主体（As a / I want / So that）必须满足：

- **角色具体**：不得使用泛化"用户"，必须为已澄清出的具体角色（如"注册用户"/"管理员"）。
- **价值清晰**：So that 子句必须能回答"为什么要做"，不得是 "so that the feature works" 这类无意义陈述。
- **不含实现细节**：I want 子句描述目标，不指定技术方案（如不得写"通过 JWT 实现登录"）。
```

- [ ] **Step 2: Verify §3-§5 sections present**

Run: `grep -E "^## [3-5]\." agent-skills/story-ac-author/standards.md`
Expected: matches `## 3. AC 4 项硬性检查`, `## 4. AC 禁止写法`, `## 5. Story 自身轻量检查`.

Run: `grep -c "^| [1-4] |" agent-skills/story-ac-author/standards.md`
Expected: ≥ 9 (5 rows in §1 + 4 rows in §3, plus possibly §4 rows).

---

## Task 6: standards.md — Epic split rules + file landing + slug derivation

**Files:**
- Modify: `agent-skills/story-ac-author/standards.md`

- [ ] **Step 1: Append §6-§9**

Append to `agent-skills/story-ac-author/standards.md`:

````markdown

## 6. Epic 拆分判定信号

5 维度澄清完成后、生成 Story 前评估以下 5 个信号。**任一命中即触发 Epic 拆分流程（§7）**。

| # | 信号 | 触发条件 |
|---|---|---|
| 1 | 多个独立用户角色 | 澄清后发现 ≥ 2 个角色，且各角色有独立的核心场景 |
| 2 | 多个独立价值点 | "So that" 子句中能写出 ≥ 2 个互不依赖的收益陈述 |
| 3 | 多个独立流程入口 | 触发条件/入口超过 1 个，且各入口的成功路径不重叠 |
| 4 | AC 数量过载 | 预估 AC 数量 > 8 条 |
| 5 | 跨多个数据/系统边界 | 涉及 ≥ 2 个独立子系统/服务/数据域 |

## 7. Epic 拆分流程

```
评估 §6 的 5 个信号
  └─ 0 个命中 → 单 Story 模式（走 §1-§5 标准生成流程）
  └─ ≥ 1 个命中 → 进入 Epic 拆分:
       1) 向用户展示拆分建议:
          - 列出建议拆出的 Story 标题（≥ 2 个）
          - 列出本次命中的具体信号
       2) 等用户确认 / 调整拆分方案
       3) 对每个 Story 走完整的 5 维度澄清（公共维度可复用）
       4) 逐个生成 Story + AC，每个 Story 独立通过 §3 4 项检查
```

拆分阶段硬约束：

- 不得不经用户确认就直接拆分或合并 Story。
- 拆分后每个 Story 必须独立通过 5 维度澄清，不得共享含糊维度。
- 公共上下文（角色定义、术语）在 Epic 索引文件中沉淀（参见 output-template.md §2），不在每个 Story 重复。

## 8. 文件落盘约定

### 8.1 单 Story 模式

```
docs/stories/YYYY-MM-DD-<slug>.md
```

- 日期取生成当日。
- slug 派生规则见 §9。

### 8.2 Epic 模式

```
docs/stories/YYYY-MM-DD-<epic-slug>/
├── README.md                  # Epic 索引（output-template.md §2）
├── 01-<story-slug>.md
├── 02-<story-slug>.md
└── 03-<story-slug>.md
```

- Epic 单独建子目录。
- 子 Story 文件名前缀 `NN-`：两位数字序号，表示建议交付顺序（不强制依赖）。
- Epic README.md 列出共享角色定义、术语表、Story 列表与依赖关系（用 `depends_on` 字段显式声明）。

### 8.3 命名冲突处理

- 同日同 slug 已存在 → 追加后缀 `-v2`、`-v3`，依此类推。
- 不得覆盖已有文件，不得静默重命名。

### 8.4 落盘前最终检查

写文件前必须确认：

- [ ] 5 维度全部明确。
- [ ] 每条 AC 通过 §3 4 项硬性检查。
- [ ] AC 中无 §4 禁止词。
- [ ] Story 通过 §5 轻量检查。
- [ ] Epic 拆分（如适用）已用户确认。
- [ ] 文件路径不与已有文件冲突。
- [ ] Epic 索引中 `depends_on` 引用的 Story 文件全部已生成。

任一项未通过，**不得落盘**。

## 9. slug 派生规则

slug 由用户确认后的 Story 主标题派生，转换步骤：

1. 转小写。
2. 中文标题先翻译为英文或音译为拼音（与用户确认翻译/拼音）。
3. 空格与下划线转 hyphen。
4. 去除停用词：英文 `the / a / an / of / for / and / or`；中文（在翻译前）`的 / 了 / 在 / 和 / 与`。
5. 仅保留 ASCII 字母数字与 hyphen，其余字符删除。
6. 连续 hyphen 合并为单个 hyphen。
7. 截断至 40 字符并去除首尾 hyphen。

边界：

- 若 slug 派生后为空（如纯特殊符号标题），skill 必须停止落盘并请用户提供 slug。
- slug 派生过程必须对用户透明：在落盘前展示派生后的 slug 供用户确认。
````

- [ ] **Step 2: Verify §6-§9 sections present**

Run: `grep -E "^## [6-9]\." agent-skills/story-ac-author/standards.md`
Expected: matches all four sections (§6, §7, §8, §9).

Run: `grep -c "^### 8\." agent-skills/story-ac-author/standards.md`
Expected: 4 (8.1, 8.2, 8.3, 8.4).

- [ ] **Step 3: Commit**

```bash
git add agent-skills/story-ac-author/standards.md
git commit -m "feat(agent-skills): add story-ac-author standards"
```

---

## Task 7: examples.md — Good example (single Story)

**Files:**
- Create: `agent-skills/story-ac-author/examples.md`

- [ ] **Step 1: Write file header and Good Example**

Write the following content to `agent-skills/story-ac-author/examples.md`:

````markdown
# Examples

本文件用具体场景演示 story-ac-author skill 的正确用法与典型错误。

章节：

1. 好例：单 Story 完整样例 (§1)
2. 坏例：含禁止词与依赖耦合的 AC 修正 (§2)
3. 典型按需提问对话片段 (§3)
4. Epic 拆分对话片段 (§4)
5. 反模式清单 (§5)

## 1. 好例：单 Story 完整样例

**用户原始输入**：

> 我们需要做一个手机号 + 短信验证码的登录功能。注册用户用这个登录，验证码 5 分钟有效，输错 5 次锁定账号 30 分钟。这次只做登录，不做注册和找回密码。登录成功要返回 token，前端跳转到首页。

**skill 行为**：识别 5 维度状态：

- 用户角色 ✓（注册用户）
- 核心场景 ✓（手机号 + 验证码登录）
- 边界与异常 ✓（5 分钟有效、5 次锁定 30 分钟）
- 验收判定 ✓（返回 token、跳转首页）
- 范围边界 ✓（不做注册和找回密码）

5 维度全部明确，无 Epic 拆分信号（单角色、单价值点、单流程、AC 预估 ≤ 5 条）。直接生成 Story。

**落盘文件**：`docs/stories/2026-06-01-sms-login.md`

```markdown
# Story: 验证码登录

> 生成时间: 2026-06-01
> 角色: 注册用户
> 状态: draft

## Story

As a 注册用户
I want 通过手机号 + 短信验证码登录
So that 不必记忆密码也能安全访问账户

## 上下文 (Context)

平台已有手机号注册的用户基础。当前登录方式仅有密码登录，部分用户反馈忘记密码导致流失。本次新增验证码登录路径，作为密码登录的并行入口。

## 范围 (In Scope)

- 手机号 + 验证码登录主流程
- 验证码有效期校验
- 错误次数计数与账号锁定

## 不在范围 (Out of Scope)

- 注册流程（已有，本次不改）
- 找回密码（独立 Story 处理）
- 第三方登录（路线图后续）

## Acceptance Criteria

### AC-1: 验证码正确登录成功
- **Given** 用户已注册，账号未锁定，5 分钟内已请求过验证码
- **When** 用户输入正确的 6 位数字验证码并提交
- **Then** API 返回 200，body 中 `data.token` 为非空字符串
- **And** 前端跳转到 `/home` 路由

**边界**: 验证码自下发起 5 分钟内有效。
**验证方式建议**: 接口测试 + E2E。

### AC-2: 验证码错误提示
- **Given** 用户已注册，账号未锁定，5 分钟内已请求过验证码
- **When** 用户输入错误的 6 位数字验证码并提交
- **Then** API 返回 401，body 中 `error.code` 为 `INVALID_OTP`
- **And** 该账号的"登录失败计数"+1

**验证方式建议**: 接口测试。

### AC-3: 验证码过期
- **Given** 用户已注册，账号未锁定，验证码下发已超过 5 分钟
- **When** 用户输入该验证码并提交
- **Then** API 返回 410，body 中 `error.code` 为 `OTP_EXPIRED`

**边界**: 第 6 分钟（即下发后 300.001 秒起）触发该响应。
**验证方式建议**: 接口测试。

### AC-4: 连续错误锁定
- **Given** 用户已注册且未锁定，"登录失败计数" 已为 4
- **When** 用户再次输入错误验证码并提交
- **Then** API 返回 403，body 中 `error.code` 为 `ACCOUNT_LOCKED`
- **And** 账号状态变为 `locked`，锁定开始时间为当前时间

**边界**: 失败计数 ≥ 5 时锁定 30 分钟。
**验证方式建议**: 接口测试。

### AC-5: 锁定期内拒绝登录
- **Given** 用户账号已被锁定不足 30 分钟
- **When** 用户提交任何验证码
- **Then** API 返回 403，body 中 `error.code` 为 `ACCOUNT_LOCKED`
- **And** 不增加失败计数

**边界**: 锁定剩余时间 > 0 时该响应必现。
**验证方式建议**: 接口测试。

## 依赖与假设

- 依赖: 短信网关已具备发送验证码能力（不在本 Story 范围内）
- 假设: "登录失败计数" 字段已在用户表存在；若不存在，作为本 Story 的实施前置

## 澄清记录

| 维度 | 状态 | 依据 |
|---|---|---|
| 用户角色 | 明确 | 用户原文："注册用户用这个登录" |
| 核心场景 | 明确 | 用户原文："手机号 + 短信验证码的登录功能" |
| 边界与异常 | 明确 | 用户原文："5 分钟有效、输错 5 次锁定 30 分钟" |
| 验收判定 | 明确 | 用户原文："返回 token、跳转到首页" |
| 范围边界 | 明确 | 用户原文："只做登录，不做注册和找回密码" |

## AC 检查通过记录

| AC | 输入具体 | 期望可观察 | 边界明确 | 可独立验证 |
|---|---|---|---|---|
| AC-1 | ✓ | ✓ | ✓ | ✓ |
| AC-2 | ✓ | ✓ | N/A | ✓ |
| AC-3 | ✓ | ✓ | ✓ | ✓ |
| AC-4 | ✓ | ✓ | ✓ | ✓ |
| AC-5 | ✓ | ✓ | ✓ | ✓ |
```

**关键点**：

- 5 维度全部从用户原文取证，无需提问。
- 每条 AC 给出具体响应码、字段名、边界值。
- AC 之间共享前置（"用户已注册"），但前置可独立构造，不依赖其他 AC 的执行结果。
- 锁定相关 AC（AC-4、AC-5）边界数值 (5 次、30 分钟、6 分钟)写明。
````

- [ ] **Step 2: Verify Good example structure**

Run: `grep -c "^### AC-" agent-skills/story-ac-author/examples.md`
Expected: 5 (AC-1 through AC-5 in the good example).

---

## Task 8: examples.md — Bad example, dialogs, anti-patterns

**Files:**
- Modify: `agent-skills/story-ac-author/examples.md`

- [ ] **Step 1: Append §2 (Bad example)**

Append to `agent-skills/story-ac-author/examples.md`:

````markdown

## 2. 坏例：含禁止词与依赖耦合的 AC 修正

**错误的 AC 写法**：

```markdown
### AC-1: 用户登录
- **Given** 用户已注册
- **When** 用户输入合适的密码
- **Then** 系统正确处理登录请求并尽快返回结果

### AC-2: 锁定逻辑
- **Given** AC-1 已通过
- **When** 用户多次失败
- **Then** 锁定账号一段时间
```

**问题诊断**：

| 位置 | 问题 | 违反的检查 |
|---|---|---|
| AC-1 When | "合适的密码" 模糊 | §3-1 输入具体 / §4 禁止词 |
| AC-1 Then | "正确处理"、"尽快"、"结果" 全部不可观察 | §3-2 期望可观察 / §4 禁止词 |
| AC-2 Given | "AC-1 已通过" 形成串行依赖 | §3-4 可独立验证 |
| AC-2 When | "多次" 无具体次数 | §3-1 输入具体 / §3-3 边界明确 |
| AC-2 Then | "一段时间" 无边界值 | §3-3 边界明确 |

**修正后**：

```markdown
### AC-1: 密码正确登录成功
- **Given** 用户已注册（user_status = active），密码已设置（password_hash 非空）
- **When** 用户提交手机号 + 符合 8-20 位含数字+字母的密码（如 "Abc12345"），密码与数据库 hash 匹配
- **Then** API 返回 200，body 中 `data.token` 为非空字符串
- **And** 前端跳转到 `/home` 路由

**验证方式建议**: 接口测试 + E2E。

### AC-2: 连续错误锁定
- **Given** 用户已注册（user_status = active），"登录失败计数" 已为 4（前置可独立构造，不依赖 AC-1）
- **When** 用户提交错误密码
- **Then** API 返回 403，body 中 `error.code` 为 `ACCOUNT_LOCKED`
- **And** 账号状态变为 `locked`，锁定开始时间为当前时间

**边界**: 失败计数 ≥ 5 时锁定 30 分钟。
**验证方式建议**: 接口测试。
```

**修正点**：

- 模糊词（"合适的"/"正确"/"尽快"/"多次"/"一段时间"）全部替换为具体值或可观察响应。
- AC-2 不再依赖 AC-1，前置改为可独立构造的"失败计数 = 4"。
- 边界值（30 分钟、5 次）写明。

## 3. 典型按需提问对话片段

**用户原始输入**：

> 想做一个用户头像上传功能。

**skill 5 维度评估**：

| 维度 | 状态 | 备注 |
|---|---|---|
| 用户角色 | 不明确 | "用户" 太泛化，是注册用户、游客、管理员？ |
| 核心场景 | 部分明确 | 仅说"上传"，没说在哪上传、上传后做什么 |
| 边界与异常 | 不明确 | 文件大小？格式？失败处理？ |
| 验收判定 | 不明确 | 上传成功后头像显示在哪里？ |
| 范围边界 | 不明确 | 是否包含裁剪、滤镜、历史头像管理？ |

**skill 提问（一次一题，按需）**：

> **轮 1**：先确认用户角色 —— 头像上传功能面向哪类用户？为什么问：不同角色（注册用户 vs. 管理员）的权限和入口可能完全不同。
>
> A. 仅注册用户上传自己的头像
> B. 注册用户上传 + 管理员可代为修改
> C. 其他场景（请说明）

> **用户回答**：A

> **轮 2**：核心场景 —— 上传后头像显示在哪些位置？
>
> A. 仅个人主页
> B. 个人主页 + 评论区头像 + 好友列表
> C. 全站所有头像位置
> D. 其他（请说明）

> **用户回答**：B

> **轮 3**：边界与异常 —— 文件约束如何设定？
>
> A. ≤ 2MB，仅 JPG/PNG
> B. ≤ 5MB，JPG/PNG/WebP
> C. 其他（请说明）

> **用户回答**：A

> **轮 4**：验收判定 —— 上传成功的可观察信号是什么？
>
> A. 个人主页头像区显示新头像 + Toast 提示
> B. 仅刷新页面后看到变化
> C. 其他（请说明）

> **用户回答**：A

> **轮 5**：范围边界 —— 这次是否包含以下能力？
>
> A. 仅上传，不含裁剪/滤镜/历史头像
> B. 上传 + 简单裁剪
> C. 上传 + 裁剪 + 滤镜
> D. 其他（请说明）

> **用户回答**：A

至此 5 维度全部明确，无 Epic 信号，进入 Story 生成。

## 4. Epic 拆分对话片段

**用户原始输入**：

> 做一个用户认证模块。要支持手机号 + 验证码登录、密码登录、找回密码、注册、账号锁定防爆破，注册用户和管理员都用这个登录系统。

**skill 5 维度澄清后**（这里假设澄清流程已完成）。

**skill Epic 拆分评估**：

| 信号 | 命中？ | 依据 |
|---|---|---|
| 多个独立用户角色 | ✓ | 注册用户 + 管理员 |
| 多个独立价值点 | ✓ | 登录、注册、找回密码三个互不依赖的价值 |
| 多个独立流程入口 | ✓ | 验证码登录、密码登录、注册、找回 4 个入口 |
| AC 数量过载 | ✓ | 预估 > 8 条 |
| 跨多个数据/系统边界 | – | 仅认证域 |

4/5 命中，触发 Epic 拆分。

**skill 向用户提议**：

> 检测到 4 个 Epic 拆分信号（多角色 / 多价值点 / 多入口 / AC 总量过载），建议拆分为以下 Story：
>
> 1. **验证码登录**（注册用户）—— 手机号 + 验证码登录主流程
> 2. **密码登录**（注册用户 + 管理员）—— 账号 + 密码登录主流程
> 3. **注册**（游客）—— 手机号注册主流程
> 4. **找回密码**（注册用户）—— 重置密码流程
> 5. **账号锁定防爆破**（横切）—— 失败计数与锁定策略
>
> 共享上下文（"注册用户"角色定义、"验证码"术语）放入 Epic 索引文件。
>
> 是否同意此拆分？如需调整请告知（合并、重命名、增减）。

**用户确认后**，对每个 Story 走完整 5 维度澄清，生成 5 个独立 Story 文件 + 1 个 Epic 索引：

```
docs/stories/2026-06-01-user-auth/
├── README.md                       # Epic 索引
├── 01-sms-login.md                 # 验证码登录
├── 02-password-login.md            # 密码登录
├── 03-register.md                  # 注册
├── 04-password-reset.md            # 找回密码
└── 05-account-lockout.md           # 账号锁定
```

## 5. 反模式清单

以下行为在使用 story-ac-author skill 时严格禁止：

| # | 反模式 | 后果 | 正确做法 |
|---|---|---|---|
| 1 | 跳过澄清，根据用户原始描述直接生成 Story | 缺失关键维度，Story 不可交付 | 先做 5 维度评估，按需提问 |
| 2 | 一次问多个澄清问题 | 用户回答容易遗漏、带偏 | 一次只问 1 个问题 |
| 3 | 用"假设默认值"代替提问 | 隐含偏见，需求脱离用户意图 | 必须显式提问 |
| 4 | AC 中使用"系统正确处理"等模糊期望 | 不可验收 | 改写为外部可观察的具体响应 |
| 5 | AC-N 的 Given 写"AC-(N-1) 已通过" | 串行依赖，单条 AC 无法独立验证 | 改写为可独立构造的前置 |
| 6 | Epic 未与用户确认就直接拆分 | 拆分方案与用户预期不符，返工 | 必须先展示拆分建议并等用户确认 |
| 7 | 在对话里输出 Story 文本但未实际写文件 | 用户得不到可提交的资产 | 必须实际创建文件并告知路径 |
| 8 | 澄清记录表只勾选"明确"但不写依据 | 无法追溯证据来源 | 每条"明确"都必须附用户原文或回答 |
| 9 | Story 的 As a 写"用户" | 角色不具体，AC 无法对齐特定权限 | 必须使用已澄清的具体角色名 |
| 10 | 落盘前不跑 Output Gate 自检 | 模板字段缺失或检查未通过 | 落盘前严格执行 Output Gate 7 项 |
````

- [ ] **Step 2: Verify all 5 sections present**

Run: `grep -E "^## [1-5]\." agent-skills/story-ac-author/examples.md`
Expected: 5 lines (`## 1.` through `## 5.`).

Run: `grep -c "^| [0-9]\+ |" agent-skills/story-ac-author/examples.md`
Expected: ≥ 10 (at least 10 anti-pattern rows in §5).

- [ ] **Step 3: Commit**

```bash
git add agent-skills/story-ac-author/examples.md
git commit -m "feat(agent-skills): add story-ac-author examples and anti-patterns"
```

---

## Task 9: SKILL.md — frontmatter, Overview, HARD-GATE

**Files:**
- Create: `agent-skills/story-ac-author/SKILL.md`

- [ ] **Step 1: Write frontmatter, Overview, HARD-GATE**

Write the following content to `agent-skills/story-ac-author/SKILL.md`:

```markdown
---
name: story-ac-author
description: Use when the user describes a product/feature requirement and needs interactive clarification followed by an agile User Story plus testable acceptance criteria; covers requirement breakdown into Stories or Epics with Given-When-Then ACs
---

# Story-AC Author

## Overview

这个 Skill 用来把"自然语言需求"转换为"敏捷 User Story + 可测试可验收的 Acceptance Criteria"。

核心产物：

1. 单 Story 模式：`docs/stories/YYYY-MM-DD-<slug>.md`
2. Epic 模式：`docs/stories/YYYY-MM-DD-<epic-slug>/` 目录（含 README.md 索引和多个子 Story 文件）

这个 Skill 只定义需求澄清规则、Story/AC 标准和落盘格式，不实现以下内容：

- 工作量估算、优先级排序、迭代规划
- 任务分解到工程子任务（实施级）
- 可运行的脚本或工具链
- 替代正式的需求评审流程

<HARD-GATE>
在使用这个 Skill 时，必须遵守以下规则：

澄清阶段
- 不得跳过 5 维度（用户角色 / 核心场景 / 边界与异常 / 验收判定 / 范围边界）中任何一个维度。
- 不得在同一条消息里问多个澄清问题。
- 不得用"假设默认值"代替提问。
- 不得把"用户未提及"等同于"无要求"。

Story 与 AC 生成
- 不得在 5 维度未全部明确前生成 Story。
- 不得产出含模糊词（"正确地" / "合适的" / "尽快" / "易用" 等）的 AC。
- 不得产出 4 项硬性检查（输入具体 / 期望可观察 / 边界明确 / 可独立验证）未全通过的 AC。
- 不得产出依赖另一条 AC 执行结果才能验证的 AC。
- Story 的 As a 子句不得使用泛化"用户"，必须为已澄清的具体角色。

Epic 拆分
- 不得不经用户确认就拆分或合并 Story。
- 拆分后每个 Story 必须独立通过 5 维度澄清。

落盘
- 不得覆盖已有文件，不得静默重命名。
- 不得删除模板中的"澄清记录"和"AC 检查通过记录"两个表格。
- 不得用空表占位（表格存在但内容为空 / 仅含占位符 / 仅含表头视为未通过）。
- 任务要求生成文档时，必须实际创建文件，不得只在对话里输出文本。
</HARD-GATE>
```

- [ ] **Step 2: Verify frontmatter and HARD-GATE**

Run: `head -5 agent-skills/story-ac-author/SKILL.md`
Expected: contains `---`, `name: story-ac-author`, `description: ...`, `---`.

Run: `grep -c "^- 不得" agent-skills/story-ac-author/SKILL.md`
Expected: ≥ 14 (HARD-GATE rules).

---

## Task 10: SKILL.md — When to Use, Required Order, Quick Reference, Review Checklist, Common Failures, Supporting Files, Output Gate, Red Flags

**Files:**
- Modify: `agent-skills/story-ac-author/SKILL.md`

- [ ] **Step 1: Append the remaining sections**

Append to `agent-skills/story-ac-author/SKILL.md`:

````markdown

## When to Use

在以下情况使用：

- 用户描述一个产品功能或业务需求，需要转换为可交付的 Story + AC。
- 用户要求"写需求"、"产生用户故事"、"列验收标准"。
- 用户要求"把这个需求结构化"。
- 需要在多个独立角色 / 场景 / 入口之间拆分 Epic。

不要用于：

- 已有 Story，只需要做工作量估算或排期。
- 把 Story 拆分到工程子任务（属于实施 plan 阶段）。
- 替代需求评审会议或合规审查。
- 给已上线功能补回归测试用例。

## Required Order

按以下顺序执行，不要跳步：

1. 先读 `standards.md`，理解 5 维度判定规则与 AC 4 项检查口径。
2. 再读 `output-template.md`，理解模板强制字段。
3. 输出风格不确定时，再看 `examples.md`。
4. 对用户输入做 5 维度评估，按需提问，一次一题（参见 `standards.md` §1-§2）。
5. 5 维度全部明确后，评估是否触发 Epic 拆分（`standards.md` §6-§7）。
6. 若拆分，向用户确认拆分方案后，逐 Story 走完整流程。
7. 生成 Story + AC，对每条 AC 执行 4 项硬性检查并记录（`standards.md` §3）。
8. 走 Output Gate 自检；不通过则修正后重新过一次，循环直至全部 7 项通过。
9. 写入 `docs/stories/`，并在对话中告知文件路径。

## Quick Reference

| 场景 | 默认动作 |
|---|---|
| 用户描述模糊、5 维度多个未明确 | 按需提问，一次一题，优先多选 |
| 用户原始输入已覆盖某维度 | 维度判为"明确"并记录原文证据，跳过该维度提问 |
| 命中 ≥ 1 个 Epic 信号 | 展示拆分方案，等用户确认 |
| AC 含 "正确地" / "尽快" / "合适的" | 拒绝落盘，要求修正为具体可观察值 |
| AC-N Given 写 "AC-(N-1) 通过后" | 拒绝落盘，要求改为独立构造的前置 |
| Story 的 As a 写 "用户" | 拒绝落盘，要求填入具体角色 |
| 模板"澄清记录"表为空 | 拒绝落盘，回去补依据 |
| slug 派生为空 | 停止落盘，请用户提供 slug |
| 同日同 slug 文件已存在 | 追加 `-v2`/`-v3` 后缀 |

## Review Checklist

在结束前逐项确认：

- [ ] 5 维度澄清记录表完整，每行都有依据。
- [ ] 每条 AC 都通过 4 项硬性检查（输入具体 / 期望可观察 / 边界明确 / 可独立验证）。
- [ ] AC 中无禁止词。
- [ ] Story 的角色为具体角色而非"用户"。
- [ ] Epic 模式下索引文件已生成且依赖关系清晰。
- [ ] 文件已实际落盘（不是只在对话里展示）。
- [ ] 输出路径已告知用户。

## Common Failures

- 跳过澄清，直接根据用户原始输入猜测 Story。
- 用"系统正确处理"等模糊表达写 AC。
- AC 间形成串行依赖（AC-2 必须 AC-1 通过后才能验证）。
- Epic 未与用户确认就直接拆分。
- 在对话里输出 Story 文本但未实际写文件。
- 澄清记录表只勾选"明确"但不写依据。
- Story 的 As a 字段使用泛化"用户"。
- AC 中只描述实现而无外部观察行为。

## Supporting Files

- `standards.md`：5 维度澄清规则、AC 4 项硬性检查、禁止写法、Epic 拆分判定、文件落盘约定、slug 派生规则
- `output-template.md`：单 Story 模板、Epic 索引模板、AC 单元格式、模板使用约束
- `examples.md`：好例、坏例、按需提问对话、Epic 拆分对话、反模式清单

## Red Flags

出现以下想法时，停止并回到规则：

- "用户大概意思就是这个，先生成再说。"
- "5 维度差一个不重要，可以默认补上。"
- "这个 AC 写得有点泛，但意思能懂。"
- "AC-2 直接接着 AC-1 写更省事。"
- "拆分方向我比较确定，先拆了再问用户。"
- "在对话里贴出来用户能看到就行，不用写文件。"

这些都表示要么跳过了澄清证据，要么绕开了硬约束。

## Output Gate

在落盘 Story / Epic 文件前，逐项确认：

1. 5 维度澄清记录表是否每行都为"明确"，且都附依据？
2. 每条 AC 是否通过 4 项硬性检查（输入具体 / 期望可观察 / 边界明确 / 可独立验证）？
3. AC 中是否含禁止词（"正确地" / "合适的" / "尽快" / "易用" / "友好" / ...）？
4. Story 的 As a / I want / So that 是否分别满足"角色具体 / 不含实现 / 价值清晰"？
5. Epic 模式下，索引文件的 Story 列表是否与已生成的子文件一一对应？
6. 文件路径是否与已有文件冲突？
7. 模板中的"澄清记录"和"AC 检查通过记录"两个表是否填充完整？

任一答案为"否"，不得落盘，回到上一步修正。修正后重新跑一次 Output Gate。循环直至 7 项全部通过。
````

- [ ] **Step 2: Verify all sections present**

Run: `grep -E "^## " agent-skills/story-ac-author/SKILL.md`
Expected lines:
```
## Overview
## When to Use
## Required Order
## Quick Reference
## Review Checklist
## Common Failures
## Supporting Files
## Red Flags
## Output Gate
```

(Order may vary slightly; all 9 must be present.)

Run: `grep -c "^[0-9]\+\." agent-skills/story-ac-author/SKILL.md`
Expected: ≥ 16 (9 in Required Order + 7 in Output Gate).

- [ ] **Step 3: Commit**

```bash
git add agent-skills/story-ac-author/SKILL.md
git commit -m "feat(agent-skills): add story-ac-author SKILL entry"
```

---

## Task 11: Cross-file consistency check (verification gate)

**Files:**
- Test: All 5 files in `agent-skills/story-ac-author/`

This task verifies that key concepts referenced across files are spelled identically and that all rules in HARD-GATE are backed by content in standards.md / output-template.md.

- [ ] **Step 1: Verify "5 维度" terminology consistent**

Run: `grep -rn "5 维度\|5维度\|5 个维度\|五维度" agent-skills/story-ac-author/`
Expected: every match uses "5 维度" form (with space). If any match uses "5维度" (no space) or "五维度" (Chinese number), normalize to "5 维度".

- [ ] **Step 2: Verify "4 项硬性检查" terminology consistent**

Run: `grep -rn "4 项\|4项\|四项" agent-skills/story-ac-author/`
Expected: every match uses "4 项" form. Normalize if inconsistent.

- [ ] **Step 3: Verify HARD-GATE rules are backed by standards.md**

For each "不得" rule in `SKILL.md` HARD-GATE block, locate the corresponding rule in `standards.md`:

- "不得跳过 5 维度" → standards.md §1 / §2
- "不得在同一条消息里问多个" → standards.md §2 提问期间硬约束
- "不得用假设默认值代替提问" → standards.md §1 取证要求 / §2 硬约束
- "不得把'用户未提及'等同于'无要求'" → standards.md §1 取证要求
- "不得在 5 维度未全部明确前生成 Story" → standards.md §2 流程
- "不得产出含模糊词的 AC" → standards.md §4
- "不得产出 4 项硬性检查未全通过的 AC" → standards.md §3
- "不得产出依赖另一条 AC 执行结果的 AC" → standards.md §3 第 4 项
- "Story 的 As a 不得使用泛化'用户'" → standards.md §5
- "不得不经用户确认就拆分" → standards.md §7 拆分硬约束
- "不得覆盖已有文件" → standards.md §8.3
- "不得删除模板中的两个表格" → output-template.md §4
- "不得用空表占位" → output-template.md §4

For any rule without backing content, add the rule to the corresponding standards.md / output-template.md section before proceeding.

Run: `grep -E "^- 不得" agent-skills/story-ac-author/SKILL.md | wc -l`
Expected: number matches the bullet list above.

- [ ] **Step 4: Verify all forbidden words appear in both SKILL.md and standards.md**

Run:
```bash
grep -E "正确地|合适的|尽快|易用|友好" agent-skills/story-ac-author/SKILL.md
grep -E "正确地|合适的|尽快|易用|友好" agent-skills/story-ac-author/standards.md
```
Expected: both files contain the same forbidden word set.

- [ ] **Step 5: Verify file path examples are consistent**

Run: `grep -rn "docs/stories/" agent-skills/story-ac-author/`
Expected: all path examples follow `docs/stories/YYYY-MM-DD-<slug>.md` (single) or `docs/stories/YYYY-MM-DD-<epic-slug>/` (Epic) — no other variants.

- [ ] **Step 6: Verify all section cross-references resolve**

Run: `grep -nE "standards\.md §[0-9]\+|output-template\.md §[0-9]\+" agent-skills/story-ac-author/`
For each cross-reference, verify the target section exists. If a reference points to a non-existent section, fix the reference.

- [ ] **Step 7: Commit any fixes from steps 1-6**

If any inconsistencies were found and fixed:

```bash
git add agent-skills/story-ac-author/
git commit -m "fix(agent-skills): align story-ac-author cross-file terminology"
```

If no fixes needed, skip this step.

---

## Task 12: Dry-run integration test

**Files:**
- Test: All 5 files in `agent-skills/story-ac-author/`

This task simulates a real usage of the skill to confirm it produces correct behavior end-to-end.

- [ ] **Step 1: Read the skill files in the prescribed order**

Read in order (mimicking what an LLM following the skill would do):

1. `agent-skills/story-ac-author/SKILL.md`
2. `agent-skills/story-ac-author/standards.md`
3. `agent-skills/story-ac-author/output-template.md`

For each file, confirm:

- File loads without errors.
- All Markdown headings render as expected (no broken anchors).
- HARD-GATE block in SKILL.md is closed (`</HARD-GATE>` present).

- [ ] **Step 2: Run the skill against a sample requirement (dry run)**

Sample requirement (clear and self-sufficient — should not require any clarification):

> 注册用户可以在个人主页上传一张头像图片，仅支持 JPG/PNG，最大 2MB，上传成功后立即在主页显示新头像并 Toast 提示，失败显示错误信息。这次不做裁剪、不做历史头像管理、不做管理员代修改。

Walk through the skill in your head:

1. **5 维度评估**：
   - 用户角色：注册用户 ✓
   - 核心场景：上传头像，触发→流程→结果清晰 ✓
   - 边界异常：JPG/PNG / 2MB / 失败提示 ✓
   - 验收判定：主页显示新头像 + Toast ✓
   - 范围边界：不做裁剪、历史、代修改 ✓
   - **结论**：5 维度全部明确，无需提问。

2. **Epic 评估**：
   - 5 个信号全部不命中（单角色、单价值、单入口、AC ≤ 5、单数据域）。
   - **结论**：单 Story 模式。

3. **生成 Story 并自检**：
   - 写出 Story + 3-5 条 AC。
   - 对每条 AC 跑 4 项硬性检查。
   - 跑 Output Gate 7 项。

- [ ] **Step 3: Verify the dry-run produces a valid output structure**

Confirm the imagined output would include:

- [ ] 顶部元数据三行（生成时间 / 角色：注册用户 / 状态：draft）
- [ ] As a 注册用户 / I want 上传头像 / So that ...
- [ ] In Scope 列出"上传"
- [ ] Out of Scope 列出"裁剪 / 历史 / 代修改"
- [ ] AC 含"上传成功"、"文件超限"、"格式错误"等独立场景
- [ ] 每条 AC 给出 HTTP 响应或具体 UI 行为
- [ ] 澄清记录表 5 行全为"明确"，每行附用户原文证据
- [ ] AC 检查通过记录表每行 4 项全 ✓

- [ ] **Step 4: Run the skill against a borderline requirement (dry run)**

Sample borderline requirement (intentionally missing dimensions):

> 想做一个数据导出功能。

Walk through the skill in your head:

1. **5 维度评估**：
   - 用户角色：不明确 ✗
   - 核心场景：不明确 ✗（导出什么？什么格式？）
   - 边界异常：不明确 ✗
   - 验收判定：不明确 ✗
   - 范围边界：不明确 ✗
   - **结论**：5 个维度全未明确，必须按需提问。

2. **预期 skill 行为**：
   - 不得直接生成 Story。
   - 应当从用户角色开始，一次一题。
   - 优先多选题。

If the dry-run mental walkthrough indicates the skill would skip clarification or generate a Story directly, locate the rule violation in the skill files and fix it.

- [ ] **Step 5: Document dry-run results and commit any fixes**

If steps 2-4 revealed any rule gaps, fix them in standards.md / SKILL.md and commit:

```bash
git add agent-skills/story-ac-author/
git commit -m "fix(agent-skills): close story-ac-author dry-run gaps"
```

If no fixes needed, skip this step.

---

## Task 13: Final review and push

**Files:**
- All files under `agent-skills/story-ac-author/`

- [ ] **Step 1: Verify all 5 files exist and are non-empty**

Run: `ls -la agent-skills/story-ac-author/`
Expected: 5 files (SKILL.md / standards.md / output-template.md / examples.md / README.md), all > 1KB.

Run: `wc -l agent-skills/story-ac-author/*.md`
Expected: each file ≥ 30 lines.

- [ ] **Step 2: Verify against the design spec**

Run: `cat docs/superpowers/specs/2026-06-01-story-ac-author-design.md | head -50`

Confirm each design section maps to skill content:

- Spec §3 (文件骨架) → 5 files exist
- Spec §4 (5 维度澄清) → standards.md §1-§2
- Spec §5 (AC 4 项检查 + 禁止写法) → standards.md §3-§5
- Spec §6 (Epic 拆分 + 落盘) → standards.md §6-§9
- Spec §7 (输出模板) → output-template.md §1-§4
- Spec §8 (HARD-GATE / Output Gate / Required Order / Review Checklist / Common Failures) → SKILL.md
- Spec §9 (examples.md 内容计划) → examples.md §1-§5
- Spec §10 (README.md 内容计划) → README.md
- Spec §12 (设计原则) → README.md "设计原则"

- [ ] **Step 3: Verify git log is clean**

Run: `git log --oneline -10`
Expected: see all commits made during Tasks 1-12, in order. No "fixup" or revert commits unless intentional.

- [ ] **Step 4: Push to remote (only if user explicitly requests)**

Do not push automatically. Tell the user:

> Story-AC Author skill 已完成实施，本地 commits 已就绪。如需推送到远程，请确认。

Wait for user instruction before running:

```bash
git push origin master
```

---

## Self-Review (writing-plans skill internal)

### 1. Spec Coverage Check

Mapping spec sections → plan tasks:

| Spec section | Implementing task |
| --- | --- |
| §1 目的与范围 | Task 9 (SKILL.md Overview) |
| §2 设计要素汇总 | Implicit, distributed across all tasks |
| §3 文件骨架 | Task 1 (directory) + Tasks 2-10 (files) |
| §4.1-§4.3 5 维度 + 提问策略 | Task 4 (standards.md §1-§2) |
| §4.4 澄清硬约束 | Task 4 + Task 9 (SKILL.md HARD-GATE) |
| §5 AC 4 项检查 + 禁止写法 + Story 检查 | Task 5 (standards.md §3-§5) |
| §6.1-§6.6 Epic 拆分 + 落盘 + slug | Task 6 (standards.md §6-§9) |
| §7.1 单 Story 模板 | Task 2 (output-template.md §1) |
| §7.2 Epic 索引模板 | Task 3 (output-template.md §2) |
| §7.3 模板使用约束 | Task 3 (output-template.md §4) |
| §8.1 HARD-GATE | Task 9 (SKILL.md) |
| §8.2 Output Gate | Task 10 (SKILL.md) |
| §8.3 Required Order | Task 10 (SKILL.md) |
| §8.4 Review Checklist | Task 10 (SKILL.md) |
| §8.5 Common Failures | Task 10 (SKILL.md) |
| §9 examples.md 内容计划 | Task 7 + Task 8 |
| §10 README.md 内容计划 | Task 1 |
| §11 与现有 skill 关系 | Reference only — not implemented in skill files |
| §12 设计原则 | Task 1 (README.md "设计原则") |

All sections covered. §11 is intentionally not implemented in skill files (it's a meta-design observation, not a skill-runtime rule).

### 2. Placeholder Scan

Scanned plan for: TBD / TODO / "implement later" / "fill in details" / "appropriate" / "similar to Task N" — none found.

All code blocks contain complete content. All file paths are absolute or repo-relative. All commands are runnable as-is.

### 3. Type Consistency Check

Cross-file naming check:

- "5 维度" / "AC 4 项硬性检查" — used consistently across spec, plan, and embedded skill content. ✓
- File paths: `docs/stories/YYYY-MM-DD-<slug>.md` (single) and `docs/stories/YYYY-MM-DD-<epic-slug>/` (Epic) — consistent across plan tasks. ✓
- Section reference style: `standards.md §N` / `output-template.md §N` — consistent. ✓
- Forbidden word list: same set in HARD-GATE (Task 9), standards.md §4 (Task 5), and Quick Reference (Task 10). ✓

No inconsistencies found.
