# 金数据收款 → SeeWord 会员自动开通（2026-10 接入说明）

> **已下线（2026-11）**：会员收费链路已整体移除，全站功能对登录用户免费开放。
> 本文只作历史实施记录，文中提到的端点（`/upgrade`、`/payments/*`、
> `/api/v1/admin/payments*`）、服务（`jinshuju_service`、`payment_tasks`）、
> 数据表（`orders`、`jinshuju_payments`）与环境变量（`JINSHUJU_*`）都已删除，
> 不要再据此恢复。删除迁移为 `d4e5f6a7b8c9`。


站内仍不收款（`payments_enabled=false`，ICP 合规）。会员在金数据收款页成交后，
后端按「站内购买标识」自动把 Pro 开到买家账号上 —— 买家不用找客服、不用兑换码，
**收款页也不需要收集手机号**。

## 方案：站内购买（B）

所有购买入口都放在 SeeWord 站内（登录后进入 `/upgrade`）。站内链接带一个
`x_field_1` 参数，值是服务端签名的 `user_id + 过期时间 + HMAC`；买家付款后，
同步任务从金数据 entry 读回它，直接延长该账号的 Pro。

```
买家在 SeeWord 登录 → /upgrade（微信内点「去支付」；桌面显示二维码扫码；手机浏览器复制链接去微信打开）
  → 金数据快捷收款页（链接带 x_field_1=<签名 token>）
  → 微信支付
  → 金数据数据推送 webhook（可选，秒级）──┐
  → Celery beat 每 5 分钟同步（必跑，补漏）──┴→ 后端重新拉 entry 核对
                                                → 校验 trade_status / 档位 / 金额
                                                → 验签 token → 延长对应账号 Pro
```

- **必须从站内入口进入**：直接扫金数据收款页二维码/转发的链接没有 `x_field_1`，
  无法确定账号，订单会落 `ignored`（`error_message` 写明原因），需人工处理。
- **收款页只能在微信内付款**（该页只开微信支付、且要求微信身份，2026-10-19 实测非微信
  环境「立即支付」是灰色禁用态、点了不建单）。所以 `/upgrade` 按环境分流：微信 UA 直接
  跳转；桌面渲染收款链接的二维码让用户微信扫；手机非微信浏览器引导复制链接去微信打开。
  桌面付款发生在手机上，本页会轮询账号状态，开通后自动刷新。
- 付款成功后金数据不会自动跳回 SeeWord：成功页文案要提示「回到 SeeWord 刷新」，
  轮询最多延迟 5 分钟。
- 手机号匹配路径保留，但它是**兼容分支**（兼容旧数据/人工补单），不是主路径：
  站内购买链接在 `x_field_1` 里带一个签名 token（HMAC），落账时据此直接定位
  `user_id` —— **买家不需要填手机号**。手机号只在老订单与人工补单时才是主定位手段。

## 已验证的事实（2026-10-18 实测）

- 金数据 **API 主机是 `https://jinshuju.net/api/v1`**；`open.jinshuju.net` 只是文档站。
- 提供的 Access Token 有效，能读表单 `ed8TXL` 及其数据。
- entry 里有 `token` / `serial_number` / `trade_status` / `total_price`（元）/ `trade_no` /
  `payment_method` / `x_field_1`，以及各字段值（`field_2` 档位、`field_5` 手机号…）。
- 已付款状态集合（按其支付页前端源码确认）：`SUCCESS` / `WAIT_SELLER_SEND_GOODS` /
  `WAIT_BUYER_CONFIRM_GOODS` / `TRADE_FINISHED` / `TRADE_SUCCESS`；未付款为
  `WAIT_BUYER_PAY`；退款为 `refunded` / `partial_refunded`。
- 账号是**免费版**：`x_field_1`（扩展属性追踪）免费版可用；带签名的 URL 字段传参是
  企业高级版专属，不能用来预填手机号。免费版每月收款额度 ¥500（约 25 张月卡）。
- 带 `x_field_1` 的收款页 SSR 数据里能读到 `searchParams:{"x_field_1": …}`，说明参数被
  收款页接收（最终以真实付款后的 entry 为准，见「已知限制」）。

## 代码

| 文件 | 作用 |
|---|---|
| `backend/app/services/jinshuju_service.py` | 拉取/核对 entry、档位与金额校验、落账、token 签发/验签、延长 Pro |
| `backend/app/tasks/payment_tasks.py` | 两个 Celery 任务：单条处理（webhook）与定时同步（beat） |
| `backend/app/api/v1/payments.py` | `GET /payments/jinshuju/purchase-link`（登录后拿带 token 的支付链接）+ `POST /payments/jinshuju/webhook?secret=…` |
| `backend/app/api/v1/auth.py` | 短信登录/注册后补发「手机号匹配」路径的 pending 订单（兼容保留） |
| `backend/app/models/jinshuju_payment.py` | 落账表（幂等键 `entry_token`） |
| `backend/migrations/versions/j1i2n3s4h5u6_add_jinshuju_payments.py` | 建表迁移 |
| `backend/app/tasks/celery_app.py` | beat：`sync-jinshuju-payments`，每 300 秒 |
| `backend/tests/test_jinshuju.py` | 27 条测试（开通/未付款/金额/幂等/补发/webhook/同步/签名 token/购买链接） |
| `frontend/src/app/(main)/upgrade/page.tsx` | 会员购买页（登录墙 + 套餐；微信内跳转 / 桌面扫码 / 手机复制链接；付款后轮询自动刷新） |
| `frontend/src/components/profile/ProfileTab.tsx` | 资料页会员状态与「升级/续费」入口 |

