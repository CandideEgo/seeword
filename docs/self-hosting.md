# 自托管安装与升级

本页是源码自托管的唯一操作说明。根代码许可尚未转换、对外贡献接收尚未开放；当前以根 [LICENSE](../LICENSE) 为准，不把已选的 AGPL 方向当成生效授权。SLCS 独立包许可不变。P1–P5 本地工程、合成 smoke 均不等于权利、人工听校或正式阶段验收。

## 范围与前提

基础栈包含 PostgreSQL、持久化 Redis、API、前端、nginx、生命周期 Celery worker 和**独立 beat**。不带 GPU、模型、短信、官方语料、私人 ECDICT、原卷 PDF 或官方配置；课程基础阅读不依赖词典数据库。相关词典/试卷功能没有合法数据时不应当作可用。需要 Docker Compose v2（支持 `service_completed_successfully`）、足够的本机构建资源和 TLS 证书；手工工具使用 Python 3.12。

`docker-compose.selfhost.yml` 是独立入口，**不要与生产站的 `docker-compose.prod.yml`、开发或旧 testing smoke 合并**。以下命令在仓库根用 Bash/Git Bash 执行；Windows 的 Python 均加 `PYTHONUTF8=1`，使用 `backend/.venv/Scripts/python.exe`。这里展示操作，不授权对现有业务库、生产机或外部系统执行。

## 1. 配置、密钥与证书

将 `deploy/selfhost.env.example` 复制到仓库外，如 `$HOME/.seeword/selfhost.env`；不要复制官方 `.env`。配置文件含敏感数据，限制为当前运营者可读（Linux `chmod 600`；Windows 设置等价 ACL），不提交仓库、不贴日志。

分别运行三次 `openssl rand -hex 32`，给 `DB_PASSWORD`、`REDIS_PASSWORD`、`JWT_SECRET` 填入三个不同随机值。DB/Redis 密码建议仅用 hex，避免 URL 编码歧义。`ENV=production` 在模板固定，`LLM_ENABLED=false`、`CONTENT_PRODUCTION_ENABLED=false` 显式关闭可选能力；JWT 强度、显式 DB/Redis、生产短信 fake 禁止仍生效。遗留供应商凭据不会自动开启模型。

`SSL_CERT_DIR` 填仓库外**绝对路径**（Windows 用 `C:/...`），目录内需有 `fullchain.pem` 和 `privkey.pem`。本机演练可在该目录生成短期自签证书：

```bash
openssl req -x509 -nodes -newkey rsa:2048 -days 2 -subj '/CN=localhost' \
  -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1' \
  -keyout "$HOME/.seeword/tls/privkey.pem" -out "$HOME/.seeword/tls/fullchain.pem"
```

先创建目录；只在本机演练信任该证书，不关闭生产证书验证。模板仅发布 `127.0.0.1:19443`，DB/Redis/API/前端没有宿主端口。公网开放需要另行审查可信 TLS、域名、防火墙、备份及反代链；不能直接把回环地址改成公网当成安全部署。`SITE_URL`/`HTTPS_PORT` 和证书域名一致；`NEXT_PUBLIC_SITE_URL` 构建期固定，变更后重建前端。

## 2. 构建、迁移门与首启

```bash
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml build
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml up -d db redis
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml run --rm migrate
```

**每条命令成功后才继续**。`migrate` 调用 `entrypoint.sh migrate-only`，失败返回非零；随后 `check_schema_revision.py` 比较数据库实际 revision 集合与镜像迁移 heads，完全一致才通过。不要只看 `/health`，不要手工 `stamp head` 掩盖失败。

```bash
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml up -d --wait
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml exec -T backend python scripts/check_schema_revision.py
```

完整 `up` 的 API/worker/beat 还依赖 `migrate` 成功。三者均 `RUN_MIGRATIONS=0`，不能并发竞争迁移。worker 消费默认 `celery` 队列，beat 独立排程到期注销、媒体清理重试等；仅起 API 或仅起 worker 都不够。不要运行第二个 beat。持久卷保存 DB、Redis AOF 和 media；不要对真实自托管实例使用 `down --volumes`。

## 3. 首建管理员与密码用户

先核对专用库和 revision，再在交互终端运行：

```bash
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml run --rm --no-deps backend python scripts/create_admin.py --phone 13900000001 --prompt-password
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml run --rm --no-deps backend python scripts/create_admin.py --role user --phone 13900000002 --prompt-password
```

