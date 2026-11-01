# 加载/处理速度优化 · 实施与实测记录（2026-11）

日期：2026-11-01。需求：「代码审查优化，提升所有的加载/处理速度」。
环境：Windows 11；`backend/.venv`（Python 3.12.10）；本机开发 Postgres 16 / Redis 7
（`speaking-db-1` / `speaking-redis-1`）。**未接触生产，未修改运行中的开发栈进程**：
基线 A/B 用 `git archive HEAD` 导出的同一提交源码跑在同一台开发库上，改动后代码在
worktree 里按同一输入跑，两边只差本次改动。

## 1 改了什么

| 面 | 位置 | 改动 |
| --- | --- | --- |
| 观看页详情 | `backend/app/services/video_service.py` | 详情缓存命中不再读字幕行；首看学习记录改 `INSERT … ON CONFLICT DO NOTHING`（去掉每次观看的行锁探测） |
| 首页 overview | `backend/app/services/overview_service.py`、`exam_service.py`、`vocabulary_service.py`、`study_time_service.py` | 20 条 SELECT 合并为 9 条；观看时长在 Postgres 侧按本地日分桶（只回 ≤7 行） |
| 观看页收藏/笔记 | `backend/app/api/v1/favorites.py` | `watch-meta` 3 条查询 → 1 条 |
| 搜索索引 | `backend/migrations/versions/c9d0e1f2a3b4_perf_search_indexes.py` | `pg_trgm` + GIN（字幕中英、视频标题/标签、频道名）与两条复合 btree |
| 首页请求 | `frontend/src/hooks/useContinueLearning.ts`、`lib/channelSubscriptions.ts`、`lib/sharedRequest.ts` | 「继续学习」与「订阅频道」各只发一次请求（模块级共享请求） |
| 观看页词表 | `backend/app/api/v1/vocabulary.py`、`frontend/src/hooks/useWatchVocabulary.ts` | 新增 `GET /vocabulary/watch-context`，3 个请求 → 1 个 |
| 打包 | `frontend/src/components/admin/StatsCharts.tsx`、`app/(main)/upgrade/page.tsx` | recharts 与 qrcode 按需动态加载 |
| 管线 | `backend/app/tasks/video_processing.py` | 翻译批次按 `TRANSLATION_BATCH_CONCURRENCY`（默认 2）并发，缺失条目的补译分组并发 |

## 2 实测（同一开发库、同一用户/数据，HEAD 与改动后各跑一遍）

基准脚本：直接调用服务层函数、监听 `before_cursor_execute` 统计 SELECT 数，
各 10 次取中位数。**HEAD 源码**由 `git archive HEAD` 导出到临时目录后以同一
`PYTHONPATH` 运行。

### 2.1 `/users/me/overview`（首页右栏，每次首页加载）

| 指标 | HEAD | 改动后 |
| --- | --- | --- |
| SELECT / 次 | 20 | **9** |
| 中位耗时 | 68.13 ms | **33.23 ms** |
| 最小耗时 | 65.48 ms | 31.60 ms |

### 2.2 观看页详情 `/videos/{id}`（匿名，800 条字幕）

HEAD 会先读完 800 行字幕（含 `word_levels` / 逐词时间戳 JSON），再因为未登录而
把它们丢掉。同一事务内插入 800 行后各调用 10 次（每轮 `expunge_all()` 强制重查），
结束回滚，库内不留数据。

| 指标 | HEAD | 改动后 |
| --- | --- | --- |
| 中位耗时 | 43.72 ms | **3.28 ms** |
| 最小耗时 | 39.80 ms | 2.75 ms |

登录且已缓存的路径同理：HEAD 的缓存命中仍会执行字幕查询。

### 2.3 字幕行读取本身（Postgres，800 行）

`select(Video).options(selectinload(subtitles))` 对比仅取视频：

| 指标 | 带字幕 | 仅元数据 |
| --- | --- | --- |
| 中位耗时 | 48.27 ms | **8.11 ms** |
| 最小耗时 | 39.90 ms | 6.49 ms |

### 2.4 `pg_trgm` 索引（200,000 行合成表，事务内建表并回滚）

```sql
-- 无索引
Seq Scan on perf_subtitles ... Execution Time: 260.558 ms
-- CREATE INDEX ... USING gin (text_en gin_trgm_ops) 后
Bitmap Heap Scan on perf_subtitles ... Execution Time: 68.166 ms
```

迁移里的建索引语句也在真实 `subtitles` 表上以 `BEGIN … ROLLBACK` 验证过（扩展与
GIN 索引均可创建，`pg_indexes` 可见），未在开发库留下对象。

### 2.5 Postgres 专用分支与旧实现的等价性

在开发库上以事务内造数、结束回滚（不落库）的方式逐项对照：

| 检查 | 结果 |
| --- | --- |
| `watch_seconds_by_local_day`（SQL 本地日分桶 vs 旧 Python 分桶；4 条事件跨本地午夜，覆盖 2 个本地日） | 完全一致 |
| `exam_stats`（单条 FILTER 查询 vs 旧 3 条查询） | 四字段完全一致 |
| `INSERT … ON CONFLICT DO NOTHING`（连续两次，断言第二次不插入、不抛错） | 通过 |

## 3 门禁

| 检查 | 结果 |
| --- | --- |
| 后端全量 `pytest tests/ -q` | **1497 passed, 23 skipped**（18m10s） |
| 新增 `tests/test_perf_hot_paths.py` | 4 passed（缓存命中不查字幕、首看只建一条记录、overview ≤11 SELECT、watch-context 分组） |
| `ruff check app/` | 通过 |
| 前端 `npm run check` | 设计系统 9 条、会话写入 2 条、`tsc --noEmit`、ESLint、Prettier 全部通过 |
| 前端 `npm run test:unit` | 375 passed（另新增 `sharedRequest.test.ts` 5 条，共 380） |

## 4 未执行 / 未覆盖

- **浏览器端到端核对未执行**：本机 :3000/:8000 跑的是**未改动的基线**（主检出），
  Next 的 dev 代理写死指向 127.0.0.1:8000；要在浏览器里验证改动后的前端与
  `watch-context`，需要一个已登录会话，而本会话的凭据策略拒绝了从开发库签发
  token 的操作。因此请求数合并（首页 `subscriptions` 2→1、`learning` 2→1、
  观看页词表 3→1）只由代码与 `sharedRequest` 单测证明，未做浏览器抓包。
- **生产构建未能在本 worktree 执行**：worktree 的 `frontend/node_modules` 是指向主检出的
  junction，Turbopack 以「files outside of the workspace root are not compiled」拒绝解析
  `next/package.json`（在任何模块编译之前就失败）。这是 worktree 环境产物，不是本次改动
  的结果；`tsc --noEmit`、ESLint、Prettier、380 条单测与 `npm run check` 均通过。
- **生产规模数据未测**：开发库只有 7 条字幕、2 个视频，真实 p95 与索引收益需要
  生产量级数据；2.4 的合成表只证明计划形态，不代表线上数字。
- **GPU 转录并发未动**：`whisper_max_concurrent_chunks` 在分块循环里实际未生效
  （循环内串行 await），单卡并发有显存与对齐质量风险，需要单独设计与压测。
