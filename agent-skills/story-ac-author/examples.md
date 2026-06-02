# Examples

本文件提供 story-ac-author skill 的好例与坏例。所有例子均严格遵循 `standards.md` 与 `output-template.md`。

目录：

1. 好例 1：单 Story 模式（含完整澄清记录与 AC 检查表）
2. 好例 2：Epic 拆分模式（README + 2 个子 Story）
3. 坏例：违规 AC 与修正
4. 对话片段：5 维度按需提问的真实问答
5. 反模式：常见越界与合理化

---

## 1. 好例 1：单 Story 模式

**场景**：用户提出"邮箱验证码注册"需求。经过 5 维度按需提问澄清后（详见 §4 对话片段示例），生成单 Story。

**落盘路径**：`docs/stories/2026-06-02-email-otp-register.md`

```markdown
# Story: 注册访客通过邮箱验证码完成账号创建

> 生成时间: 2026-06-02
> 角色: 注册访客
> 状态: draft

## Story

As a 注册访客
I want 通过邮箱接收一次性验证码完成账号创建
So that 我能用经过邮箱所有权校验的账号登录平台并使用付费功能

## 上下文 (Context)

平台目前仅支持手机号注册，海外用户无法使用。本 Story 增加邮箱验证码注册路径，与手机号注册并列。注册成功后用户进入"已激活"状态，下一次登录通过密码登录（密码设置由独立 Story 承担）。

## 范围 (In Scope)

- 输入邮箱、获取验证码、提交验证码、创建账号 4 步主流程
- 验证码有效期、错误提示、邮箱已占用 3 类异常分支
- 验证码冷却（防刷）

## 不在范围 (Out of Scope)

- 设置/修改密码（由 Story `password-setup` 承担）
- 邮箱变更、注销账号
- 第三方登录、邀请制注册
- 多端 SDK（本 Story 仅 Web 端）

## Acceptance Criteria

### AC-1: 合法邮箱获取验证码并 5 分钟内完成注册
- **Given** 注册访客在 Web 注册页输入符合 RFC 5322 的邮箱 `alice@example.com`，且该邮箱未在 `users` 表中
- **When** 访客点击"获取验证码"按钮
- **Then** 后端在 2 秒内向 `alice@example.com` 发送一封含 6 位数字验证码的邮件，页面 toast 显示"验证码已发送，5 分钟内有效"
- **And** Redis 中写入 key `otp:register:alice@example.com` value 为该 6 位验证码，TTL = 300 秒

**边界**: 验证码 = 6 位 `[0-9]`；TTL = 300 秒
**验证方式建议**: 接口测试 + Redis 断言

### AC-2: 验证码 5 分钟内提交，账号创建成功
- **Given** Redis 中存在 key `otp:register:alice@example.com` value `123456`，剩余 TTL > 0
- **When** 访客在 5 分钟内提交邮箱 `alice@example.com` 与验证码 `123456`
- **Then** 后端返回 HTTP 200，body `{"userId": "<新生成 uuid>", "status": "active"}`
- **And** `users` 表新增一行 `email=alice@example.com, status=active, created_at=<now>`，Redis key `otp:register:alice@example.com` 被删除
- **And** 浏览器跳转到 `/login`，页面顶部 toast 显示"注册成功，请登录"

**边界**: 提交时刻 ≤ 验证码发送时刻 + 300 秒
**验证方式建议**: 接口测试 + DB 断言 + E2E

### AC-3: 验证码已过期
- **Given** Redis 中 key `otp:register:alice@example.com` 已 TTL 过期（不存在）
- **When** 访客提交邮箱 `alice@example.com` 与验证码 `123456`
- **Then** 后端返回 HTTP 410 Gone，body `{"error": "OTP_EXPIRED", "message": "验证码已过期，请重新获取"}`
- **And** `users` 表无新增行

**边界**: 第 301 秒起即视为过期
**验证方式建议**: 接口测试

### AC-4: 验证码错误
- **Given** Redis 中 key `otp:register:alice@example.com` value `123456`，剩余 TTL > 0
- **When** 访客提交邮箱 `alice@example.com` 与验证码 `999999`
- **Then** 后端返回 HTTP 400，body `{"error": "OTP_INVALID", "message": "验证码不正确"}`
- **And** `users` 表无新增行；Redis key 保留（不因单次错误立即作废）

**边界**: 同一 key 累计错误 ≥ 5 次后强制作废（独立 AC-7 覆盖此分支）
**验证方式建议**: 接口测试

### AC-5: 邮箱已注册
- **Given** `users` 表已存在 `email=alice@example.com, status=active`
- **When** 访客在注册页输入 `alice@example.com` 并点击"获取验证码"
- **Then** 后端不发送邮件，返回 HTTP 409，body `{"error": "EMAIL_EXISTS", "message": "该邮箱已注册，请直接登录"}`
- **And** Redis 无 key 写入；前端 toast 显示后端返回的 message 文案

**边界**: 仅当 `users.status` ∈ {`active`, `pending`} 时视为已注册；`status=deleted` 视为可重新注册
**验证方式建议**: 接口测试 + DB 断言

### AC-6: 同邮箱获取验证码冷却 60 秒
- **Given** Redis 中 key `otp:cooldown:alice@example.com` 存在（上次发送 < 60 秒）
- **When** 访客再次点击"获取验证码"
- **Then** 后端不发送邮件，返回 HTTP 429，body `{"error": "OTP_COOLDOWN", "retryAfterSeconds": <剩余秒数>}`
- **And** 前端按 `retryAfterSeconds` 倒计时禁用按钮

**边界**: 冷却期 = 60 秒；同邮箱在冷却期内任意次数请求均返回 429
**验证方式建议**: 接口测试 + 前端单测

### AC-7: 同一验证码错误尝试 ≥ 5 次后强制作废
- **Given** Redis 中 key `otp:register:alice@example.com` value `123456`，对应 `otp:fail:alice@example.com` 计数 = 4
- **When** 访客第 5 次提交错误验证码 `999999`
- **Then** 后端返回 HTTP 423 Locked，body `{"error": "OTP_LOCKED", "message": "验证码已作废，请重新获取"}`
- **And** Redis key `otp:register:alice@example.com` 与 `otp:fail:alice@example.com` 均被删除

**边界**: 失败计数阈值 = 5；达到阈值后无论 TTL 是否未到都作废
**验证方式建议**: 接口测试

## 依赖与假设

- 依赖: 邮件服务 `mail-service` 提供 `POST /send` 接口；Redis 单实例可用
- 假设: 用户已澄清密码设置由独立 Story `password-setup` 承担（轮 4 提问）
- 假设: 用户已澄清"已注册"判定包含 `pending` 状态（轮 5 提问）

## 澄清记录

| 维度 | 状态 | 依据 |
|---|---|---|
| 用户角色 | 明确 | 用户原文："注册访客（未注册的人）"（轮 1 提问回答） |
| 核心场景 | 明确 (轮 2 提问) | 用户回答："输入邮箱→收到 6 位数字验证码→输入验证码→创建账号→跳转登录页" |
| 边界与异常 | 明确 (轮 3 提问) | 用户回答："验证码 5 分钟过期、错误提示、邮箱已占用、冷却 60 秒、错 5 次作废" |
| 验收判定 | 明确 (轮 3 提问) | 用户回答："HTTP 状态码 200/400/409/410/423/429 + body 中的 error code + DB 行变化" |
| 范围边界 | 明确 (轮 4-5 提问) | 用户回答："本次只做 Web；密码、邮箱变更、第三方登录都不做" |

## AC 检查通过记录

| AC | 输入具体 | 期望可观察 | 边界明确 | 可独立验证 |
|---|---|---|---|---|
| AC-1 | ✓ | ✓ | ✓ | ✓ |
| AC-2 | ✓ | ✓ | ✓ | ✓ |
| AC-3 | ✓ | ✓ | ✓ | ✓ |
| AC-4 | ✓ | ✓ | ✓ | ✓ |
| AC-5 | ✓ | ✓ | ✓ | ✓ |
| AC-6 | ✓ | ✓ | ✓ | ✓ |
| AC-7 | ✓ | ✓ | ✓ | ✓ |
```