手机号须符合现有站内格式。示例号码只是占位，替换为运营者管理的真实账号标识；无短信时不会验证该号码所有权，运营者需用可信方式交付密码和确认身份。密码至少 8 字符，含大写、小写和数字，最多 72 个 UTF-8 字节；不截断、不提供默认密码。避免 `--password` 或明文环境变量进入命令行历史。无默认数据库回退，脚本不迁移、不导入语料。

重复执行默认不改密码；管理员角色只提升不降级。明确加 `--reset-password --prompt-password` 可重置并使旧会话失效；封禁或注销冷静期账号拒绝修改。用户在 `/login` 用密码登录，管理员走 `/admin/login`，会话相互独立。

基础模板没有短信凭据，短信注册/发码/重置路径会失败关闭，**不能启用固定验证码绕过**。运营者创建密码账号就是无短信的首建入口；如将来接真实短信，须单独提供自身签名、模板及凭据并验证真实失败路径，不使用官方默认签名冒充服务。

## 4. 课程包、审核与签名发布

默认 `SLCS_LESSONS_ENABLED=false`。本地演练先在仓库外生成课程发布专用 Ed25519 密钥：

```bash
PYTHONUTF8=1 backend/.venv/Scripts/python.exe backend/scripts/sign_lesson_receipt.py keygen \
  --out "$HOME/.seeword/lesson-signing/private.pem" --issuer selfhost-local --kid release-local
```

工具向 stderr 给出公钥环境配置。把 `SLCS_LESSON_RECEIPT_ISSUER` 和 `SLCS_LESSON_RECEIPT_PUBLIC_KEYS` 写入外部 selfhost.env；JSON 值用单引号包裹，PEM 的换行保留为 JSON `\n`。仅公钥传入 API。设置 `SLCS_LESSONS_ENABLED=true`，需要课程收词再设 `SLCS_VOCABULARY_ENABLED=true`；重建容器让 API/worker/beat 读取相同配置，不需模型凭据。课程试点门、教学/V2 门和管理员内容门不是一回事。

1. 在 `/admin/lessons` 导入合法 `schema_version=0.1.0` 学习包作为候选；后续纠错导入新修订并查看 diff，不覆盖旧版。
2. 按媒体/字幕/译文/词汇记录出处与权利，分别核对站内展示、模型处理、外部分发用途。页面审核中记录真实依据、核对方法、限制；合成演练标为测试，未知人工工时不填假值。
3. 核对目标 `lesson_id`、`revision_id`、包指纹、指纹版本与 `review_sha256`。只有对应审核的短期签名收据才能发布。签名不代替内容核验。
4. 签发工具只读 DB，私钥不挂进长期 API/worker。可在运营者单次容器中只读挂载仓库外的**专用密钥目录**：

```bash
docker compose --env-file "$HOME/.seeword/selfhost.env" -f docker-compose.selfhost.yml run --rm --no-deps \
  -v "$HOME/.seeword/lesson-signing:/run/lesson-signing:ro" --entrypoint python backend \
  scripts/sign_lesson_receipt.py sign --private-key /run/lesson-signing/private.pem \
  --issuer selfhost-local --kid release-local --lesson-id YOUR_LESSON --revision-id YOUR_REVISION
```

stderr 是待比对声明，stdout 仅 JWT。确认吻合后在管理端粘贴收据并显式发布；不把收据、私钥或连接口令放进仓库。默认收据 600 秒，站点最长 900 秒。撤回停止正文提供但保留个人事实；恢复须先重新审核，再新签收据，撤回前旧审核/旧未用收据均不能恢复。回退到另一个已发布修订是显式 CAS 操作，不静默替换学习者的固定引用。

合成夹具可从 `backend/scripts/smoke_selfhost.py::synthetic_pack()` 复用；来源 `example.invalid` 仅标识测试，不会播放或下载外部媒体。真实素材仍需独立权利、听校与人工证据。

## 5. 无模型与可选生产能力

关闭 `LLM_ENABLED` 时，模型出口（含已有缓存客户端、翻译和教学网关）明确拒绝，不伪造评分或掌握事实。关闭 `CONTENT_PRODUCTION_ENABLED` 时，视频/GPU/首页草稿生产派发与执行停止；持久派发意图保留待后续处理，不把开关当 exactly-once 或撤销已发往独立 GPU 的消息。切换前应排空/隔离独立 GPU 队列并停 worker；已披露给外部系统的数据不能由开关收回。手工课程导入/审核/签名发布不受该 AI 生产开关阻断。

