# 实验性学习接口与参考调用

本页是新增在线学习接口的契约入口；目标和正式验收仍认[大纲](../seeword-open-source-development-outline-2026-11-13.md)及[验收卡](../evidence/open-learning/acceptance-cards.md)。这些接口尚非稳定 API／1.0 承诺，不代表官方站已启用。包正文与指纹规则仍只认 [SLCS](../slcs/README.md)，用途判定仍只认[权限矩阵](content-access-matrix.md)。

## 安装和取得授权

- **本地包：**按 SLCS 说明构建／安装 wheel，`slcs resolve` 和本地 stdio MCP 只读显式选定的包／段；宿主自行配置模型。引用输出包含指纹版本及指纹，不添加包正文 v0.1 字段。本地副本不能保证被远程撤回。
- **在线站点：**先由运营者完成[自托管](../self-hosting.md)、迁移及相应试点准入；本人在 `/profile?tab=account` 创建限时连接，勾选动作和明确的课程／词条范围。课程专用连接无需教学题面权限。保存只显示一次的凭据到调用端秘密存储，不能粘贴普通聊天、日志或仓库。
- **REST：**使用 `Authorization: Bearer <外部连接凭据>`；站内 JWT 不能替代。站内 `/api/v1/lessons/*` 仍走第一方 JWT，和外部入口分开。匿名不新增正文权限。
- **MCP：**远程入口 `/api/v1/mcp/`，需运营者显式配置 SDK 兼容环境、Host／Origin 及开关；云端锁定的 Uvicorn 与 SDK 依赖不能直接混装。本轮验证过独立锁定 SDK 环境的协议调用，不等于官方宿主模型或生产运行环境验收。

连接期限当前为 7 日，轮换使旧凭据失效，撤销停止后续访问；二者都不删除本人历史。旧连接不会获得新增权限或全部课程／词库；旧 `review:read` 没有资源授权时返回空队列，应重新创建明确范围的连接，轮换不会扩大范围。

## 资源、用途与 scope

新增能力按以下 scope 区分：

| Scope                       | 能力及必要边界                                                       |
| --------------------------- | -------------------------------------------------------------------- |
| `materials:read`            | 查询所选课程、表达出现项、固定语境及可用状态                         |
| `learning:vocabulary:write` | 保存获准课程出现项到本人词库；还须 `materials:read`                  |
| `learning:progress:read`    | 读取所选课程的本人恢复位置                                           |
| `learning:progress:write`   | 更新恢复位置或准备明确完成操作；还须相应读取权限                     |
| `review:read`               | 读取本人获授权且到期的学习中／复习中词条；不包含新词或已退出复习的词 |
| `review:write`              | 准备及执行经本人在网站确认的复习结果；还须 `review:read`             |

连接的 `resource_limits` 为 `{lesson_ids: [...], word_ids: [...]}`；每组最多 200 个，不允许重复，新增学习授权至少有一项资源。词条必须属于本人；课程创建授权时必须符合当前用途。资料选择器只展示已准许外部接收及模型披露的课程，不能用普通站内展示许可冒充 AI 可接收。

每次调用重新认证连接、scope、账号和资源；检索在计数／分页／片段生成前过滤。连接用途在创建时绑定，不能由 REST/MCP 路径、请求参数或宿主标签降级：默认 `audience="model"`（包括没有用途元数据的旧连接），所有路径均要求模型披露用途。纯第三方应用须本人通过第一方 `POST /api/v1/external-connections` 显式选择 `audience="application"` 并授权资源；其 REST 正文仍须站内展示及第三方接收许可，但该凭据不能用于 MCP 模型披露。用途不可原地更新，需撤销并新建连接；轮换不改变用途。scope 不是内容权利，材料中的指令、工具 annotations、调用端自报用户 ID 或“已确认”都不能扩权。当前上下文只返回请求段，不自动附邻段或私人完整集合。

## 固定引用与支持范围

材料身份由 `lesson_id`、`fingerprint_version`、`fingerprint` 固定；可附 `revision_id`，但它必须与包身份吻合。语境引用再加 `segment_id` 和有序、连续、非空 `token_ids`。不传在线修订 ID 时按指纹映射固定修订，**不是改查当前版**；歧义、未知版本、无匹配及错误锚点明确失败。原文有词未对齐时沿用读取器的整段定位回退，不换原句。

**站内接收范围与便携格式分开：**站内包上限 4 MiB、材料 ID／段 ID／词 ID 最长 100 字符，单个词汇锚点最多 128 个词。站内导入在创建候选前给出 422 字段路径；这些是现有在线存储与消费者的限制，不修改离线 SLCS v0.1。历史超范围包的基础正文仍可读，新语境服务会明确拒绝不支持的锚点，不在构造成功响应时崩溃或静默改定位。

当前检索支持标题／材料 ID 的大小写归一子串查询，以及词条／多词短语的 `strip + casefold` 精确匹配；不同语境的出现项分开返回。未实现词形还原、模糊或语义检索。按当前版检索，固定引用可读历史获准修订；页面切换当前版不改写引用。返回的 `total` 只包含获准结果，`offset` 非负、`limit` 为 1–100；排序稳定，但不承诺跨发布／撤回的多次请求是一份快照，集合变化后应重新检索。

## HTTP 操作