**为什么是好例**：

- 5 维度都有用户原文证据，无"业内常识"补缺。
- AC 全部用具体值（`alice@example.com` / `123456` / HTTP 状态码 / Redis key 名）。
- 边界清晰（300 秒 / 60 秒冷却 / 5 次失败阈值）。
- 每条 AC 自带前置，互不依赖（如 AC-7 没写"在 AC-2 之后"，而是直接给出 Redis 状态）。
- 文档严格按 output-template.md，无 Story Points / DoD / NFR 越界。

---

## 2. 好例 2：Epic 拆分模式

**场景**：用户提需求"电商订单管理系统：买家可以下单/取消/退款，卖家能发货/查看订单/批量处理订单，管理员能审批退款/封禁账号/导出报表"。

**Epic 信号评估**：

| 信号 | 命中 | 依据 |
|---|---|---|
| 多角色 | ✓ | 买家 / 卖家 / 管理员 三个独立角色 |
| 多价值点 | ✓ | "完成购买" / "履约发货" / "运营管控" 三个互不依赖收益 |
| 多入口 | ✓ | 买家 App / 卖家后台 / 管理后台 三个独立入口 |
| AC 过载 | ✓ | 预估 ≥ 12 条 AC |
| 跨子系统 | ✓ | 涉及 `order-service` / `payment-service` / `audit-service` 三个域 |