模型与视频生产都不是基础安装必需。以后显式开启相应能力时，原生产安全要求仍在：模型凭据、GPU 回调密钥、完整 head → 独立 GPU → callback → tail、合法数据及持久派发。GPU 不在 API 镜像，本模板不自动起它；部署拓扑认 [GPU worker](../gpu-worker/README.md)。教学模型还必须走独立验收过的网关治理，不能仅因 `LLM_ENABLED=true` 绕过额度、用途或用户授权。本模板没有复制官方连接配置，也不附授予这些能力的安全验收。

## 6. 升级与备份

先备份 PostgreSQL（连同迁移 revision）、media 和外部配置/密钥，验证恢复过程，记录代码 commit 与镜像。停 API/worker/beat，避免旧代码写入新 schema；DB/Redis 可保留运行。重建新镜像，再执行第 2 节的 `run --rm migrate`，**非零立即停止**；核对实际 revision 与新镜像 heads 后再启动所有服务。自托管 compose 固定让迁移门先完成，不以健康端点代替 schema 核验。

本页不提供自动降级、清库或删除历史迁移。失败时保持停服并分析，按已验证的备份恢复方案人工处理；不要混跑不兼容的新旧镜像。

## 7. Localhost production smoke

旧 `docker-compose.smoke.yml` / `frontend/scripts/production-smoke.ps1` 使用 testing 与短信 fake，是旧 e2e 环境，**不能证明无模型 production 基础模式**。新入口：

```bash
PYTHONUTF8=1 backend/.venv/Scripts/python.exe backend/scripts/smoke_selfhost.py --confirm-isolated-stack
```

这条命令会实际构建镜像、起服务并迁移**新生成的可丢弃库**，仅在你明确要演练时执行。脚本拒绝远程 Docker context；自动生成随机 Docker project/DB/独立凭据和仓库外短期 TLS/课程公钥，不接受已有数据库 URL、官方配置或外部站点。仅监听 localhost，可用 `--port` 选择空闲端口。使用完在 finally 仅移除本次随机 project 及其卷，不碰真实实例；若进程被强杀，按输出的随机 project 精确清理，不使用真实实例的项目名。

脚本串行构建后端与前端镜像以限制峰值内存，再验证 migration heads、production 密码登录、匿名拒绝、关闭能力拒绝、合成包导入/用途审核/签名发布、固定修订阅读/进度、真实 worker 本人 ZIP 导出和一次性下载、独立 beat+worker 到期注销。仅对合成测试用户加速到期时间，beat 仅本次演练将清理排程改为 5 秒；不改正式 30 天政策、不使用 Celery eager 或直接调用任务体代替 worker。合成演练不证明真实视频播放、私人词典、正式考试或界面体验。

脚本存在和单测通过都不等于已执行；实际运行结果、真实浏览器检查与人工证据分别进入已有 [验收卡](evidence/open-learning/acceptance-cards.md)，不另建平行验收文档。

## 8. 版本与接入支持边界

| 层                  | 当前契约                                               | 不能据此宣称                            |
| ------------------- | ------------------------------------------------------ | --------------------------------------- |
| 学习包              | `schema_version=0.1.0`，未知版本/字段/重复键拒绝       | 支持未来包版本                          |
| 内容指纹            | `slcs-pack-v1`，段/有序词锚点固定修订                  | 不同正文自动重定位兼容                  |
| 独立读取器          | 源码包版本 `0.1.0`，CLI 与可选本地 stdio MCP           | 多个历史发行版已交叉兼容                |
| 站内 HTTP           | 既有 `/api/v1/lessons` 与固定修订路径；JWT 本人授权    | 匿名获取或用途自动扩展                  |
| 在线外部 HTTP / MCP | 实验性，独立 token/scope、用途和资源授权；默认开关关闭 | 默认给旧连接新增权限、正式 API 稳定承诺 |

在线接入的输入／输出、凭据、scope、用途、幂等与确认边界认[实验性学习接口](open-learning/api.md)，框架事实仍只在[架构](project-audit/architecture.md)维护；独立 wheel 安装、CLI/MCP 一致性验证按 [SLCS 说明](slcs/README.md) 与发行 CI 执行。网站测试不能冒充 wheel/site-packages 验证，单一源码版本测试也不能冒充多发行版兼容证据。
