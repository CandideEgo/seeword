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

五条腿长期是绿的：`consistency`（ubuntu + windows）、`frontend`、`production-config`、`gpu-worker`。`backend` 是红的；`e2e` 会随运行波动，失败时见下面第二节。

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

CI 日志里异常栈落在 `app/services/listening_service.py:102`（`start()` 里对 pending session 行的 `SELECT ... FOR UPDATE`）。`submit()` 先持有同一 session 行的锁，随后经 `record_event` 写 `learning_events` / `user_learning_profiles`；`start()` 在正要阻塞的那一刻，手里只有 `users` 行上的 `FOR NO KEY UPDATE`（见 `:99`，测试正是靠监听它才确认了时序）。两个事务交叉成环：`start` 等 session 行，`submit` 等 `start` 手里的东西。

**我今天推翻了自己上一版写在这页的一个说法**：上一版建议「统一成先 account、后 session」。那条建议基于「`submit` 侧会去拿 users 行」这个假设，我用真实 Postgres 直接测了：`FOR NO KEY UPDATE` 与「插入一条外键指向 users 的子行」**不冲突**（探针见下）。所以 `start` 手里那把锁本身不会挡住 `submit` 写 `learning_events`——环必然从 `submit` 侧的**另一处写**（`submit()` 自己会写 `learning_sessions.submitted_at`，并用 `ON CONFLICT DO NOTHING` 插 `user_learning_profiles`）去合上。**不要照上一版那条建议改**：改加锁顺序之前，要先用 `pg_locks` 抓到真实的等待边，而不是推断。

**为什么仍然没修**：本机连跑 16 次（直接跑、用真实服务代码驱动同一时序、加 `--cov`）一次都没复现；今天用本地 Postgres 跑整套 `test_listening_pg.py` 也是 7 项全过（50.91s）。盲改一个无法复现、也无法验证的并发缺陷，比留着它更糟。

**也不要把它标成 `xfail`**：`pytest.ini` 没设 `xfail_strict`，标了会让这个真实缺陷变成静默通过。

要处理它的人，建议顺序：先在 CI 上把 `statement_timeout` 固定住拿到稳定复现，同时抓 `pg_locks` 的等待边，再动手。**不要从文档推断加锁顺序。**

**「account 锁不会挡住子行插入」的实测**（本地 Postgres 16，两个连接）：

```
A: BEGIN; SELECT id FROM probe_parent WHERE id=1 FOR NO KEY UPDATE;
B: BEGIN; INSERT INTO probe_child VALUES (1,1);   -- probe_child.pid REFERENCES probe_parent(id)
=> RESULT: child INSERT did NOT block on FOR NO KEY UPDATE  -> no conflict
```

### `e2e` 那几条：两条是确定性的，两条是抖动

没有一条与课程有关。但要分清性质——**四条里只有两条是真抖动**，另外两条每轮必红，原因是固定的：

| 用例                                | 失败在哪                                | 性质                                      |
| ----------------------------------- | --------------------------------------- | ----------------------------------------- |
| `design-rollout.spec.ts:139`        | 找不到「视频 / 字幕 / 词汇 / 频道」标题 | **确定性**：CI 的搜索数据是空的（见下）   |
| `design-rollout.spec.ts:303`        | 记下 `500 /api/v1/…`（每轮端点不同）    | **确定性**：CI 起后端少了 keep-alive 参数 |
| `watch-immersive.mobile.spec.ts:74` | 按 `r` 重听后，播放器 6 秒内未暂停      | 播放器时序抖动                            |
| `home-feed.spec.ts:163`             | 20 秒内没等到带 `level=B2` 的 feed 响应 | 请求时序抖动                              |

**`design-rollout:139` 是 fixture 缺口，不是回归。** 这个用例搜 `habit`，然后断言四个分组各有 `<h2>` 标题。CI 的库是「空库迁移 + `seed_e2e.py`」：种子字幕里没有 `habit`，视频标题里也没有；而「词汇」组要靠 ECDICT，`backend/data/ecdict.db` 被 `.gitignore` 忽略、CI 从不下载（`grep ecdict .github/workflows/` 为空）。四组计数全 0 ⇒ `totalHits === 0` ⇒ `allEmpty` 成立 ⇒ 页面渲染空态、**四个分组标题根本不渲染**（`search/page.tsx:165` 与 `:414`）。本机看不出来，是因为本机有 51 条视频和一份 ECDICT（实测把词典指到不存在的路径后，`habit` 的「词汇」组从 10 条掉到 0 条）。修法二选一：给种子加一条含 `habit` 的字幕，或在 CI 提供词典——**不要去改那条断言**，页面在空结果下渲染空态是设计行为。

**`design-rollout:303` 是 CI 漏了一个参数。** 这条用例从 `page.on("response")` 收集 5xx，同一轮里报的端点在四轮之间每次不同（`plan/profile`、`discovery/practice-summary`、`users/me`、`users/me/deletion`、`videos/search/hot`），且**这些请求在后端日志里一次都不存在**——没到后端，是 `next dev` 代理回了 500。仓库里已经把原因写清楚了：`playwright.config.ts:53-55` 的注释说 uvicorn 默认 5s keep-alive 与 Next 代理复用的空闲连接撞车会 `ECONNRESET` → 代理 500，因此那行显式加了 `--timeout-keep-alive 120`。`cross-browser.yml:74` 也加了。**只有 `ci.yml` 的那行没有**（`nohup uvicorn app.main:app --port 8000`，自 2026-07 建 job 起就没跟过）。补上这一个参数即可。

这两条的关闭应当各自单独验证，不要因为「e2e 其它也红」就一起算作波动。

## 六、这一轮补了什么（相对昨晚）

- `backend/scripts/sign_lesson_receipt.py` + 22 项测试：签发方与站点验签器的一致性由测试钉住；三条发布路径（首次、恢复、回退）都能签。
- `backend/scripts/smoke_lesson_publication.py`：真实 Postgres 上的全链路演练，37/37，含重放拒绝与回退，结束时自清理。
- 隔离站点上的**真实浏览器走查**：维护者导入 → 审核 → 签收据 → 粘贴发布 → 学习者读课、点词、收词 → 撤回即时生效 → 恢复。
- 独立 review 报出的六项已全部修复并复验（回退路径签不出收据、演练的重放检查形同虚设、时钟漂移、密码进日志、演练留垃圾账号、一条不会失败的断言）。
- 嵌入**失败态**实测：显示「嵌入播放暂不可用」，字幕与释义仍可读。
- 移动端 390px 无横向溢出。
- 修掉两个只在真实库上暴露的签发方缺陷（见验收记录）。

细节与证据：[`docs/evidence/slcs-2026-11-11/acceptance.md`](../evidence/slcs-2026-11-11/acceptance.md)。
