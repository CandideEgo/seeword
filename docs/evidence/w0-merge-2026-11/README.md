# W0 分支合入与门禁归位（2026-11-09）

范围：把远端 `codex/slcs-v2`（SLCS v0.1）与本地 `claude/keen-gauss-4bfa7c`（性能优化）
合入 master，并让合并后的门禁回到全绿、迁移链回到单头。**未部署、未对业务库执行迁移。**

## 1 合入了什么

| 来源 | 内容 | 提交 |
| --- | --- | --- |
| `origin/codex/slcs-v2` | SLCS v0.1 学习包规范（`backend/app/slcs/`）、只读材料投影（`services/video_learning_material.py`）、参考包与设计文档 | fast-forward 到 `b26a5c30` |
| 本轮的 SLCS 修补 | 见 §2 | `7a56795d` |
| `claude/keen-gauss-4bfa7c` | 热路径 SELECT 合并、详情缓存、`/vocabulary/watch-context`、`pg_trgm` 索引、翻译批次并发 | `7f3c7537`（merge） |

## 2 SLCS 合入后修补的三件事

1. **`progress.txt` 的测试声明与代码不符**：原文写「73 项测试与 11 项 PostgreSQL 回归」，
   实测 `pytest tests/test_slcs.py` 收集 **23 项**、不含任何 PG 用例。已改为实测值并保留改正说明。
2. **两处契约缺口补上**：同一字幕段的同一组词只允许一条 `vocabulary`（两个释义争一段原文
   会使读者与已存修订都拿不到唯一答案；同一词跨段多语境仍合法，有正向用例）；
   指纹纳入 `FINGERPRINT_VERSION`（`slcs-pack-v1`）——契约变更时递增会让所有摘要显式失效，
   而不是悄悄改写没动过的包。
3. **兑现 README 给贡献者的承诺**：CI backend job 增加
   `python -m app.slcs validate ../docs/slcs/examples/welcome-to-wikisource.json`。

## 3 性能分支合并中的冲突与修正

三处冲突逐 hunk 定夺，**均以 master 的新事实为准**：

| 文件 | 冲突原因 | 处理 |
| --- | --- | --- |
| `backend/app/services/overview_service.py` | master 删了 `unlock_service.is_active_pro` 并加了 `MEANINGFUL_EVENT_TYPES` 过滤 | 保留 master 的过滤条件，把分支「事件日期只查一次、供累计与本周边活跃共用」移植到新结构 |
| `frontend/src/app/(admin)/admin/(shell)/stats/page.tsx` | master 删了「用户行为与权益分布」区块与方案分布图 | 按 master 保留；只接收分支的 recharts 按需加载（`StatsCharts` + `next/dynamic`） |
| `frontend/src/app/(main)/upgrade/page.tsx` | master 已删（会员链路下线），分支改过它 | 按删除处理，`git ls-files` 里已无该文件 |

合并本身引入/暴露的两处真实缺陷：

- **`backend/app/tasks/video_processing.py` 丢了 `import asyncio`**。master 曾删除该导入，
  三方合并取走了 master 的导入块，而分支新增的 `asyncio.TaskGroup` 并发翻译需要它——
  不补会让翻译路径 `NameError`。已补回。
- **`StatsPlanPieChart` 在 master 上已无消费者**（方案分布图随会员下线删除）。删掉该导出与
  `Pie`/`PieChart` 导入，不留死代码。
- **drift 门报红（6 条 trgm 索引）**：`c9d0e1f2a3b4` 只在 PostgreSQL 上用 `CREATE INDEX`
  建了 6 条 `gin_trgm_ops` 索引，模型没声明它们，`check_schema_drift.py` 因此报 6 条
  `remove_index`——CI 的 e2e job 会跑这个门，合并即红。处置：在 `Subtitle` / `Video` /
  `Channel` 的 `__table_args__` 里声明同名的 `postgresql_using="gin"` + `postgresql_ops`
  索引（SQLite 的 `create_all` 忽略这些方言参数）。**没有**加 `KNOWN_DRIFT` 豁免——仓规禁止
  为让检查变绿放宽门禁。修后 drift 门 `0 known / 0 new`。

迁移重挂：`c9d0e1f2a3b4` 的 `down_revision` 由 `b7c8d9e0f1a2` 改为 `c4a1b2c3d4e5`。
不改会与 `c8d9e0f1a2b3` 并列形成两个 head（脚本验证过）。

## 4 实际执行的检查

| 检查 | 结果 |
| --- | --- |
| `alembic heads` | **单行** `c9d0e1f2a3b4 (head)` |
| `git ls-files \| grep upgrade/page.tsx` | 无结果（已删除） |
| `grep -rn "isProUser\|plan_expires_at" frontend/src backend/app` | 无结果 |
| `ruff check app/ tests/` | 通过 |
| `ruff format --check app/ tests/` | **401 files already formatted** |
| mypy 基线门 | **0 新增**（实测 33 对，`.mypy-baseline` 36 行；有 3 对已可下调，本波不动） |
| 后端全量 `pytest tests -q -m "not integration"` | **1720 passed / 1 skipped / 62 deselected**，1399s，exit 0 |
| 后端定点（favorites / perf / listening / exams） | 46 passed |
| `pytest tests/test_slcs.py` | 26 passed |
| 前端 `npm run check` | exit 0（设计系统 + 会话写入 + tsc + eslint + prettier） |
| 前端 `npm run test:unit` | 40 文件 / **384 项**通过 |
| CLI `python -m app.slcs validate` | exit 0，`Valid SLCS 0.1.0: welcome-to-wikisource` |
| `alembic upgrade head`（本机 dev PostgreSQL） | 通过：`d4e5f6a7b8c9 → c4a1b2c3d4e5 → c9d0e1f2a3b4`，含 `pg_trgm` 索引 |
| `scripts/check_schema_drift.py` | **0 known / 0 new**（修 trgm 声明前是 6 条 new，见 §3） |

**未执行**：`measure_baseline.py --json` 的前后对比（需要迁移后的本机库与 dev 栈；
记住这条）。`-m integration`（需 `PG_TEST_URL` 隔离 PG）。e2e 全量。

## 5 刻意没合的两条依赖升级

`dependabot/npm_and_yarn/frontend/eslint-plugin-react-hooks-7.1.1` 试合后失败：
该版本把 React Compiler 规则并入 `recommended`，在现有代码上新增 **111 条错误**
（`set-state-in-effect` 89、`refs` 19、`immutability` 2、`purity` 1）。

按仓规不能为让检查变绿去裁剪规则集或加豁免，所以**整条撤出**（`git merge --abort`），
`package.json`/`package-lock.json` 回到 `^5.2.0`，`node_modules` 用 `npm ci` 复原。
这需要单独一片迁移工作：逐条判断是改代码（真正消除级联渲染）还是把个别用例改成豁免并写明理由。
gpu-worker 的 `celery@5.6.3` / `mpmath@1.4.1` 两条同样未合（需 GPU 机重装 venv + 转录回归）。

## 6 遗留

- 本机 `node_modules` 与 lockfile 已复原到 `eslint-plugin-react-hooks@5.2.0`；跑过一次
  `npm ci` 时因 dev server 占用文件报 EPERM，先按 `.claude/reference/kill-ports.md` 释放
  8000/3000 端口后成功。
- 生产仍是 8 天前的版本（会员页仍在），见计划 W4；本波未触碰生产。
