# 明早从这里开始 · SLCS v0.1 放行手册

这是给「手术」当天的操作单：按顺序做，每步都有可核对的判据。规范与设计不在这里（[README](README.md) 是文件契约，[06](06-implementation-roadmap.md) 是阶段），这里只有「现在要按什么顺序动，动完怎么知道成了」。

**你昨晚的决定**：暂不接生产（2026-11-12）。代码与迁移留在 `docs/slcs-six-docs`，生产库不跑课程迁移。下面第三节讲将来放行时的顺序，现在不做。

---

## 一、现在仓库处于什么状态

| 项       | 值                                                                                   |
| -------- | ------------------------------------------------------------------------------------ |
| 分支     | `docs/slcs-six-docs`，评审见 [PR #46](https://github.com/CandideEgo/seeword/pull/46) |
| 代码     | 阶段 0–4 全部落地，三个开关默认关                                                    |
| 生产     | **没有部署，业务库没有跑课程迁移**（按你的决定）                                     |
| 公开发行 | 已完成：<https://github.com/CandideEgo/slcs>（`main`，两条 OS 腿全绿）               |
| 签发工具 | 本轮新增，见第二节第 1 步                                                            |

## 二、今天要做的四件事

### 第 1 步 · 配好签发方（不做这步，任何课都发不出去）

发布收据是 Ed25519 签名，**站点只拿公钥**。仓库里原先没有签发工具，现在有了：

```sh
cd backend
PYTHONUTF8=1 .venv/Scripts/python.exe scripts/sign_lesson_receipt.py keygen \
  --out ~/.seeword/slcs-receipt-key.pem \
  --issuer seeword-slcs-editorial --kid release-2026
```

它会把私钥写到仓库外，并把要填进后端环境的两行打印出来：

```
SLCS_LESSON_RECEIPT_ISSUER=seeword-slcs-editorial
SLCS_LESSON_RECEIPT_PUBLIC_KEYS={"release-2026": "-----BEGIN PUBLIC KEY-----\n..."}
```

**判据**：私钥文件不在仓库里（脚本会拒绝写进去）；环境里配的是公钥，不是私钥。

换钥时不要删旧 kid：把新公钥加进那个 JSON，等所有旧收据过期后再删。收据有效期默认 600 秒，站点上限 900，所以「先签后发」不会过期，隔夜存着的会。

### 第 2 步 · 选第一份真实材料（这是唯一还需要你决定的）

随包的唯一材料是 Wikisource 那条外链。要开嵌入模式，roadmap 要求先逐项核对**署名、字幕授权与平台嵌入条件**——这件事只能你或维护者做，我不能替你判断授权。

三条路，选一条：

- **只走外链**：现在就能开，`SLCS_LESSONS_ENABLED=true` 即可。风险最低。
- **上一条已核对的 YouTube 短片**：需要你给出一份「署名 + 字幕授权 + 允许嵌入」都能成立的材料，我再做逐段听审与嵌入正样本走查。
- **暂不开任何材料**：只把 `/admin/lessons` 当内部审核台用。

### 第 3 步 · 在隔离环境先走一遍，再决定开不开

隔离环境的完整重建步骤在 [`docs/evidence/slcs-2026-11-11/isolated-environment.md`](../evidence/slcs-2026-11-11/isolated-environment.md)。起来之后：

```sh
cd backend
PYTHONUTF8=1 .venv/Scripts/python.exe scripts/smoke_lesson_publication.py --database-url "$DB"
```

**判据**：输出 `冒烟结果：37/37 通过`。这条会把签发脚本当子进程调用，因此签发方与站点验签器的任何漂移都会在这里红；它结束时还会删掉自己建的课程与账号，指到共享库上也不留垃圾。

### 第 4 步 · 决定放行范围

| 开关                      | 打开后发生什么                            | 还差什么                                                                                                                                       |
| ------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `SLCS_LESSONS_ENABLED`    | `/lessons` 目录与学习页、导入审核发布可用 | 第 1 步、第 2 步                                                                                                                               |
| `SLCS_VOCABULARY_ENABLED` | 能从课程收词，复习日志写 `s6-v1`          | 上面 + 迁移已跑                                                                                                                                |
| `SLCS_TUTOR_ENABLED`      | 站内导师可用                              | 上面 + `TEACHING_STREAMING_ENABLED`（它又要求 `TEACHING_DIALOGUE_ENABLED`）+ 该账号在 `teaching_access_grants` 有行 + `teaching` 队列有 worker |

导师那行四个条件缺一个就 503 或排队不执行，不是配一个开关就行。

## 三、将来接生产时的顺序（现在不做）

1. **部署必须与迁移同批**。HEAD 不能跑在 V2 迁移之前的库上；`entrypoint.sh` 只在 backend 容器跑迁移（`RUN_MIGRATIONS`）。
2. **先配签发方与公钥再开开关**。开关已在 `docker-compose.prod.yml` 的白名单里（`production_preflight.py` 会拦漏项），默认值仍是 `false`。
3. 最后才 `SLCS_LESSONS_ENABLED=true`。

放行前跑 `python backend/scripts/production_preflight.py`，它不连库、不建容器，只证明「不会带着错配置上线」。

## 四、已知的坑（都是实测的）

- **Windows 上每个 Python 进程都要 `PYTHONUTF8=1`**，否则读 UTF-8 的 `.env` 直接 `UnicodeDecodeError`。
- **签发私钥不能进仓库，也不能进镜像**。`keygen` 会拒绝写进仓库；`.env` 只放公钥。
- **发布收据是一次性的**：同一个 `jti` 第二次用会 409。恢复已撤回的修订要重新签。
- **`--revision-id` 可以省略**，但前提是该课程只有一个可发布的修订（候选、已撤回待恢复，或已发布但被新版本取代）。有多个时会列出来让你指定。
- **三条发布路径都要收据**：首次发布（候选）、恢复已撤回、以及**回退到被新版本取代的旧修订**。最后这条在后台显示为「发布为当前版」，别以为旧修订就不用签名。
- **收据是一次性的**：同一个 `jti` 第二次用会 409「发布收据已使用」。恢复或回退都要重新签。
- **签发方的时钟可以慢一点，不能快**：脚本会把 `iat` 回拨 30 秒，所以笔记本比服务器快几秒也不影响；但如果站点验签时间比签发时间早（本机时钟严重超前），仍会 422。
- **错误的库地址不会把密码漏进日志**：脚本在 `main()` 边界把驱动异常收敛成一行并抹掉密码。库地址建议用环境变量 `DATABASE_URL` 传，少一处进 `ps` 与 shell history。
- **课程读取不走缓存**，撤回即时生效；`_VIDEO_ACCESS_CACHE` 只服务旧视频链路。
- **`backend/` 下跑 `pytest slcs_tests` 会 skip**：那套测试要求先装发行 wheel。

## 五、CI 现在是什么颜色，为什么

五条腿长期是绿的：`consistency`（ubuntu + windows）、`frontend`、`production-config`、`gpu-worker`。`backend` 是红的（`test_listening_pg` 死锁，见本章末尾）；`e2e` 曾有两条确定性失败，2026-11-12 已修但**尚未经 CI 确认**，另两条仍是抖动，见下面。

**不是这个分支引入的。** 证据：

- master 从 2026-10-31 起**连续 12 轮 CI 全部失败**（10-31 早期是 mypy 门禁，11-05 起固定成下面这条）。
- `git diff master...HEAD` 对 `listening_service.py`、`test_listening_pg.py`、`learning_event_service.py` 的加锁路径均为空（唯一的改动是新增一个与本问题无关的 `claim_watch_day`）。
- 本机连跑 10 次（含用真实服务代码在迁移库上驱动同一时序）**一次都没复现**；CI 上则每轮必现（两次运行各 2 条失败）。说明它依赖 CI 的执行时序，尤其是全量套件在同一进程里跑完 1761 项之后留下的连接池与事务状态。（2026-11-12 追加：本地 Postgres 上整套 `test_listening_pg.py` 7 项全过。）

**注意 `paths-ignore` 在 PR 上不生效**：同一个只改 `.md` 的提交会在 PR 上产生两个 run，一个按 `paths-ignore` 跳过 backend，另一个照跑全量（PR 的 diff 含整条分支）。所以「只改文档」并不能让 backend 那条红腿消失。

### `backend` 那一条：真实的并发缺陷，但没有被修

```
tests/test_listening_pg.py::test_start_waiting_for_submit_does_not_deadlock_or_delete_submitted_history[True/False]
asyncpg.exceptions.DeadlockDetectedError: deadlock detected
```

CI 日志里异常栈落在 `app/services/listening_service.py:102`（`start()` 里对 pending session 行的 `SELECT ... FOR UPDATE`）。`start()` 在正要阻塞的那一刻，手里只有 `users` 行上的 `FOR NO KEY UPDATE`（见 `:99`，测试靠监听它确认时序）。`submit()` 先持有同一 session 行的锁，再经 `record_event` 写 `learning_events` 与 `user_learning_profiles`。

**2026-11-12：拿到了 Postgres 服务端日志，这是十几轮里第一次看到真语句对。** CI 之前丢弃了 service 容器的日志，现在 `backend` job 失败时会导出（`ci.yml` 的「Dump Postgres server log on failure」）。实际内容：

```
Process 790 waits for ShareLock on transaction 979; blocked by process 789.
Process 789 waits for ShareLock on transaction 980; blocked by process 790.
Process 790: SELECT ... FROM listening_sessions
             WHERE user_id=$1 AND video_id=$2 AND submitted_at IS NULL
             ORDER BY started_at DESC LIMIT $3 FOR UPDATE
Process 789: INSERT INTO learning_events (...) VALUES (...)
Process 790 CONTEXT: while locking tuple (0,1) in relation "listening_sessions"
```

**但这两条语句按字面推不出环，我用真实表结构验过。** 在迁移到 head 的库上原样复演（A 取 `users` 的 `FOR NO KEY UPDATE` 后等 session 行，B 持 session 行后执行那条 INSERT）：

```
A blocked on session row: True
B blocked on learning_events INSERT: False
=> no cycle
```

并且把 `submit()` 的四种写入逐个试了一遍，在 A 持锁期间**没有一种阻塞**：

```
ok  learning_events INSERT
ok  user_learning_profiles INSERT ON CONFLICT DO NOTHING
ok  user_learning_profiles SELECT
ok  listening_sessions UPDATE (submitted_at)
```

（这与另一条独立的实测一致：`FOR NO KEY UPDATE` 不会阻塞插入外键指向该行的子行。）

所以结论只能到这里：**语句对是硬证据，但环如何闭合还没定论。** 可能 B 在事件 INSERT 之前已经因为别的写拿到/等待了某个锁（`learning_events` 上的唯一约束或索引、序列，或测试自身 `seed()` 那条 `start()` 留下的行），也可能阻塞点是 CI 特有的（同一进程内已跑完 1800 项后的连接池状态）。**在没有抓到真实等待边之前不要改加锁顺序**——我这一页上一版给过一条「统一成先 account、后 session」的建议，就是没验就写下的，已被上面两个探针推翻。

**为什么仍然没修**：本机连跑 16 次一次没复现；本地 Postgres 上整套 `test_listening_pg.py` 7 项全过（50.91s）；按 CI 方式跑全套还没跑完就因 `test_catalog_pg.py` 超时中断（**这次实验未完成，不构成证据**）。

**也不要把它标成 `xfail`**：`pytest.ini` 没设 `xfail_strict`，标了会让这个真实缺陷变成静默通过。

**下一步**：服务端日志已经在 CI 里了，下一轮再红时先看 `pg_stat_activity` 与 deadlock 段里的 `CONTEXT` 行（它指出具体等的是哪张表的哪个 tuple）。若仍不足以定环，就在测试里按 CI 的执行顺序把 `pg_locks` 快照打出来——而不是继续从代码推断。

### `e2e` 那几条：两条是确定性的，两条是抖动

没有一条与课程有关。但要分清性质——**四条里只有两条是真抖动**，另外两条每轮必红，原因是固定的：

| 用例                                | 失败在哪                                | 性质                                              |
| ----------------------------------- | --------------------------------------- | ------------------------------------------------- |
| `design-rollout.spec.ts:139`        | 找不到「视频 / 字幕 / 词汇 / 频道」标题 | **确定性**：CI 的搜索数据是空的 —— 已修           |
| `design-rollout.spec.ts:303`        | 记下 `500 /api/v1/…`（每轮端点不同）    | **确定性**：CI 起后端少了 keep-alive 参数 —— 已修 |
| `watch-immersive.mobile.spec.ts:74` | 按 `r` 重听后，播放器 6 秒内未暂停      | 播放器时序抖动（未修）                            |
| `home-feed.spec.ts:163`             | 20 秒内没等到带 `level=B2` 的 feed 响应 | 请求时序抖动（未修）                              |

**`design-rollout:139` 是 fixture 缺口，不是回归。** 这个用例搜 `habit`，然后断言四个分组各有 `<h2>` 标题。CI 的库是「空库迁移 + `seed_e2e.py`」：种子字幕里没有 `habit`，视频标题里也没有；而「词汇」组要靠 ECDICT，`backend/data/ecdict.db` 被 `.gitignore` 忽略、CI 从不下载（`grep ecdict .github/workflows/` 为空）。四组计数全 0 ⇒ `totalHits === 0` ⇒ `allEmpty` 成立 ⇒ 页面渲染空态、**四个分组标题根本不渲染**（`search/page.tsx:165` 与 `:414`）。本机看不出来，是因为本机有 51 条视频和一份 ECDICT。

**修法**：给种子的字幕、演示视频标题与频道描述各加一处 `habit`，让四组里三组命中（`words` 仍为 0 也没关系——`groupSection` 只要 `data` 存在就渲染 `<h2>`）。**没有改那条断言**：页面在空结果下渲染空态是设计行为。种子对既有行做了回填（按旧标题匹配、重写字幕与描述），所以在长时间没重建的库上重跑也不会插出第二个演示视频。

**验证（双向）**：建一个空库迁到 head、用**旧**种子播种，`habit` 四组全 0（`allEmpty: true`）；同一个库换**新**种子重播，变成 `videos 1 / subtitles 1 / words 0 / channels 1`（`allEmpty: false`）。在无词典的后端上真跑这条 spec：新种子 **1 passed**，把种子行改回旧文案后 **1 failed，且失败点就是 `:148`**——与 CI 的失败行一致。

**`design-rollout:303` 是 CI 漏了一个参数。** 这条用例从 `page.on("response")` 收集 5xx，同一轮里报的端点在四轮之间每次不同（`plan/profile`、`discovery/practice-summary`、`users/me`、`users/me/deletion`、`videos/search/hot`），且**这些请求在后端日志里一次都不存在**——没到后端，是 `next dev` 代理回了 500。仓库里已经把原因写清楚了：`playwright.config.ts:53-55` 的注释说 uvicorn 默认 5s keep-alive 与 Next 代理复用的空闲连接撞车会 `ECONNRESET` → 代理 500，因此那行显式加了 `--timeout-keep-alive 120`。`cross-browser.yml:74` 也加了。**只有 `ci.yml` 的那行没有**（`nohup uvicorn app.main:app --port 8000`，自 2026-07 建 job 起就没跟过）。已补上。

**机制是实测的，不是推断**：两个最小 uvicorn 实例，一个默认、一个 `--timeout-keep-alive 120`；同一条 keep-alive 连接先用一次、空闲 7 秒后再用一次：

```
默认 5s      -> ConnectionAbortedError: [WinError 10053] ...
120s         -> 正常返回 {"ok": true}
```

uvicorn 在每个响应结束后都会 `call_later(timeout_keep_alive, ...)` 关掉空闲连接，所以「代理复用被服务端关掉的连接」是必然而非偶发。

两条都已修，但**结论要等 CI 跑过才算确认**：本地能复现的是机制，不是 CI 的整体时序。`watch-immersive:74` 与 `home-feed:163` 仍属抖动，没动。

**本地跑 `:303` 会先撞上另一件事（不是这次修的）**：这条用例在本地失败于 `/history` 页的 `#main-scroll` 横向溢出（`:385`），而 CI 失败于更后面的 5xx 收集（`:392`）。两者都真实存在：把种子文案改回旧版、以及把本次两处修复整体 stash 掉，`/history main` 都照样失败——**这是既存问题，与本次修复无关，也还没修**。它挡在本地复现 `:303` 的路上，排查这条 spec 时别把它当成本次改动引入的。

## 六、这一轮补了什么（相对昨晚）

- `backend/scripts/sign_lesson_receipt.py` + 22 项测试：签发方与站点验签器的一致性由测试钉住；三条发布路径（首次、恢复、回退）都能签。
- `backend/scripts/smoke_lesson_publication.py`：真实 Postgres 上的全链路演练，37/37，含重放拒绝与回退，结束时自清理。
- 隔离站点上的**真实浏览器走查**：维护者导入 → 审核 → 签收据 → 粘贴发布 → 学习者读课、点词、收词 → 撤回即时生效 → 恢复。
- 独立 review 报出的六项已全部修复并复验（回退路径签不出收据、演练的重放检查形同虚设、时钟漂移、密码进日志、演练留垃圾账号、一条不会失败的断言）。
- 嵌入**失败态**实测：显示「嵌入播放暂不可用」，字幕与释义仍可读。
- 移动端 390px 无横向溢出。
- 修掉两个只在真实库上暴露的签发方缺陷（见验收记录）。
- 两条确定性 e2e 失败（fixture 缺口与 CI 少 keep-alive 参数）已修并双向验证，待 CI 确认。

- 详情与证据：[`docs/evidence/slcs-2026-11-11/acceptance.md`](../evidence/slcs-2026-11-11/acceptance.md)。
