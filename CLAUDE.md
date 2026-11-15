# SeeWord 项目工作规则

SeeWord 是视频、双语字幕点读、词汇复习与试卷学习站。当前框架和链路只在 [架构说明](docs/project-audit/architecture.md) 维护；新人从 [项目审计](docs/project-audit/README.md) 进入。当前产品讨论基线是 [开源开发大纲](docs/seeword-open-source-development-outline-2026-11-13.md)；本轮已授权 P1–P5 分阶段本地工程，具体边界认 [P0 工作记录](docs/open-learning/p0-worklog.md)。P0 与阶段正式验收尚未通过，工程完成不能代替权利、人工与独立验收证据。

## 入口与运行边界

| 目录 | 局部规则/运行说明 |
| --- | --- |
| `backend/` | [后端规则](backend/CLAUDE.md) |
| `frontend/` | [前端规则](frontend/CLAUDE.md) |
| `gpu-worker/` | [独立 GPU worker](gpu-worker/README.md) |
| `backend/slcs/` | [独立读取器](backend/slcs/README.md)、[数据规范](docs/slcs/README.md) |
| `deploy/v2-gateway/` | [候选模型网关](deploy/v2-gateway/README.md) |

根目录没有 package.json 或 Makefile。Python 3.12；中文 Windows 的 Python 命令带 `PYTHONUTF8=1`，后端显式使用 `backend/.venv/Scripts/python.exe`，GPU 机器使用自己的环境，不能假设本机已安装 GPU 栈。

- 启动/重启开发服务优先 `/dev`，停止优先 `/dev-stop`；具体流程只在 `.claude/skills/` 维护。
- `Start-Redesign.ps1` 仍是轻量 API + 前端 + DB/Redis 入口，不起 Celery/GPU/beat。
- worker 不等于 beat；需要周期调度时必须单独启动 beat。GPU worker 不运行在后端镜像中。
- 部署只在用户明确授权后用 `/deploy`；本机构建 amd64 镜像再上传，不在小规格生产机就地构建。
- 真实主机/凭据文件位置查本机 `~/.seeword/ACCESS.md`，不把密码、私钥、token 写入仓库或报告。

## 改动前必须保持的边界

- 错误 envelope `{code, message, detail?}` 与 `frontend/src/lib/createApiClient.ts` 成对修改；AI 不可用不能伪造零分。
- HTTP、媒体/PDF/WS 的身份校验复用 `backend/app/api/dependencies.py`；`?token=` 走 `resolve_token_user`。前端 proxy 只检查镜像 cookie 存在，不能当授权。
- 新密码至少 8 位、最多 72 个 UTF-8 字节。校验/哈希不得静默截断；历史密码比对兼容认 `core/security.py`。
- 用户和管理员各有独立 token/store/API 实例。会话写入只经 `frontend/src/lib/authHelpers.ts`。
- 视频生产只有管理员/catalog 入口。保留 head → 独立 GPU → callback → tail 与持久派发意图；GPU 旧任务名是兼容契约，不能当失效 import 改名。
- 任务可能重投，不能把 Redis 锁或 outbox 当 exactly-once；重要学习事实与业务写入同事务。新拆分不得无意改变 commit/rollback 所有权。
- 首页的草稿、不可变发布版本、布局分开；字幕指纹控制失效，不给每个字幕写入口另挂同义钩子。
- 正式考试/听力服务端判分、冻结题面、重复提交重放；模型建议不能变成正式成绩或掌握事实。
- 课程引用固定修订和段/词锚点；撤回按当前权限投影，不静默换材料。SLCS 课程收据与教学核验收据是两套 audience/配置，私钥在仓库外。
- `backend/slcs` 不 import `app.*`；改独立包要构建并安装 wheel 测试。另一个发行仓库不会自动同步，本轮授权不覆盖发布它。
- models 必须在 `app/models/__init__.py` 注册；不删除历史迁移来假装回退数据库。功能开关不是 schema 隔离。

## 试点和退役功能

`TEACHING_*`、`MCP_*`、`SLCS_*` 默认关闭。代码已存在不等于已验收/上线；每次涉及部署都重新核对真实 commit、revision、凭据与任务。本地代码审计不能断言生产状态。

用户 V2 入口受 `v2_access` 控制；`/admin/teaching-content` 只受管理员鉴权；`/admin/lessons` 还要通过课程开关和表检查。不能把这些门混为一谈。关开关不能让当前考试 ORM 在 V2 迁移前的数据库上正常工作。

跟读、成就、热力图、周报、里程碑等旧入口由 `retired_features` 返回 410，是兼容壳。会员收费链路已全部删除（端点、页面、任务、配置、表），全站对登录用户免费，**不恢复收费、解锁额度或退役功能**。历史迁移/录音文件/成就表仍可能存在，不代表入口应复活。

## 常驻原则

- 中文沟通。代码是事实源；先验证再下结论，未执行的检查如实写明。
- 永不为变绿而放宽检查器、基线或豁免，尤其 `.mypy-baseline`、`.pip-audit-ignore`、`check-design-system.mjs`。
- 一个事实只放一个家。不要重建旧方案、过程记录和截图的大量平行文档；本轮保留组及审计交付见 `docs/project-audit/`。
- 用户授权限于当前任务，不延伸到生产、额外系统、发布或不可逆操作。高影响改动先查消费者和退路。
- 优先复用成熟实现，不重复造轮子；不做过度开发，以用户体验为第一性原理。
- 前端质感与丝滑动效是核心要求。实际浏览器走查用 `ego-browser` skill，先启动服务再打开、点击、读取；不得因 Playwright 环境问题跳过应做的浏览器验证。自动化 e2e 与人工浏览器走查不能互替。
- UI 默认不加 slogan、冗余标签、说明段落和重复微文案；靠层级、布局、间距与清楚的主操作解释。必要说明优先 info + tooltip，但表单标签、可访问名称、危险操作后果提示必须保留。初次使用者应看得懂下一步。
- 较大代码改动最终交付前，派一次当前最强可用模型的独立子代理 review，主代理核实、修复有效问题并重测；不无必要重复复审。
- 有实质进展时，根 `progress.txt` 追加 `YYYY-MM-DD HH:mm（北京时间）| 工作概要`。

`AGENTS.md` 只是入口；`.agents/` 是本地镜像，不是规则源。旧知识层和旧审计/蓝图说明已清理，源码中的 `INV-*` 认活测试/检查器，不找已经删除的编号清单。