5/5 命中 → 必须拆 Epic。

**用户确认拆分**（对话见 §4）后落盘以下结构：

```
docs/stories/2026-06-02-order-management/
├── README.md
├── 01-buyer-place-and-cancel-order.md
├── 02-seller-ship-and-batch-process.md
└── 03-admin-refund-approval-and-ban.md
```

### 2.1 Epic 索引：`README.md`

```markdown
# Epic: 电商订单管理系统

> 生成时间: 2026-06-02
> 状态: draft

## 背景

平台当前订单流转分散在多个旧系统中，买家无法自助取消订单、卖家发货效率低、管理员缺乏统一的退款审批与运营报表入口。本 Epic 一次性梳理"买家下单/取消/退款"、"卖家发货/批量处理"、"管理员退款审批/账号封禁/报表导出"三条主链路，形成统一的订单管理域，作为后续支付、物流、运营子系统的基础。

## 共享角色定义

| 角色 | 定义 |
|---|---|
| 买家 | 已注册并完成实名认证的 C 端用户，可在 App 端下单与发起售后 |
| 卖家 | 已签约并通过资质审核的商家账号，使用卖家后台管理订单 |
| 管理员 | 平台运营/客服内部账号，使用管理后台进行审批、封禁、报表导出 |

## 术语表

| 术语 | 定义 |
|---|---|
| 订单状态 | `pending_pay` / `pending_ship` / `shipped` / `received` / `cancelled` / `refunding` / `refunded` |
| 退款单 | `refund` 实体，与订单 1:1 或 1:N，状态 ∈ {`pending`, `approved`, `rejected`} |
| 操作日志 | 写入 `audit-service` 的 append-only 记录，包含 actor / action / target / reason / timestamp |

## Story 列表

| 序号 | Story | 依赖 (depends_on) | 文件 |
|---|---|---|---|
| 01 | 买家下单与取消未发货订单 | 无 | [01-buyer-place-and-cancel-order.md](./01-buyer-place-and-cancel-order.md) |
| 02 | 卖家发货与批量发货 | 01 | [02-seller-ship-and-batch-process.md](./02-seller-ship-and-batch-process.md) |
| 03 | 管理员退款审批与账号封禁 | 01, 02 | [03-admin-refund-approval-and-ban.md](./03-admin-refund-approval-and-ban.md) |

## 拆分依据

- **信号 1（多角色）**：买家/卖家/管理员三个角色的核心场景互不依赖。
- **信号 2（多价值点）**：完成购买 / 履约发货 / 运营管控是三类独立收益。
- **信号 3（多入口）**：买家 App / 卖家后台 / 管理后台三个独立产品入口。
- **信号 4（AC 过载）**：合并写预估 ≥ 12 条 AC，远超单 Story 推荐 8 条上限。
- **信号 5（跨子系统）**：涉及 `order-service` / `payment-service` / `audit-service` 三个独立域。
```

### 2.2 子 Story 1：`01-buyer-place-and-cancel-order.md`