## 签名 token 格式

```
<user_id>.<exp_ts>.<base64url(hmac_sha256("<user_id>.<exp_ts>", secret)[:16])>
```

- 默认有效期 24 小时（`JINSHUJU_PURCHASE_TOKEN_TTL_MINUTES=1440`）。
- 篡改/过期验签失败 → 不会开通（订单落 `ignored`）。
- 泄露/转发的影响：别人用你的链接付款，会员开到你账号（等于替人付款），不会白拿。
- `x_field_1` 没有签名保护，所以签名放在值里，而不是信任参数本身。

## 配置

`backend/.env` 已写入（默认 `JINSHUJU_ENABLED=false`，开卖前改 `true`）：

```
JINSHUJU_ENABLED=false
JINSHUJU_ACCESS_TOKEN=...
JINSHUJU_FORM_TOKEN=ed8TXL
JINSHUJU_WEBHOOK_SECRET=...
JINSHUJU_TIER_FIELD=field_2
JINSHUJU_PHONE_FIELD=field_5
JINSHUJU_SYNC_LOOKBACK_HOURS=72
JINSHUJU_PURCHASE_URL=https://vjgdrvgy.jsjform.com/p/ed8TXL
JINSHUJU_PURCHASE_TOKEN_SECRET=...
JINSHUJU_PURCHASE_TOKEN_TTL_MINUTES=1440
```

生产服务器同样要配这些变量，然后重启 `backend`、`celery`（worker）与 `celery-beat`。

## 金数据后台设置

1. **收款页 →「收集买家信息」保持不勾选**（B 方案不需要手机号；勾了反而增加买家操作）。
2. 表单 **设置 → 数据推送**（可选，秒级开通）：
   `https://<你的域名>/api/v1/payments/jinshuju/webhook?secret=<JINSHUJU_WEBHOOK_SECRET>`
   没有公网域名可以不配，轮询最多延迟 5 分钟。
3. **支付成功页文案**改成（收款页编辑器 → 支付成功页 → 成功提示）：

   ```
   ✅ 支付成功，会员将自动开通
   请回到 SeeWord 刷新页面查看
   通常 1 分钟内生效，感谢支持 😊
   ```

   免费版不会自动跳回站内，所以这句引导很重要。
4. 不要把金数据收款页二维码直接对外发；对外发 SeeWord 的 `/upgrade` 链接/二维码
   （或带登录回跳的站内链接）。只有从站内进入的订单才能自动认账号。

## 上线顺序

1. `alembic upgrade head`（只由 backend 容器跑）—— 新增 `jinshuju_payments` 表。
2. 三个服务都配好 env，`JINSHUJU_ENABLED=true`，重启 backend / celery worker / celery beat。
3. 确认 beat 生效（`celery inspect scheduled` 应有 `sync-jinshuju-payments`）。
4. 登录 SeeWord → `/upgrade` →（桌面用微信扫页面上的二维码，或在手机微信里直接打开）
   用自己账号实付一单月卡（¥19.90）→ 5 分钟内查 `users.plan_expires_at`；
   **重点确认 entry 的 `x_field_1` 有值**（这是 B 的命门）。
5. 开卖前打开 `redeem_tasks.downgrade_expired_pro` 的 beat（目前内测期被注释），
   否则会员到期后 `plan` 不会回落。
6. 更新用户协议里「内测期间不销售会员」的表述。

## 安全 / 运维

- Access Token 只放服务端 env。它曾出现在聊天里，**建议在金数据后台撤销重建后更新 env**。
- webhook 的 secret 在 URL 上，别贴进公开仓库/截图。
- 伪造推送发不出会员：任务会按 `serial_number` 重新拉取 entry 核对，不信任推送内容。
- 退款不自动回收会员，只把落账行标成 `refunded`，由人工决定是否追回。
- **同步窗口限制**：定时同步只扫 `[现在 - max(1, JINSHUJU_SYNC_LOOKBACK_HOURS), 现在]` 内创建的 entry。
  服务停机超过该窗口时，更早的已付款订单不会自动开通。恢复后人工补：
  临时调大 `JINSHUJU_SYNC_LOOKBACK_HOURS` 跑一次同步，或用 `fetch_entry(serial_number)` 按单号拉取，
  经 `process_entry` 重新处理（`sync_recent_entries` 只认窗口内的 entry，窗口外要靠这一条）。
- 需要人工核对的数据：`SELECT * FROM jinshuju_payments WHERE status IN ('ignored','error');`
  - `x_field_1` 缺失/无效/账号不存在 → `ignored`（可能是从站外直接买的）
  - 金额不符 → `ignored`（可能改价后表单与代码不一致）

## 已知限制 / 待办

- **B 的覆盖面**：只有从 SeeWord 站内进入的买家能自动开通；站外直购必须人工补。
- **`x_field_1` 透传仍需一单实测**：收款页已确认接收 URL 参数（SSR `searchParams` 里有
  我们塞的 token），但「付款后写进 entry」这一步还没被真实订单验证过。若平台不透传，
  B 失效，需退回手机号收集或升级套餐走「支付后跳转认领」。
- 免费版每月收款上限 ¥500（约 25 单月卡），放量前要升套餐。
- 新用户注册有 3 天试用：月卡会从试用到期日再延 30 天（共 33 天）。若希望从付款日
  起算 30 天，需要改 `_extend_pro` 的基数。
- 站内功能尚未按 Pro 做权限差异；购买页展示的是会员权益，真正 gating 是另一件事。
