"""A12 事件契约——事件版本、有效学习口径与 flow 关联的唯一正文。

这个模块只放**跨前后端的事实**，不放业务逻辑：版本号、事件名、有效类型集合。
前端镜像在 ``frontend/src/lib/analytics.ts``（只能靠测试对齐，不能靠 import）。

三条约定：

1. **版本只增不改**。给已有字段换含义必须升版本；消费方按 ``schema_version``
   决定怎么读。历史行按 v1 回填（迁移 ``b7c8d9e0f1a2``）。
2. **不新增第三套事件总线**。客户端原始交互仍在 ``behavior_events``（含
   ``flow_result`` 意图与 ``web_vital`` RUM），服务端学习结果仍在
   ``learning_events``；两者用 ``flow_id`` 对齐，不另造「结果事件表」。
3. **有效学习日只认 ``MEANINGFUL_EVENT_TYPES``**。激活、留存、DAU 的分母都从
   这里取，别处不得自造一份集合——2026-10 之前个人页与后台各有一套口径，正是
   这次要收敛的东西。
"""

from __future__ import annotations

#: v2 = flow_id/source；v3 = 独立教学事实（不进入有效学习日与旧计数）。
LEARNING_EVENT_SCHEMA_VERSION = 3

#: 客户端行为事件（``behavior_events``）的契约版本。
#: v2 = 带 flow_id；v3 = 词卡会话事件 ``gloss_open`` / ``replay``（A14 预注册指标）。
BEHAVIOR_EVENT_SCHEMA_VERSION = 3

#: 计入「有效学习日」的事件类型。``met_daily_goal`` 是元事件（由别的学习事件
#: 触发），不能单独把一天算成学习日；``watched_video`` 是 A02 定义的「当天看过
#: 视频」事实，算有效学习。
MEANINGFUL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "completed_video",
        "learned_words",
        "practiced_items",
        "reviewed_words",
        "watched_video",
    }
)

#: 学习流程路径（``learning_events.source`` 与客户端 ``flow_result`` 的 path 同值）。
FLOW_SOURCES: frozenset[str] = frozenset({"listening", "exam", "practice", "vocabulary", "video", "teaching"})

#: 客户端上报的意图事件名：流程开始 / 流程提交结果。
#: 只用于路径分析，**不是**学习事实；事实以 ``learning_events`` 为准。
CLIENT_FLOW_START = "flow_start"
CLIENT_FLOW_RESULT = "flow_result"

#: RUM 事件：``web_vital``（payload: metric/value/v/path）与 ``first_play``
#: （payload: ms/v）。两者都落 ``behavior_events``，不单独建表。
CLIENT_WEB_VITAL = "web_vital"
CLIENT_FIRST_PLAY = "first_play"
WEB_VITAL_METRICS: frozenset[str] = frozenset({"lcp", "inp", "cls"})

#: 观看页词卡会话（A14 单项实验的主指标事件，v3 起）。
#: ``gloss_open`` 在词卡打开时发一次，带本次词卡自己的 ``flow_id``；
#: ``replay`` 在触发原句重听时发，若它发生在同一词卡会话的窗口内，就带上
#: 同一个 ``flow_id``——「查词后回到同一句重听」因此可以直接按 flow_id 配对。
#: 两者都**不进** ``MEANINGFUL_EVENT_TYPES``：它们是交互意图，不是学习事实，
#: 不能让一次查词改变有效学习日的分母。
CLIENT_GLOSS_OPEN = "gloss_open"
CLIENT_REPLAY = "replay"

#: ``replay`` 被判定为「同一次查词的回看」的最大间隔（秒）。与
#: ``backend/app/services/measurement_service.py`` 的主指标窗口一致；前端镜像在
#: ``frontend/src/lib/analytics.ts`` 的 ``GLOSS_REPLAY_WINDOW_MS``。
GLOSS_REPLAY_WINDOW_SECONDS = 10


#: 学习事件里允许出现 ``source`` 的路径；``None`` 表示历史或非路径事件。
def normalize_source(source: str | None) -> str | None:
    """把未知 source 折成 None，避免拼写漂移污染按路径对账。"""
    if source is None:
        return None
    return source if source in FLOW_SOURCES else None
