# 运行组件、工具、基础设施和当前文档索引

本分册 147 项。每项来自实际文件、符号/表/路由和引用提取；关系未显示的其余项在 [完整机器清单](../inventory.json)。无 import 不等于无调用，动态入口/收集器/配置关系另列。

## `.claude`

### [.claude/launch.json](../../../.claude/launch.json)

桌面预览进程配置，描述本机 API/前端启动，不是产品服务发现。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `.claude/reference`

### [.claude/reference/kill-ports.md](../../../.claude/reference/kill-ports.md)

开发服务重启前清端口的必要本机操作说明；广域进程终止需遵守停止条件。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `.claude/skills/deploy`

### [.claude/skills/deploy/SKILL.md](../../../.claude/skills/deploy/SKILL.md)

明确授权下的构建→上传→校验→迁移→切换→复验发布流程。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

## `.claude/skills/deploy/scripts`

### [.claude/skills/deploy/scripts/sshx.py](../../../.claude/skills/deploy/scripts/sshx.py)

由环境提供凭据执行显式远程命令，不是自动授权生产；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [.claude/skills/deploy/scripts/upload.py](../../../.claude/skills/deploy/scripts/upload.py)

按远端大小续传发布归档并在断线后重连；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`connect`、`remote_size`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `.claude/skills/dev-stop`

### [.claude/skills/dev-stop/SKILL.md](../../../.claude/skills/dev-stop/SKILL.md)

本机停止流程；显式 infra 选项才停基础设施。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `.claude/skills/dev`

### [.claude/skills/dev/SKILL.md](../../../.claude/skills/dev/SKILL.md)

本机开发启动/重启流程与队列分工，不自动部署生产。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

## `.`

### [.gitattributes](../../../.gitattributes)

固定跨平台文本换行/二进制属性，保护发行校验和和脚本可执行语义。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `.github`

### [.github/dependabot.yml](../../../.github/dependabot.yml)

GitHub 依赖更新范围和周期，不是业务进程。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `.github/workflows`

### [.github/workflows/ci.yml](../../../.github/workflows/ci.yml)

后端/GPU/前端/e2e 自动门禁及失败证据收集；不部署。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [.github/workflows/cross-browser.yml](../../../.github/workflows/cross-browser.yml)

夜间/手动 Firefox 与 WebKit 回归，补充 PR 的 Chromium。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [.github/workflows/slcs.yml](../../../.github/workflows/slcs.yml)

独立安装 wheel、一致性套件和公开发行树的 Windows/Linux CI。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `.`

### [.gitignore](../../../.gitignore)

忽略凭据、依赖、媒体、缓存、构建与本地临时证据；白名单允许安全模板。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [.pre-commit-config.yaml](../../../.pre-commit-config.yaml)

提交前本地安全、Python lint/格式和前端检查，不替代完整 CI。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [AGENTS.md](../../../AGENTS.md)

只链接到项目/局部规则的入口，不再复制规则。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [CLAUDE.md](../../../CLAUDE.md)

全项目工作规则、真实入口及不可破坏边界；架构正文改为引用审计。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [LICENSE](../../../LICENSE)

整站当前专有许可；没有因开发大纲而自动改为开源。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [Start-Redesign.ps1](../../../Start-Redesign.ps1)

保留的轻量本地启动入口：API/前端/DB/Redis，不起 Celery/GPU/beat。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `deploy/redis`

### [deploy/redis/redis.conf](../../../deploy/redis/redis.conf)

Redis AOF/淘汰/持久化运行策略，被生产和隔离栈挂载。

- 配置/资源消费者：[docker-compose.prod.yml](../../../docker-compose.prod.yml)、[docker-compose.isolation.yml](../../../docker-compose.isolation.yml)。
- 处置：更新必要说明/引用或生成路径。

### [deploy/redis/users.acl.template](../../../deploy/redis/users.acl.template)

云端/GPU 权限策略模板；真实口令由环境渲染，不提交。

- 配置/资源消费者：[scripts/isolation/render_redis_acl.py](../../../scripts/isolation/render_redis_acl.py)。
- 处置：保留。

## `deploy/v2-gateway`

### [deploy/v2-gateway/README.md](../../../deploy/v2-gateway/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

## `deploy/v2-gateway/adapter`

### [deploy/v2-gateway/adapter/Dockerfile](../../../deploy/v2-gateway/adapter/Dockerfile)

