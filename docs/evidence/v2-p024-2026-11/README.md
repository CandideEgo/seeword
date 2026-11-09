# P02.4 四题小测与统一命令层（2026-11-09）

范围：把「已核验材料 → 冻结四题小测 → 按钮与卡片走同一命令层 → 原位反馈 →
幂等与正式测评边界」做成可验证切片。**全程不调用模型、不新增表、不新增迁移。**

## 1 为什么没有新表

小测 = 一个 `TeachingSession` 里的 4 个 `TeachingItem`。既有投影已经按 item 遍历出卡、
`_prepare` 已经按 `item_id` 定位并校验 `expected_revision`，所以缺的只是「一次建四道」
的创建路径。作答数、正确数、揭晓状态全部从 `teaching_attempts`、`user_question_disclosures`、
`item.state` 投影——没有第二个成绩账本。

幂等同样复用 `TeachingOperation` 的 `(user_id, operation_namespace, operation_id)` 唯一键与
`request_hash`；命令层把调用方的 `operation_id` 原样透传，不新增计数器。

## 2 落点

| 文件 | 作用 |
| --- | --- |
| `backend/app/services/teaching/service.py::create_quiz` | 按 `paper_id` 或显式 `revision_ids` 冻结 4 道 `auto_verified` 且来源仍可用的题；去重、不足 4 道即 422 |
| 同文件 `project_session` | 逐题 `answered/correct`，多题时追加 `progress` 卡（`answered/correct/total/item_ids`） |
| `backend/app/services/teaching/commands.py` | 唯一写入口，6 个动作分派到既有领域服务；只接受 `user_ui` |
| `backend/app/api/v1/teaching.py` | 新增 `POST /teaching/quizzes`、`POST /teaching/sessions/{id}/actions` |
| `backend/scripts/grant_teaching_access.py` | `TeachingAccessGrant` 此前**没有写入路径**（只有 env 白名单），补 `--phone/--revoke/--list` |
| `backend/scripts/seed_teaching_quiz.py` | 复用 `tests/teaching_fixtures.py` 的合成素材播种（脚本内不含候选构造器副本） |
| `frontend/src/components/teaching/TeachingQuiz.tsx` | 多题时的「已答 n/总」切换条；单题会话不渲染 |
| `frontend/src/components/teaching/TeachingWorkspace.tsx` | 6 个写调用点全部改走 `/actions`，删除 5 条直连分支 |
| 同文件 | 「正在看第几题」是客户端状态；提交后自动前进到下一道未回答的题 |
| `frontend/src/components/teaching/TeachingCatalog.tsx` | `/practice` 目录按试卷聚合出「四题小测」入口 |

## 3 可见性口径（复用，不是新规则）

`answered` / `correct` / `progress` 与答案历史用**同一条** `answer_history_visible`：
只读外部 scope（`teaching:read`）看不到，避免「猜一次、看正确数是否 +1」这种答案 oracle。
`test_progress_hidden_where_answer_history_is_hidden` 钉住它。

## 4 独立 review 发现并已修复的四类缺陷

一次独立 review（真实 pytest 复现）指出的问题，全部已修并补回归：

| # | 级别 | 问题 | 处理 |
| --- | --- | --- | --- |
| 1 | blocker | 四题小测与固定「≤8 张卡」上限冲突：4 题基线 5 张，两题看解析 → 9 张 → 第二次 reveal 409；四题各看提示 → 8 张 → `complete` 每次 409，换 revision 重试也一样，会话永久停在 `active` | 卡片上限按题数推导 `max(8, 4*n+2)`，响应模型 `max_length` 同步 |
| 2 | blocker | 「结束本次」从网页不可达：前端发 `{action:"complete", action:"abandon"}`，扁平 body 让两个 action 互相覆盖 → 422 | `abandon` 成为独立命令；`SessionActionRequest` 增该取值，命令层据此构造 `CompleteSession` |
| 3 | high | `paper_id` 路径要求整卷**恰好** 4 道已核验题；真实四级卷是 10 或 30 道，一律 422 | 按**题目编号**取前 4（`question_key` 是字符串，`":"` 排序会把第 100 题排到第 46 题前）；扫描模式跳过已撤回/来源失效的题，显式列表模式报错；合法题不足 4 道仍 422，不建「3 题小测」 |
| 4 | high | `attempts` 列表跨题混排，工作台「第 N 次作答」面板显示的是别的题的作答 | 按当前 `item_id` 过滤，提交按钮文案也按本题判断 |
| 5 | medium | 答完自动前进从第 0 题开始找，会跳回已答过的题 | 从当前题之后开始、环状回绕 |
| 6 | low | `quizProgressLabel` 是死代码，同一事实三处 | 删除；前端用 `items` 自行计算 |

