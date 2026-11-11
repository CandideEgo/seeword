# SLCS 隔离环境验收记录 · 2026-11-11

隔离环境：独立 Postgres 库 `slcs_accept`（容器 `slcs-handoff-pg-7814`，从空库跑 `alembic upgrade head` 到 `d7e21b4c9f82`）、隔离后端 `127.0.0.1:8014`、隔离前端的真实副本（`C:/Users/Fuwei/ego/slcs-preview-app`，`/api` 反代到 8014）。**未触碰生产与业务库。**

## 已执行并通过

| 项                       | 结果                                                                                                                                                                                |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 迁移与并发（PostgreSQL） | 空库升级通过；`tests/test_slcs_lessons.py` 的 PostgreSQL 腿通过（并发导入、并发发布只有一个赢家、签名校验、撤回保留进度）                                                           |
| 课程进度语义             | 新增 `tests/test_lesson_progress.py` 6 项：跨修订保存位置不清除完成、在旧修订上完成仍计入、外链可「标为学完」但拒绝播放计时、重复事件幂等、超出时长拒绝、课程与视频时长按本地日合并 |
| HTTP 层                  | 新增 `tests/test_lessons_http.py` 8 项：试点关闭 503、管理员鉴权、导入幂等、字段路径诊断、超限请求 413、候选不可见、未配签发方发布 503、未登录 401                                  |
| 导师（阶段 3，服务层）   | `tests/test_lesson_learning.py`：撤回后排队中的运行不调模型、重试首轮在撤回后仍返回原 run、归档对话拒绝新回合、仅展示用途的修订不能入队                                             |
| 复习日志与 FSRS 评估     | `tests/test_lesson_learning.py` 的 `s6-v1` 回放；`fsrs_candidate_eval.py` 四组评分序列与两次重放一致                                                                                |
| 导出与注销               | 导出包新增五个课程数据段（`test_account_data.py`）；`test_account_purge_removes_lesson_anchors` 在 Postgres 上验证词的定位锚点随账号删除                                            |
| 独立读取器               | 仓库外虚拟环境装 wheel：11 项通过、1 项跳过（stdio 需 mcp extra）；发行树自身 12 项通过；校验和逐项核对无差异                                                                                      |

## ego-browser 走查（隔离站点，桌面 1080×595 与移动 390×844）

| 步骤                  | 实测结果                                                                                                                                                 |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 登录后打开 `/lessons` | 目录列出 `welcome-to-wikisource`，标注「原站观看」                                                                                                       |
| 打开课程页            | 12 段双语字幕全部渲染，h1 为课程标题，无横向溢出（桌面分栏 406px/336px）                                                                                 |
| 点选 `public domain`  | 词卡显示词头、释义、`0:13.602 – 0:14.242`、复制原句链接、加入词库                                                                                        |
| 加入词库              | `POST /lessons/{id}/vocabulary` 200；`/vocabulary` 出现该词                                                                                              |
| 外链课程「标为学完」  | `POST /lessons/{id}/activity` 200（修复前必然 422）；刷新后显示「已学完 · 继续学习 0:13」                                                                |
| 维护者撤回            | 后台 `/admin/lessons` 提交撤回成功，修订显示「已撤回」并出现「以新收据恢复发布」表单                                                                     |
| 撤回后学习者          | 课程页显示「材料已不可用 / 学习状态：已学完」，目录显示「暂无已发布课程」+ 历史里「材料已不可用 · 已学完」；`GET /lessons/{id}` 410，`GET /progress` 200 |
| 恢复                  | 用新签名收据重新发布成功，学习者页恢复 12 段字幕且「已学完」保留                                                                                         |
| 移动端                | 390px 无横向溢出、无越界元素                                                                                                                             |

## 未执行（不得写成通过）

- **嵌入模式（`provider_embed`）实测**：随包的唯一材料是 `external_link`。候选短片《This is the Wikimedia Foundation》的署名、字幕授权与嵌入能力尚未核对，因此 YouTube iframe 播放、字幕跟随与嵌入失败态没有在浏览器里走查过；相关路径只有前端单测（`lessonYouTubeId` 拒绝非官方 watch 链接）与服务端校验覆盖。
- **站内导师的真实模型回合**：隔离后端以 `SLCS_TUTOR_ENABLED=false` 启动（打开还要求 `LLM_GATEWAY_GOVERNANCE_VERIFIED` 与真实网关凭据）。派发、投影、撤回失效已由服务层测试覆盖，但「选词提问 → 回复 → 原句回跳」的真实模型验收未做。
- **键盘走查的最后一步**：浏览器空间在复制深链前被用户接管，键盘 Enter 选中与「复制原句链接」的实测未完成（深链不含媒体 token 由 `lessons.test.ts` 断言）。
- 逐段听审。
- 生产部署与业务库迁移：按约定另行放行。

## 公开发行（2026-11-12 补记）

`CandideEgo/slcs` 已由用户创建并登录 `gh`，发行树推送到 `main`（提交 `8393146`，29 个文件，历史只有占位 `Initial commit` 与本提交）。已执行的核对：

| 项 | 结果 |
| --- | --- |
| 仓库自己的 `consistency` CI | `ubuntu-latest` 与 `windows-latest` 两条腿均 success（run `43071111538`） |
| 匿名克隆（`https://`，无凭据） | `sha256sum -c SHA256SUMS` 零失败 |
| 仓外安装 | `pip install -c requirements-mcp.lock 'dist/slcs-0.1.0-py3-none-any.whl[mcp]'` 成功，`pip check` 无破损 |
| 发行树测试 | 12 项通过（含 `SLCS_REQUIRE_INSTALLED` 断言导入自 `site-packages`） |
| 文档命令 | `validate --json` / `schema` / `fingerprint` / `resolve` 逐条按文档执行，退出码与输出符合规格，指纹为 `d06cd8fa…55ab4` |

推送前修掉四处只有远端才会暴露的问题：`slcs_tests` 在 `--import-mode=importlib -o pythonpath=` 下无法解析同级导入；Windows 控制台脚本不在解释器旁目录；发行树自测导入树内源码副本而非已安装 wheel；发行树按构建机行尾写出导致 `SHA256SUMS` 跨平台失效（现统一 LF 并生成 `.gitattributes`）。

## 独立 review 修复（2026-11-11）

一次独立审查（correctness / security / data-integrity / tests-docs-release 四个维度，逐条反驳后才计入）报出六项，全部已修：

| 缺陷                                                                                                   | 修复                                                            |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| `check_schema_drift.py` 的 `from app import models` 被 lint 当成未使用删掉，漂移门改为空 metadata 比对 | 恢复为副作用导入并注明原因；隔离库上跑门禁得 0/0                |
| 注销无条件调 `purge_learner_facts`，未跑课程迁移的库上整个注销事务回滚                                 | 按表是否存在分步删除，缺表即跳过                                |
| 课程锚点在其会话被删之后才清，留下孤儿行                                                               | 会话清扫之前先删锚点                                            |
| `SLCS_VOCABULARY_ENABLED` 打开但迁移未落时，普通复习/训练/练习提交全部 503                             | 日志不可写时回落到 S6 排程，复习本身不再被阻断                  |
| `vocabulary_review_log` 的 `ON DELETE CASCADE` 让删一个词抹掉「只追加」的复习历史                      | 外键改 `SET NULL`，并把词形复制进日志行（`word`），导出保留词形 |
| 练习提交对每个词各查一次全库表名                                                                       | 表存在性按 session 缓存一次                                     |
