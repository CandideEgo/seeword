# 本轮验证与边界

日期：2026-11-14（北京时间）。基线 `a93979c3`，所有结果来自本轮本机实际运行，不继承旧 CI/截图的通过状态。机器结果见 [检查摘要](checks/results.json)、[全量覆盖检查](checks/coverage.json)、[风险探针](checks/risk-probes.json)。

## 已完成

| 检查 | 实际结果 | 证明范围 |
| --- | --- | --- |
| 全量文件/目录覆盖、清理恢复哈希、保留组/许可/迁移、链接 | 见 coverage.json 的本轮最终计数与 passed | 基线每个路径恰有记录；恢复副本原字节可找回；当前文档链接有效；不是所有业务都无缺陷 |
| 后端全量非集成 pytest | **1,790 passed，68 deselected，64 warnings**；33 分 56 秒 | 内存 SQLite/fake Redis 的全部非 integration 回归；不是 PG 事务证明 |
| 最终文件状态的定向后端回归 | **133 passed，4 warnings** | 架构不变量、维护脚本、模型 provider、GPU 回调、响应契约；与全量有重复，不能相加成独立覆盖数 |
| 后端 ruff app/tests/scripts | 通过 | 扩展到 scripts；发现的 5 个无用导入已删，ORM 注册副作用 import 保留并标记 |
| 后端 ruff format app/tests | 418 个文件已符合 | 没有放宽 formatter 或原检查范围 |
| mypy baseline | 通过“不新增”门；原始 exit=1，33 个 file:code 对，基线 36 对，新增 0 | 仍有存量类型问题，不是 mypy 零错误；没有修改基线 |
| Bandit 中/高危静态扫描 | exit=0 | 当前扫描规则未报中/高危，不证明没有安全风险 |
| 前端 npm run check | 审查修正后再次通过 | 设计/会话、tsc、ESLint、Prettier；没有放宽规则 |
| 前端 Vitest | **42 文件、393 项通过** | node 环境纯规则/工具回归；不是浏览器回归 |
| 前端生产 build | 通过，Next 16.4.3，44 个静态生成项 | 入口/资源/类型与编译装配有效；未部署生产 |
| Playwright --list | **45 文件、779 项可收集** | 只证明测试能解析收集，**不是 779 项通过** |
| GPU ruff/format | 通过；26 文件符合格式 | 修正一个原有换行格式差异，业务 AST 未变 |
| GPU 轻量 pytest | **68 项通过** | 复用本机 backend 解释器的兼容依赖、mock 模型/网络；本机没有独立 GPU venv，未启动真实 worker |
| 网关 adapter 单测 | **27 项通过** | 合成上游、输入/usage/签名边界 |
| 实际 loopback 收据链路 | 2 条 PASS | 实际 HTTP 签发→后端公钥验签；未授权/篡改模型族拒绝；没有真实 provider/业务 DB |
| SLCS 独立安装制品 | **11 passed，1 skipped** | 新建隔离 venv、安装实际 wheel 与锁定 MCP extra、pip check；原仓套件中仅发行树专用断言按条件 skip |
| SLCS 公开发行树 | **12 项全部通过** | 重建公开树、安装该树的 wheel，验证包括实际 site-packages 导入；不是用源码包假通过 |
| SLCS SHA256SUMS | **28/28 一致** | 最小规范/Schema/示例仍能组成可验证制品；没有发布外部仓库 |
| Python/TS 语义与 YAML 对照 | 通过允许差异核对 | UI 源码 AST 不变；迁移执行 AST 不变；CI/生产 Compose 内容语义不变；非注释差异限工具输出路径、未用 import 和测试安全提示 |
| 源码/工具语法及 git diff --check | 通过 | 无补丁空白错误；不等于全系统运行通过 |

全量后端运行期间的后续改动限说明、输出路径和上述静态卫生；最终又运行了相关定向回归。测试 warnings 主要来自结构化日志异常渲染提示，未屏蔽或修改门禁来消除它们。

## 风险探针不是“已经修复”