```markdown
# Story: 买家下单并在未发货前自助取消

> 生成时间: 2026-06-02
> 角色: 买家
> 状态: draft

## Story

As a 买家
I want 在 App 端完成下单并在订单未发货前自助取消
So that 我能掌控自己的购买决定，减少被动等待客服处理的时间

## 上下文 (Context)

本 Story 是订单管理 Epic 的入口流程。买家走完下单 → 支付 → 在未发货前取消的完整闭环；订单状态机由本 Story 首次落地。后续卖家发货（Story 02）与管理员退款（Story 03）依赖本 Story 产出的订单与状态机。

## 范围 (In Scope)

- 买家下单（含库存扣减、订单生成）
- 买家在订单未发货时自助取消（含库存回滚、原路退款）
- 取消理由记录到操作日志

## 不在范围 (Out of Scope)

- 已发货订单的退款（由 Story 03 承担）
- 优惠券、积分抵扣（独立 Epic）
- 售后/退货（独立 Story）

## Acceptance Criteria

### AC-1: 库存充足时下单成功
- **Given** 买家 `user_id=10086` 已登录，购物车含 SKU `SKU-1001`（库存 5，单价 99.00 CNY），已选收货地址 `addr_id=200`
- **When** 买家点击"提交订单"并完成支付（支付网关返回 `paid`）
- **Then** `orders` 表新增一行 `order_id=ORD-20260602-000001, buyer=10086, sku=SKU-1001, qty=1, total=99.00, status=pending_ship`
- **And** `inventory.SKU-1001.available` 由 5 变为 4
- **And** 接口返回 HTTP 200，body 含 `{"orderId": "ORD-20260602-000001", "status": "pending_ship"}`

**边界**: 下单接口 P95 ≤ 800ms
**验证方式建议**: 接口测试 + DB 断言

### AC-2: 库存不足时下单失败
- **Given** 买家 `user_id=10086`，购物车含 SKU `SKU-1001`（库存 0）
- **When** 买家点击"提交订单"
- **Then** 接口返回 HTTP 409，body `{"error": "OUT_OF_STOCK", "sku": "SKU-1001"}`
- **And** `orders` 表无新增；不调用支付网关

**边界**: 库存检查发生在调用支付网关之前
**验证方式建议**: 接口测试

### AC-3: 未发货订单可被买家取消并原路退款
- **Given** `orders` 中存在 `order_id=ORD-20260602-000001, buyer=10086, status=pending_ship, total=99.00`
- **When** 买家在订单详情页选择取消理由"不想要了"并点击确认
- **Then** `orders.status` 变为 `cancelled`，`cancel_reason='不想要了'`，`cancelled_at=<now>`
- **And** `inventory.SKU-1001.available` +1
- **And** 调用 `payment-service.refund(orderId)`，返回 `refund_id`，资金 99.00 CNY 在 24h 内原路退回（异步）
- **And** `audit-service` 写入一条 `actor=10086, action=cancel_order, target=ORD-20260602-000001, reason=不想要了`

**边界**: 取消按钮仅在 `status=pending_ship` 时可见；24h 是退款 SLA 而非接口同步等待
**验证方式建议**: 接口测试 + DB 断言 + audit-service 断言

### AC-4: 已发货订单不能被买家取消
- **Given** `orders` 中存在 `order_id=ORD-20260602-000002, status=shipped`
- **When** 买家请求取消该订单
- **Then** 接口返回 HTTP 422，body `{"error": "ORDER_NOT_CANCELLABLE", "currentStatus": "shipped"}`
- **And** `orders.status` 不变；不触发退款

**边界**: 状态白名单 = {`pending_pay`, `pending_ship`}
**验证方式建议**: 接口测试

## 依赖与假设

- 依赖: `payment-service.refund` 接口；`inventory-service` 扣减/回滚接口；`audit-service` 写入接口
- 假设: 订单号格式 `ORD-YYYYMMDD-NNNNNN` 已与用户确认（轮 3 提问）
- 假设: 退款 24h SLA 是业务承诺而非接口同步等待（轮 4 提问）

## 澄清记录

| 维度 | 状态 | 依据 |
|---|---|---|
| 用户角色 | 明确 | 用户原文："C 端买家，已实名认证"（Epic 共享角色） |
| 核心场景 | 明确 (轮 2 提问) | 用户回答："登录→下单→支付→未发货前可取消" |
| 边界与异常 | 明确 (轮 3 提问) | 用户回答："库存不足、已发货不能取消" |
| 验收判定 | 明确 (轮 3 提问) | 用户回答："HTTP 状态码 + DB 状态机 + 库存数 + audit 记录" |
| 范围边界 | 明确 (轮 4 提问) | 用户回答："已发货退款放到 Story 03，本次只做未发货取消" |

## AC 检查通过记录

| AC | 输入具体 | 期望可观察 | 边界明确 | 可独立验证 |
|---|---|---|---|---|
| AC-1 | ✓ | ✓ | ✓ | ✓ |
| AC-2 | ✓ | ✓ | ✓ | ✓ |
| AC-3 | ✓ | ✓ | ✓ | ✓ |
| AC-4 | ✓ | ✓ | ✓ | ✓ |
```

