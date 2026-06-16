# 公众号发布指南

## API 发布（开发者模式）

### 前提条件
- 公众号已通过微信认证（未认证的订阅号/服务号没有图文创建 API 权限）
- 已配置 IP 白名单（公众号后台 → 设置与开发 → 基本配置 → IP白名单）

### 权限确认
未认证的订阅号调用草稿 API 会返回 48001（api unauthorized）：
```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=TOKEN
→ {"errcode": 48001, "errmsg": "api unauthorized"}
```
旧版 `cgi-bin/material/add_news` 同样不开放。

### 可用 API（未认证账号）
- `cgi-bin/token` — 获取 access_token ✓
- `cgi-bin/draft/add` — 创建草稿 ✗（需认证）
- `cgi-bin/material/add_news` — 创建图文素材 ✗（需认证）

### 认证账号 API 流程
```python
# 1. 获取 token
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET

# 2. 创建草稿
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=TOKEN
Body: {
  "articles": [{
    "title": "标题",
    "author": "作者",
    "digest": "摘要（120字内）",
    "content": "<p>正文HTML</p>",
    "need_open_comment": 0,
    "only_fans_can_comment": 0,
    "thumb_media_id": "封面图media_id（可选）"
  }]
}
```

### Markdown → WeChat HTML 转换要点
- 不能用标准 `<p>` 标签直接贴，需要 `<section>` + 行内样式
- 代码块用 `<pre><code>` 包裹在灰色 `background:#f5f5f5` 的 `<section>` 中
- 表格用 `<table>` + `<th>/<td>` + 边框样式
- 引用用 `<blockquote>` + 绿色左边框（`border-left:3px solid #07c160`）
- 行内代码用 `<code>` + 灰色背景
- 免责声明推荐加 `⚠️` 前缀和粗体标签

## 浏览器自动化发布（未认证账号的替代方案）

### 流程
1. 导航到 `https://mp.weixin.qq.com/`
2. 选择二维码登录，用户用手机微信扫码
3. 扫码成功后进入后台首页
4. 点击 "新的创作" → "图文消息"（或直接访问编辑页）
5. 编辑页面各元素：
   - 标题输入框：填写文章标题
   - 正文编辑区：粘贴经过格式化的 HTML 内容
   - 封面图：可选上传
   - 摘要：自动生成或手动填写
6. 保存为草稿（"保存"按钮）或直接发布

### 注意事项
- 微信公众平台有反爬检测，频繁操作可能触发验证码
- 每个浏览器 session 的二维码有效期约 5 分钟
- 编辑器的富文本区域可能不是标准的 `<input>` 或 `<textarea>`，而是 contentEditable div，粘贴内容时注意保留格式
- 推荐只在 Hermes 浏览器中粘贴内容，不要尝试自动化"点击发布"（风险较高）
