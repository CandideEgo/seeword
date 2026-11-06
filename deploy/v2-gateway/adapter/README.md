# V2 模型网关薄适配层

状态：原有合成治理证据与本次 P01.3 验证分别记录，最新结果见[实施记录](../../../refactor-blueprint/docs/implementation.md)。午夜 late settle 仍未证明，不标记整体治理通过。
本目录包含两个无状态中继及可选内容收据签发器，不保存 provider key、预算或成本行；LiteLLM 仍是 usage / cost / 预算的唯一账本。收据私钥只部署到签发器，不进入业务后端。

## 为什么需要它

LiteLLM v1.106.6 已经能做出可信的部分：发包前预占、剩余不足拒绝、跨 worker 预算与并发。
它的两个缺口是源码中的有意行为：

1. 上游缺少 `usage` 时按 0 结算；
2. 客户端取消/断线时释放输出预占（`release_budget_reservation_on_cancel`）。

New API 与 Bifrost 在重新选型中表现更差，见
[`docs/evidence/v2-gateway-reselection-2026-11-03/`](../../../docs/evidence/v2-gateway-reselection-2026-11-03/README.md)。

## 两个中继

```text
backend ──► adapter:4000 ──► LiteLLM:4000 ──► adapter-shim:4100 ──► provider
```

### `app`（入站，4000）

- 对 `/chat/completions`、`/v1/chat/completions`：
  - 要求 `max_tokens`，且不得超过该模型的上限（`ADAPTER_MODEL_OUTPUT_CAPS`，
    未列出的模型用 `MODEL_MAX_OUTPUT_TOKENS`，默认 128），否则 422
    `output_cap_exceeded`；不静默改写请求。
  - 转发后如果调用方断线，**不取消 LiteLLM 请求**，而是让后台任务把响应读完，
    使 LiteLLM 走正常结算，而不是在取消路径释放预占。
- `/content-verification/{kind}` 是下文定义的专用核验入口；其余路径（`/team/*`、`/key/*`、`/health/*` 等）原样透传到 LiteLLM，查询串保留。
- `stream:true` 的补全请求**增量转发** SSE（不缓冲整包）；调用方断线后后台排空上游。
  其余 JSON 响应仍缓冲。

### `shim_app`（出站，4100）

- LiteLLM 的模型 `api_base` 指向本服务；它把请求转发到 `UPSTREAM_BASE_URL`，
  保留 LiteLLM 传来的 `Authorization`（provider key 只在网关侧流转）。
- 上游 SSE 响应逐行转发；流结束时若没有任何**结构化** usage（缺字段或 `null`），
  在 `[DONE]` 前补一个 usage chunk，不改变其余 chunk。`"usage"` 字符串出现不算。
- 保守上界按上游实际模型名查 `ADAPTER_MODEL_OUTPUT_CAPS`；查不到时取「默认值或所有配置上限中的最大值」，
  宁可高估也不少记（LiteLLM 发给 shim 的 `model` 是供应商模型名，不是路由别名）。
- 上游返回 2xx 但缺少 `usage` 时，注入保守上界：
  - `prompt_tokens = ceil(请求体字节数 / 2) + 8`（故意的上界，不是 tokenizer 声明）；
  - `completion_tokens = min(请求 max_tokens, MODEL_MAX_OUTPUT_TOKENS)`；
  - 这样 LiteLLM 用正常结算路径把保守费用写进 key / user / team 同一本账。
- 上游已返回 `usage` 时原样保留，不做二次估算。
- SSE 响应缺少 usage 时，在 `[DONE]` 前补一个 usage chunk；不改变其余 chunk。

## 环境变量

| 变量 | 用途 |
| --- | --- |
| `LITELLM_BASE_URL` | 入站代理的 LiteLLM 地址（默认 `http://gateway:4000`） |
| `UPSTREAM_BASE_URL` | shim 的真实 provider 根地址（含 `/v1`） |
| `MODEL_MAX_OUTPUT_TOKENS` | 未在 `ADAPTER_MODEL_OUTPUT_CAPS` 中列出的模型的输出上限（默认 128） |
| `ADAPTER_MODEL_OUTPUT_CAPS` | JSON：模型别名 → 已验证输出上限，如 `{"tutor": 1024}`；非法配置退回默认值 |
| `ADAPTER_TIMEOUT_SECONDS` | 中继超时（默认 60） |