### 2.3 子 Story 2：`02-seller-ship-and-batch-process.md`

```markdown
# Story: 卖家在卖家后台发货并批量处理订单

> 生成时间: 2026-06-02
> 角色: 卖家
> 状态: draft

## Story

As a 卖家
I want 在卖家后台对单笔订单填写物流并发货，或一次批量发货多笔订单
So that 我能在大促期间快速完成发货，减少遗漏与错发

## 上下文 (Context)

本 Story 紧接 Story 01：买家下单且支付完成后，订单进入 `pending_ship`，卖家在卖家后台看到待发货列表并发货。状态机推进由本 Story 承担。批量发货针对大促日均 1000+ 单的卖家诉求。

## 范围 (In Scope)

- 单笔订单发货（输入物流公司+运单号）
- 批量发货（上传 CSV 一次处理多笔）
- 物流单号格式校验

## 不在范围 (Out of Scope)

- 物流轨迹追踪（独立 Epic）
- 拆单合单（独立 Story）
- 退货收货（Story 03 涉及一部分）

## Acceptance Criteria

### AC-1: 单笔订单发货成功
- **Given** 卖家 `seller_id=2001` 在卖家后台看到 `order_id=ORD-20260602-000001, status=pending_ship`
- **When** 卖家选择物流公司"顺丰速运"（code=`SF`），运单号 `SF1234567890`，点击"确认发货"
- **Then** `orders` 表更新：`status=shipped, carrier=SF, tracking_no=SF1234567890, shipped_at=<now>`
- **And** 接口返回 HTTP 200，body `{"orderId": "ORD-20260602-000001", "status": "shipped"}`
- **And** 站内信中心写入买家通知 `template=order_shipped, params={orderId, carrier, trackingNo}`

**边界**: 运单号正则 `^[A-Z0-9]{8,32}$`
**验证方式建议**: 接口测试 + DB 断言

### AC-2: 运单号格式非法时拒绝发货
- **Given** 卖家 `seller_id=2001`，订单 `ORD-20260602-000003, status=pending_ship`
- **When** 卖家提交物流公司`SF`、运单号 `abc-123`（含小写与连字符）
- **Then** 接口返回 HTTP 400，body `{"error": "TRACKING_NO_INVALID", "pattern": "^[A-Z0-9]{8,32}$"}`
- **And** `orders.status` 不变

**边界**: 错误立即返回，不写库
**验证方式建议**: 接口测试

### AC-3: 批量发货 CSV 部分成功
- **Given** 卖家 `seller_id=2001` 上传 CSV（10 行，第 1-8 行格式合法且订单 `status=pending_ship`，第 9 行运单号格式非法，第 10 行订单 `status=cancelled`）
- **When** 卖家点击"批量发货"
- **Then** 接口返回 HTTP 207，body `{"successCount": 8, "failed": [{"row": 9, "error": "TRACKING_NO_INVALID"}, {"row": 10, "error": "ORDER_NOT_SHIPPABLE", "currentStatus": "cancelled"}]}`
- **And** 第 1-8 行对应订单 `status=shipped`，第 9-10 行对应订单状态不变

**边界**: 单次 CSV ≤ 500 行；超过 500 行返回 HTTP 413 不入队
**验证方式建议**: 接口测试 + DB 断言

### AC-4: 批量发货整体限时
- **Given** 卖家上传 100 行合法 CSV
- **When** 卖家点击"批量发货"
- **Then** 接口在 5 秒内返回结果（同步处理；> 500 行场景由 §AC-3 边界排除）

**边界**: 100 行 P95 ≤ 5s
**验证方式建议**: 性能测试

## 依赖与假设

- 依赖: `order-service` 状态机已由 Story 01 落地；`notification-service` 站内信接口
- 假设: 物流公司枚举来自配置中心 `carriers` key（轮 3 提问）
- 假设: CSV 列顺序固定为 `order_id, carrier_code, tracking_no`（轮 3 提问）

## 澄清记录

| 维度 | 状态 | 依据 |
|---|---|---|
| 用户角色 | 明确 | 用户原文："已签约卖家"（Epic 共享角色） |
| 核心场景 | 明确 (轮 2 提问) | 用户回答："单笔填物流发货 + 批量发货上传 CSV" |
| 边界与异常 | 明确 (轮 3 提问) | 用户回答："运单号格式校验、CSV 部分失败、单次 ≤ 500 行" |
| 验收判定 | 明确 (轮 3 提问) | 用户回答："HTTP 状态码 + body 失败详情 + DB 状态" |
| 范围边界 | 明确 (轮 4 提问) | 用户回答："不做轨迹追踪、不做拆单合单" |

## AC 检查通过记录

| AC | 输入具体 | 期望可观察 | 边界明确 | 可独立验证 |
|---|---|---|---|---|
| AC-1 | ✓ | ✓ | ✓ | ✓ |
| AC-2 | ✓ | ✓ | ✓ | ✓ |
| AC-3 | ✓ | ✓ | ✓ | ✓ |
| AC-4 | ✓ | ✓ | ✓ | ✓ |
```