容器构建入口：该组件运行依赖和非 root/入口装配；与同组件 Compose build 相连。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/adapter/README.md](../../../deploy/v2-gateway/adapter/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [deploy/v2-gateway/adapter/app.py](../../../deploy/v2-gateway/adapter/app.py)

两个无状态 HTTP 中继：入站输出上限/断线排空、出站 usage 补偿和核验路由。

- 代码入口/类型：`model_output_caps`、`health`、`verify_content`、`proxy`、`shim_health`、`shim`。
- 本文件路由片段（还需 router/装配前缀）：`GET /health`、`POST /content-verification/{kind}`、`API_ROUTE /{path:path}`、`GET /health`、`API_ROUTE /{path:path}`。
- 直接依赖：[deploy/v2-gateway/adapter/content_receipts.py](../../../deploy/v2-gateway/adapter/content_receipts.py)。
- 直接使用者：[deploy/v2-gateway/adapter/check_receipts_http.py](../../../deploy/v2-gateway/adapter/check_receipts_http.py)、[deploy/v2-gateway/adapter/test_adapter.py](../../../deploy/v2-gateway/adapter/test_adapter.py)、[deploy/v2-gateway/adapter/test_content_receipts.py](../../../deploy/v2-gateway/adapter/test_content_receipts.py)。
- 处置：保留。

### [deploy/v2-gateway/adapter/check_receipts_http.py](../../../deploy/v2-gateway/adapter/check_receipts_http.py)

loopback 合成 HTTP 签发→后端公钥验签检查；默认不证明生产治理通过。

- 代码入口/类型：`serve`、`ready`、`main`。
- 本文件路由片段（还需 router/装配前缀）：`POST /chat/completions`。
- 直接依赖：[deploy/v2-gateway/adapter/app.py](../../../deploy/v2-gateway/adapter/app.py)。
- 处置：保留。

### [deploy/v2-gateway/adapter/content_receipts.py](../../../deploy/v2-gateway/adapter/content_receipts.py)

网关固定内容核验输入/提示、真实响应校验及 Ed25519 签名；不保存第二账本。

- 代码入口/类型：`ReceiptConfigurationError`、`Signer`、`signer`、`completion_request`、`issue`。
- 直接使用者：[deploy/v2-gateway/adapter/app.py](../../../deploy/v2-gateway/adapter/app.py)。
- 处置：保留。

### [deploy/v2-gateway/adapter/requirements-runtime.txt](../../../deploy/v2-gateway/adapter/requirements-runtime.txt)

该组件的依赖安装/约束/审计输入：requirements-runtime.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [deploy/v2-gateway/adapter/requirements.txt](../../../deploy/v2-gateway/adapter/requirements.txt)

该组件的依赖安装/约束/审计输入：requirements.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [deploy/v2-gateway/adapter/test_adapter.py](../../../deploy/v2-gateway/adapter/test_adapter.py)

自动回归：本文件列出的领域服务/接口与边界条件。行为锚点：rejects_output_above_cap；requires_max_tokens；proxies_admin_query_string；shim_injects_conservative_usage。

- 代码入口/类型：`restore_env`、`use_transport`、`run`、`test_rejects_output_above_cap`、`test_requires_max_tokens`、`test_proxies_admin_query_string`、`test_shim_injects_conservative_usage`、`test_shim_keeps_provider_usage`、`test_shim_defaults_to_model_cap_when_max_tokens_missing`、`test_per_model_cap_only_widens_the_listed_model`（其余见机器清单）。
- 直接依赖：[deploy/v2-gateway/adapter/app.py](../../../deploy/v2-gateway/adapter/app.py)。
- 直接使用者：[deploy/v2-gateway/adapter/test_content_receipts.py](../../../deploy/v2-gateway/adapter/test_content_receipts.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [deploy/v2-gateway/adapter/test_content_receipts.py](../../../deploy/v2-gateway/adapter/test_content_receipts.py)

自动回归：教学核验输入/结果的 Ed25519 收据验签。行为锚点：fixed_prompt_uses_actual_response_identity_and_signs_only_observed_fields；callers_cannot_choose_prompt_or_attested_model_family；bad_or_incomplete_outputs_never_issue_receipts；gateway_auth_and_budget_errors_cannot_become_signed_success。

- 代码入口/类型：`question`、`payload`、`signer`、`response`、`install`、`invoke`、`test_fixed_prompt_uses_actual_response_identity_and_signs_only_observed_fields`、`test_callers_cannot_choose_prompt_or_attested_model_family`、`test_bad_or_incomplete_outputs_never_issue_receipts`、`test_gateway_auth_and_budget_errors_cannot_become_signed_success`（其余见机器清单）。
- 直接依赖：[deploy/v2-gateway/adapter/app.py](../../../deploy/v2-gateway/adapter/app.py)、[deploy/v2-gateway/adapter/test_adapter.py](../../../deploy/v2-gateway/adapter/test_adapter.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

## `deploy/v2-gateway`

### [deploy/v2-gateway/bootstrap_gateway.py](../../../deploy/v2-gateway/bootstrap_gateway.py)

显式创建模型网关 team 和预算配置，会写远端；默认不证明生产治理通过。

- 代码入口/类型：`list_teams`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/config.prod.template.yaml](../../../deploy/v2-gateway/config.prod.template.yaml)

真实网关配置模板，凭据由运行环境渲染；默认不证明生产治理通过。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/config.synthetic.yaml](../../../deploy/v2-gateway/config.synthetic.yaml)

合成网关模型和预算/Redis 配置；默认不证明生产治理通过。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/docker-compose.gateway-host.yml](../../../deploy/v2-gateway/docker-compose.gateway-host.yml)

独立网关主机和专用账本/Redis/sidecar 装配；默认不证明生产治理通过。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/entrypoint-gateway.sh](../../../deploy/v2-gateway/entrypoint-gateway.sh)

先校验和渲染配置再启动 LiteLLM；默认不证明生产治理通过。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/gateway_tunnel.ps1](../../../deploy/v2-gateway/gateway_tunnel.ps1)

主动反向 SSH 隧道保活，不是 Web API；默认不证明生产治理通过。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/gateway_tunnel.sh](../../../deploy/v2-gateway/gateway_tunnel.sh)

主动反向 SSH 隧道保活，不是 Web API；默认不证明生产治理通过。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/image-lock.json](../../../deploy/v2-gateway/image-lock.json)

LiteLLM 固定镜像/版本和治理放行状态，不能靠旧报告推断 true。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [deploy/v2-gateway/provider_stub.py](../../../deploy/v2-gateway/provider_stub.py)