外部基路径为 `/api/v1/external-learning`。准确输入 schema 可查运行实例 `/openapi.json`；未知写入字段拒绝。

| 方法与路径                          | 输入／用途                                                                                                                                |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /materials`                    | `q`（最多 200 字符）、`offset`、`limit`；返回 `items,total,offset,limit`，每项含材料／修订／指纹身份和标题                                |
| `GET /occurrences`                  | `headword`、分页；每项含完整 `reference`、词条／释义／原句／译文／时间                                                                    |
| `POST /resolve`                     | 完整固定引用；只解析该材料修订与段／词锚点                                                                                                |
| `POST /context`                     | 同一引用，返回请求段语境                                                                                                                  |
| `POST /reference-state`             | 固定材料身份；返回可用／当前状态，不含正文或标题；不可用按错误契约返回                                                                    |
| `GET /review-tasks`                 | 分页；同网站到期语义、只投影授权范围，恢复入口 `/vocabulary/review`                                                                       |
| `POST /vocabulary`                  | `{operation_id, reference}`；普通可逆收词可在持续授权内执行                                                                               |
| `GET /lessons/{lesson_id}/progress` | 读取本人进度及不透明 `version`，无进度时为 `"0"`                                                                                          |
| `PUT /lessons/{lesson_id}/progress` | `{operation_id, revision_id, position_ms, expected_version}`；版本从读取结果原样带回，不自行构造；位置须为 0–`2**63-1` 整数且在材料时长内 |
| `POST /intents`                     | 复习：`{operation_id, action:"review", word_id, quality:0..5}`；完成：`{operation_id, action:"complete", lesson_id, revision_id}`         |
| `POST /intents/{intent_id}/execute` | 不接受自由 body；只执行已保存且经本人确认的参数                                                                                           |

同一操作编号限定在本人＋连接的 namespace，输入改变返回 409；事实、操作回执和意图消费同事务。进度重放返回原操作结果，而不是最新位置；需要当前状态请重新读取。复习继续使用现行调度，不把外部结果当正式成绩或自动掌握。

### 本人确认与重试

1. 外部连接准备意图，得到 `id`、`status=pending`、到期时间和 `confirmation_url=/profile?tab=account#learning-intents`。此时不产生复习／完成事实。
2. 本人在网站查看具体资源与参数，点击确认。第一方入口是 `POST /api/v1/external-connections/learning-intents/{id}/confirm`，严格 body `{confirmed:true}`；外部凭据不能代替第一方会话。
3. 外部连接调用 execute。未确认、过期、跨用户／连接或参数不匹配均拒绝，不相信工具中的确认声明。
4. 未消费意图 10 分钟后失效，由独立 beat 定期清理；已消费的最小参数绑定作为回执墓碑保留至本人注销，清理后合法重试仍只重放一次结果。重放继续检查当前连接、scope、资源及内容用途，不泄露已撤回正文。网站待确认列表不堆积已消费墓碑。

授权、意图及回执进入本人导出和注销清理；不导出 token/hash，也不将私人事实或受限正文放进公共包。撤销连接不等于删除本人学习事实。

## 最小 REST 参考客户端

Python 3.12 标准库即可查询和解析，不需要官方模型。运营者提供的站点源地址与凭据从环境读取；远程应使用 HTTPS，HTTP 仅用于本机隔离测试。示例只读，不保存个人状态，也不把原文当可执行指令：

```python
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

origin = os.environ["SEEWORD_ORIGIN"].rstrip("/")
token = os.environ["SEEWORD_EXTERNAL_TOKEN"]
base = origin + "/api/v1/external-learning"

def call(path, body=None):
    request = Request(
        base + path,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)

matches = call("/occurrences?" + urlencode({"headword": "public domain", "limit": 10}))
if not matches["items"]:
    raise SystemExit("没有获准的匹配，不自动替换材料或扩权")
reference = matches["items"][0]["reference"]
context = call("/resolve", reference)
print(context["text"], context["start_ms"], context["end_ms"])
```

错误保持 `{code,message,detail?}`：401 凭据无效／过期；403 scope／用途不足；404 不存在或未获资源授权；410 已撤回；409 操作参数／版本冲突或尚需本人确认；422 输入或引用不支持；503 开关／schema／运行环境未就绪。不要将 403／404／410 当作查当前版重试的理由。网络重试复用原操作编号；不在错误日志打印 Authorization、收据或 token 查询串。

## MCP 对照及兼容

远程薄适配提供 `search_materials`、`search_occurrences`、`resolve_reference`、`get_context`、`get_reference_state`、`get_review_tasks`、`save_vocabulary`、`read_lesson_progress`、`save_lesson_progress`、`prepare_learning_intent`、`execute_learning_intent`。这些工具复用上述共享服务；原教学工具不因此变成通用写入口。

当前测试组合：包 `0.1.0`／指纹 `slcs-pack-v1`／读取器 `0.1.0`；在线 SDK 验证使用 MCP `2.0.0` 的独立锁定运行环境，协议 `2025-11-25` 与 `2026-07-28` 分别测试。未承诺未来包版本、多历史发行版或所有宿主兼容；实验性接口后续变更需同步本文、schema、参考客户端和兼容测试，稳定版弃用周期及责任仍待正式评审。