> Story 03（管理员）结构同上，篇幅省略。仅展示前两个子 Story 已足够说明 Epic 拆分写法。

**为什么是好例**：

- README 列出共享角色与术语，避免在每个子 Story 重复定义。
- 每个子 Story 都跑了完整 5 维度澄清，公共维度（如角色定义）通过 README 复用，但其他维度独立判定。
- `depends_on` 显式声明子 Story 间依赖（Story 02 依赖 Story 01 的状态机）。
- 每个子 Story 的 AC 数量 ≤ 8，可独立评审。

---

## 3. 坏例：违规 AC 与修正

### 3.1 模糊词违规

**坏**：

```
### AC-1: 用户登录
- Given 用户已注册
- When 用户输入合适的账号密码并点击登录
- Then 系统正确处理请求，跳转到合适的页面
```

**问题**：
- "合适的账号密码" / "合适的页面" → 命中 standards §4 模糊词
- "正确处理请求" → 不可观察
- 缺具体值与边界

**修正**：

```
### AC-1: 注册用户用账号密码登录成功
- **Given** `users` 表存在 `email=alice@example.com, password_hash=<bcrypt(Abc12345)>, status=active`
- **When** 用户在 `/login` 提交 `email=alice@example.com, password=Abc12345`
- **Then** 后端返回 HTTP 200，body 含 `{"token": "<jwt>", "expiresIn": 3600}`
- **And** 前端跳转到 `/dashboard`，header 显示 `欢迎，alice@example.com`

**边界**: token 有效期 3600 秒
**验证方式建议**: 接口测试 + E2E
```

### 3.2 期望不可观察

**坏**：

```
### AC-2: 取消订单
- Given 订单存在
- When 用户点击取消
- Then 订单被取消，库存回滚，钱退回
```

**问题**：
- "订单存在" → 状态未指定（什么状态可取消？）
- "被取消" → 不是可观察输出，而是动作描述
- "库存回滚" → 库存哪个字段、回滚到什么值未指定
- "钱退回" → 退到哪、什么时间窗口、什么调用未指定

**修正**：见好例 2.2 的 AC-3。

### 3.3 边界缺失

**坏**：

```
### AC-3: 验证码有效期内可用
- Given 用户已收到验证码
- When 用户在有效期内提交
- Then 验证通过
```

**问题**：
- "有效期内" → 没具体值
- 没有边界值（第几秒过期？）
- 没指定提交后的可观察结果

**修正**：

```
### AC-3: 验证码自下发起 300 秒内可用
- **Given** Redis 中 key `otp:register:alice@example.com` value `123456`，剩余 TTL > 0
- **When** 用户在 5 分钟内（即 TTL > 0）提交 `email=alice@example.com, otp=123456`
- **Then** 后端返回 HTTP 200，body `{"verified": true}`

**边界**: 第 301 秒起即视为过期（独立 AC 覆盖过期分支）
**验证方式建议**: 接口测试
```

### 3.4 "或 X 或 Y" 二选一未定

**坏**：

```
### AC-4: 注册成功
- Given 验证码通过
- When 系统创建账号
- Then 用户被引导至登录页（或自动登录）
```

**问题**：
- "或自动登录" → 决策没做完，让开发选
- 这是 baseline C 实测出现的合理化症状

**修正**：拆成两条 AC，或回去澄清后选一个。