## 接入

1. 后端 `LLM_GATEWAY_BASE_URL` 指向入站适配层（如 `http://llm-gateway:4000`），
   `LLM_GATEWAY_ADMIN_KEY` 仍是 LiteLLM master key。
2. LiteLLM 每个模型的 `litellm_params.api_base` 指向 shim（如
   `http://llm-gateway-shim:4100/v1`），并设置该实例的 `UPSTREAM_BASE_URL`；
   多 provider 时每个 provider 一个 shim 实例。
3. `MODEL_MAX_OUTPUT_TOKENS` 必须与供应商实测能力一致；它只是上限声明，
   不替代供应商真实计费口径。
4. `/key/generate` 会自建 user 行，但**不会**建立 team membership；成员日预算检查需要
   membership，否则会 fail-closed 503。业务侧在签发 per-run key 前先调用
   `/user/new`（409 视为已存在），`teaching_gateway` 已按此实现。
5. 生产 profile、team bootstrap 与真实 provider 的接入状态见
   [`docs/evidence/v2-gateway-real-2026-11-03/`](../../../docs/evidence/v2-gateway-real-2026-11-03/README.md)。

## 验证

- 单元测试（在 backend/，设置 `PYTHONUTF8=1`，使用该目录解释器）：
  `.venv/Scripts/python.exe -m pytest ../deploy/v2-gateway/adapter/test_adapter.py ../deploy/v2-gateway/adapter/test_content_receipts.py -q`。
- 实际 HTTP 签名/验签隔离检查（同一工作目录/解释器）：
  `.venv/Scripts/python.exe ../deploy/v2-gateway/adapter/check_receipts_http.py --backend-verifier app/services/teaching/content_receipts.py`。
  脚本创建 loopback 服务、临时签名密钥及合成上游，不连接 DB 或真实模型；不会启用业务配置。
- 合成端到端：
  `docker compose -f docker-compose.v2-gateway.yml up -d`，然后
  `docker compose -f docker-compose.v2-gateway.yml --profile check run --rm probe`。
  2026-11-03 结果：11 项中 10 项通过；唯一失败项
  `midnight_late_settle_and_member_utc_day` 是有界探针明确标注「未证明」的检查，
  不是回归，也不因日历通过。

## 内容核验收据

这是服务器到服务器的内部入口，复用 LiteLLM Bearer 凭据及其模型/预算权限，不向学习者暴露签名密钥、master key 或自由生成接口。默认关闭；原发布服务的来源、许可、证据、两模型族和答案一致性校验继续生效。

### 输入和证据边界

| POST 路径 | 请求顶层 | 受控行为 |
| --- | --- | --- |
| `/content-verification/blind-answer-v1` | `model`、`input`、`option_order` | input 为 `normalized_question` 的完整规范化题面；option_order 为 ABCD 的排列。服务端重排选项，提示中不传标准答案；输出只接受 0–3 的 selected_position |
| `/content-verification/teaching-review-v1` | `model`、`input` | input 包含 question、correct_answer、option_analyses、hints、analysis、evidence；服务端固定审查提示，输出只接受四个布尔检查 |

确切字段及固定提示以 [content_receipts.py](content_receipts.py) 为准；题面与复核输入的摘要对应后端 [content.py](../../../backend/app/services/teaching/content.py) 的规范化/摘要计算。修改提示或语义必须升 kind/prompt_version，不能悄悄复用 v1。请求限 128 KiB；不接受调用者提供 messages、model_family、verified 或任意提示。`model` 是可调用的网关别名，收据模型身份使用实际响应中的 model，而非请求别名。

成功响应为现有 manifest 收据字段加 `gateway_receipt`；JWT 使用 EdDSA/Ed25519，typ=`seeword-content-receipt+jwt`、aud=`seeword-content-publication`、v=1。签名绑定 kind、prompt_version、规范化输入 SHA-256、实际 model、配置映射的 model_family、响应 id（provider_attempt_id）、服务端生成的 logical_call_id，以及重排/选位或四项检查。每个请求的 metadata 同时携带 task=content_verification、核验类型、logical_call_id 和输入摘要，供关联 LiteLLM 原有账本；provider_attempt_id 是观察到的响应标识，不承诺等于供应商内部账单主键。