另修一处**门禁遗漏**：新增测试文件有 14 处 `RUF059` + 1 处 `I001`，此前只跑了
`ruff check app/` 没跑 `tests/`。已清，`ruff check app/ tests/` 全绿。

## 5 实现过程中自己引入并修复的缺陷

1. **`project_session` 在 `attempt_limit` 读回空行集时崩溃**：学习上下文固定传
   `attempt_limit=5`，而 `rows[0]` 在空集上抛 `IndexError`，会让教学 run 与旧聊天读路径
   500。**这是本轮引入的回归**，全量套件表现为 20 failed；修复后回到 0 failed，并补
   `test_limited_attempt_read_keeps_progress_consistent`。
2. 切换按钮原为 36px 高，低于本仓 40px 可点门槛（`frontend/CLAUDE.md` 的审计门），改 40。

## 6 实际执行的检查

| 检查 | 结果 |
| --- | --- |
| `pytest tests/test_teaching_quiz.py` | **20 passed**（含四题全揭示仍可结束、abandon 独立命令、试卷取前四题三条新回归） |
| 隔离 PG `pytest tests/test_teaching_quiz_pg.py` | **2 passed**（两并发点击只落一条 attempt；两并发建测只建一个会话） |
| `pytest tests -m integration`（隔离 PG） | **62 passed / 2 failed**；2 项是 `test_listening_pg.py` 的既有顺序耦合（在本轮之前的干净检出上同样复现） |
| 受影响回归（teaching / tutor_conversations / v2_runtime / learning_context / v2_schema_gating / v2_account_data） | 全部通过 |
| 后端全量 `pytest tests -q -m "not integration"` | **1737 passed / 1 skipped**（修复上述回归后完整复跑，exit 0） |
| `ruff check` / `format --check` | 通过 |
| mypy 基线 | 0 新增 |
| 前端 `npm run check` | exit 0 |
| 前端 `npm run test:unit` | 40 文件 / **385 项**通过 |
| `npx playwright test e2e/exam.spec.ts --project=chromium` | **1 passed**（teach 模式挂在同一路由，冒烟不回归） |
| ego-browser 走查 | 见 §7 |

**未执行**：e2e 全量（只跑了 `exam.spec.ts` 冒烟）。quiz 走查先以 ego-browser 留证；
稳定的 quiz 种子进 e2e 放在发布对齐（W4）之后。

## 7 ego-browser 走查（真实 dev 栈）

环境：Docker Postgres/Redis + uvicorn :8000 + `next dev` :3000；账号 15580607003 由
`seed_teaching_quiz.py` 播种 4 道合成题目并授予教学访问；`TEACHING_ENABLED=true`、
`TEACHING_RUNS_ENABLED=true`（本机 `.env` 既有值）。GPU worker 未启动（本机没有
`gpu-worker/.venv`，与本轮无关）。

| 步骤 | 观察到的结果 |
| --- | --- |
| `/practice` 目录 | 出现「四题小测 · Synthetic quiz walking fixture」条目 |
| 点该条目 | 跳到 `/practice/exams/<paper>?mode=teach&teaching_session_id=…`，4 题会话建立 |
| 首屏 | 切换条「已答 0/4 \| 第 1 题 … 第 4 题」，题面为第 1 题 |
| 选 B 提交 | 切换条变「已答 1/4」、第 1 题带 ✓，题面自动前进到第 2 题 |
| 答完 4 题 | 「已答 4/4」，四题均带 ✓ |
| 刷新页面 | 进度完整恢复（4/4 与四个 ✓），不会重置 |
| 四题逐个「查看答案与解析」 | 每次成功，无 409（修复前第二次即红） |
| 「结束本次」 | 会话转 `abandoned`，提交按钮消失，无告警（修复前 422） |
| 390px | 无横向溢出；四个切换按钮均 40×40 |

**截图未产出**：本机 CDP `Page.captureScreenshot` 超时（该环境问题在
`docs/evidence/iteration-5/README.md` 与 `v2-ui-2026-11-03/README.md` 已两次记录）。
以 DOM 实测值（进度文本、按钮尺寸、`scrollWidth == innerWidth`）为证。

## 8 回退

关 `TEACHING_ENABLED` 即全部 503；再成组撤 `/teaching/quizzes`、`/sessions/{id}/actions`、
`commands.py` 与 `create_quiz`。本切片没有 schema 变更，回滚不涉及数据库。