- R02：替换 Redis 连接为合成异常，运行真实撤销/消费函数，观察拒绝结果为 false、消费允许为 true；没有使用真实 token 或网络。
- R01：真实回调 handler 面对一个当前 processing 的合成行和旧结果文本，仍会转 ready_subtitles 并写字幕。锁、质量门通过前提、持久化和派发用替身；这是证明“没有代次可辨认”的规则接缝，不是实际 PG/多机竞争复现。
- 这些探针揭示原业务行为，不把问题复现当期望功能测试，也未在本轮改写业务解决它们。

## 独立审查与接力修正

按项目要求做了一轮最强可用 Opus 模型的只读独立 review。核实并修正三项：

1. Python 导入索引改按组件/脚本运行根解析 bare import，修复 adapter 的同名 app 误指向业务包，并补上 app→content_receipts、测试/HTTP 工具→adapter 等真实关系。
2. 四个仍会写旧 docs/evidence 的 e2e 输出统一移到忽略的 tmp/e2e-evidence，保留全部测试断言；截图工具和隔离 probe 也写 tmp。
3. 图标先按二进制/metadata 分类，不再误报成 UI 代码。favicon/icon/apple-icon 登记 Next 隐式入口；另两个连字符命名文件仅作备用导出，未冒称已接线。

覆盖检查为这些问题增加明确断言；修正后复验静态门、测试收集、精确引用和资源分类。未无必要重复做第二轮模型审查。

## 没有执行、不能声称通过的检查

| 项 | 本轮原因/边界 |
| --- | --- |
| 68 项 PostgreSQL integration、真实迁移/并发、完整生产 smoke | 本次 docker info 找不到 Docker Desktop Linux engine pipe；没有新建专用 PG，不用业务库替代。这只描述本轮探测，不反推历史 Docker 故障原因 |
| 完整 Playwright 执行与人工浏览器视觉/交互验收 | 本轮未改产品 UI/交互，TS AST 对照确认可见代码仅注释变化；e2e 改的是证据输出和安全诊断。没有用 --list、build 或历史截图冒充实页验收，也没有因浏览器安装问题跳过已承诺的页面改动验收 |
| 真实 GPU 转录、模型精度/吞吐、远程 broker/隧道 | 本机无 GPU worker 独立环境；轻量单测不证明硬件或云端生产链路 |
| 真实模型、真实账单/预算治理、四宿主 MCP | 未授权触发真实外部调用；合成签名/协议测试不能代替这些出口 |
| 在线 pip-audit 漏洞库刷新/完整供应链二进制审计 | 本轮未重新查询外部漏洞/许可事实；P0 许可材料原样保留为当时证据，不外推为当前全部安全。现有豁免/检查器未改 |
| 覆盖率 60% 的 CI 硬门 | 本轮 pytest 未带覆盖率参数；测试通过数不能替代该门 |
| 生产 commit、alembic_version、实际备份恢复、已部署配置 | 本轮没有访问生产、执行部署、业务库迁移或恢复；不写“线上已完成” |

## 清理的精确含义

- Git 起点的 **1,337 个旧路径移出**；另有 **151 个未入库旧证据文件**一起隔离；共 **1,488 份原字节副本**留在本机 `tmp/project-audit-recovery/`。
- 一个活收据演练配置迁到 deploy/v2-gateway；最新保留组 26 个文件，其中只为 3 份 Markdown 更新了入口，原始 JSON/图片/会话记录未改。
- **没有永久删除恢复区，没有释放这部分磁盘，没有改写 Git 历史，也没有提交/push。** 未入库项不能靠 Git 恢复，须保留本地副本。
- 恢复按 cleanup-manifest 的 recovery_path 逐项检查后移动；不要覆盖本轮新文件或对整个仓库 reset/clean。
- 原始检查日志在忽略的 tmp/project-audit；checks/results.json 保存结果与日志 SHA-256，便于对照，而不是把长日志复制回文档库。
- 保留 P0/Astryx 原文中若干 log 链接只在本机存在，始终没有入 Git；coverage.json 单列这些链接，不能声称干净 clone 自带历史日志。
