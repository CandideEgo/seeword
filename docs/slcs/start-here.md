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

**判据**：输出 `冒烟结果：29/29 通过`。这条会把签发脚本当子进程调用，因此签发方与站点验签器的任何漂移都会在这里红。

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
- **`--revision-id` 可以省略**，但前提是该课程只有一个待发布修订（候选或已撤回）。有多个时会列出来让你指定。
- **课程读取不走缓存**，撤回即时生效；`_VIDEO_ACCESS_CACHE` 只服务旧视频链路。
- **`backend/` 下跑 `pytest slcs_tests` 会 skip**：那套测试要求先装发行 wheel。

## 五、CI 现在是什么颜色，为什么

`backend` 与 `e2e` 两条腿是红的，但**不是这个分支引入的**：master 自 2026-11-01 起每一轮都是同一处失败——

- `tests/test_listening_pg.py::test_start_waiting_for_submit_does_not_deadlock_or_delete_submitted_history`（Postgres 死锁）
- `e2e/design-rollout.spec.ts`、`home-feed.spec.ts` 等几条用例

我核对过：这两处在本分支与 master 的代码完全一致（`git diff master...HEAD` 对 `listening_service.py`、`test_listening_pg.py`、相关 e2e 均为空）。**修它们属于另一个任务**，而且会改到与 SLCS 无关的路径，所以没有顺手动。

其余五条腿在本分支全绿：`consistency`（ubuntu + windows）、`frontend`、`production-config`、`gpu-worker`。

## 六、这一轮补了什么（相对昨晚）

- `backend/scripts/sign_lesson_receipt.py` + 14 项测试：签发方与站点验签器的一致性由测试钉住。
- `backend/scripts/smoke_lesson_publication.py`：真实 Postgres 上的全链路演练，29/29。
- 隔离站点上的**真实浏览器走查**：维护者导入 → 审核 → 签收据 → 粘贴发布 → 学习者读课、点词、收词 → 撤回即时生效 → 恢复。
- 嵌入**失败态**实测：显示「嵌入播放暂不可用」，字幕与释义仍可读。
- 移动端 390px 无横向溢出。
- 修掉两个只在真实库上暴露的签发方缺陷（见验收记录）。

细节与证据：[`docs/evidence/slcs-2026-11-11/acceptance.md`](../evidence/slcs-2026-11-11/acceptance.md)。
