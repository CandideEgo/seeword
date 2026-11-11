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
- 本机连跑 10 次（含用真实服务代码在迁移库上驱动同一时序）**一次都没复现**；CI 上则每轮必现（两次运行各 2 条失败）。说明它依赖 CI 的执行时序，尤其是全量套件在同一进程里跑完 1761 项之后留下的连接池与事务状态。

**注意 `paths-ignore` 在 PR 上不生效**：同一个只改 `.md` 的提交会在 PR 上产生两个 run，一个按 `paths-ignore` 跳过 backend，另一个照跑全量（PR 的 diff 含整条分支）。所以「只改文档」并不能让 backend 那条红腿消失。

### `backend` 那一条：真实的并发缺陷，但没有被修

```
tests/test_listening_pg.py::test_start_waiting_for_submit_does_not_deadlock_or_delete_submitted_history[True/False]
asyncpg.exceptions.DeadlockDetectedError: deadlock detected
```

CI 日志里异常栈落在 `app/services/listening_service.py:102`（`start()` 里对 pending session 行的 `SELECT ... FOR UPDATE`）。`submit()` 先持有同一 session 行的锁，随后经 `record_event` 写 `learning_events` / `user_learning_profiles`；`start()` 在此之前已对 `users` 行取了 `FOR NO KEY UPDATE`。两个事务交叉成环。

**为什么没修**：本机复现不出来（10 次全过），改加锁顺序属于真实的并发生产路径，而且改完在本地也无法验证是否真的解决。盲改一个无法复现、无法验证的并发缺陷，比留着它更糟。

**也不要把它标成 `xfail`**：`pytest.ini` 没设 `xfail_strict`，标了会让这个真实缺陷变成静默通过。

要处理它的人，建议顺序：先在 CI 上加超时重试或固定 `statement_timeout` 拿到稳定复现，再调整两侧的加锁顺序（统一成「先 account、后 session」）。

### `e2e` 那几条：不是后端错误，也没有一条与课程有关

`e2e` 的结论会随运行波动（同一提交重跑可能不同），失败的永远是同一批用例。逐个查到的失败点：

| 用例                                | 失败在哪                                | 性质                 |
| ----------------------------------- | --------------------------------------- | -------------------- |
| `watch-immersive.mobile.spec.ts:74` | 按 `r` 重听后，播放器 6 秒内未暂停      | 播放器时序抖动       |
| `home-feed.spec.ts:163`             | 20 秒内没等到带 `level=B2` 的 feed 响应 | 请求时序抖动         |
| `design-rollout.spec.ts:139`        | 找不到「视频」分组标题                  | 撞的是已下线的旧入口 |
| `design-rollout.spec.ts:303`        | 记下 `500 /api/v1/users/me`             | 见下                 |

`design-rollout:303` 那条要单独说：它报 500，但**整场 e2e 的后端日志里零个 5xx**，同一时刻该路径返回 200 —— 请求根本没到后端，是 `next dev` 代理层的瞬时失败被 Playwright 记成 500。（master 上这条错的是 `/videos/search/hot`，原因并不相同，所以我没有拿「master 也红」当理由。）

这四条都不碰课程相关路径。想稳定它们，方向是去掉对固定网络时序的假设、或给这几条加显式重试，属于独立的 e2e 稳定性任务。

## 六、这一轮补了什么（相对昨晚）

- `backend/scripts/sign_lesson_receipt.py` + 22 项测试：签发方与站点验签器的一致性由测试钉住；三条发布路径（首次、恢复、回退）都能签。
- `backend/scripts/smoke_lesson_publication.py`：真实 Postgres 上的全链路演练，37/37，含重放拒绝与回退，结束时自清理。
- 隔离站点上的**真实浏览器走查**：维护者导入 → 审核 → 签收据 → 粘贴发布 → 学习者读课、点词、收词 → 撤回即时生效 → 恢复。
- 独立 review 报出的六项已全部修复并复验（回退路径签不出收据、演练的重放检查形同虚设、时钟漂移、密码进日志、演练留垃圾账号、一条不会失败的断言）。
- 嵌入**失败态**实测：显示「嵌入播放暂不可用」，字幕与释义仍可读。
- 移动端 390px 无横向溢出。
- 修掉两个只在真实库上暴露的签发方缺陷（见验收记录）。

细节与证据：[`docs/evidence/slcs-2026-11-11/acceptance.md`](../evidence/slcs-2026-11-11/acceptance.md)。
