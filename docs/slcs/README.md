# 04 SLCS Specification · 学习包规范 v0.1

一个学习包用单个 UTF-8 JSON 文件描述一个外部视频及其英中学习材料。字段类型、必填项和默认值以 [JSON Schema](schema.json) 为准。完整校验还须执行下文的跨字段规则。

本规范是六份文档之一，各页回答的问题如下。

| 文档                                        | 要解决的问题                                       |
| ------------------------------------------- | -------------------------------------------------- |
| [01 产品愿景](01-product-vision.md)         | 做什么、不做什么、服务谁                           |
| [02 产品需求](02-product-requirements.md)   | 页面、功能、用户流程、交互                         |
| [03 系统架构](03-system-architecture.md)    | 系统模块、数据流、技术选型、现有代码审计与迁移决定 |
| 本页                                        | 完整数据标准、Schema、示例、校验与一致性样例       |
| [05 社区治理](05-community-governance.md)   | 版权、贡献、审核、版本管理、撤回                   |
| [06 实施路线](06-implementation-roadmap.md) | 阶段任务、验收标准、回退与风险                     |

实施顺序以现有代码为验收标准逐段迁移：先审计、再抽离、最后接入，不按方案整体重写。审计结论与每个模块的保留／抽离／重设计决定在 [03 系统架构](03-system-architecture.md)。

## 版本与锚点

- 本版读取器接受 `schema_version` 为 `0.1.0` 的包，拒绝未知版本、未知字段和重复 JSON 键。发布新的文件契约时需显式更新读取支持和一致性样例。
- 同一学习包修订时保留 `lesson_id`，未变动的字幕段和词保留原 ID。段 ID 在包内唯一，词 ID 在所属段内唯一。包内位置用 `segment_id` 和有序 `token_ids` 表达。跨修订引用还要固定所读版本，具体归属见 [System Architecture](03-system-architecture.md)。

## 媒体与字幕

- 原文语言为 `en`，译文语言为 `zh-CN`。
- 包内 URL 使用 `https://` 开头，必须有主机名，端口须有效。URL 中禁止凭据、空白、ASCII 控制字符和反斜杠。
- `media.source_url` 指向 HTTPS 原视频页。`external_link` 供读者打开原片。`provider_embed` 使用 `https://www.youtube.com/watch?v=VIDEO_ID` 或无 `www` 的同等网址。`v` 查询参数恰有一个，值匹配 `[A-Za-z0-9_-]{11}`。客户端通过官方播放器嵌入，失败时提供原链接。
- `duration_ms`、段时间和词时间使用原视频的时间轴，以整数毫秒表示。时间和字符偏移均使用 JSON 整数形式，小数或指数形式会被拒绝。时间区间左闭右开，时长为正。字幕段按时间排序，允许间隔，区间不得重叠或超出媒体时长。每段提供原文与简体中文翻译，可附说话人。
- `tokens` 与段内原文的词逐一对应，顺序与原文一致。`start_char`、`end_char` 是零起点、左闭右开的 Unicode 码点索引。字母和数字构成词，组合附加符号 `U+0300–U+036F` 可跟在其后，`'`、`’` 和 `-` 可连接词内片段。空白和其余标点留在原文。JavaScript 读取时须按码点切片，例如用 `Array.from(text)` 建立码点数组。
- 每段至少 80% 的词有对齐时间，最低词数向上取整。词时间必须落在所属段内，按词序排列且互不重叠。未对齐词填写 `"timing": null`，保留字符区间。

## 词汇与授权

每项 `vocabulary` 记录 `headword`、中文语境释义 `gloss`、`segment_id` 与 `token_ids`。词引用必须指向同一字幕段内按原文顺序出现的连续词。一个词条可出现在不同位置，每个由段 ID 和有序词 ID 定义的区间只允许一条词汇记录。词面从首词的 `start_char` 切到末词的 `end_char`，保留中间的空白和标点。

`provenance` 分别给媒体、字幕、翻译和词汇提供 `attribution`、`basis` 与 `evidence_url`。如素材经改编，可在 `changes` 记录变化。离线校验只检查声明与链接格式。

[参考包](examples/welcome-to-wikisource.json) 使用 Bodhisattwa 的《Welcome to Wikisource》。包内对素材和学习数据声明 CC BY-SA 4.0，并记录署名和改动。 [原片与授权](https://commons.wikimedia.org/wiki/File:Welcome_to_Wikisource_-_short_explanatory_video.webm) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

## 校验与 V2 读取

在 `backend/` 使用仓库的 Python 3.12 虚拟环境运行，Windows 下设置 `PYTHONUTF8=1`。校验器只依赖现有 Pydantic 和标准库。

```sh
python -m app.slcs validate ../docs/slcs/examples/welcome-to-wikisource.json
python -m app.slcs schema
```

校验成功退出码为 `0`，读取或校验错误为 `1`，格式诊断给出字段路径或根路径。更新契约时，从第二条命令重新生成 `schema.json`。CI 的 backend job 会跑第一条命令校验参考包，贡献者提交的包应使用同一校验器。

V2 后端入口 `app.services.video_learning_material.load_video_material(payload)` 接收学习包的原始字节，返回只读视频材料。引用中的词全部有对齐时，定位区间从首词起点到末词终点。有任意词未对齐时使用整段时间。

内容指纹由含 `fingerprint_version` 和 `pack` 的对象计算。`pack` 是校验后的 JSON，包含模型补入的默认值。将对象键排序，保留数组顺序，使用紧凑分隔符、不额外转义非 ASCII 字符，编码为 UTF-8 后计算 SHA-256 并输出小写十六进制。文件排版和对象键顺序不影响指纹。当前指纹版本为 `slcs-pack-v1`（`app.slcs.FINGERPRINT_VERSION`）。会改变相同包指纹的契约改动须显式递增指纹版本。

## 一致性样例

| 输入                                                       | 预期结果                                                                                                                      |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 完整参考包                                                 | `welcome-to-wikisource` 有 12 个字幕段和 7 条词汇。`public domain` 对应 `s03` 的 `w04`、`w05`，定位到 `[13602, 14242)` 毫秒。 |
| 完整参考包或仅变更 JSON 排版和键顺序                       | 指纹均为 `d06cd8fa05b10e71d0030fb2e1a5569639c561d565117df91c14057f2f355ab4`。                                                 |
| 原文 `🎬 We’re café-ready!`                                | 两个词的码点区间分别为 `[2, 7)` 和 `[8, 18)`。第二个区间提取 `café-ready`。                                                   |
| 同一段引用连续的三个词，中间词未对齐，且全段仍达到对齐门槛 | 定位回退至整段时间。                                                                                                          |
| `schema_version` 改为 `0.2.0` 或删除首段 `translation`     | 校验失败，分别报告 `/schema_version` 或 `/segments/0/translation`。                                                           |

负例构造及 Schema 生成对照见 [SLCS 测试](../../backend/tests/test_slcs.py)，独立客户端的验收见 [Implementation Roadmap](06-implementation-roadmap.md)。