```
### AC-4: 注册成功后跳转到登录页
- **Given** ...（具体前置）
- **When** ...（具体动作）
- **Then** 浏览器跳转到 `/login`，页面 toast 显示"注册成功，请登录"
**边界**: 跳转响应 P95 ≤ 500ms

# 不再写"或自动登录"。如果用户希望自动登录，在澄清阶段就要决定，
# 然后只写一条匹配选择的 AC（或新增独立 AC 覆盖另一种入口）。
```

### 3.5 伪精确（自己编的具体数字）

**坏**：

```
### AC-5: 邮箱验证码注册
- Given 用户输入邮箱
- When 系统发送验证码
- Then 6 位数字验证码发送至邮箱

# 但澄清记录里没出现"6 位数字"是用户回答的证据
```

**问题**：
- "6 位数字" 看起来很精确，但用户从未确认过
- 后续可能是 4 位 / 8 位 / 数字+字母组合，全是不返工不知道的雷

**修正**：

回到澄清阶段补提问"验证码是 N 位的什么字符集？"，把答案写入"澄清记录"表，再写入 AC。

### 3.6 AC 之间强依赖（不可独立验证）

**坏**：

```
### AC-1: 用户下单
- Given ...
- When ...
- Then 订单创建成功

### AC-2: 取消订单
- Given AC-1 已完成
- When 用户点击取消
- Then 订单被取消
```

**问题**：
- AC-2 依赖 AC-1 的执行 → 测试时无法单独构造 AC-2 的前置
- 修正方向：每条 AC 自带可独立构造的前置

**修正**：

```
### AC-2: 取消未发货订单
- **Given** `orders` 表存在 `order_id=ORD-20260602-000001, status=pending_ship`（前置由 fixture 直接构造，无需依赖 AC-1 执行）
- **When** ...
- **Then** ...
```

### 3.7 越界扩字段（baseline 实测高频）

**坏**：

```markdown
# Story: 用户登录

## Story Points: 21
## Priority: P0
## Story Type: Feature

## Definition of Done
- 单元测试覆盖率 ≥ 80%
- 上线灰度 24h 无 P0 缺陷

## Non-Functional Requirements
| 类别 | 要求 |
|---|---|
| 性能 | P95 ≤ 1.5s |
| 安全 | ... |
```

**问题**：
- output-template.md 没有这些章节
- Story Points / Priority 是排期工具职责
- DoD 是项目级别，不写进单 Story
- NFR 应进独立的"性能 Story"或架构文档，不混在功能 Story 里

**修正**：删除上述全部章节，只保留 output-template.md §1 列出的强制字段。

---

## 4. 对话片段：5 维度按需提问的真实问答

以好例 1（邮箱验证码注册）为蓝本，展示 skill 与用户的真实对话节奏。

> **一次只问一个问题；每个问题附"为什么问"。**

### 轮 0：用户初次提需求

> 用户："用户注册功能，邮箱验证码注册，验证码 5 分钟内有效，验证失败要给提示。需求挺清楚的吧？直接写 Story 就行。"

### 轮 1：判定 5 维度，发现"用户角色"未明确

5 维度判定：
- 用户角色：未明确（"用户"是泛化词）
- 核心场景：部分明确
- 边界异常：未明确
- 验收判定：部分明确
- 范围边界：未明确

> Skill：「我读了一遍需求，5 个澄清维度里还有 4 个不够具体，会让后续 AC 写不出可验证条款。我每次只问一个，最少的提问量。
>
> **第 1 题（用户角色）**：注册的"用户"具体指谁？
> A. 任意访客（未注册过）
> B. 受邀用户（持有邀请码）
> C. 企业管理员（代表组织注册）
> D. 其他（请描述）
>
> 为什么问：不同角色对邮箱合法性、是否需要邀请码、是否要求企业邮箱有完全不同的验收点。」

> 用户："A，未注册过的访客。"

### 轮 2：核心场景澄清

> Skill：「**第 2 题（核心场景）**：注册成功后立刻进入哪一步？
> A. 跳转到登录页，下一次用密码登录（密码本次设置）
> B. 跳转到登录页，下一次还用邮箱验证码登录（无密码模式）
> C. 自动登录进入首页
> D. 其他
>
> 为什么问：决定本 Story 是否需要包含"设密码"环节，直接影响 Story 范围与 AC 数量。」

