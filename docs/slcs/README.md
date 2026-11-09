# SeeWord 学习包规范 SLCS v0.1

一个学习包用单个 UTF-8 JSON 文件描述一个外部视频及其英中学习材料。字段类型和必填项以 [JSON Schema](schema.json) 为准。下面的跨字段规则由参考校验器执行。

从社区贡献到 V2 学习体验的实施顺序见[后续设计思路](next-design.md)。

## 媒体与字幕

- `schema_version` 为 `0.1.0`，语言为 `en` 和 `zh-CN`。同一学习包修订时保留 `lesson_id`，未变动的字幕段和词保留原 ID。段 ID 在包内唯一，词 ID 在所属段内唯一。
- `media.source_url` 指向 HTTPS 原视频页。`external_link` 供读者打开原片。`provider_embed` 使用 `https://www.youtube.com/watch?v=VIDEO_ID` 或无 `www` 的同等网址，客户端通过官方播放器嵌入，失败时提供原链接。
- `duration_ms`、段时间和词时间使用原视频的时间轴，以整数毫秒表示。区间左闭右开，时长为正。字幕段按时间排序，允许间隔，区间不得重叠或超出媒体时长。每段提供原文与简体中文翻译，可附说话人。
- `tokens` 对应段内原文中的词，顺序与原文一致。`start_char`、`end_char` 是零起点、左闭右开的 Unicode 码点索引。字母和数字构成词，常用拉丁组合音标及词内撇号和连字符可留在词中。空白和其余标点留在原文。读者通过字符区间取词面。
- 每段至少 80% 的词有对齐时间，最低词数向上取整。词时间必须落在所属段内，按词序排列且互不重叠。未对齐词填写 `"timing": null`，保留字符区间。

## 词汇与授权

每项 `vocabulary` 记录 `headword`、中文语境释义 `gloss`、`segment_id` 与 `token_ids`。包内至少有一项。词引用必须指向同一字幕段内按原文顺序出现的连续词。同一个词跨多个字幕段各记一条（多语境），但同一段内的同一组词只能有一条——两个释义争一段原文会让读者与已存修订都拿不到唯一答案。

`provenance` 分别给媒体、字幕、翻译和词汇提供 `attribution`、`basis` 与 `evidence_url`。如素材经改编，可在 `changes` 记录变化。发布审核须核对实际授权范围和嵌入条件。离线校验只检查声明与链接格式。

[参考包](examples/welcome-to-wikisource.json) 使用 Bodhisattwa 的《Welcome to Wikisource》。素材与学习包按 CC BY-SA 4.0 提供，署名与改动记录见包内。 [原片与授权](https://commons.wikimedia.org/wiki/File:Welcome_to_Wikisource_-_short_explanatory_video.webm) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

## 校验与 V2 读取

在 `backend/` 使用仓库的 Python 3.12 虚拟环境运行，Windows 下设置 `PYTHONUTF8=1`。校验器只依赖现有 Pydantic 和标准库。

```sh
python -m app.slcs validate ../docs/slcs/examples/welcome-to-wikisource.json
python -m app.slcs schema
```

校验成功退出码为 `0`，输入或格式错误为 `1`，诊断指向出错字段。重复 JSON 键会被拒绝。更新契约时，从第二条命令重新生成 `schema.json`。CI 的 backend job 会跑第一条命令校验参考包，贡献者提交的包应使用同一校验器。

V2 后端入口 `app.services.video_learning_material.load_video_material(payload)` 接收学习包的原始字节，返回只读视频材料。词汇引用全部有对齐时，定位区间从首词起点到末词终点，其他情况使用整段时间。内容指纹是 `{"fingerprint_version", "pack"}` 这个对象（`pack` 为校验后的 JSON）按键排序、使用紧凑分隔符序列化成 UTF-8 后再计算的 SHA-256；`fingerprint_version` 当前是 `slcs-pack-v1`（`app.slcs.FINGERPRINT_VERSION`），契约变更时显式递增。列表顺序保留，文件排版和对象键顺序不影响指纹。