响应必须正常 stop、恰好一个 choice、结构严格符合预期。未知实际模型、截断、非法 JSON、鉴权或预算失败不签发；审查 false 原样签为 false，不能提升成通过。返回 no-store。断开调用方后仍屏蔽取消并排空原请求，确保网关有机会按原路径结算；进程崩溃不在此保证内。

签名认证调用与结果的绑定，不证明素材版权、证据正确性、独立模型族或真实账单已核对。两个别名映射到同一族不能满足发布门；model_family 配置必须依据实际供应商/模型核实，不得靠改名制造独立性。当前完成合成上游签发→实际后端验签→管理发布回归；服务器采集/恢复工具见[操作说明](../../../refactor-blueprint/docs/content-verification.md)，不代表真实材料资格或真实模型验收。

### 配置、轮换与关闭

签发器环境变量：

| 变量 | 要求 |
| --- | --- |
| `CONTENT_RECEIPTS_ENABLED` | 默认 false，明确 true 才签发 |
| `CONTENT_RECEIPT_PRIVATE_KEY_FILE` | 专用 Ed25519 PEM 私钥文件，不能复用登录 JWT 密钥 |
| `CONTENT_RECEIPT_KEY_ID` | 1–64 位字母/数字/下划线/连字符 |
| `CONTENT_RECEIPT_ISSUER` | 默认 seeword-content-gateway，后端必须相同 |
| `CONTENT_RECEIPT_MODEL_FAMILIES` | JSON 对象：实际响应 model → 已核实模型族；缺失或未知身份拒绝 |
| `CONTENT_RECEIPT_TTL_SECONDS` | 默认 3600，范围 60–86400 |

后端配置见 [backend/.env.example](../../../backend/.env.example)：开关 `CONTENT_RECEIPTS_ENABLED`、公钥环 `CONTENT_RECEIPT_PUBLIC_KEYS`（JSON 的 kid→PEM，换行在 JSON 字符串中转义为 `\n`）、同一 issuer 和 `CONTENT_RECEIPT_MAX_AGE_SECONDS`。后端只装公钥；签名算法固定，未知 kid/额外 JOSE 头/过期/未来时间/不匹配字段拒绝，不从请求 URL 下载密钥。配置不全时启动校验拒绝，关闭时发布返回服务不可用，不退回 True 验证器。

[host compose](../docker-compose.gateway-host.yml) 只定义默认关闭的变量及容器内私钥路径，**未默认挂载私钥**。真正启用时，操作者须在仓库外 override 中只为 adapter 增加私钥文件的只读挂载（目标 `/run/secrets/content-receipt.pem`），文件读取权限允许容器非 root UID 1000。shim、业务容器、导出、日志和仓库均不得持有私钥。本批未生成长期密钥或修改真实环境。

轮换先给后端加入新 kid 的公钥，再切签发器私钥/kid；旧公钥按运维窗口保留至旧收据过期。移除某 kid 会使依赖该键的新发布核验失效，已发布 revision 不自动撤回；内容撤回走现有管理流程。紧急停签关闭网关开关，停止新发布同时关闭后端开关。代码回退须保持已发布数据和审计，不以删除记录回退。

## 运行镜像

[Dockerfile](Dockerfile) 将入站与出站 sidecar 从完整 LiteLLM 运行时拆成专用非 root Python 镜像。基础镜像按 digest 固定；[requirements-runtime.txt](requirements-runtime.txt) 钉住直接运行依赖并在构建时 pip check，[requirements.txt](requirements.txt) 仅补测试依赖；不声称所有传递依赖已生成锁文件。LiteLLM 主服务及其账本版本仍由原锁文件管理。

两个 compose 的 sidecar 已声明 build context；使用部署配置前应构建该镜像并核对新运行时，不能假定此前主机已有此镜像。本批只做本地镜像和隔离容器验证，没有重建或升级已有 host 网关。

## 边界

- 不保存 provider key、不构建第二套成本账本、不复制 LiteLLM 的计价。
- 入站缓冲会牺牲首 token 延迟；需要流式教学回合时再扩展为边转发边排空。
- shim 只在「上游完全没有 usage」时注入；若上游返回错误 usage，仍以 LiteLLM 结算为准。
- 适配层进程被杀时，正在排空的请求仍会随连接消失；这一点与任何单跳代理相同，
  不能替代宿主/供应商侧的幂等与对账。