> 用户："B 太麻烦每次都发码；A 吧，但密码设置我想放下一个 Story。这次只做注册，下一个 Story 做设密码。"

→ skill 内部记录：核心场景 = 输入邮箱→收到 6 位数字验证码→输入验证码→创建账号→跳转登录页；密码设置在范围之外。

### 轮 3：边界与异常 + 验收判定（一并澄清）

> Skill：「**第 3 题（边界与异常）**：以下异常分支需要本次覆盖哪些？（多选）
> a. 验证码 5 分钟过期 → 返回什么？
> b. 验证码错误 → 返回什么？错几次作废？
> c. 邮箱已注册 → 返回什么？
> d. 同邮箱重复请求验证码（防刷）
> e. 同 IP 限流（防刷）
> f. 邮件服务挂掉（降级）
>
> 为什么问：异常分支决定 AC 条数与可观察判据；漏掉就只能在评审会上重写。」

> 用户："a, b, c, d 必做。e 不做，有运维侧 WAF。f 也不做，先假设邮件服务可用。"
> 用户：「a 返回 410，提示'已过期'；b 错 5 次作废；c 返回 409；d 同邮箱 60 秒冷却。」

→ skill 内部记录：5 个异常分支均明确；可观察判定为 HTTP 状态码 + body error code + DB 行变化。

### 轮 4：范围边界

> Skill：「**第 4 题（范围边界）**：本次本 Story 不做的项目，请确认列表：
> - 设置/修改密码（独立 Story）
> - 邮箱变更、注销账号
> - 第三方登录、邀请制注册
> - 多端 SDK（仅 Web 端）
>
> 漏了什么或不同意的请指出。
>
> 为什么问：'不做什么'必须明确，避免开发推断到 SDK / Mobile 端等扩张范围。」

> 用户："列得全，就这样。"

### 轮 5：补漏 — "已注册"边界

判定 5 维度发现"已注册判定"还有歧义：

> Skill：「**第 5 题（边界补漏）**：'邮箱已注册'判定时，`status=pending`（注册了但 24h 未激活）的邮箱算已注册还是可重新注册？
>
> 为什么问：直接影响 AC-5 的判定条件。」

> 用户："`pending` 也算已注册（24h 内不能重复注册）；`deleted` 算可重新注册。"

→ 5 维度全部明确，进入 Epic 信号评估（信号 0 命中，单 Story 模式），开始写 AC。

### 全过程小结

- skill 共问了 5 个问题，每条消息只 1 个，每个都附"为什么问"。
- 用户起初说"挺清楚的"，但实际有 7 个未明确决策点。
- 每个用户回答都被写入"澄清记录"表（见好例 1）作为可追溯证据。
- 没有用"业内常识"补任何一个空。

---

## 5. 反模式：常见越界与合理化（参照 SKILL.md 的合理化对照表）

| 反模式 | 实例 | 修正方向 |
|---|---|---|
| 一次问多 | 「请告诉我：1) 角色是什么？2) 验证码几位？3) 多久过期？4) 错几次作废？」 | 一次只问 1 个；按 5 维度顺序问 |
| 跳过提问 | 用户说"挺清楚"→直接写 Story | 维度不明确就要问；姿态柔软但绝不省 |
| 业内常识补 | 自己写"6 位数字"、"60 秒冷却"，澄清记录为空 | 提问让用户给值；或标注"轮 N 提问后用户给出" |
| 顺从合并 Epic | PO 说"一个 Story 搞定"，agent 把 9 动作塞一个 Story | 信号命中时必须先与用户确认拆分；不得为了顺从而违规 |
| 加 DoD/NFR/Story Points | Story 文档里有"Story Points: 21" / "Definition of Done" / "Non-Functional Requirements" 章节 | output-template 之外的字段一律删掉 |
| "或 X 或 Y" | "Then 跳转登录页或自动登录" | 二选一拆两条 AC，或回去澄清 |
| 对话里贴 Markdown | 任务要求落盘 → 只在回答里贴文档 | 用 Write 工具实际写到 `docs/stories/...` |
| AC 抽象 | "Then 系统正确处理订单" | 给具体值（HTTP / body / DB / 事件） |
| AC 强依赖 | "AC-2 在 AC-1 完成后..." | 每条 AC 自带可独立构造的前置 |
| 静默拆分 | 不与用户确认就把单需求拆成 5 个 Story | 拆分必须先展示拆分方案并等用户确认 |