合成 OpenAI 兼容 provider，不调用外部服务；默认不证明生产治理通过。

- 代码入口/类型：`Handler`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/render_config.py](../../../deploy/v2-gateway/render_config.py)

仅替换已知变量并私有写入真实网关配置；默认不证明生产治理通过。

- 代码入口/类型：`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [deploy/v2-gateway/synthetic.receipts.override.yaml](../../../deploy/v2-gateway/synthetic.receipts.override.yaml)

从旧蓝图迁出的活合成收据演练配置，输出到 tmp/gateway-receipts。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：本轮新增。

## `.`

### [docker-compose.dev.yml](../../../docker-compose.dev.yml)

开发 PostgreSQL/Redis 基础设施，不启动 API/前端。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [docker-compose.isolation.yml](../../../docker-compose.isolation.yml)

独立 Redis ACL/恢复及专用 PostgreSQL 演练装配。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [docker-compose.prod.yml](../../../docker-compose.prod.yml)

生产 API/云 worker/beat/前端/nginx/持久层及可选网关的装配与变量白名单。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [docker-compose.smoke.yml](../../../docker-compose.smoke.yml)

本机独立生产镜像/HTTPS 回归 override，不写远程业务环境。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [docker-compose.v2-gateway.yml](../../../docker-compose.v2-gateway.yml)

只用合成 provider 和独立账本的候选网关治理探针装配。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [docker-compose.yml](../../../docker-compose.yml)

开发全栈装配，teaching 可选 profile；不带 beat/GPU。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `docs/evidence/astryx-integration`

### [docs/evidence/astryx-integration/acceptance.md](../../../docs/evidence/astryx-integration/acceptance.md)

最新 Astryx 词汇试点的 acceptance 验收/截图证据；关联词汇布局与 e2e，不代表全站已迁移。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/login-diagnostic.png](../../../docs/evidence/astryx-integration/login-diagnostic.png)

二进制静态资源：历史证据/生成素材；不是应用执行代码。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/manual-interactions.json](../../../docs/evidence/astryx-integration/manual-interactions.json)

最新 Astryx 词汇试点的 manual-interactions 验收/截图证据；关联词汇布局与 e2e，不代表全站已迁移。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/mobile-dark-metrics.json](../../../docs/evidence/astryx-integration/mobile-dark-metrics.json)

最新 Astryx 词汇试点的 mobile-dark-metrics 验收/截图证据；关联词汇布局与 e2e，不代表全站已迁移。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/vocabulary-desktop-light.png](../../../docs/evidence/astryx-integration/vocabulary-desktop-light.png)

二进制静态资源：历史证据/生成素材；不是应用执行代码。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/vocabulary-mobile-dark.png](../../../docs/evidence/astryx-integration/vocabulary-mobile-dark.png)

二进制静态资源：历史证据/生成素材；不是应用执行代码。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/vocabulary-mobile-light.png](../../../docs/evidence/astryx-integration/vocabulary-mobile-light.png)

二进制静态资源：历史证据/生成素材；不是应用执行代码。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/astryx-integration/vocabulary-visible-light.png](../../../docs/evidence/astryx-integration/vocabulary-visible-light.png)

二进制静态资源：历史证据/生成素材；不是应用执行代码。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `docs/evidence/open-learning`

### [docs/evidence/open-learning/acceptance-cards.md](../../../docs/evidence/open-learning/acceptance-cards.md)

最新 P0 acceptance-cards 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `docs/evidence/open-learning/p0`

### [docs/evidence/open-learning/p0/d04-consumer-evidence.json](../../../docs/evidence/open-learning/p0/d04-consumer-evidence.json)

最新 P0 d04-consumer-evidence 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/d04-local-license-evidence.json](../../../docs/evidence/open-learning/p0/d04-local-license-evidence.json)

最新 P0 d04-local-license-evidence 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/d04-python-registry.json](../../../docs/evidence/open-learning/p0/d04-python-registry.json)

最新 P0 d04-python-registry 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/d04-review-checks.json](../../../docs/evidence/open-learning/p0/d04-review-checks.json)

最新 P0 d04-review-checks 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/d04-upstream-source-checks.json](../../../docs/evidence/open-learning/p0/d04-upstream-source-checks.json)

最新 P0 d04-upstream-source-checks 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/d04-version-matrix.json](../../../docs/evidence/open-learning/p0/d04-version-matrix.json)

最新 P0 d04-version-matrix 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/d04-wheel-license-evidence.json](../../../docs/evidence/open-learning/p0/d04-wheel-license-evidence.json)

最新 P0 d04-wheel-license-evidence 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/document-checks.json](../../../docs/evidence/open-learning/p0/document-checks.json)

最新 P0 document-checks 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/gsap-removal.json](../../../docs/evidence/open-learning/p0/gsap-removal.json)

最新 P0 gsap-removal 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/evidence/open-learning/p0/inventory.json](../../../docs/evidence/open-learning/p0/inventory.json)

最新 P0 inventory 原始核对证据；关联 open-learning 许可/来源记录，保留当时版本/边界，不是运行配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `docs/open-learning`

### [docs/open-learning/content-access-matrix.md](../../../docs/open-learning/content-access-matrix.md)

最新大纲的 P0 按用途/身份的内容访问矩阵；不是已放行产品实现。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [docs/open-learning/p0-worklog.md](../../../docs/open-learning/p0-worklog.md)

最新大纲的 P0 阻塞决策与事实盘点；不是已放行产品实现。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `docs/open-learning/p0`

### [docs/open-learning/p0/d04-license-inventory.md](../../../docs/open-learning/p0/d04-license-inventory.md)

最新大纲的 P0 各运行/发行依赖许可清单；不是已放行产品实现。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/open-learning/p0/d04-license-review-2026-11-13.md](../../../docs/open-learning/p0/d04-license-review-2026-11-13.md)

最新大纲的 P0 关键依赖来源和版本逐项核对；不是已放行产品实现。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [docs/open-learning/p0/source-evidence-ledger.md](../../../docs/open-learning/p0/source-evidence-ledger.md)

最新大纲的 P0 逐份素材来源/授权证据台账；不是已放行产品实现。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

## `docs/project-audit`

### [docs/project-audit/README.md](../../../docs/project-audit/README.md)

新人入口、审计结论、优先级与重构建议。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/architecture.md](../../../docs/project-audit/architecture.md)

本地代码现状、模块/数据归属和关键链路。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

## `docs/project-audit/catalog`

### [docs/project-audit/catalog/backend.md](../../../docs/project-audit/catalog/backend.md)

本轮按组件或历史材料拆分的逐文件职责/关系/处置索引。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/catalog/frontend.md](../../../docs/project-audit/catalog/frontend.md)

本轮按组件或历史材料拆分的逐文件职责/关系/处置索引。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/catalog/history.md](../../../docs/project-audit/catalog/history.md)

本轮按组件或历史材料拆分的逐文件职责/关系/处置索引。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/catalog/runtime.md](../../../docs/project-audit/catalog/runtime.md)

本轮按组件或历史材料拆分的逐文件职责/关系/处置索引。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

## `docs/project-audit/checks`

### [docs/project-audit/checks/coverage.json](../../../docs/project-audit/checks/coverage.json)

文件/目录清单覆盖、许可/迁移/保留组和链接验证结果。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/checks/results.json](../../../docs/project-audit/checks/results.json)

本轮实际测试/门禁结果、未执行边界与本地原始日志哈希。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/checks/risk-probes.json](../../../docs/project-audit/checks/risk-probes.json)

本轮隔离替身探针结果，不是生产故障证据。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

## `docs/project-audit`

### [docs/project-audit/cleanup-manifest.json](../../../docs/project-audit/cleanup-manifest.json)

逐项清理/迁移/修改、原哈希、恢复位置与授权边界。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/directory-catalog.md](../../../docs/project-audit/directory-catalog.md)

审计前后所有版本化目录及本地边界的作用和处置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/file-catalog.md](../../../docs/project-audit/file-catalog.md)

按组件进入每个文件的导航索引。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/inventory.json](../../../docs/project-audit/inventory.json)

每个文件职责、精确 import 上下游、表/路由/迁移和处置的机器清单。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

### [docs/project-audit/verification.md](../../../docs/project-audit/verification.md)

本轮实际检查/失败/跳过/环境限制与证据。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：本轮新增。

## `docs`

### [docs/seeword-open-source-development-outline-2026-11-13.md](../../../docs/seeword-open-source-development-outline-2026-11-13.md)

历史说明/方案/验收材料：seeword-open-source-development-outline-2026-11-13；处置原因和恢复位置见清理账本。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

## `docs/session-notes`

### [docs/session-notes/2026-11-13-ci-fix-session.md](../../../docs/session-notes/2026-11-13-ci-fix-session.md)

最新提交附带的会话边界复述，区分历史 CI 与未完成验证；不作为当前启动入口。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `docs/slcs`

### [docs/slcs/LICENSES.md](../../../docs/slcs/LICENSES.md)

法律许可、署名与适用范围，供发行/合规消费者；不是冗余使用说明。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)。
- 处置：保留。

### [docs/slcs/README.md](../../../docs/slcs/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：更新必要说明/引用或生成路径。

## `docs/slcs/examples/invalid`

### [docs/slcs/examples/invalid/duplicate-key.json](../../../docs/slcs/examples/invalid/duplicate-key.json)

SLCS 故意非法的 duplicate-key 负例；测试应拒绝它。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

### [docs/slcs/examples/invalid/missing-translation.json](../../../docs/slcs/examples/invalid/missing-translation.json)

SLCS 故意非法的 missing-translation 负例；测试应拒绝它。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

### [docs/slcs/examples/invalid/unknown-field.json](../../../docs/slcs/examples/invalid/unknown-field.json)

SLCS 故意非法的 unknown-field 负例；测试应拒绝它。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

### [docs/slcs/examples/invalid/unknown-version.json](../../../docs/slcs/examples/invalid/unknown-version.json)

SLCS 故意非法的 unknown-version 负例；测试应拒绝它。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

## `docs/slcs/examples`

### [docs/slcs/examples/read_example.py](../../../docs/slcs/examples/read_example.py)

SLCS 具有独立署名/许可的参考包或其离线读取演示；被发行器和一致性测试消费。

- 代码入口/类型：`main`。
- 直接依赖：[backend/slcs/__init__.py](../../../backend/slcs/__init__.py)。
- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

### [docs/slcs/examples/welcome-to-wikisource.json](../../../docs/slcs/examples/welcome-to-wikisource.json)

SLCS 具有独立署名/许可的参考包或其离线读取演示；被发行器和一致性测试消费。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

## `docs/slcs`

### [docs/slcs/schema.json](../../../docs/slcs/schema.json)

由 SLCS 模型生成并在一致性测试逐字段比对的 JSON Schema。

- 配置/资源消费者：[backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 处置：保留。

## `gpu-worker`

### [gpu-worker/.env.gpu-worker.example](../../../gpu-worker/.env.gpu-worker.example)

安全的环境变量模板，不是真实凭据；加载方为对应组件 Settings/启动脚本。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/.gitignore](../../../gpu-worker/.gitignore)

该组件构建/版本化排除边界，防依赖、凭据和生成物误入制品。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/.pip-audit-ignore](../../../gpu-worker/.pip-audit-ignore)

检查基线/带期限安全豁免；不是允许任意新增错误的白名单。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/README.md](../../../gpu-worker/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

## `gpu-worker/gpu_worker`

### [gpu-worker/gpu_worker/__init__.py](../../../gpu-worker/gpu_worker/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[gpu-worker/tests/test_callback_delivery.py](../../../gpu-worker/tests/test_callback_delivery.py)、[gpu-worker/tests/test_contracts.py](../../../gpu-worker/tests/test_contracts.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/alerts.py](../../../gpu-worker/gpu_worker/alerts.py)

独立 GPU 组件：独立 GPU worker 的站外告警；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`send_alert`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/logging.py](../../../gpu-worker/gpu_worker/logging.py)。
- 直接使用者：[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/broker_recovery.py](../../../gpu-worker/gpu_worker/broker_recovery.py)

独立 GPU 组件：启动时恢复 GPU 私有 unacked 孤儿消息；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`restore_orphaned_unacked`。
- 直接依赖：[gpu-worker/gpu_worker/broker_settings.py](../../../gpu-worker/gpu_worker/broker_settings.py)。
- 直接使用者：[gpu-worker/scripts/start_gpu_worker.py](../../../gpu-worker/scripts/start_gpu_worker.py)、[scripts/isolation/gpu_stub_worker.py](../../../scripts/isolation/gpu_stub_worker.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/broker_settings.py](../../../gpu-worker/gpu_worker/broker_settings.py)

独立 GPU 组件：GPU 私有在途消息命名空间；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`broker_transport_options`。
- 直接使用者：[gpu-worker/gpu_worker/broker_recovery.py](../../../gpu-worker/gpu_worker/broker_recovery.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/scripts/start_gpu_worker.py](../../../gpu-worker/scripts/start_gpu_worker.py)、[gpu-worker/tests/test_broker_settings.py](../../../gpu-worker/tests/test_broker_settings.py)、[scripts/isolation/gpu_stub_worker.py](../../../scripts/isolation/gpu_stub_worker.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)

独立 GPU 组件：消息队列、路由、beat 排程和任务注册；不得依赖云端 app/数据库/OSS key。

- 直接依赖：[gpu-worker/gpu_worker/broker_settings.py](../../../gpu-worker/gpu_worker/broker_settings.py)、[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/contracts.py](../../../gpu-worker/gpu_worker/contracts.py)、[gpu-worker/gpu_worker/logging.py](../../../gpu-worker/gpu_worker/logging.py)、[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)。
- 直接使用者：[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)、[gpu-worker/scripts/start_gpu_worker.py](../../../gpu-worker/scripts/start_gpu_worker.py)、[gpu-worker/tests/test_broker_settings.py](../../../gpu-worker/tests/test_broker_settings.py)、[gpu-worker/tests/test_contracts.py](../../../gpu-worker/tests/test_contracts.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)

独立 GPU 组件：环境配置、合法环境名与生产安全校验；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`Settings`、`get_settings`。
- 直接使用者：[gpu-worker/gpu_worker/alerts.py](../../../gpu-worker/gpu_worker/alerts.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/gpu_worker/logging.py](../../../gpu-worker/gpu_worker/logging.py)、[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)、[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)、[gpu-worker/gpu_worker/transcription/audio_extractor.py](../../../gpu-worker/gpu_worker/transcription/audio_extractor.py)；其余 5 项见机器清单。
- 处置：保留。

### [gpu-worker/gpu_worker/contracts.py](../../../gpu-worker/gpu_worker/contracts.py)

独立 GPU 组件：GPU 跨机任务名/队列/回调头/心跳契约常量；不得依赖云端 app/数据库/OSS key。

- 直接使用者：[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)、[gpu-worker/scripts/start_gpu_worker.py](../../../gpu-worker/scripts/start_gpu_worker.py)、[gpu-worker/tests/test_contracts.py](../../../gpu-worker/tests/test_contracts.py)、[scripts/isolation/gpu_stub_worker.py](../../../scripts/isolation/gpu_stub_worker.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/logging.py](../../../gpu-worker/gpu_worker/logging.py)

独立 GPU 组件：结构化日志与请求/任务关联；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`configure_logging`、`get_logger`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)。
- 直接使用者：[gpu-worker/gpu_worker/alerts.py](../../../gpu-worker/gpu_worker/alerts.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)、[gpu-worker/scripts/start_gpu_worker.py](../../../gpu-worker/scripts/start_gpu_worker.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/sources.py](../../../gpu-worker/gpu_worker/sources.py)

独立 GPU 组件：跨机 local/imported 来源枚举；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`VideoSource`。
- 直接使用者：[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)、[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)、[gpu-worker/tests/test_contracts.py](../../../gpu-worker/tests/test_contracts.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)

独立 GPU 组件：GPU 转录、异常重试、云端回调与告警；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`transcribe_video_gpu`。
- 直接依赖：[gpu-worker/gpu_worker/alerts.py](../../../gpu-worker/gpu_worker/alerts.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/contracts.py](../../../gpu-worker/gpu_worker/contracts.py)、[gpu-worker/gpu_worker/logging.py](../../../gpu-worker/gpu_worker/logging.py)、[gpu-worker/gpu_worker/sources.py](../../../gpu-worker/gpu_worker/sources.py)；其余 1 项见机器清单。
- 直接使用者：[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/tests/test_callback_delivery.py](../../../gpu-worker/tests/test_callback_delivery.py)、[gpu-worker/tests/test_contracts.py](../../../gpu-worker/tests/test_contracts.py)。
- 配置/资源消费者：[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)。
- 处置：更新必要说明/引用或生成路径。

## `gpu-worker/gpu_worker/transcription`

### [gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)

GPU 转录编排：提取音频、模型转录/回退、标点、逐词对齐与字幕分段。

- 代码入口/类型：`TranscriptionService`、`transcribe_video`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/sources.py](../../../gpu-worker/gpu_worker/sources.py)、[gpu-worker/gpu_worker/transcription/audio_extractor.py](../../../gpu-worker/gpu_worker/transcription/audio_extractor.py)、[gpu-worker/gpu_worker/transcription/chunked_transcription.py](../../../gpu-worker/gpu_worker/transcription/chunked_transcription.py)、[gpu-worker/gpu_worker/transcription/exceptions.py](../../../gpu-worker/gpu_worker/transcription/exceptions.py)、[gpu-worker/gpu_worker/transcription/formatters.py](../../../gpu-worker/gpu_worker/transcription/formatters.py)；其余 1 项见机器清单。
- 直接使用者：[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)、[gpu-worker/tests/test_whisperx_oom_retry.py](../../../gpu-worker/tests/test_whisperx_oom_retry.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/transcription/audio_extractor.py](../../../gpu-worker/gpu_worker/transcription/audio_extractor.py)

独立 GPU 组件：下载或提取源音频和探测时长；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`extract_streaming_audio`、`extract_local_audio`、`download_http_to_temp`、`get_video_duration`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/transcription/exceptions.py](../../../gpu-worker/gpu_worker/transcription/exceptions.py)、[gpu-worker/gpu_worker/ytdlp_cookies.py](../../../gpu-worker/gpu_worker/ytdlp_cookies.py)。
- 直接使用者：[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/transcription/chunked_transcription.py](../../../gpu-worker/gpu_worker/transcription/chunked_transcription.py)

独立 GPU 组件：长音频分块提取、并发转录和时间轴拼接；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`transcribe_in_chunks`、`transcribe_local_chunks`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/transcription/exceptions.py](../../../gpu-worker/gpu_worker/transcription/exceptions.py)、[gpu-worker/gpu_worker/transcription/formatters.py](../../../gpu-worker/gpu_worker/transcription/formatters.py)、[gpu-worker/gpu_worker/transcription/whisper_model.py](../../../gpu-worker/gpu_worker/transcription/whisper_model.py)。
- 直接使用者：[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/transcription/exceptions.py](../../../gpu-worker/gpu_worker/transcription/exceptions.py)

独立 GPU 组件：转录/音频提取/不支持平台的错误类型；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`TranscriptionError`、`AudioExtractionError`、`UnsupportedPlatformError`。
- 直接使用者：[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)、[gpu-worker/gpu_worker/transcription/audio_extractor.py](../../../gpu-worker/gpu_worker/transcription/audio_extractor.py)、[gpu-worker/gpu_worker/transcription/chunked_transcription.py](../../../gpu-worker/gpu_worker/transcription/chunked_transcription.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/transcription/formatters.py](../../../gpu-worker/gpu_worker/transcription/formatters.py)

独立 GPU 组件：把引擎分段与对齐词转换成云端字幕结构，执行长句拆分/短句合并；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`faster_whisper_segments_to_dicts`、`whisperx_segments_to_subtitles`、`split_long_segments`、`merge_short_segments`、`whisper_segments_to_subtitles`。
- 直接使用者：[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)、[gpu-worker/gpu_worker/transcription/chunked_transcription.py](../../../gpu-worker/gpu_worker/transcription/chunked_transcription.py)、[gpu-worker/gpu_worker/transcription/whisper_model.py](../../../gpu-worker/gpu_worker/transcription/whisper_model.py)、[gpu-worker/tests/test_whisperx_oom_retry.py](../../../gpu-worker/tests/test_whisperx_oom_retry.py)、[gpu-worker/tests/test_whisperx_segmentation.py](../../../gpu-worker/tests/test_whisperx_segmentation.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/transcription/punctuation.py](../../../gpu-worker/gpu_worker/transcription/punctuation.py)

独立 GPU 组件：可选标点恢复与无模型降级；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`restore_punctuation`。
- 直接使用者：[gpu-worker/gpu_worker/transcription/whisper_model.py](../../../gpu-worker/gpu_worker/transcription/whisper_model.py)、[gpu-worker/tests/test_whisperx_segmentation.py](../../../gpu-worker/tests/test_whisperx_segmentation.py)。
- 处置：保留。

### [gpu-worker/gpu_worker/transcription/whisper_model.py](../../../gpu-worker/gpu_worker/transcription/whisper_model.py)

独立 GPU 组件：模型加载、设备/精度、分块/批大小与转录执行；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`get_whisperx_model`、`get_align_model`、`release_whisperx_models`、`transcribe_with_whisperx`、`transcribe_with_faster_whisper`、`transcribe_audio`、`get_whisper_model`、`get_asr_whisper_model`、`release_whisper_model`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/transcription/formatters.py](../../../gpu-worker/gpu_worker/transcription/formatters.py)、[gpu-worker/gpu_worker/transcription/punctuation.py](../../../gpu-worker/gpu_worker/transcription/punctuation.py)。
- 直接使用者：[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)、[gpu-worker/gpu_worker/transcription/chunked_transcription.py](../../../gpu-worker/gpu_worker/transcription/chunked_transcription.py)、[gpu-worker/tests/test_whisperx_oom_retry.py](../../../gpu-worker/tests/test_whisperx_oom_retry.py)。
- 处置：保留。

## `gpu-worker/gpu_worker`

### [gpu-worker/gpu_worker/ytdlp_cookies.py](../../../gpu-worker/gpu_worker/ytdlp_cookies.py)

独立 GPU 组件：GPU 下载使用的临时 cookiefile 副本；不得依赖云端 app/数据库/OSS key。

- 代码入口/类型：`disposable_cookiefile`。
- 直接使用者：[gpu-worker/gpu_worker/transcription/audio_extractor.py](../../../gpu-worker/gpu_worker/transcription/audio_extractor.py)。
- 处置：保留。

## `gpu-worker`

### [gpu-worker/pyproject.toml](../../../gpu-worker/pyproject.toml)

该 Python 组件的构建元数据或 lint/类型规则；具体节决定用途，不是顶层统一包。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/pytest.ini](../../../gpu-worker/pytest.ini)

pytest 收集范围、async/超时/marker 配置；测试运行器隐式读取。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/requirements-ci.txt](../../../gpu-worker/requirements-ci.txt)

该组件的依赖安装/约束/审计输入：requirements-ci.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [gpu-worker/requirements-dev.txt](../../../gpu-worker/requirements-dev.txt)

该组件的依赖安装/约束/审计输入：requirements-dev.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [gpu-worker/requirements.lock.txt](../../../gpu-worker/requirements.lock.txt)

该组件的依赖安装/约束/审计输入：requirements.lock.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [gpu-worker/requirements.txt](../../../gpu-worker/requirements.txt)

该组件的依赖安装/约束/审计输入：requirements.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `gpu-worker/scripts`

### [gpu-worker/scripts/gpu_worker_tunnel.ps1](../../../gpu-worker/scripts/gpu_worker_tunnel.ps1)

GPU 到云 broker 的受限隧道保活；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/scripts/lock_requirements.py](../../../gpu-worker/scripts/lock_requirements.py)

生成 GPU 运行依赖完整闭包锁；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/scripts/run_gpu_worker.ps1](../../../gpu-worker/scripts/run_gpu_worker.ps1)

加载 GPU 专属环境并启动其独立解释器；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [gpu-worker/scripts/start_gpu_worker.py](../../../gpu-worker/scripts/start_gpu_worker.py)

GPU 安全闸、心跳及 solo worker 启动；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[gpu-worker/gpu_worker/broker_recovery.py](../../../gpu-worker/gpu_worker/broker_recovery.py)、[gpu-worker/gpu_worker/broker_settings.py](../../../gpu-worker/gpu_worker/broker_settings.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/contracts.py](../../../gpu-worker/gpu_worker/contracts.py)、[gpu-worker/gpu_worker/logging.py](../../../gpu-worker/gpu_worker/logging.py)。
- 处置：保留。

## `gpu-worker/tests`

### [gpu-worker/tests/test_broker_settings.py](../../../gpu-worker/tests/test_broker_settings.py)

自动回归：GPU 私有在途消息命名空间。直接覆盖 broker_settings、celery_app。行为锚点：gpu_transport_keys_are_private_and_not_the_cloud_defaults；celery_app_closes_result_and_remote_control_channels。

- 代码入口/类型：`test_gpu_transport_keys_are_private_and_not_the_cloud_defaults`、`test_celery_app_closes_result_and_remote_control_channels`。
- 直接依赖：[gpu-worker/gpu_worker/broker_settings.py](../../../gpu-worker/gpu_worker/broker_settings.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [gpu-worker/tests/test_callback_delivery.py](../../../gpu-worker/tests/test_callback_delivery.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 __init__、tasks。行为锚点：TestCallbackDelivery；TestGpuTaskRetry。

- 代码入口/类型：`fake_httpx`、`TestCallbackDelivery`、`fake_transcription`、`TestGpuTaskRetry`。
- 直接依赖：[gpu-worker/gpu_worker/__init__.py](../../../gpu-worker/gpu_worker/__init__.py)、[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [gpu-worker/tests/test_contracts.py](../../../gpu-worker/tests/test_contracts.py)

自动回归：GPU 跨机任务名/队列/回调头/心跳契约常量。直接覆盖 __init__、celery_app、config、contracts、sources、tasks。行为锚点：TestTaskName；TestQueueRouting；TestHeartbeat；TestCallbackContract。

- 代码入口/类型：`TestTaskName`、`TestQueueRouting`、`TestHeartbeat`、`TestCallbackContract`、`TestVideoSourceEnum`。
- 直接依赖：[gpu-worker/gpu_worker/__init__.py](../../../gpu-worker/gpu_worker/__init__.py)、[gpu-worker/gpu_worker/celery_app.py](../../../gpu-worker/gpu_worker/celery_app.py)、[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/contracts.py](../../../gpu-worker/gpu_worker/contracts.py)、[gpu-worker/gpu_worker/sources.py](../../../gpu-worker/gpu_worker/sources.py)、[gpu-worker/gpu_worker/tasks.py](../../../gpu-worker/gpu_worker/tasks.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [gpu-worker/tests/test_security_guard.py](../../../gpu-worker/tests/test_security_guard.py)

自动回归：密码哈希/强度和 JWT 创建/解码。行为锚点：database_url_is_rejected；oss_credentials_are_rejected；clean_environment_starts。

- 代码入口/类型：`test_database_url_is_rejected`、`test_oss_credentials_are_rejected`、`test_clean_environment_starts`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [gpu-worker/tests/test_whisperx_oom_retry.py](../../../gpu-worker/tests/test_whisperx_oom_retry.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 config、__init__、formatters、whisper_model。行为锚点：TestIsOom；TestOomBatchLadder；TestClearCudaCache；TestTranscribeAudioRetry。

- 代码入口/类型：`TestIsOom`、`TestOomBatchLadder`、`TestClearCudaCache`、`TestTranscribeAudioRetry`、`TestSplitLongSegments`。
- 直接依赖：[gpu-worker/gpu_worker/config.py](../../../gpu-worker/gpu_worker/config.py)、[gpu-worker/gpu_worker/transcription/__init__.py](../../../gpu-worker/gpu_worker/transcription/__init__.py)、[gpu-worker/gpu_worker/transcription/formatters.py](../../../gpu-worker/gpu_worker/transcription/formatters.py)、[gpu-worker/gpu_worker/transcription/whisper_model.py](../../../gpu-worker/gpu_worker/transcription/whisper_model.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [gpu-worker/tests/test_whisperx_segmentation.py](../../../gpu-worker/tests/test_whisperx_segmentation.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 formatters、punctuation。行为锚点：TestWhisperxSegmentsToSubtitles；TestRestorePunctuation；TestWhisperSegmentsToSubtitles；TestWordsPreservation。

- 代码入口/类型：`TestWhisperxSegmentsToSubtitles`、`TestRestorePunctuation`、`MockSegment`、`TestWhisperSegmentsToSubtitles`、`TestWordsPreservation`、`TestMergeShortSegments`。
- 直接依赖：[gpu-worker/gpu_worker/transcription/formatters.py](../../../gpu-worker/gpu_worker/transcription/formatters.py)、[gpu-worker/gpu_worker/transcription/punctuation.py](../../../gpu-worker/gpu_worker/transcription/punctuation.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

## `logs`

### [logs/.gitkeep](../../../logs/.gitkeep)

保留空日志目录的版本占位；真实日志/会话文件忽略。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `.`

### [nginx.conf](../../../nginx.conf)

HTTP 反代装配，保留给本机/配置选择者；不能冒充生产 TLS 配置。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [nginx.ssl.conf](../../../nginx.ssl.conf)

TLS 反代、请求头、API/媒体路由与脱敏访问日志。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [progress.txt](../../../progress.txt)

简短历史进展与本轮追加；历史路径只作当时记录，不当当前入口。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [promtail.yml](../../../promtail.yml)

日志采集配置，只定义采集/转发目标，不证明生产已运行采集器。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `scripts/backup`

### [scripts/backup/README.md](../../../scripts/backup/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [scripts/backup/backup.sh](../../../scripts/backup/backup.sh)

备份 DB/媒体/配置并校验归档；不等于已有定时和异地计划；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [scripts/backup/restore.sh](../../../scripts/backup/restore.sh)

校验备份并向指定目标恢复；recreate/force 可破坏数据；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `scripts/isolation`

### [scripts/isolation/README.md](../../../scripts/isolation/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [scripts/isolation/gpu_stub_worker.py](../../../scripts/isolation/gpu_stub_worker.py)

隔离演练只用的轻量队列/回调桩，不加载 GPU 模型；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`StubArgs`、`build_app`、`main`。
- 直接依赖：[gpu-worker/gpu_worker/broker_recovery.py](../../../gpu-worker/gpu_worker/broker_recovery.py)、[gpu-worker/gpu_worker/broker_settings.py](../../../gpu-worker/gpu_worker/broker_settings.py)、[gpu-worker/gpu_worker/contracts.py](../../../gpu-worker/gpu_worker/contracts.py)。
- 处置：保留。

### [scripts/isolation/render_redis_acl.py](../../../scripts/isolation/render_redis_acl.py)

将无凭据 ACL 模板和环境口令合成实际权限文件；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`render`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [scripts/isolation/test_a07_redis_recovery.py](../../../scripts/isolation/test_a07_redis_recovery.py)

A07 独立容器/卷的 Redis AOF 与队列恢复演练，会重建隔离资源；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`render_acl`、`compose`、`CaseLog`、`redis_client`、`wait_redis`、`wipe_redis`、`persistence_info`、`wait_pg`、`t1_restart`、`t2_recreate`（其余见机器清单）。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/core/token_blacklist.py](../../../backend/app/core/token_blacklist.py)；其余 5 项见机器清单。
- 隐式入口：显式命令行演练/回归驱动，不由后端默认 tests/ 自动收集。
- 处置：更新必要说明/引用或生成路径。

### [scripts/isolation/test_a10_gpu_acl.py](../../../scripts/isolation/test_a10_gpu_acl.py)

A10 独立容器/桩 worker 的云端/GPU 权限演练，会重建隔离资源；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`SkippedCaseError`、`compose`、`CaseLog`、`render_acl`、`redis_client`、`wait_redis`、`wait_pg`、`start_worker`、`stop_worker`、`wait_heartbeat`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)。
- 隐式入口：显式命令行演练/回归驱动，不由后端默认 tests/ 自动收集。
- 处置：更新必要说明/引用或生成路径。
