# SLCS 隔离验收环境

这里记录怎么从零重建本轮的隔离验收环境，让任何人都能复现 `acceptance.md` 里的实测结果，而不是相信我留在机器上的进程。**不触碰生产库与业务库。**

## 组成

| 部件   | 位置                                                    | 说明                                                                         |
| ------ | ------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 数据库 | 容器 `slcs-handoff-pg-7814`，库 `slcs_accept`           | 从空库 `alembic upgrade head`，与生产同一个 head（`d7e21b4c9f82`）           |
| Redis  | 容器 `seeword-slcs-acceptance-redis`（127.0.0.1:16381） | 隔离后端自己的限流与缓存                                                     |
| 后端   | `127.0.0.1:8014`                                        | `uvicorn app.main:app`，`ENV=testing` 让限流装饰器变 no-op                   |
| 前端   | `C:/Users/Fuwei/ego/slcs-preview-app`                   | 仓库的副本，只改 `next.config.js` 把 `/api`、`/media`、`/health` 反代到 8014 |

## 重建步骤

数据库：

```sh
docker rm -f slcs-handoff-pg-7814
docker run -d --name slcs-handoff-pg-7814 \
  -e POSTGRES_USER=slcs_test -e POSTGRES_PASSWORD=slcs_test_local -e POSTGRES_DB=slcs_test \
  -p 127.0.0.1:62381:5432 postgres:16
docker exec slcs-handoff-pg-7814 psql -U slcs_test -d postgres -c "CREATE DATABASE slcs_accept;"
```

迁移（在 `backend/`，`PYTHONUTF8=1`）：

```sh
DATABASE_URL="postgresql+asyncpg://slcs_test:slcs_test_local@127.0.0.1:62381/slcs_accept" \
  .venv/Scripts/python.exe -m alembic upgrade head
```

后端。**必须带 `PYTHONUTF8=1`**，否则读 UTF-8 的 `.env` 直接 `UnicodeDecodeError`：

```sh
ENV=testing \
DATABASE_URL="postgresql+asyncpg://slcs_test:slcs_test_local@127.0.0.1:62381/slcs_accept" \
REDIS_URL="redis://127.0.0.1:16381/0" \
SLCS_LESSONS_ENABLED=true \
SLCS_VOCABULARY_ENABLED=true \
SLCS_LESSON_RECEIPT_ISSUER=seeword-slcs-editorial \
SLCS_LESSON_RECEIPT_PUBLIC_KEYS='{"release-2026":"<公钥 PEM>"}' \
PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8014
```

公钥由签发脚本生成（见下）；`ENV=testing` 还要求 `JWT_SECRET` 至少 32 个字符且不是开发默认值。

前端：

```sh
cd C:/Users/Fuwei/ego/slcs-preview-app && npm run dev -- --port 3014
```

## 签发收据（本轮新增）

仓库原先没有任何东西能产出发布收据，所以第一门课程导入并审核之后仍然发不出去。现在有了：

```sh
# 一次：生成密钥对，私钥写到仓库外，公钥按打印的 JSON 填进后端环境
.venv/Scripts/python.exe scripts/sign_lesson_receipt.py keygen --out ~/.seeword/slcs-receipt-key.pem

# 核对某修订会被签进去的声明（只读）
.venv/Scripts/python.exe scripts/sign_lesson_receipt.py claims \
  --database-url "$DB" --lesson-id <lesson> --revision-id <revision>

# 签发，stdout 就是可以粘进 /admin/lessons 的那一行
.venv/Scripts/python.exe scripts/sign_lesson_receipt.py sign \
  --database-url "$DB" --private-key ~/.seeword/slcs-receipt-key.pem \
  --lesson-id <lesson> --revision-id <revision>
```

## 一次跑完整条发布链路

`backend/scripts/smoke_lesson_publication.py` 会启动真实 ASGI 应用、连真实 Postgres、把签发脚本当子进程调用，跑完导入 → 审核 → 签收据 → 发布 → 学习 → 撤回 → 恢复 → 拒收异常收据，并在最后核对「整套流程只产生一个修订」：

```sh
.venv/Scripts/python.exe scripts/smoke_lesson_publication.py \
  --database-url "postgresql+asyncpg://slcs_test:slcs_test_local@127.0.0.1:62381/slcs_signer_drill"
```

它只往库里加一个带随机后缀的临时课程，不迁移、不删别人的数据。
