# 后端逐文件索引

本分册 616 项。每项来自实际文件、符号/表/路由和引用提取；关系未显示的其余项在 [完整机器清单](../inventory.json)。无 import 不等于无调用，动态入口/收集器/配置关系另列。

## `backend`

### [backend/.dockerignore](../../../backend/.dockerignore)

该组件构建/版本化排除边界，防依赖、凭据和生成物误入制品。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/.env.example](../../../backend/.env.example)

安全的环境变量模板，不是真实凭据；加载方为对应组件 Settings/启动脚本。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [backend/.mypy-baseline](../../../backend/.mypy-baseline)

检查基线/带期限安全豁免；不是允许任意新增错误的白名单。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/.pip-audit-ignore](../../../backend/.pip-audit-ignore)

检查基线/带期限安全豁免；不是允许任意新增错误的白名单。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/CLAUDE.md](../../../backend/CLAUDE.md)

后端本机命令、测试门、迁移所有权和脚本操作边界。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [backend/Dockerfile.cloud](../../../backend/Dockerfile.cloud)

容器构建入口：该组件运行依赖和非 root/入口装配；与同组件 Compose build 相连。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/alembic.ini](../../../backend/alembic.ini)

Alembic 脚本路径、日志和 Python 路径配置；数据库 URL 来自应用设置。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `backend/app`

### [backend/app/__init__.py](../../../backend/app/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/scripts/check_schema_drift.py](../../../backend/scripts/check_schema_drift.py)、[backend/scripts/test_watch_mobile.py](../../../backend/scripts/test_watch_mobile.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 处置：保留。

## `backend/app/api`

### [backend/app/api/__init__.py](../../../backend/app/api/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)

把 Bearer/query token 统一解析为有效账号，组合必选/可选/管理员鉴权。

- 代码入口/类型：`resolve_token_user`、`get_current_user`、`get_optional_user`、`get_admin_user`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/core/time_utils.py](../../../backend/app/core/time_utils.py)、[backend/app/core/token_blacklist.py](../../../backend/app/core/token_blacklist.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)、[backend/app/api/v1/catalog.py](../../../backend/app/api/v1/catalog.py)；其余 27 项见机器清单。
- 处置：保留。

## `backend/app/api/v1`

### [backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_internal_callback.py](../../../backend/tests/test_internal_callback.py)、[backend/tests/test_media_access.py](../../../backend/tests/test_media_access.py)、[backend/tests/test_notifications.py](../../../backend/tests/test_notifications.py)、[backend/tests/test_phase1_b0_smoke.py](../../../backend/tests/test_phase1_b0_smoke.py)、[backend/tests/test_teaching_dialogue.py](../../../backend/tests/test_teaching_dialogue.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)

HTTP 接口边界：管理员工作台、用户和系统设置；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`get_worker_status`、`get_admin_stats`、`get_learning_metrics`、`list_admin_users`、`ban_user`、`change_user_role`、`get_settings`、`update_settings`、`list_admin_accounts`。
- 本文件路由片段（还需 router/装配前缀）：`GET /worker-status`、`GET /stats`、`GET /metrics/learning`、`GET /users`、`PATCH /users/{user_id}/ban`、`PATCH /users/{user_id}/role`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/admin.py](../../../backend/app/schemas/admin.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)；其余 5 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)

HTTP 接口边界：管理员首页内容编辑发布；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`get_video_content_state`、`generate_content`、`get_generation_state`、`save_draft`、`publish_content`、`restore_draft`、`preview_video`、`get_layout`、`save_layout_draft`、`publish_layout`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /videos/{video_id}`、`POST /videos/{video_id}/generate`、`GET /videos/{video_id}/generation`、`PUT /videos/{video_id}/draft`、`POST /videos/{video_id}/publish`、`POST /videos/{video_id}/restore-draft`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/home_content.py](../../../backend/app/schemas/home_content.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)

HTTP 接口边界：管理员教学候选内容预检、发布和撤回；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_drafts`、`create_draft`、`get_draft`、`update_draft`、`preflight`、`publish`、`withdraw`、`audit`。
- 本文件路由片段（还需 router/装配前缀）：`GET /drafts`、`POST /drafts`、`GET /drafts/{draft_id}`、`PUT /drafts/{draft_id}`、`GET /drafts/{draft_id}/preflight`、`POST /drafts/{draft_id}/publish`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/content_publication.py](../../../backend/app/schemas/content_publication.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)

HTTP 接口边界：短信/密码登录、注册、续签、改密、手机号和退出；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`sms_send_code`、`sms_login`、`sms_register`、`phone_login`、`refresh_token`、`sms_reset_password`、`change_phone`、`logout`、`change_password`。
- 本文件路由片段（还需 router/装配前缀）：`POST /sms/send-code`、`POST /sms/login`、`POST /sms/register`、`POST /phone-login`、`POST /refresh`、`POST /sms/reset-password`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)；其余 6 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)

HTTP 接口边界：原始浏览学习行为事件；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`post_event`、`post_batch`。
- 本文件路由片段（还需 router/装配前缀）：`POST /events`、`POST /events/batch`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/behavior.py](../../../backend/app/schemas/behavior.py)、[backend/app/services/behavior_service.py](../../../backend/app/services/behavior_service.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)

HTTP 接口边界：主题分类与精选视频流；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_categories`、`browse_feed`、`browse_featured`、`invalidate_browse_cache`。
- 本文件路由片段（还需 router/装配前缀）：`GET /categories`、`GET /feed`、`GET /featured`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/browse.py](../../../backend/app/schemas/browse.py)；其余 7 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/catalog.py](../../../backend/app/api/v1/catalog.py)

HTTP 接口边界：待收录视频候选池；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_catalog`、`catalog_summary`、`get_catalog_item`、`promote_catalog_item`、`mark_catalog_item`。
- 本文件路由片段（还需 router/装配前缀）：`GET `、`GET /summary`、`GET /{item_id}`、`POST /{item_id}/promote`、`PATCH /{item_id}`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/catalog.py](../../../backend/app/schemas/catalog.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)

HTTP 接口边界：频道列表、详情与管理员维护；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_channels`、`channel_detail`、`ChannelCreate`、`ChannelUpdate`、`ChannelAttachVideos`、`admin_list_channels`、`admin_create_channel`、`admin_update_channel`、`admin_delete_channel`、`admin_attach_videos`。
- 本文件路由片段（还需 router/装配前缀）：`GET `、`GET /{slug}`、`GET /admin/all`、`POST /admin`、`PATCH /admin/{channel_id}`、`DELETE /admin/{channel_id}`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)

HTTP 接口边界：视频/字幕/频道发现、词典、订阅、收藏与每日练习；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`learning_metadata`、`dictionary`、`search`、`subscriptions`、`subscribe`、`CreateSet`、`SetWords`、`RenameSet`、`create_set`、`rename_set`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /learning-metadata`、`GET /dictionary`、`GET /search`、`GET /subscriptions`、`PUT /subscriptions/{slug}`、`POST /sets`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/user_content.py](../../../backend/app/models/user_content.py)；其余 7 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/exam_pdfs.py](../../../backend/app/api/v1/exam_pdfs.py)

HTTP 接口边界：原卷 PDF 清单与受保护下载；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_exam_pdfs`、`download_exam_pdf`。
- 本文件路由片段（还需 router/装配前缀）：`GET `、`GET /{slug}/file`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/exam_pdf.py](../../../backend/app/schemas/exam_pdf.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/exams.py](../../../backend/app/api/v1/exams.py)

HTTP 接口边界：试卷浏览、错题、每日检查、作答与交卷；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_exams`、`start_daily_check`、`list_wrong_questions`、`redo_wrong_questions`、`get_exam_stats`、`list_attempts`、`get_attempt`、`submit_attempt`、`get_exam_paper`、`create_paper_attempt`。
- 本文件路由片段（还需 router/装配前缀）：`GET `、`GET /daily/start`、`GET /wrong`、`POST /wrong/redo`、`GET /stats`、`GET /attempts`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/exam.py](../../../backend/app/schemas/exam.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/external_connections.py](../../../backend/app/api/v1/external_connections.py)

HTTP 接口边界：本人外部连接的创建、轮换和撤销；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`ConnectionCreate`、`list_connections`、`create_connection`、`revoke_connection`、`rotate_connection`。
- 本文件路由片段（还需 router/装配前缀）：`GET `、`POST `、`POST /{connection_id}/revoke`、`POST /{connection_id}/rotate`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/favorites.py](../../../backend/app/api/v1/favorites.py)

HTTP 接口边界：视频收藏、笔记及观看元数据；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`NoteUpdate`、`FavoriteStatus`、`NoteResponse`、`WatchMeta`、`get_watch_meta`、`add_favorite`、`remove_favorite`、`get_note`、`upsert_note`、`delete_note`。
- 本文件路由片段（还需 router/装配前缀）：`GET /{video_id}/watch-meta`、`POST /{video_id}/favorite`、`DELETE /{video_id}/favorite`、`GET /{video_id}/note`、`PUT /{video_id}/note`、`DELETE /{video_id}/note`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/feedback.py](../../../backend/app/api/v1/feedback.py)

HTTP 接口边界：用户反馈与管理员回复/公告；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`submit_feedback`、`list_my_feedback`、`list_admin_feedback`、`update_admin_feedback`、`broadcast_admin_announcement`。
- 本文件路由片段（还需 router/装配前缀）：`POST `、`GET /mine`、`GET /feedback`、`PATCH /feedback/{feedback_id}`、`POST /announcements`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/feedback.py](../../../backend/app/models/feedback.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/feedback.py](../../../backend/app/schemas/feedback.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/home_editorial.py](../../../backend/app/api/v1/home_editorial.py)

HTTP 接口边界：公共已发布首页编排读取，不暴露草稿；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`home_editorial`。
- 本文件路由片段（还需 router/装配前缀）：`GET /home-editorial`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/schemas/home_content.py](../../../backend/app/schemas/home_content.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)

HTTP 接口边界：独立 GPU 的共享密钥转录回调、质量门与尾段派发；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`transcription_callback`。
- 本文件路由片段（还需 router/装配前缀）：`POST /transcription/callback`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)；其余 7 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_internal_callback.py](../../../backend/tests/test_internal_callback.py)。
- 处置：保留。

### [backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)

HTTP 接口边界：个人观看进度、词汇与学习记录；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_learning_records`、`continue_learning`、`get_learning_record`、`save_watch_progress`、`get_watch_progress`、`stats_weekly`、`stats_event_distribution`、`stats_heatmap`、`list_weekly_reports`、`latest_weekly_report`。
- 本文件路由片段（还需 router/装配前缀）：`GET /records`、`GET /continue`、`GET /records/{record_id}`、`PATCH /progress`、`GET /progress/{video_id}`、`GET /stats/weekly`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 11 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_phase1_b0_smoke.py](../../../backend/tests/test_phase1_b0_smoke.py)。
- 处置：保留。

### [backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)

HTTP 接口边界：学习档案、有效学习事件与掌握趋势；不是已删除的每日计划；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`get_learning_profile`、`refresh_learning_profile`、`get_mastery_trend`、`get_milestones`。
- 本文件路由片段（还需 router/装配前缀）：`GET /profile`、`POST /profile/refresh`、`GET /mastery-trend`、`GET /milestones`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/learning_plan.py](../../../backend/app/schemas/learning_plan.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 5 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)

HTTP 接口边界：修订/段/词锚点的多来源收词、复习事实与导出清理；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`OccurrenceRef`、`LessonTurn`、`save_vocabulary_source`、`vocabulary_sources`、`start_tutor_turn`、`tutor_history`。
- 本文件路由片段（还需 router/装配前缀）：`POST /lessons/{lesson_id}/vocabulary`、`GET /vocabulary/{word_id}/sources`、`POST /lessons/{lesson_id}/tutor`、`GET /lessons/{lesson_id}/tutor/{conversation_id}/messages`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 5 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/lessons.py](../../../backend/app/api/v1/lessons.py)

HTTP 接口边界：SLCS 课程导入、审核、签名发布、撤回和按权限读取；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`status`、`index`、`history`、`current`、`by_revision`、`state`、`progress`、`update_progress`、`activity`、`admin_index`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /_status`、`GET `、`GET /_history`、`GET /{lesson_id}`、`GET `、`GET /{lesson_id}/_state`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/lesson.py](../../../backend/app/schemas/lesson.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/listening.py](../../../backend/app/api/v1/listening.py)

HTTP 接口边界：字幕句冻结的听力练习会话；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`Start`、`Draft`、`videos`、`sessions`、`start`、`detail`、`draft`、`submit`。
- 本文件路由片段（还需 router/装配前缀）：`GET /videos`、`GET /sessions`、`POST /sessions`、`GET /sessions/{session_id}`、`PUT /sessions/{session_id}`、`POST /sessions/{session_id}/submit`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/listening.py](../../../backend/app/models/listening.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/listening.py](../../../backend/app/schemas/listening.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)

HTTP 接口边界：media；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`close_proxy_client`、`proxy_image`、`upload_shadowing_audio`、`serve_media`。
- 本文件路由片段（还需 router/装配前缀）：`GET /proxy`、`POST /shadowing-audio`、`GET /{file_path:path}`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/core/media_hosts.py](../../../backend/app/core/media_hosts.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/api/v1/exam_pdfs.py](../../../backend/app/api/v1/exam_pdfs.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_media_access.py](../../../backend/tests/test_media_access.py)。
- 处置：保留。

### [backend/app/api/v1/notes.py](../../../backend/app/api/v1/notes.py)

HTTP 接口边界：本人笔记库与当前视频可用性；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_notes`。
- 本文件路由片段（还需 router/装配前缀）：`GET `。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)

HTTP 接口边界：通知列表、已读、偏好和鉴权 WebSocket；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`notification_websocket`、`list_notifications`、`unread_count`、`mark_as_read`、`mark_all_as_read`、`get_notification_preferences`、`update_notification_preferences`。
- 本文件路由片段（还需 router/装配前缀）：`WEBSOCKET /ws`、`GET `、`GET /unread-count`、`PATCH /{notification_id}/read`、`PATCH /read-all`、`GET /preferences`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_notifications.py](../../../backend/tests/test_notifications.py)、[backend/tests/test_watch_baseline.py](../../../backend/tests/test_watch_baseline.py)。
- 处置：保留。

### [backend/app/api/v1/presence.py](../../../backend/app/api/v1/presence.py)

HTTP 接口边界：可见页面在线心跳；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`heartbeat`。
- 本文件路由片段（还需 router/装配前缀）：`POST /heartbeat`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/common.py](../../../backend/app/schemas/common.py)。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/recommendations.py](../../../backend/app/api/v1/recommendations.py)

HTTP 接口边界：首页与分类推荐接口；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`home_feed`、`category_feed`。
- 本文件路由片段（还需 router/装配前缀）：`GET /home`、`GET /category/{tag}`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/recommendation.py](../../../backend/app/schemas/recommendation.py)、[backend/app/services/recommendation_service.py](../../../backend/app/services/recommendation_service.py)。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/shadowing.py](../../../backend/app/api/v1/shadowing.py)

HTTP 接口边界：退役录音功能的鉴权兼容壳，不执行跟读；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_shadowing_attempts`、`create_shadowing_attempt`、`update_shadowing_attempt`、`delete_shadowing_attempt`、`shadowing_stats`。
- 本文件路由片段（还需 router/装配前缀）：`GET /attempts`、`POST /attempts`、`PATCH /attempts/{attempt_id}`、`DELETE /attempts/{attempt_id}`、`GET /stats`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/retired_features.py](../../../backend/app/services/retired_features.py)。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)

HTTP 接口边界：确定性教学材料、会话、作答、提示和揭晓；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`content`、`sessions`、`create`、`create_quiz`、`action`、`detail`、`context`、`draft`、`attempt`、`hint`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /content`、`GET /sessions`、`POST /sessions`、`POST /quizzes`、`POST /sessions/{session_id}/actions`、`GET /sessions/{session_id}`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/learning_context.py](../../../backend/app/schemas/learning_context.py)、[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)；其余 5 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)

HTTP 接口边界：持久模型运行、租约、取消、事件恢复与流式消息写入；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`CreateRun`、`create_run`、`create_turn`、`messages`、`resume_cursor`、`get_run`、`cancel_run`、`run_events`。
- 本文件路由片段（还需 router/装配前缀）：`POST /sessions/{session_id}/runs`、`POST /sessions/{session_id}/messages`、`GET /sessions/{session_id}/messages`、`GET /runs/{run_id}`、`POST /runs/{run_id}/cancel`、`GET /runs/{run_id}/events`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_teaching_dialogue.py](../../../backend/tests/test_teaching_dialogue.py)、[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)。
- 处置：保留。

### [backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)

HTTP 接口边界：独立导师聊天生命周期及共享回合入口；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`create_conversation`、`list_conversations`、`get_conversation`、`patch_conversation`、`delete_conversation`、`create_turn`、`messages`。
- 本文件路由片段（还需 router/装配前缀）：`POST /conversations`、`GET /conversations`、`GET /conversations/{conversation_id}`、`PATCH /conversations/{conversation_id}`、`DELETE /conversations/{conversation_id}`、`POST /conversations/{conversation_id}/messages`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)、[backend/app/schemas/tutor.py](../../../backend/app/schemas/tutor.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 5 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)。
- 处置：保留。

### [backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)

HTTP 接口边界：本人资料/偏好、头像、引导、注销申请和导出任务；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`get_me`、`get_my_overview`、`update_me`、`upload_avatar`、`complete_onboarding`、`get_preferences`、`update_preferences`、`get_deletion_status`、`request_deletion`、`cancel_deletion`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /me`、`GET /me/overview`、`PATCH /me`、`POST /me/avatar`、`POST /me/onboarding`、`GET /me/preferences`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/core/uploads.py](../../../backend/app/core/uploads.py)；其余 7 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)

HTTP 接口边界：videos；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`list_public_videos`、`get_demo_video`、`search_videos`、`suggest_search`、`hot_searches`、`search_subtitles`、`list_admin_videos`、`get_admin_pending_count`、`update_admin_video`、`delete_admin_video`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /public`、`GET /demo`、`GET /search`、`GET /search/suggest`、`GET /search/hot`、`GET /search/subtitles`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)；其余 18 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_phase1_b0_smoke.py](../../../backend/tests/test_phase1_b0_smoke.py)。
- 处置：保留。

### [backend/app/api/v1/vocab_sets.py](../../../backend/app/api/v1/vocab_sets.py)

HTTP 接口边界：词集列表、加入学习和快速过筛操作；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`CollectSetRequest`、`SieveJudgeRequest`、`collect_vocab_set`、`list_vocab_sets`、`get_vocab_set`、`get_sieve_state`、`mark_sieve_word_learned`、`unmark_sieve_word_learned`、`judge_sieve_word`、`celebrate_vocab_set`。
- 本文件路由片段（还需 router/装配前缀）：`POST `、`GET `、`GET /{set_id}`、`GET /{set_id}/sieve`、`POST /{set_id}/words/{set_word_id}/learned`、`POST /{set_id}/words/{set_word_id}/unmark`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/vocab_set.py](../../../backend/app/schemas/vocab_set.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)

HTTP 接口边界：个人词条、复习、自评、训练与观看上下文；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`VocabPracticeResultItem`、`VocabPracticeSubmitRequest`、`VocabPracticeSubmitResponse`、`vocabulary_stats`、`get_daily_session`、`get_vocabulary_preferences`、`update_vocabulary_preferences`、`get_current_study_session`、`start_study_session`、`answer_study_session`（其余见机器清单）。
- 本文件路由片段（还需 router/装配前缀）：`GET /stats`、`GET /daily-session`、`GET /preferences`、`PUT /preferences`、`GET /sessions/current`、`POST /sessions`；完整列表见机器清单。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)；其余 8 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

### [backend/app/api/v1/words.py](../../../backend/app/api/v1/words.py)

HTTP 接口边界：点词静态词典、预生成 AI 注释和真题例句聚合；负责请求身份/参数与响应，调用列出的 service/模型。

- 代码入口/类型：`WordGloss`、`gloss_word`、`gloss_static`、`gloss_enrich`。
- 本文件路由片段（还需 router/装配前缀）：`GET /gloss`、`GET /gloss/static`、`GET /gloss/enrich`。
- 直接依赖：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

## `backend/app/core`

### [backend/app/core/__init__.py](../../../backend/app/core/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/tests/conftest.py](../../../backend/tests/conftest.py)、[backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)、[backend/tests/test_auth.py](../../../backend/tests/test_auth.py)、[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)、[backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)、[backend/tests/test_redis_close.py](../../../backend/tests/test_redis_close.py)；其余 4 项见机器清单。
- 处置：保留。

### [backend/app/core/cache.py](../../../backend/app/core/cache.py)

共享基础：Redis 可降级缓存封装；被上层多个领域复用。

- 代码入口/类型：`cache_get`、`cache_set`、`cache_delete`、`cache_get_json`、`cache_set_json`、`cached`。
- 直接依赖：[backend/app/core/redis.py](../../../backend/app/core/redis.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/app/services/ranking_service.py](../../../backend/app/services/ranking_service.py)、[backend/app/services/recommendation_service.py](../../../backend/app/services/recommendation_service.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)；其余 4 项见机器清单。
- 处置：保留。

### [backend/app/core/config.py](../../../backend/app/core/config.py)

共享基础：环境配置、合法环境名与生产安全校验；被上层多个领域复用。

- 代码入口/类型：`Settings`、`get_settings`。
- 直接依赖：[backend/app/services/teaching/content_receipts.py](../../../backend/app/services/teaching/content_receipts.py)。
- 直接使用者：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)、[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)；其余 82 项见机器清单。
- 处置：保留。

### [backend/app/core/database.py](../../../backend/app/core/database.py)

共享基础：懒建 async engine/session、请求会话与显式提交辅助；被上层多个领域复用。

- 代码入口/类型：`Base`、`get_engine`、`get_session_maker`、`get_async_session_maker`、`get_db`、`commit_refresh`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)；其余 165 项见机器清单。
- 处置：保留。

### [backend/app/core/errors.py](../../../backend/app/core/errors.py)

共享基础：错误码、业务异常和安全的统一 envelope 格式化；被上层多个领域复用。

- 代码入口/类型：`ErrorCode`、`AppError`、`DomainError`、`NotFoundError`、`BadRequestError`、`ForbiddenError`、`UnprocessableEntityError`、`ConflictError`、`ServiceUnavailableError`、`format_validation_errors`（其余见机器清单）。
- 直接使用者：[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)、[backend/app/api/v1/external_connections.py](../../../backend/app/api/v1/external_connections.py)、[backend/app/api/v1/lessons.py](../../../backend/app/api/v1/lessons.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)；其余 82 项见机器清单。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)

共享基础：考试词难度排序与展示规则权威；被上层多个领域复用。

- 代码入口/类型：`level_order`、`max_level`、`should_display`、`display_level`、`normalize_levels`、`normalize_word_levels`、`validate_word_levels`。
- 直接使用者：[backend/app/models/types.py](../../../backend/app/models/types.py)、[backend/app/schemas/user.py](../../../backend/app/schemas/user.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)、[backend/app/services/difficulty_service.py](../../../backend/app/services/difficulty_service.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)；其余 8 项见机器清单。
- 处置：保留。

### [backend/app/core/heartbeat.py](../../../backend/app/core/heartbeat.py)

共享基础：云端 worker/beat 活性 key 与时间判断；被上层多个领域复用。

- 代码入口/类型：`touch`、`age_seconds`。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)、[backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)、[backend/app/tasks/health_tasks.py](../../../backend/app/tasks/health_tasks.py)、[backend/tests/test_health_heartbeats.py](../../../backend/tests/test_health_heartbeats.py)、[backend/tests/test_health_monitor.py](../../../backend/tests/test_health_monitor.py)。
- 处置：保留。

### [backend/app/core/limiter.py](../../../backend/app/core/limiter.py)

共享基础：按环境和身份/IP 的请求限速；被上层多个领域复用。

- 代码入口/类型：`rate_limit`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)、[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)；其余 26 项见机器清单。
- 处置：保留。

### [backend/app/core/logging.py](../../../backend/app/core/logging.py)

共享基础：结构化日志与请求/任务关联；被上层多个领域复用。

- 代码入口/类型：`configure_logging`、`get_logger`、`mask_phone`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/core/observability.py](../../../backend/app/core/observability.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)；其余 28 项见机器清单。
- 处置：保留。

### [backend/app/core/media_hosts.py](../../../backend/app/core/media_hosts.py)

共享基础：外站媒体主机白名单和 Referer 策略；被上层多个领域复用。

- 代码入口/类型：`host_allowed`、`referer_for`。
- 直接使用者：[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)、[backend/app/services/thumbnail_service.py](../../../backend/app/services/thumbnail_service.py)。
- 处置：保留。

### [backend/app/core/media_probe.py](../../../backend/app/core/media_probe.py)

共享基础：云端 ffprobe 音频视频时长读取；被上层多个领域复用。

- 代码入口/类型：`get_video_duration`。
- 直接使用者：[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_video_duration.py](../../../backend/scripts/backfill_video_duration.py)。
- 处置：保留。

### [backend/app/core/observability.py](../../../backend/app/core/observability.py)

共享基础：Sentry 按进程角色初始化与敏感信息清洗；被上层多个领域复用。

- 代码入口/类型：`init_sentry`、`celery_role`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redaction.py](../../../backend/app/core/redaction.py)。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)。
- 处置：保留。

### [backend/app/core/redaction.py](../../../backend/app/core/redaction.py)

共享基础：token/口令连接串等外发日志脱敏；被上层多个领域复用。

- 代码入口/类型：`redact`、`redact_value`。
- 直接使用者：[backend/app/core/observability.py](../../../backend/app/core/observability.py)、[backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)、[backend/tests/test_redaction.py](../../../backend/tests/test_redaction.py)。
- 处置：保留。

### [backend/app/core/redis.py](../../../backend/app/core/redis.py)

共享基础：进程复用的 async Redis 连接池与关闭；被上层多个领域复用。

- 代码入口/类型：`get_redis`、`close_redis`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/api/v1/presence.py](../../../backend/app/api/v1/presence.py)、[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/token_blacklist.py](../../../backend/app/core/token_blacklist.py)、[backend/app/main.py](../../../backend/app/main.py)；其余 19 项见机器清单。
- 处置：保留。

### [backend/app/core/security.py](../../../backend/app/core/security.py)

共享基础：密码哈希/强度和 JWT 创建/解码；被上层多个领域复用。

- 代码入口/类型：`hash_password`、`verify_password`、`create_token`、`decode_token`、`validate_password_strength`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/core/limiter.py](../../../backend/app/core/limiter.py)、[backend/app/schemas/user.py](../../../backend/app/schemas/user.py)、[backend/scripts/create_admin.py](../../../backend/scripts/create_admin.py)、[backend/scripts/smoke_free_access.py](../../../backend/scripts/smoke_free_access.py)；其余 27 项见机器清单。
- 处置：保留。

### [backend/app/core/time_utils.py](../../../backend/app/core/time_utils.py)

共享基础：UTC aware/naive 时间归一与序列化；被上层多个领域复用。

- 代码入口/类型：`iso_or_none`、`to_aware_utc`。
- 直接使用者：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/services/admin_service.py](../../../backend/app/services/admin_service.py)、[backend/app/services/admin_stats.py](../../../backend/app/services/admin_stats.py)。
- 处置：保留。

### [backend/app/core/token_blacklist.py](../../../backend/app/core/token_blacklist.py)

共享基础：Redis 令牌撤销与单次 refresh 消费，故障按显式策略降级；被上层多个领域复用。

- 代码入口/类型：`blacklist_token`、`claim_token_once`、`is_token_blacklisted`。
- 直接依赖：[backend/app/core/redis.py](../../../backend/app/core/redis.py)。
- 直接使用者：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[scripts/isolation/test_a07_redis_recovery.py](../../../scripts/isolation/test_a07_redis_recovery.py)。
- 处置：保留。

### [backend/app/core/uploads.py](../../../backend/app/core/uploads.py)

共享基础：上传分块限量读取，避免先全量读入再判断大小；被上层多个领域复用。

- 代码入口/类型：`read_upload_bounded`。
- 直接使用者：[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/tests/test_uploads.py](../../../backend/tests/test_uploads.py)。
- 处置：保留。

## `backend/app/integrations`

### [backend/app/integrations/__init__.py](../../../backend/app/integrations/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `backend/app/integrations/mcp`

### [backend/app/integrations/mcp/__init__.py](../../../backend/app/integrations/mcp/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/tests/test_mcp_adapter.py](../../../backend/tests/test_mcp_adapter.py)。
- 处置：保留。

### [backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)

在线官方 MCP SDK 挂载适配与凭据 gate；工具复用现有教学服务，不把协议当业务授权。

- 代码入口/类型：`CredentialGate`、`invoke`、`create_mcp_app`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_mcp_adapter.py](../../../backend/tests/test_mcp_adapter.py)。
- 处置：保留。

## `backend/app`

### [backend/app/main.py](../../../backend/app/main.py)

FastAPI 唯一装配入口：路由、中间件、统一错误、健康检查及应用生命周期。

- 代码入口/类型：`lifespan`、`create_app`。
- 本文件路由片段（还需 router/装配前缀）：`GET /health`、`GET /health/heartbeats`、`API_ROUTE /api/v1/mcp/`。
- 直接依赖：[backend/app/__init__.py](../../../backend/app/__init__.py)、[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)；其余 46 项见机器清单。
- 直接使用者：[backend/run_with_utf8.py](../../../backend/run_with_utf8.py)、[backend/scripts/smoke_free_access.py](../../../backend/scripts/smoke_free_access.py)、[backend/scripts/smoke_lesson_publication.py](../../../backend/scripts/smoke_lesson_publication.py)、[backend/scripts/smoke_takedown.py](../../../backend/scripts/smoke_takedown.py)、[backend/scripts/smoke_vocab_loop.py](../../../backend/scripts/smoke_vocab_loop.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)；其余 14 项见机器清单。
- 配置/资源消费者：[docker-compose.yml](../../../docker-compose.yml)、[docker-compose.prod.yml](../../../docker-compose.prod.yml)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 处置：保留。

## `backend/app/models`

### [backend/app/models/__init__.py](../../../backend/app/models/__init__.py)

按依赖导入全部 ORM 模型，填充 Base.metadata；应用/迁移/建表测试必需。

- 直接依赖：[backend/app/models/admin_setting.py](../../../backend/app/models/admin_setting.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/catalog.py](../../../backend/app/models/catalog.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)、[backend/app/models/data_export.py](../../../backend/app/models/data_export.py)；其余 31 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/migrations/env.py](../../../backend/migrations/env.py)、[backend/scripts/check_schema_drift.py](../../../backend/scripts/check_schema_drift.py)、[backend/scripts/inventory_orphan_media.py](../../../backend/scripts/inventory_orphan_media.py)、[backend/scripts/test_watch_mobile.py](../../../backend/scripts/test_watch_mobile.py)；其余 5 项见机器清单。
- 处置：保留。

### [backend/app/models/admin_setting.py](../../../backend/app/models/admin_setting.py)

数据库模型：admin_setting。表 admin_settings；业务读写由上游服务完成。

- 代码入口/类型：`AdminSetting`。
- 表：`admin_settings`；外键 未声明直接外键。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/admin_service.py](../../../backend/app/services/admin_service.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_admin_panel.py](../../../backend/tests/test_admin_panel.py)、[backend/tests/test_pipeline_watchdog.py](../../../backend/tests/test_pipeline_watchdog.py)。
- 处置：保留。

### [backend/app/models/behavior.py](../../../backend/app/models/behavior.py)

数据库模型：原始浏览学习行为事件。表 behavior_events；业务读写由上游服务完成。

- 代码入口/类型：`BehaviorEvent`。
- 表：`behavior_events`；外键 `users.id`、`videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/behavior_service.py](../../../backend/app/services/behavior_service.py)、[backend/app/services/measurement_service.py](../../../backend/app/services/measurement_service.py)、[backend/app/services/ranking_service.py](../../../backend/app/services/ranking_service.py)、[backend/app/services/recommendation_service.py](../../../backend/app/services/recommendation_service.py)；其余 13 项见机器清单。
- 处置：保留。

### [backend/app/models/catalog.py](../../../backend/app/models/catalog.py)

数据库模型：待收录视频候选池。表 catalog_items；业务读写由上游服务完成。

- 代码入口/类型：`CatalogStatus`、`CatalogItem`。
- 表：`catalog_items`；外键 `videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/catalog_service.py](../../../backend/app/services/catalog_service.py)、[backend/tests/test_catalog_api.py](../../../backend/tests/test_catalog_api.py)、[backend/tests/test_catalog_pg.py](../../../backend/tests/test_catalog_pg.py)。
- 处置：保留。

### [backend/app/models/channel.py](../../../backend/app/models/channel.py)

数据库模型：频道身份和展示信息。表 channels；业务读写由上游服务完成。

- 代码入口/类型：`Channel`。
- 表：`channels`；外键 未声明直接外键。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)；其余 7 项见机器清单。
- 处置：保留。

### [backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)

数据库模型：教学可编辑候选和发布操作回执。表 teaching_content_drafts、content_publication_operations；业务读写由上游服务完成。

- 代码入口/类型：`TeachingContentDraft`、`ContentPublicationOperation`。
- 表：`teaching_content_drafts`、`content_publication_operations`；外键 `exam_analysis_revisions.id`、`users.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)、[backend/tests/test_content_publication.py](../../../backend/tests/test_content_publication.py)、[backend/tests/test_content_publication_pg.py](../../../backend/tests/test_content_publication_pg.py)、[backend/tests/test_teaching_content_cli.py](../../../backend/tests/test_teaching_content_cli.py)、[backend/tests/test_v2_schema_gating.py](../../../backend/tests/test_v2_schema_gating.py)。
- 处置：保留。

### [backend/app/models/data_export.py](../../../backend/app/models/data_export.py)

数据库模型：异步数据导出状态和短期下载记录。表 data_export_tasks；业务读写由上游服务完成。

- 代码入口/类型：`DataExportTask`。
- 表：`data_export_tasks`；外键 `users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/scripts/inventory_orphan_media.py](../../../backend/scripts/inventory_orphan_media.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_account_deletion.py](../../../backend/tests/test_account_deletion.py)。
- 处置：保留。

### [backend/app/models/engagement.py](../../../backend/app/models/engagement.py)

数据库模型：用户点赞事实与唯一关系。表 video_likes；业务读写由上游服务完成。

- 代码入口/类型：`VideoLike`。
- 表：`video_likes`；外键 `videos.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/video_like_service.py](../../../backend/app/services/video_like_service.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)。
- 处置：保留。

### [backend/app/models/exam_corpus.py](../../../backend/app/models/exam_corpus.py)

数据库模型：真题例句、词索引和词频语料。表 exam_sentences、exam_sentence_words、exam_word_freq；业务读写由上游服务完成。

- 代码入口/类型：`ExamSentence`、`ExamSentenceWord`、`ExamWordFreq`。
- 表：`exam_sentences`、`exam_sentence_words`、`exam_word_freq`；外键 `exam_sentences.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/exam_corpus.py](../../../backend/app/services/exam_corpus.py)、[backend/scripts/ingest_exam_papers.py](../../../backend/scripts/ingest_exam_papers.py)。
- 处置：保留。

### [backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)

数据库模型：试卷、题目、作答会话和冻结答案事实。表 exam_papers、exam_questions、exam_sessions、exam_answers；业务读写由上游服务完成。

- 代码入口/类型：`ExamPaper`、`ExamQuestion`、`ExamSession`、`ExamAnswer`。
- 表：`exam_papers`、`exam_questions`、`exam_sessions`、`exam_answers`；外键 `exam_papers.id`、`users.id`、`videos.id`、`exam_papers.id`、`exam_sessions.id`、`exam_questions.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/daily_recommendation_service.py](../../../backend/app/services/daily_recommendation_service.py)、[backend/app/services/exam_service.py](../../../backend/app/services/exam_service.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)、[backend/app/services/question_exposure_service.py](../../../backend/app/services/question_exposure_service.py)；其余 18 项见机器清单。
- 处置：保留。

### [backend/app/models/favorite.py](../../../backend/app/models/favorite.py)

数据库模型：按用户/视频保存的收藏和笔记。表 user_favorites、user_notes；业务读写由上游服务完成。

- 代码入口/类型：`UserFavorite`、`UserNote`。
- 表：`user_favorites`、`user_notes`；外键 `users.id`、`videos.id`、`users.id`、`videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/favorites.py](../../../backend/app/api/v1/favorites.py)、[backend/app/api/v1/notes.py](../../../backend/app/api/v1/notes.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)；其余 10 项见机器清单。
- 处置：保留。

### [backend/app/models/feedback.py](../../../backend/app/models/feedback.py)

数据库模型：用户反馈与管理员回复/公告。表 feedbacks；业务读写由上游服务完成。

- 代码入口/类型：`Feedback`。
- 表：`feedbacks`；外键 `users.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/feedback.py](../../../backend/app/api/v1/feedback.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_feedback.py](../../../backend/tests/test_feedback.py)。
- 处置：保留。

### [backend/app/models/home_content.py](../../../backend/app/models/home_content.py)

数据库模型：首页内容草稿、不可变版本、布局及生成状态。表 home_content_drafts、home_content_revisions、home_page_config；业务读写由上游服务完成。

- 代码入口/类型：`HomeContentGenerationStatus`、`HomeContentDraft`、`HomeContentRevision`、`HomePageConfig`。
- 表：`home_content_drafts`、`home_content_revisions`、`home_page_config`；外键 `videos.id`、`users.id`、`users.id`、`videos.id`、`users.id`、`users.id`、`users.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)、[backend/app/tasks/home_content_tasks.py](../../../backend/app/tasks/home_content_tasks.py)、[backend/tests/test_home_content.py](../../../backend/tests/test_home_content.py)、[backend/tests/test_home_content_concurrency.py](../../../backend/tests/test_home_content_concurrency.py)；其余 1 项见机器清单。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/models/learning.py](../../../backend/app/models/learning.py)

数据库模型：个人观看进度、词汇与学习记录。表 learning_records、vocabulary；业务读写由上游服务完成。

- 代码入口/类型：`LearningRecord`、`Vocabulary`。
- 表：`learning_records`、`vocabulary`；外键 `users.id`、`videos.id`、`users.id`、`videos.id`、`subtitles.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)；其余 57 项见机器清单。
- 处置：保留。

### [backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)

数据库模型：学习档案、有效学习事件与掌握趋势；不是已删除的每日计划。表 user_learning_profiles、learning_events；业务读写由上游服务完成。

- 代码入口/类型：`UserLearningProfile`、`LearningEvent`。
- 表：`user_learning_profiles`、`learning_events`；外键 `users.id`、`users.id`、`videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/admin_stats.py](../../../backend/app/services/admin_stats.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)；其余 25 项见机器清单。
- 处置：保留。

### [backend/app/models/lesson.py](../../../backend/app/models/lesson.py)

数据库模型：课程、修订、操作、进度与学习活动。表 lessons、lesson_revisions、lesson_operations、lesson_progress、lesson_activities；业务读写由上游服务完成。

- 代码入口/类型：`Lesson`、`LessonRevision`、`LessonOperation`、`LessonProgress`、`LessonActivity`。
- 表：`lessons`、`lesson_revisions`、`lesson_operations`、`lesson_progress`、`lesson_activities`；外键 `lesson_revisions.id`、`lessons.id`、`users.id`、`users.id`、`lesson_revisions.id`、`users.id`、`lessons.id`、`lesson_revisions.id`、`users.id`、`lesson_revisions.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/lesson_progress.py](../../../backend/app/services/lesson_progress.py)、[backend/app/services/lesson_tutor.py](../../../backend/app/services/lesson_tutor.py)、[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)；其余 7 项见机器清单。
- 处置：保留。

### [backend/app/models/lesson_learning.py](../../../backend/app/models/lesson_learning.py)

数据库模型：修订/段/词锚点的多来源收词、复习事实与导出清理。表 lesson_vocabulary_sources、vocabulary_review_log、lesson_tutor_anchors；业务读写由上游服务完成。

- 代码入口/类型：`LessonVocabularySource`、`VocabularyReviewLog`、`LessonTutorAnchor`。
- 表：`lesson_vocabulary_sources`、`vocabulary_review_log`、`lesson_tutor_anchors`；外键 `vocabulary.id`、`lesson_revisions.id`、`users.id`、`vocabulary.id`、`tutor_conversations.id`、`lesson_revisions.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/lesson_tutor.py](../../../backend/app/services/lesson_tutor.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)、[backend/tests/test_lesson_learning.py](../../../backend/tests/test_lesson_learning.py)。
- 处置：保留。

### [backend/app/models/listening.py](../../../backend/app/models/listening.py)

数据库模型：字幕句冻结的听力练习会话。表 listening_sessions；业务读写由上游服务完成。

- 代码入口/类型：`ListeningSession`。
- 表：`listening_sessions`；外键 `users.id`、`videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/listening.py](../../../backend/app/api/v1/listening.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)；其余 2 项见机器清单。
- 处置：保留。

### [backend/app/models/media_cleanup.py](../../../backend/app/models/media_cleanup.py)

数据库模型：注销后文件删除重试队列。表 media_cleanup_tasks；业务读写由上游服务完成。

- 代码入口/类型：`MediaCleanupTask`。
- 表：`media_cleanup_tasks`；外键 未声明直接外键。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/scripts/inventory_orphan_media.py](../../../backend/scripts/inventory_orphan_media.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)。
- 处置：保留。

### [backend/app/models/milestone.py](../../../backend/app/models/milestone.py)

数据库模型：历史成就记录和仍使用的每日掌握快照。表 user_milestones、mastery_snapshots；业务读写由上游服务完成。

- 代码入口/类型：`UserMilestone`、`MasterySnapshot`。
- 表：`user_milestones`、`mastery_snapshots`；外键 `users.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/milestone_service.py](../../../backend/app/services/milestone_service.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_milestone_service.py](../../../backend/tests/test_milestone_service.py)。
- 处置：保留。

### [backend/app/models/notification.py](../../../backend/app/models/notification.py)

数据库模型：本人通知记录。表 notifications；业务读写由上游服务完成。

- 代码入口/类型：`Notification`。
- 表：`notifications`；外键 `users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_feedback.py](../../../backend/tests/test_feedback.py)；其余 5 项见机器清单。
- 处置：保留。

### [backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)

数据库模型：数据库 outbox 派发、重试、过期放弃和积压盘点。表 pipeline_dispatches；业务读写由上游服务完成。

- 代码入口/类型：`PipelineDispatch`。
- 表：`pipeline_dispatches`；外键 `videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/measurement_service.py](../../../backend/app/services/measurement_service.py)、[backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)、[backend/tests/test_internal_callback.py](../../../backend/tests/test_internal_callback.py)、[backend/tests/test_measurement_service.py](../../../backend/tests/test_measurement_service.py)、[backend/tests/test_pipeline_dispatch.py](../../../backend/tests/test_pipeline_dispatch.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/app/models/preferences.py](../../../backend/app/models/preferences.py)

数据库模型：个人学习与通知偏好。表 user_preferences；业务读写由上游服务完成。

- 代码入口/类型：`UserPreferences`。
- 表：`user_preferences`；外键 `users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)、[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/exam_service.py](../../../backend/app/services/exam_service.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)；其余 9 项见机器清单。
- 处置：保留。

### [backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)

数据库模型：跨考试/教学的题目答案暴露事实。表 user_question_exposures、user_exposure_mapping_states；业务读写由上游服务完成。

- 代码入口/类型：`UserQuestionExposure`、`UserExposureMappingState`。
- 表：`user_question_exposures`、`user_exposure_mapping_states`；外键 `users.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/question_exposure_service.py](../../../backend/app/services/question_exposure_service.py)、[backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)、[backend/scripts/seed_teaching_quiz.py](../../../backend/scripts/seed_teaching_quiz.py)、[backend/tests/teaching_fixtures.py](../../../backend/tests/teaching_fixtures.py)；其余 5 项见机器清单。
- 处置：保留。

### [backend/app/models/study_session.py](../../../backend/app/models/study_session.py)

数据库模型：可恢复的单词训练轮次和逐词项目。表 study_sessions、study_session_items；业务读写由上游服务完成。

- 代码入口/类型：`StudySession`、`StudySessionItem`。
- 表：`study_sessions`、`study_session_items`；外键 `users.id`、`study_sessions.id`、`vocabulary.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/study_session_service.py](../../../backend/app/services/study_session_service.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_study_sessions.py](../../../backend/tests/test_study_sessions.py)、[backend/tests/test_vocabulary_transactions.py](../../../backend/tests/test_vocabulary_transactions.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)

数据库模型：英文/译文、顺序、句词时间和难度标注。表 subtitles；业务读写由上游服务完成。

- 代码入口/类型：`Subtitle`。
- 表：`subtitles`；外键 `videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/types.py](../../../backend/app/models/types.py)。
- 直接使用者：[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/difficulty_service.py](../../../backend/app/services/difficulty_service.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/home_content_content.py](../../../backend/app/services/home_content_content.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)；其余 64 项见机器清单。
- 处置：保留。

### [backend/app/models/subtitle_resegment_snapshot.py](../../../backend/app/models/subtitle_resegment_snapshot.py)

数据库模型：整批重断句前的恢复快照。表 subtitle_resegment_snapshots；业务读写由上游服务完成。

- 代码入口/类型：`SubtitleResegmentSnapshot`。
- 表：`subtitle_resegment_snapshots`；外键 `videos.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/subtitle_edit_service.py](../../../backend/app/services/subtitle_edit_service.py)、[backend/tests/test_subtitle_resegment.py](../../../backend/tests/test_subtitle_resegment.py)。
- 处置：保留。

### [backend/app/models/subtitle_revision.py](../../../backend/app/models/subtitle_revision.py)

数据库模型：单条字幕变更审计与回退前后值。表 subtitle_revisions；业务读写由上游服务完成。

- 代码入口/类型：`SubtitleRevision`。
- 表：`subtitle_revisions`；外键 `subtitles.id`、`videos.id`、`users.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/subtitle_edit_service.py](../../../backend/app/services/subtitle_edit_service.py)、[backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)、[backend/tests/test_subtitle_resegment.py](../../../backend/tests/test_subtitle_resegment.py)、[backend/tests/test_subtitle_revisions.py](../../../backend/tests/test_subtitle_revisions.py)。
- 处置：保留。

### [backend/app/models/teaching.py](../../../backend/app/models/teaching.py)

数据库模型：确定性教学材料、会话、作答、提示和揭晓。表 exam_analysis_revisions、exam_evidence、teaching_sessions、teaching_items、teaching_attempts、user_question_disclosures、teaching_operations、teaching_feedbacks、learning_event_outbox；业务读写由上游服务完成。

- 代码入口/类型：`ExamAnalysisRevision`、`ExamEvidence`、`TeachingSession`、`TeachingItem`、`TeachingAttempt`、`UserQuestionDisclosure`、`TeachingOperation`、`TeachingFeedback`、`LearningEventOutbox`。
- 表：`exam_analysis_revisions`、`exam_evidence`、`teaching_sessions`、`teaching_items`、`teaching_attempts`、`user_question_disclosures`、`teaching_operations`、`teaching_feedbacks`、`learning_event_outbox`；外键 `exam_questions.id`、`exam_analysis_revisions.id`、`users.id`、`exam_sessions.id`、`exam_answers.id`、`teaching_sessions.id`、`exam_analysis_revisions.id`、`exam_answers.id`、`teaching_items.id`、`exam_answers.id`、`users.id`、`exam_analysis_revisions.id`、`users.id`、`users.id`、`teaching_sessions.id`、`users.id`、`teaching_attempts.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)、[backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)、[backend/app/services/teaching/events.py](../../../backend/app/services/teaching/events.py)；其余 22 项见机器清单。
- 处置：保留。

### [backend/app/models/types.py](../../../backend/app/models/types.py)

数据库模型：SQLAlchemy 词难度 JSON 自定义类型。表 类型/注册辅助；业务读写由上游服务完成。

- 代码入口/类型：`WordLevelsJSON`。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)。
- 直接使用者：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/tests/test_word_levels_column.py](../../../backend/tests/test_word_levels_column.py)。
- 处置：保留。

### [backend/app/models/user.py](../../../backend/app/models/user.py)

数据库模型：账号、角色、封禁、改密与注销身份字段。表 users；业务读写由上游服务完成。

- 代码入口/类型：`RoleType`、`User`。
- 表：`users`；外键 未声明直接外键。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/dependencies.py](../../../backend/app/api/dependencies.py)、[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)；其余 129 项见机器清单。
- 处置：保留。

### [backend/app/models/user_content.py](../../../backend/app/models/user_content.py)

数据库模型：个人频道订阅和字幕句收藏。表 channel_subscriptions、sentence_favorites；业务读写由上游服务完成。

- 代码入口/类型：`ChannelSubscription`、`SentenceFavorite`。
- 表：`channel_subscriptions`、`sentence_favorites`；外键 `users.id`、`channels.id`、`users.id`、`subtitles.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)；其余 7 项见机器清单。
- 处置：保留。

### [backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)

数据库模型：外部凭据、访问授权、运行事件、长期消息和外部生命周期意图。表 teaching_access_grants、external_connections、external_credentials、tutor_conversations、tutor_conversation_tasks、agent_runs、agent_steps、agent_run_events、teaching_messages、teaching_message_blocks、gateway_lifecycle_intents；业务读写由上游服务完成。

- 代码入口/类型：`new_id`、`now`、`TeachingAccessGrant`、`ExternalConnection`、`ExternalCredential`、`TutorConversation`、`TutorConversationTask`、`AgentRun`、`AgentStep`、`AgentRunEvent`（其余见机器清单）。
- 表：`teaching_access_grants`、`external_connections`、`external_credentials`、`tutor_conversations`、`tutor_conversation_tasks`、`agent_runs`、`agent_steps`、`agent_run_events`、`teaching_messages`、`teaching_message_blocks`、`gateway_lifecycle_intents`；外键 `users.id`、`users.id`、`external_connections.id`、`users.id`、`teaching_sessions.id`、`tutor_conversations.id`、`teaching_sessions.id`、`users.id`、`teaching_sessions.id`、`tutor_conversations.id`、`agent_runs.id`、`agent_runs.id`、`users.id`、`tutor_conversations.id`、`teaching_sessions.id`、`exam_analysis_revisions.id`、`agent_runs.id`、`teaching_messages.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/external_connections.py](../../../backend/app/api/v1/external_connections.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)；其余 18 项见机器清单。
- 处置：保留。

### [backend/app/models/video.py](../../../backend/app/models/video.py)

数据库模型：视频身份、来源、状态、媒体、发布和派生指标。表 videos；业务读写由上游服务完成。

- 代码入口/类型：`VideoStatus`、`VideoSource`、`VideoReviewStatus`、`Video`。
- 表：`videos`；外键 `users.id`、`users.id`、`channels.id`、`videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)、[backend/app/api/v1/favorites.py](../../../backend/app/api/v1/favorites.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)；其余 124 项见机器清单。
- 处置：保留。

### [backend/app/models/video_quality_report.py](../../../backend/app/models/video_quality_report.py)

数据库模型：追加式管线质量报告。表 video_quality_reports；业务读写由上游服务完成。

- 代码入口/类型：`VideoQualityReport`。
- 表：`video_quality_reports`；外键 `videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/transcription_quality.py](../../../backend/app/services/transcription_quality.py)、[backend/app/services/translation/quality.py](../../../backend/app/services/translation/quality.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/tests/test_admin_quality_inspection.py](../../../backend/tests/test_admin_quality_inspection.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/models/video_score.py](../../../backend/app/models/video_score.py)

数据库模型：视频评分分项与计算结果。表 video_scores；业务读写由上游服务完成。

- 代码入口/类型：`VideoScore`。
- 表：`video_scores`；外键 `videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/scoring_service.py](../../../backend/app/services/scoring_service.py)、[backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)、[backend/tests/test_scoring.py](../../../backend/tests/test_scoring.py)。
- 处置：保留。

### [backend/app/models/video_standard.py](../../../backend/app/models/video_standard.py)

数据库模型：同源视频的标准版本注册。表 video_standards；业务读写由上游服务完成。

- 代码入口/类型：`VideoStandard`。
- 表：`video_standards`；外键 `videos.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/subtitle_edit_service.py](../../../backend/app/services/subtitle_edit_service.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_subtitle_revisions.py](../../../backend/tests/test_subtitle_revisions.py)。
- 处置：保留。

### [backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)

数据库模型：有序词集及个人过筛进度。表 vocab_sets、vocab_set_words；业务读写由上游服务完成。

- 代码入口/类型：`VocabSet`、`VocabSetWord`。
- 表：`vocab_sets`、`vocab_set_words`；外键 `users.id`、`videos.id`、`vocab_sets.id`、`vocabulary.id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)、[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/library_service.py](../../../backend/app/services/library_service.py)、[backend/app/services/vocab_set_service.py](../../../backend/app/services/vocab_set_service.py)；其余 6 项见机器清单。
- 处置：保留。

### [backend/app/models/word_note.py](../../../backend/app/models/word_note.py)

数据库模型：预生成的全局/视频词注。表 word_ai_notes；业务读写由上游服务完成。

- 代码入口/类型：`WordAINote`。
- 表：`word_ai_notes`；外键 未声明直接外键。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)。
- 直接使用者：[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/services/word_notes.py](../../../backend/app/services/word_notes.py)、[backend/scripts/precompute_global_word_notes.py](../../../backend/scripts/precompute_global_word_notes.py)、[backend/scripts/precompute_global_word_notes_dual.py](../../../backend/scripts/precompute_global_word_notes_dual.py)、[backend/scripts/reprocess_official_videos.py](../../../backend/scripts/reprocess_official_videos.py)、[backend/tests/test_word_notes.py](../../../backend/tests/test_word_notes.py)。
- 处置：保留。

## `backend/app/schemas`

### [backend/app/schemas/__init__.py](../../../backend/app/schemas/__init__.py)

schema 包边界标记；有意不做公共 re-export，消费者 import 具体模块。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/app/schemas/admin.py](../../../backend/app/schemas/admin.py)

Pydantic 接口契约：管理员工作台、用户和系统设置；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`AdminUserBanRequest`、`AdminUserRoleRequest`、`AdminSettingsUpdate`、`AdminUserRow`、`AdminSettingsResponse`、`WorkerStatusResponse`、`AdminStatsTrend`、`AdminStatsCount`、`AdminStatsVideoStatus`、`AdminStatsVideoTopic`（其余见机器清单）。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)。
- 处置：保留。

### [backend/app/schemas/behavior.py](../../../backend/app/schemas/behavior.py)

Pydantic 接口契约：原始浏览学习行为事件；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`BehaviorEventRequest`、`BehaviorBatchRequest`、`BehaviorIngestResponse`。
- 直接依赖：[backend/app/services/event_contract.py](../../../backend/app/services/event_contract.py)。
- 直接使用者：[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)、[backend/tests/test_behavior_api.py](../../../backend/tests/test_behavior_api.py)。
- 处置：保留。

### [backend/app/schemas/browse.py](../../../backend/app/schemas/browse.py)

Pydantic 接口契约：主题分类与精选视频流；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`Category`、`CategoriesResponse`、`FeaturedVideosResponse`。
- 直接依赖：[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)。
- 处置：保留。

### [backend/app/schemas/catalog.py](../../../backend/app/schemas/catalog.py)

Pydantic 接口契约：待收录视频候选池；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`CatalogItemResponse`、`CatalogPromoteRequest`、`CatalogMarkRequest`、`CatalogSummaryResponse`。
- 直接使用者：[backend/app/api/v1/catalog.py](../../../backend/app/api/v1/catalog.py)、[backend/app/services/catalog_service.py](../../../backend/app/services/catalog_service.py)。
- 处置：保留。

### [backend/app/schemas/channel.py](../../../backend/app/schemas/channel.py)

Pydantic 接口契约：频道身份和展示信息；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ChannelDirection`、`ChannelDifficultyRange`、`LatestVideo`、`ChannelBase`、`ChannelCard`、`ChannelDetailChannel`、`RecommendedStart`、`ChannelDetailResponse`、`AdminChannelItem`、`AdminChannelListResponse`（其余见机器清单）。
- 直接依赖：[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)、[backend/app/schemas/discovery.py](../../../backend/app/schemas/discovery.py)。
- 处置：保留。

### [backend/app/schemas/common.py](../../../backend/app/schemas/common.py)

Pydantic 接口契约：跨领域简短响应与主体摘要；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`OkResponse`、`AcknowledgedResponse`、`UserProfileBrief`、`VideoBrief`。
- 直接使用者：[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/presence.py](../../../backend/app/api/v1/presence.py)、[backend/app/schemas/learning.py](../../../backend/app/schemas/learning.py)。
- 处置：保留。

### [backend/app/schemas/content_publication.py](../../../backend/app/schemas/content_publication.py)

Pydantic 接口契约：教学可编辑候选和发布操作回执；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`PublicationModel`、`Operation`、`CreateContentDraft`、`UpdateContentDraft`、`PublishContentDraft`、`WithdrawContentRevision`、`ContentDraftSummary`、`ContentDraftResponse`、`ContentPreflightResponse`、`WithdrawContentResponse`。
- 直接使用者：[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)、[backend/tests/test_teaching_content_cli.py](../../../backend/tests/test_teaching_content_cli.py)。
- 处置：保留。

### [backend/app/schemas/discovery.py](../../../backend/app/schemas/discovery.py)

Pydantic 接口契约：视频/字幕/频道发现、词典、订阅、收藏与每日练习；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ContinueVideo`、`ChannelSubscriptionCard`、`SubscriptionState`、`SentenceFavoriteItem`、`SentenceFavoriteStatus`、`DictionaryWord`、`DictionaryResponse`、`MetadataSampleWord`、`WordTimestamp`、`LearningMetadataItem`（其余见机器清单）。
- 直接依赖：[backend/app/schemas/channel.py](../../../backend/app/schemas/channel.py)、[backend/app/schemas/exam.py](../../../backend/app/schemas/exam.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/schemas/exam.py](../../../backend/app/schemas/exam.py)

Pydantic 接口契约：真题请求响应和作答格式；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ExamQuestionPublic`、`ExamPaperDetail`、`ExamAttemptCreateResponse`、`ExamAnswerSubmit`、`ExamSubmitRequest`、`ExamQuestionResult`、`ExamSubmitResponse`、`WrongRedoRequest`、`ExamPaperSection`、`ExamPaperRow`（其余见机器清单）。
- 直接依赖：[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)。
- 直接使用者：[backend/app/api/v1/exams.py](../../../backend/app/api/v1/exams.py)、[backend/app/schemas/discovery.py](../../../backend/app/schemas/discovery.py)。
- 处置：保留。

### [backend/app/schemas/exam_pdf.py](../../../backend/app/schemas/exam_pdf.py)

Pydantic 接口契约：原卷清单字段；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ExamPdfItem`、`ExamPdfListResponse`。
- 直接使用者：[backend/app/api/v1/exam_pdfs.py](../../../backend/app/api/v1/exam_pdfs.py)。
- 处置：保留。

### [backend/app/schemas/feedback.py](../../../backend/app/schemas/feedback.py)

Pydantic 接口契约：用户反馈与管理员回复/公告；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`FeedbackCreate`、`FeedbackResponse`、`AdminFeedbackResponse`、`AdminFeedbackUpdate`、`AdminFeedbackRow`、`AnnouncementCreate`、`AnnouncementResponse`。
- 直接使用者：[backend/app/api/v1/feedback.py](../../../backend/app/api/v1/feedback.py)。
- 处置：保留。

### [backend/app/schemas/home_content.py](../../../backend/app/schemas/home_content.py)

Pydantic 接口契约：首页内容草稿、不可变版本、布局及生成状态；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`HomeContentClipRef`、`HomeContentDraftExpression`、`HomeContentDraftScenario`、`HomeContentDraftInteractionOption`、`HomeContentDraftInteraction`、`HomeContentDraft`、`HomeEditorialSentence`、`HomeEditorialExpression`、`HomeEditorialInteractionOption`、`HomeEditorialInteraction`（其余见机器清单）。
- 直接依赖：[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/home_editorial.py](../../../backend/app/api/v1/home_editorial.py)、[backend/app/services/home_content_content.py](../../../backend/app/services/home_content_content.py)、[backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)。
- 处置：保留。

### [backend/app/schemas/learning.py](../../../backend/app/schemas/learning.py)

Pydantic 接口契约：个人观看进度、词汇与学习记录；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`LearningRecordResponse`、`SaveProgressRequest`、`SaveProgressResponse`、`ContinueLearningItem`、`ContinueLearningResponse`、`WatchProgressResponse`、`DailyMinutes`、`WeeklyStatsResponse`、`EventDistributionItem`。
- 直接依赖：[backend/app/schemas/common.py](../../../backend/app/schemas/common.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)。
- 处置：保留。

### [backend/app/schemas/learning_context.py](../../../backend/app/schemas/learning_context.py)

Pydantic 接口契约：任务、材料、权限、草稿和恢复动作的共享上下文；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ContextModel`、`ContextTask`、`ContextMaterial`、`ContextHelp`、`ContextProgress`、`LearningContext`。
- 直接依赖：[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)。
- 直接使用者：[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)、[backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)。
- 处置：保留。

### [backend/app/schemas/learning_plan.py](../../../backend/app/schemas/learning_plan.py)

Pydantic 接口契约：学习档案、有效学习事件与掌握趋势；不是已删除的每日计划；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`LearningProfileResponse`、`MilestoneResponse`、`MasterySnapshotItem`、`MasteryTrendResponse`。
- 直接使用者：[backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)。
- 处置：保留。

### [backend/app/schemas/lesson.py](../../../backend/app/schemas/lesson.py)

Pydantic 接口契约：课程、修订、操作、进度与学习活动；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ImportLesson`、`UseReview`、`LessonUses`、`ReviewLesson`、`PublishLesson`、`WithdrawLesson`、`SaveLessonProgress`、`RecordLessonActivity`。
- 直接使用者：[backend/app/api/v1/lessons.py](../../../backend/app/api/v1/lessons.py)、[backend/app/services/lesson_progress.py](../../../backend/app/services/lesson_progress.py)、[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)、[backend/tests/test_lesson_progress.py](../../../backend/tests/test_lesson_progress.py)、[backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)。
- 处置：保留。

### [backend/app/schemas/listening.py](../../../backend/app/schemas/listening.py)

Pydantic 接口契约：字幕句冻结的听力练习会话；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ListeningVideoCard`、`ListeningQuestion`、`ListeningDiffPart`、`ListeningResult`、`ListeningSessionResponse`、`ListeningSessionSummary`、`ListeningDraftResponse`。
- 直接依赖：[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/listening.py](../../../backend/app/api/v1/listening.py)。
- 处置：保留。

### [backend/app/schemas/note.py](../../../backend/app/schemas/note.py)

Pydantic 接口契约：本人笔记库响应；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`NoteItem`。
- 直接使用者：[backend/app/api/v1/notes.py](../../../backend/app/api/v1/notes.py)。
- 处置：保留。

### [backend/app/schemas/notification.py](../../../backend/app/schemas/notification.py)

Pydantic 接口契约：本人通知记录；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`NotificationResponse`、`UnreadCountResponse`、`NotificationPreferencesResponse`、`NotificationPreferencesUpdate`。
- 直接使用者：[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)。
- 处置：保留。

### [backend/app/schemas/overview.py](../../../backend/app/schemas/overview.py)

Pydantic 接口契约：个人学习概览字段；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`OverviewUser`、`OverviewStreak`、`OverviewLearning`、`OverviewDaily`、`OverviewWeek`、`OverviewVideos`、`OverviewExams`、`OverviewLibrary`、`OverviewResponse`。
- 直接依赖：[backend/app/schemas/vocabulary.py](../../../backend/app/schemas/vocabulary.py)。
- 直接使用者：[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)。
- 处置：保留。

### [backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)

Pydantic 接口契约：分页输入和统一分页响应封装；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`PaginationParams`、`PaginatedResponse`、`has_more`、`paginated`。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/catalog.py](../../../backend/app/api/v1/catalog.py)、[backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)、[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)；其余 17 项见机器清单。
- 处置：保留。

### [backend/app/schemas/recommendation.py](../../../backend/app/schemas/recommendation.py)

Pydantic 接口契约：recommendation；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`RecommendationHomeResponse`、`RecommendationCategoryResponse`。
- 直接依赖：[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 直接使用者：[backend/app/api/v1/recommendations.py](../../../backend/app/api/v1/recommendations.py)。
- 处置：保留。

### [backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)

Pydantic 接口契约：确定性教学材料、会话、作答、提示和揭晓；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`StrictModel`、`CreateSession`、`SessionAction`、`ItemAction`、`DraftAnswer`、`SubmitAttempt`、`Feedback`、`CompleteSession`、`CardHeader`、`QuestionPayload`（其余见机器清单）。
- 直接使用者：[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/app/schemas/learning_context.py](../../../backend/app/schemas/learning_context.py)、[backend/app/services/teaching/commands.py](../../../backend/app/services/teaching/commands.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/tests/test_teaching.py](../../../backend/tests/test_teaching.py)、[backend/tests/test_teaching_quiz.py](../../../backend/tests/test_teaching_quiz.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)

Pydantic 接口契约：导师回复、消息块、引用和页游标字段；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`TutorReply`、`DialogueBlock`、`DialogueMessage`、`DialoguePage`。
- 直接使用者：[backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)、[backend/tests/test_teaching_dialogue_pg.py](../../../backend/tests/test_teaching_dialogue_pg.py)。
- 处置：保留。

### [backend/app/schemas/tutor.py](../../../backend/app/schemas/tutor.py)

Pydantic 接口契约：独立导师聊天生命周期及共享回合入口；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`ConversationCreate`、`ConversationPatch`、`ConversationTask`、`ConversationSummary`、`ConversationPage`、`SendMessage`。
- 直接使用者：[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)。
- 处置：保留。

### [backend/app/schemas/user.py](../../../backend/app/schemas/user.py)

Pydantic 接口契约：账号、角色、封禁、改密与注销身份字段；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`SendSmsCodeRequest`、`SmsLoginRequest`、`PhoneLoginRequest`、`SmsRegisterRequest`、`SmsResetPasswordRequest`、`ChangePhoneRequest`、`UserUpdate`、`UserResponse`、`TokenResponse`、`RefreshRequest`（其余见机器清单）。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/services/video_classification.py](../../../backend/app/services/video_classification.py)。
- 直接使用者：[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/tests/test_password_contract.py](../../../backend/tests/test_password_contract.py)、[backend/tests/test_profile.py](../../../backend/tests/test_profile.py)。
- 处置：保留。

### [backend/app/schemas/video.py](../../../backend/app/schemas/video.py)

Pydantic 接口契约：视频身份、来源、状态、媒体、发布和派生指标；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`VideoCreate`、`VideoResponse`、`SubtitleResponse`、`VideoDetailResponse`、`VideoAdminResponse`、`VideoAdminUpdate`、`SubtitleUpdate`、`SubtitleBatchItem`、`SubtitleSplit`、`SubtitleBatchUpdate`（其余见机器清单）。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/schemas/browse.py](../../../backend/app/schemas/browse.py)、[backend/app/schemas/channel.py](../../../backend/app/schemas/channel.py)、[backend/app/schemas/discovery.py](../../../backend/app/schemas/discovery.py)；其余 12 项见机器清单。
- 处置：保留。

### [backend/app/schemas/vocab_set.py](../../../backend/app/schemas/vocab_set.py)

Pydantic 接口契约：有序词集及个人过筛进度；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`CollectVocabSetResponse`、`VocabSetSummary`、`VocabSetWordItem`、`VocabSetDetail`、`SieveWordPayload`、`SieveStateResponse`、`SetWordProgressResponse`。
- 直接使用者：[backend/app/api/v1/vocab_sets.py](../../../backend/app/api/v1/vocab_sets.py)。
- 处置：保留。

### [backend/app/schemas/vocabulary.py](../../../backend/app/schemas/vocabulary.py)

Pydantic 接口契约：个人词条、复习、自评、训练与观看上下文；校验输入、限制响应字段，不是数据库表或前端界面。

- 代码入口/类型：`VocabularyResponse`、`VocabularyEnrichResponse`、`VocabularyStatsResponse`、`VocabularyPreferencesResponse`、`VocabularyPreferencesUpdate`、`TodayTrainingSummary`、`StudySessionItemResponse`、`StudySessionResponse`、`StudySessionEnvelope`、`StudySessionStartRequest`（其余见机器清单）。
- 直接使用者：[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/app/schemas/overview.py](../../../backend/app/schemas/overview.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)、[backend/tests/test_phase1_b0_smoke.py](../../../backend/tests/test_phase1_b0_smoke.py)。
- 处置：保留。

## `backend/app/services`

### [backend/app/services/__init__.py](../../../backend/app/services/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/catalog.py](../../../backend/app/api/v1/catalog.py)、[backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)、[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)、[backend/app/api/v1/exam_pdfs.py](../../../backend/app/api/v1/exam_pdfs.py)；其余 104 项见机器清单。
- 处置：保留。

### [backend/app/services/account_data.py](../../../backend/app/services/account_data.py)

业务/规则实现：本人数据导出清单、媒体引用和可重试清理；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`scalar`、`row_to_dict`、`gather_user_data`、`profile_dict`、`gather_export`、`resolve_media_url`、`export_media_entries`、`cleanup_paths`、`enqueue_media_cleanup`、`process_media_cleanup`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/engagement.py](../../../backend/app/models/engagement.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)；其余 23 项见机器清单。
- 直接使用者：[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_exam_snapshots.py](../../../backend/tests/test_exam_snapshots.py)、[backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)、[backend/tests/test_teaching_dialogue.py](../../../backend/tests/test_teaching_dialogue.py)、[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)；其余 2 项见机器清单。
- 处置：保留。

### [backend/app/services/admin_service.py](../../../backend/app/services/admin_service.py)

业务/规则实现：管理用户、封禁/角色与单例设置；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`list_admin_users`、`get_admin_settings`、`update_admin_settings`、`list_admin_accounts`、`ban_user`、`change_user_role`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/time_utils.py](../../../backend/app/core/time_utils.py)、[backend/app/models/admin_setting.py](../../../backend/app/models/admin_setting.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/tests/test_admin_panel.py](../../../backend/tests/test_admin_panel.py)。
- 处置：保留。

### [backend/app/services/admin_stats.py](../../../backend/app/services/admin_stats.py)

业务/规则实现：管理仪表盘聚合读模型；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_admin_stats`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/core/time_utils.py](../../../backend/app/core/time_utils.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/tests/test_teaching.py](../../../backend/tests/test_teaching.py)。
- 处置：保留。

### [backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)

业务/规则实现：共享 AI 请求、结构化响应、重试与错误归一；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`AIServiceError`、`AIService`、`get_ai_service`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)、[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)、[backend/app/services/video_classification.py](../../../backend/app/services/video_classification.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)、[backend/app/services/word_notes.py](../../../backend/app/services/word_notes.py)、[backend/scripts/check_llm_provider.py](../../../backend/scripts/check_llm_provider.py)；其余 5 项见机器清单。
- 处置：保留。

### [backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)

业务/规则实现：站外告警及站内管理员通知降级；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`send_alert`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redaction.py](../../../backend/app/core/redaction.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)。
- 直接使用者：[backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)、[backend/app/tasks/pipeline_dispatch_tasks.py](../../../backend/app/tasks/pipeline_dispatch_tasks.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_alert_service.py](../../../backend/tests/test_alert_service.py)。
- 处置：保留。

### [backend/app/services/behavior_service.py](../../../backend/app/services/behavior_service.py)

业务/规则实现：行为入库、去重和观看计数投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`ingest_event`、`ingest_batch`、`drop_unknown_video_ids`。
- 直接依赖：[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)。
- 直接使用者：[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)。
- 处置：保留。

### [backend/app/services/catalog_service.py](../../../backend/app/services/catalog_service.py)

业务/规则实现：候选视频排序、标记和晋升至处理管线；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`compute_fit_score`、`import_records`、`list_items`、`get_item`、`get_item_response`、`summary`、`promote_item`、`mark_item`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/catalog.py](../../../backend/app/models/catalog.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/catalog.py](../../../backend/app/schemas/catalog.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/api/v1/catalog.py](../../../backend/app/api/v1/catalog.py)、[backend/scripts/import_catalog.py](../../../backend/scripts/import_catalog.py)、[backend/tests/test_catalog_api.py](../../../backend/tests/test_catalog_api.py)。
- 处置：保留。

### [backend/app/services/channel_learning.py](../../../backend/app/services/channel_learning.py)

业务/规则实现：从真实频道视频推导难度、学习方向和起学依据；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`ChannelProfile`、`channel_facts`、`recommended_start_basis`。
- 直接依赖：[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 直接使用者：[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)、[backend/tests/test_channel_learning.py](../../../backend/tests/test_channel_learning.py)。
- 处置：保留。

### [backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)

业务/规则实现：频道查询、自动创建、订阅统计与缓存；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`slugify`、`latest_video_payload`、`public_video_counts`、`subscriber_stats`、`latest_public_videos`、`list_public_channels`、`search_channel_cards`、`get_channel_detail`、`ensure_channel_for`、`auto_attach_channel`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/user_content.py](../../../backend/app/models/user_content.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/channels.py](../../../backend/app/api/v1/channels.py)、[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/notes.py](../../../backend/app/api/v1/notes.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)；其余 8 项见机器清单。
- 处置：保留。

### [backend/app/services/daily_recommendation_service.py](../../../backend/app/services/daily_recommendation_service.py)

业务/规则实现：轻量题库索引、每日预览及显式开始作答；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`invalidate_bank_index`、`complete_question_groups`、`summary`、`preview`、`start`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/exam_service.py](../../../backend/app/services/exam_service.py)。
- 直接使用者：[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)、[backend/tests/test_daily_recommendation_index.py](../../../backend/tests/test_daily_recommendation_index.py)。
- 处置：保留。

### [backend/app/services/difficulty_service.py](../../../backend/app/services/difficulty_service.py)

业务/规则实现：从字幕词汇难度分布计算视频 CEFR 难度；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`beyond_basic_ratio`、`compute_difficulty_from_word_levels`、`compute_video_difficulty`。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 直接使用者：[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_classification.py](../../../backend/scripts/backfill_classification.py)、[backend/scripts/backfill_difficulty.py](../../../backend/scripts/backfill_difficulty.py)、[backend/tests/test_difficulty_service.py](../../../backend/tests/test_difficulty_service.py)。
- 处置：保留。

### [backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)

业务/规则实现：公共可见性过滤与搜索/订阅/原句收藏投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`public_video_filters`、`page_items`、`dictionary_words`、`learning_metadata`、`channel_subscriptions`、`set_channel_subscription`、`sentence_favorites`、`set_sentence_favorite`、`search`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 8 项见机器清单。
- 直接使用者：[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)、[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)、[backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)。
- 处置：保留。

### [backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)

业务/规则实现：只读词典索引、词形还原与考试词标注；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`levels_of`、`is_available`、`get_index`、`lookup`、`entries`、`lookup_inflection`、`inflection_label`、`seen_tags`、`annotate_text`、`verify_tag_coverage`。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)。
- 直接使用者：[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/app/api/v1/words.py](../../../backend/app/api/v1/words.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/exam_corpus.py](../../../backend/app/services/exam_corpus.py)、[backend/app/services/home_content_content.py](../../../backend/app/services/home_content_content.py)；其余 22 项见机器清单。
- 处置：保留。

### [backend/app/services/event_contract.py](../../../backend/app/services/event_contract.py)

业务/规则实现：前后端事件版本、类型、有效学习口径与来源归一；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`normalize_source`。
- 直接使用者：[backend/app/schemas/behavior.py](../../../backend/app/schemas/behavior.py)、[backend/app/services/admin_stats.py](../../../backend/app/services/admin_stats.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/app/services/measurement_service.py](../../../backend/app/services/measurement_service.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)、[backend/tests/test_measurement_service.py](../../../backend/tests/test_measurement_service.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/services/exam_corpus.py](../../../backend/app/services/exam_corpus.py)

业务/规则实现：真题例句、词索引和词频语料；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`find_example_sentence`、`is_high_freq_word`、`example_sentences_for_words`、`recompute_freq_for_levels`、`ingest_sentences`。
- 直接依赖：[backend/app/models/exam_corpus.py](../../../backend/app/models/exam_corpus.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)。
- 直接使用者：[backend/app/api/v1/words.py](../../../backend/app/api/v1/words.py)、[backend/scripts/import_exam_papers.py](../../../backend/scripts/import_exam_papers.py)、[backend/scripts/ingest_exam_papers.py](../../../backend/scripts/ingest_exam_papers.py)、[backend/tests/test_exam_corpus.py](../../../backend/tests/test_exam_corpus.py)。
- 处置：保留。

### [backend/app/services/exam_pdf_service.py](../../../backend/app/services/exam_pdf_service.py)

业务/规则实现：从受控清单解析原卷路径、防路径穿越；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`list_pdfs`、`resolve`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/api/v1/exam_pdfs.py](../../../backend/app/api/v1/exam_pdfs.py)、[backend/tests/test_exam_pdfs.py](../../../backend/tests/test_exam_pdfs.py)。
- 处置：保留。

### [backend/app/services/exam_service.py](../../../backend/app/services/exam_service.py)

业务/规则实现：冻结题面、作答生命周期、条件交卷认领和服务端判分；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_paper_with_questions`、`is_answerable`、`create_paper_session`、`create_daily_session`、`list_wrong_questions`、`create_wrong_redo_session`、`exam_stats`、`submit_answers`、`grade_choice`、`list_papers`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/app/services/question_exposure_service.py](../../../backend/app/services/question_exposure_service.py)。
- 直接使用者：[backend/app/api/v1/exams.py](../../../backend/app/api/v1/exams.py)、[backend/app/services/daily_recommendation_service.py](../../../backend/app/services/daily_recommendation_service.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)、[backend/app/services/vocab_set_service.py](../../../backend/app/services/vocab_set_service.py)、[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)、[backend/tests/test_exam_snapshots.py](../../../backend/tests/test_exam_snapshots.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)

业务/规则实现：不透明外部凭据哈希、scope 与有效性验证；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`utc`、`view`、`owned`、`issue`、`create`、`revoke`、`rotate`、`authenticate`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/app/services/v2_access.py](../../../backend/app/services/v2_access.py)、[backend/app/services/v2_schema.py](../../../backend/app/services/v2_schema.py)。
- 直接使用者：[backend/app/api/v1/external_connections.py](../../../backend/app/api/v1/external_connections.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/app/services/tutor_conversations.py](../../../backend/app/services/tutor_conversations.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/app/services/external_meta.py](../../../backend/app/services/external_meta.py)

业务/规则实现：将下载器元信息映射成可追溯来源字段；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`pick_best_thumbnail`、`parse_external_meta`、`apply_external_meta`。
- 直接使用者：[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_external_meta.py](../../../backend/scripts/backfill_external_meta.py)、[backend/scripts/seed_official_videos.py](../../../backend/scripts/seed_official_videos.py)、[backend/tests/test_external_meta_and_speech_metrics.py](../../../backend/tests/test_external_meta_and_speech_metrics.py)。
- 处置：保留。

### [backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)

业务/规则实现：独立于 worker/beat 的 Web 进程健康巡检；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`HealthProblem`、`collect_problems`、`check_once`、`run_health_monitor`、`start_health_monitor`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/heartbeat.py](../../../backend/app/core/heartbeat.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/main.py](../../../backend/app/main.py)、[backend/tests/test_health_monitor.py](../../../backend/tests/test_health_monitor.py)。
- 处置：保留。

### [backend/app/services/home_content_content.py](../../../backend/app/services/home_content_content.py)

业务/规则实现：字幕来源指纹、字段问题校验与展示内容投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`empty_layout`、`compute_source_fingerprint`、`current_source_fingerprint`、`collect_issues`、`resolve_sentences`、`resolve_clip`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/schemas/home_content.py](../../../backend/app/schemas/home_content.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)。
- 直接使用者：[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)

业务/规则实现：把字幕规划为有界模型输入并严格校验生成草稿；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`DraftGenerationError`、`SubtitleLine`、`TranscriptSegment`、`InputPlan`、`DraftGenerationResult`、`coerce_subtitle_line`、`normalize_subtitles`、`plan_transcript_input`、`draft_transcript_char_budget`、`candidate_transcript_char_budget`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/schemas/home_content.py](../../../backend/app/schemas/home_content.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)、[backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)。
- 直接使用者：[backend/app/tasks/home_content_tasks.py](../../../backend/app/tasks/home_content_tasks.py)、[backend/tests/test_home_content_generation.py](../../../backend/tests/test_home_content_generation.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)

业务/规则实现：首页布局草稿/发布/回退、候选池与无缓存公共页读取；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`resolve_public_page`、`get_layout_state`、`save_layout_draft`、`publish_layout`、`rollback_layout`、`preview_layout`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/home_content.py](../../../backend/app/models/home_content.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)；其余 6 项见机器清单。
- 直接使用者：[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)、[backend/tests/test_home_content_concurrency.py](../../../backend/tests/test_home_content_concurrency.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)

业务/规则实现：首页内容草稿/版本写入、生成占位与冲突状态机；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_video_state`、`get_generation_state`、`save_draft`、`publish_content`、`restore_draft`、`preview_video`、`GenerationClaim`、`GenerationContext`、`claim_generation`、`enqueue_generation`（其余见机器清单）。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/home_content.py](../../../backend/app/models/home_content.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/home_content.py](../../../backend/app/schemas/home_content.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/api/v1/admin_home_content.py](../../../backend/app/api/v1/admin_home_content.py)、[backend/app/api/v1/home_editorial.py](../../../backend/app/api/v1/home_editorial.py)、[backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)、[backend/app/tasks/home_content_tasks.py](../../../backend/app/tasks/home_content_tasks.py)、[backend/tests/test_home_content.py](../../../backend/tests/test_home_content.py)、[backend/tests/test_home_content_concurrency.py](../../../backend/tests/test_home_content_concurrency.py)；其余 1 项见机器清单。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)

业务/规则实现：同事务必达学习事实与兼容容错事件、计数和 streak 投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`claim_watch_day`、`emit_event`、`record_event`、`get_weekly_cycle_count`、`get_today_progress`。
- 直接依赖：[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/services/event_contract.py](../../../backend/app/services/event_contract.py)、[backend/app/services/local_time.py](../../../backend/app/services/local_time.py)、[backend/app/services/milestone_service.py](../../../backend/app/services/milestone_service.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/services/behavior_service.py](../../../backend/app/services/behavior_service.py)、[backend/app/services/exam_service.py](../../../backend/app/services/exam_service.py)、[backend/app/services/lesson_progress.py](../../../backend/app/services/lesson_progress.py)、[backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)、[backend/app/services/practice_service.py](../../../backend/app/services/practice_service.py)、[backend/app/services/profile_service.py](../../../backend/app/services/profile_service.py)；其余 6 项见机器清单。
- 处置：保留。

### [backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)

业务/规则实现：修订/段/词锚点的多来源收词、复习事实与导出清理；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`require_vocabulary_pilot`、`resolve_occurrence`、`source_view`、`save_source`、`list_sources`、`detach_lesson_words_from_videos`、`purge_learner_facts`、`export_sections`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/models/lesson_learning.py](../../../backend/app/models/lesson_learning.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)；其余 7 项见机器清单。
- 直接使用者：[backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/lesson_tutor.py](../../../backend/app/services/lesson_tutor.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/tests/test_lesson_learning.py](../../../backend/tests/test_lesson_learning.py)。
- 处置：保留。

### [backend/app/services/lesson_progress.py](../../../backend/app/services/lesson_progress.py)

业务/规则实现：课程级完成状态和按实际修订保存的恢复位置；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`read_progress`、`read_history`、`save_progress`、`record_activity`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/schemas/lesson.py](../../../backend/app/schemas/lesson.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)。
- 直接使用者：[backend/app/api/v1/lessons.py](../../../backend/app/api/v1/lessons.py)、[backend/tests/test_lesson_progress.py](../../../backend/tests/test_lesson_progress.py)、[backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)。
- 处置：保留。

### [backend/app/services/lesson_receipts.py](../../../backend/app/services/lesson_receipts.py)

业务/规则实现：只用公钥验证外部签发的课程发布收据；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`verify_lesson_receipt`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/teaching/content_receipts.py](../../../backend/app/services/teaching/content_receipts.py)。
- 直接使用者：[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)、[backend/tests/test_lesson_receipt_signer.py](../../../backend/tests/test_lesson_receipt_signer.py)、[backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)。
- 处置：保留。

### [backend/app/services/lesson_tutor.py](../../../backend/app/services/lesson_tutor.py)

业务/规则实现：绑定课程修订的导师上下文与当前权限投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`require_tutor`、`require_anchor_schema`、`get_anchor`、`material_context`、`model_context`、`projection`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/models/lesson_learning.py](../../../backend/app/models/lesson_learning.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)。
- 处置：保留。

### [backend/app/services/lessons.py](../../../backend/app/services/lessons.py)

业务/规则实现：SLCS 课程导入、审核、签名发布、撤回和按权限读取；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`insert_for`、`lesson_router_enabled`、`require_lessons_ready`、`may_display_revision`、`material_for_revision`、`get_visible_revision`、`public_detail`、`revision_state`、`list_lessons`、`list_admin_lessons`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/schemas/lesson.py](../../../backend/app/schemas/lesson.py)、[backend/app/services/lesson_receipts.py](../../../backend/app/services/lesson_receipts.py)、[backend/app/services/v2_schema.py](../../../backend/app/services/v2_schema.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/api/v1/lessons.py](../../../backend/app/api/v1/lessons.py)、[backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/lesson_progress.py](../../../backend/app/services/lesson_progress.py)、[backend/app/services/lesson_tutor.py](../../../backend/app/services/lesson_tutor.py)、[backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)。
- 处置：保留。

### [backend/app/services/library_service.py](../../../backend/app/services/library_service.py)

业务/规则实现：复用 Vocabulary 的非视频词集增删与本人权限；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`create_set`、`owned_set`、`add_words`、`remove_word`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 2 项见机器清单。
- 直接使用者：[backend/app/api/v1/discovery.py](../../../backend/app/api/v1/discovery.py)。
- 处置：保留。

### [backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)

业务/规则实现：从可播放视频选句、存草稿、锁定提交并逐词判分；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`iso_utc`、`cue_filters`、`playable_filters`、`catalog`、`playable_video`、`owned_session`、`start`、`payload`、`normalized_words`、`grade`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/listening.py](../../../backend/app/models/listening.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/api/v1/listening.py](../../../backend/app/api/v1/listening.py)、[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)、[backend/tests/test_listening_api.py](../../../backend/tests/test_listening_api.py)、[backend/tests/test_listening_grading.py](../../../backend/tests/test_listening_grading.py)、[backend/tests/test_listening_pg.py](../../../backend/tests/test_listening_pg.py)。
- 处置：保留。

### [backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)

业务/规则实现：供应商/模型配置目录、任务路由和兼容客户端参数；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`ModelSpec`、`ProviderSpec`、`is_free_model_id`、`catalog_lookup`、`free_model_ids`、`resolve_provider`、`resolve_model`、`build_client_kwargs`、`provider_headers`、`mask_secret`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)、[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)、[backend/app/services/video_classification.py](../../../backend/app/services/video_classification.py)、[backend/scripts/check_llm_provider.py](../../../backend/scripts/check_llm_provider.py)、[backend/tests/test_home_content_generation.py](../../../backend/tests/test_home_content_generation.py)；其余 1 项见机器清单。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/services/local_time.py](../../../backend/app/services/local_time.py)

业务/规则实现：用户时区与本地日边界的唯一归一入口；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`resolve_user_timezone`、`user_local_now`、`user_local_date`、`get_user_local_now`、`local_zone`、`get_user_local_date`。
- 直接依赖：[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)；其余 8 项见机器清单。
- 处置：保留。

### [backend/app/services/measurement_service.py](../../../backend/app/services/measurement_service.py)

业务/规则实现：按固定分母和样本量计算激活、留存、事件质量与性能读模型；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`percentile`、`learning_metrics`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/event_contract.py](../../../backend/app/services/event_contract.py)。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/scripts/measure_baseline.py](../../../backend/scripts/measure_baseline.py)、[backend/tests/test_measurement_service.py](../../../backend/tests/test_measurement_service.py)。
- 处置：保留。

### [backend/app/services/milestone_service.py](../../../backend/app/services/milestone_service.py)

业务/规则实现：历史掌握趋势读取和快照维护；不再颁发成就；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`check_and_award`、`get_mastery_trend`、`ensure_today_snapshot`。
- 直接依赖：[backend/app/models/milestone.py](../../../backend/app/models/milestone.py)。
- 直接使用者：[backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)、[backend/tests/test_milestone_service.py](../../../backend/tests/test_milestone_service.py)、[backend/tests/test_vocabulary_transactions.py](../../../backend/tests/test_vocabulary_transactions.py)、[backend/tests/test_watch_baseline.py](../../../backend/tests/test_watch_baseline.py)。
- 处置：保留。

### [backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)

业务/规则实现：通知记录、去重、提交后推送与公告分页扇出；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`create_notification`、`commit_and_push`、`notify_admins`、`count_announcement_recipients`、`fan_out_announcement`。
- 直接依赖：[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/notification_transport.py](../../../backend/app/services/notification_transport.py)、[backend/app/services/retired_features.py](../../../backend/app/services/retired_features.py)。
- 直接使用者：[backend/app/api/v1/feedback.py](../../../backend/app/api/v1/feedback.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)、[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/app/tasks/notification_tasks.py](../../../backend/app/tasks/notification_tasks.py)、[backend/app/tasks/reminder_tasks.py](../../../backend/app/tasks/reminder_tasks.py)；其余 4 项见机器清单。
- 处置：保留。

### [backend/app/services/notification_transport.py](../../../backend/app/services/notification_transport.py)

业务/规则实现：进程内连接和 Redis pubsub 跨 worker 通知传输；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`ConnectionManager`、`push_to_user`、`start_notification_subscriber`、`stop_notification_subscriber`。
- 直接依赖：[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/services/retired_features.py](../../../backend/app/services/retired_features.py)。
- 直接使用者：[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)。
- 处置：保留。

### [backend/app/services/oss_service.py](../../../backend/app/services/oss_service.py)

业务/规则实现：按开关上传/删除对象并生成签名媒体 URL；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`upload_file`、`delete_file`、`get_signed_url`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)。
- 处置：保留。

### [backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)

业务/规则实现：聚合档案、观看、词汇、考试与资料库的统一读模型；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`build_overview`。
- 直接依赖：[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 7 项见机器清单。
- 直接使用者：[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/tests/test_teaching.py](../../../backend/tests/test_teaching.py)。
- 处置：保留。

### [backend/app/services/pipeline_alerting.py](../../../backend/app/services/pipeline_alerting.py)

业务/规则实现：短期管线失败窗口记录与告警读取；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`record_pipeline_failure`、`read_pipeline_failures`。
- 直接依赖：[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)。
- 直接使用者：[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)、[backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_health_monitor.py](../../../backend/tests/test_health_monitor.py)。
- 处置：保留。

### [backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)

业务/规则实现：数据库 outbox 派发、重试、过期放弃和积压盘点；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`enqueue`、`dispatch_now`、`DispatchSweep`、`dispatch_pending`、`prune_settled`、`DispatchBacklog`、`backlog`、`pending_video_ids`。
- 直接依赖：[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)。
- 直接使用者：[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/app/tasks/pipeline_dispatch_tasks.py](../../../backend/app/tasks/pipeline_dispatch_tasks.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_internal_callback.py](../../../backend/tests/test_internal_callback.py)、[backend/tests/test_pipeline_dispatch.py](../../../backend/tests/test_pipeline_dispatch.py)；其余 4 项见机器清单。
- 处置：保留。

### [backend/app/services/practice_service.py](../../../backend/app/services/practice_service.py)

业务/规则实现：从个人词库生成练习及接受自评结果、更新复习状态；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`shuffle_options`、`DistractorCandidate`、`select_distractors`、`build_vocabulary_drill`、`submit_practice_results`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/tests/test_vocabulary_drill_levels.py](../../../backend/tests/test_vocabulary_drill_levels.py)、[backend/tests/test_vocabulary_quiz.py](../../../backend/tests/test_vocabulary_quiz.py)、[backend/tests/test_vocabulary_transactions.py](../../../backend/tests/test_vocabulary_transactions.py)、[backend/tests/test_vocabulary_transactions_pg.py](../../../backend/tests/test_vocabulary_transactions_pg.py)。
- 处置：保留。

### [backend/app/services/profile_service.py](../../../backend/app/services/profile_service.py)

业务/规则实现：从原始词汇/事件重算掌握分布与学习档案；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_or_create_profile`、`refresh_profile`。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)。
- 直接使用者：[backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/app/services/study_session_service.py](../../../backend/app/services/study_session_service.py)。
- 处置：保留。

### [backend/app/services/question_exposure_service.py](../../../backend/app/services/question_exposure_service.py)

业务/规则实现：不自行提交的题目暴露锁定、映射和记录；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`question_key_from_identity`、`ensure_exposure_mapping_state`、`lock_question_exposure`、`record_answer_available`、`backfill_user_exposures`。
- 直接依赖：[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)。
- 直接使用者：[backend/app/services/exam_service.py](../../../backend/app/services/exam_service.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/tests/test_exam_snapshots.py](../../../backend/tests/test_exam_snapshots.py)。
- 处置：保留。

### [backend/app/services/ranking_service.py](../../../backend/app/services/ranking_service.py)

业务/规则实现：最新/周播放/周收藏榜单与缓存快照；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`current_week_start_utc`、`rankings_cache_key`、`get_rankings`、`compute_rankings`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/tasks/ranking_tasks.py](../../../backend/app/tasks/ranking_tasks.py)、[backend/tests/test_browse_feed.py](../../../backend/tests/test_browse_feed.py)、[backend/tests/test_rankings.py](../../../backend/tests/test_rankings.py)。
- 处置：保留。

### [backend/app/services/recommendation_service.py](../../../backend/app/services/recommendation_service.py)

业务/规则实现：候选池分桶、多样性和个人信号软排序；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_home_feed`、`get_category_feed`、`invalidate_home_cache`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/api/v1/recommendations.py](../../../backend/app/api/v1/recommendations.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)、[backend/tests/test_recommendations.py](../../../backend/tests/test_recommendations.py)、[backend/tests/test_vocab_recurrence.py](../../../backend/tests/test_vocab_recurrence.py)。
- 处置：保留。

### [backend/app/services/retired_features.py](../../../backend/app/services/retired_features.py)

业务/规则实现：已退役能力的明确 410 与旧通知偏好清洗；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`feature_gone`、`sanitize_notification_preferences`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)、[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)、[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)、[backend/app/api/v1/shadowing.py](../../../backend/app/api/v1/shadowing.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)；其余 5 项见机器清单。
- 处置：保留。

### [backend/app/services/scoring_service.py](../../../backend/app/services/scoring_service.py)

业务/规则实现：可解释的视频学习价值评分与分项记录；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`compute_video_score`、`get_latest_score`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/video_score.py](../../../backend/app/models/video_score.py)。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/tasks/scoring_tasks.py](../../../backend/app/tasks/scoring_tasks.py)、[backend/tests/test_scoring.py](../../../backend/tests/test_scoring.py)。
- 处置：保留。

### [backend/app/services/search_service.py](../../../backend/app/services/search_service.py)

业务/规则实现：PostgreSQL 全文/ILIKE 视频字幕搜索、建议与热搜；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`record_search_query`、`get_hot_searches`、`suggest_titles`、`search_videos`、`search_subtitles`。
- 直接依赖：[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)、[backend/app/services/video_card.py](../../../backend/app/services/video_card.py)。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/tests/test_search_d7.py](../../../backend/tests/test_search_d7.py)。
- 处置：保留。

### [backend/app/services/sms_service.py](../../../backend/app/services/sms_service.py)

业务/规则实现：阿里云短信发码/验码及显式开发替身；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_sms_client`、`send_verify_code`、`verify_code`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)。
- 直接使用者：[backend/app/api/v1/auth.py](../../../backend/app/api/v1/auth.py)、[backend/tests/test_auth_flows.py](../../../backend/tests/test_auth_flows.py)、[backend/tests/test_auth_sms.py](../../../backend/tests/test_auth_sms.py)、[backend/tests/test_profile.py](../../../backend/tests/test_profile.py)、[backend/tests/test_sms_security.py](../../../backend/tests/test_sms_security.py)、[backend/tests/test_video_unlock.py](../../../backend/tests/test_video_unlock.py)。
- 处置：保留。

### [backend/app/services/sr_service.py](../../../backend/app/services/sr_service.py)

业务/规则实现：错误次数分档复习调度与冻结的旧 SM-2 算法；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`calculate_review_interval`、`calculate_next_review`。
- 直接使用者：[backend/app/services/practice_service.py](../../../backend/app/services/practice_service.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)、[backend/tests/test_sr_service.py](../../../backend/tests/test_sr_service.py)。
- 处置：保留。

### [backend/app/services/study_session_service.py](../../../backend/app/services/study_session_service.py)

业务/规则实现：每日配额、轮次、选词、提交与结束；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`clamp_quota`、`get_preferences`、`set_preferences`、`get_today_summary`、`get_active_session`、`get_owned_session`、`session_rows`、`preview_new_words`、`start_session`、`submit_answer`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/study_session.py](../../../backend/app/models/study_session.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/app/services/profile_service.py](../../../backend/app/services/profile_service.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/api/v1/learning_plan.py](../../../backend/app/api/v1/learning_plan.py)、[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/tests/test_vocabulary_transactions.py](../../../backend/tests/test_vocabulary_transactions.py)、[backend/tests/test_vocabulary_transactions_pg.py](../../../backend/tests/test_vocabulary_transactions_pg.py)。
- 处置：保留。

### [backend/app/services/study_time_service.py](../../../backend/app/services/study_time_service.py)

业务/规则实现：按用户本地日聚合有效观看墙钟秒数；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`watch_seconds_by_local_day`、`week_start_local`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)、[backend/tests/test_lesson_progress.py](../../../backend/tests/test_lesson_progress.py)、[backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)。
- 处置：保留。

### [backend/app/services/subtitle_context.py](../../../backend/app/services/subtitle_context.py)

业务/规则实现：按当前用户可见字幕解析单词来源；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`resolve_context`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_access.py](../../../backend/app/services/video_access.py)、[backend/app/services/video_publish.py](../../../backend/app/services/video_publish.py)。
- 直接使用者：[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/app/api/v1/words.py](../../../backend/app/api/v1/words.py)。
- 处置：保留。

### [backend/app/services/subtitle_edit_service.py](../../../backend/app/services/subtitle_edit_service.py)

业务/规则实现：字幕编辑、结构变更、修订、用户引用重映射与回退；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`update_subtitle`、`update_subtitles_batch`、`update_word_levels`、`reorder_subtitles`、`lock_video_row`、`create_subtitle`、`delete_subtitle`、`split_subtitle`、`merge_subtitle`、`recompute_word_levels`（其余见机器清单）。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/subtitle_resegment_snapshot.py](../../../backend/app/models/subtitle_resegment_snapshot.py)、[backend/app/models/subtitle_revision.py](../../../backend/app/models/subtitle_revision.py)；其余 8 项见机器清单。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)、[backend/tests/test_subtitle_resegment.py](../../../backend/tests/test_subtitle_resegment.py)。
- 处置：保留。

### [backend/app/services/subtitle_metrics_service.py](../../../backend/app/services/subtitle_metrics_service.py)

业务/规则实现：从字幕计算语速和词汇密度；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`compute_speech_metrics`、`compute_video_speech_metrics`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 直接使用者：[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_external_meta.py](../../../backend/scripts/backfill_external_meta.py)、[backend/tests/test_external_meta_and_speech_metrics.py](../../../backend/tests/test_external_meta_and_speech_metrics.py)。
- 处置：保留。

### [backend/app/services/subtitle_resegment_rules.py](../../../backend/app/services/subtitle_resegment_rules.py)

业务/规则实现：纯重分段计划、区间映射和可恢复快照规则；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`resegment_segments`、`subtitle_snapshot_dict`、`segment_bounds`、`map_interval_to_segment`、`UserDataCapture`、`RemapPlan`、`build_remap_plan`、`remap_counts`、`snapshot_payload`、`parse_snapshot_payload`（其余见机器清单）。
- 直接依赖：[backend/app/services/subtitle_segmentation.py](../../../backend/app/services/subtitle_segmentation.py)。
- 直接使用者：[backend/app/services/subtitle_edit_service.py](../../../backend/app/services/subtitle_edit_service.py)、[backend/tests/test_subtitle_resegment_mixed.py](../../../backend/tests/test_subtitle_resegment_mixed.py)。
- 处置：保留。

### [backend/app/services/subtitle_segmentation.py](../../../backend/app/services/subtitle_segmentation.py)

业务/规则实现：云端管理重断句使用的拆分/合并规则；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`split_long_segments`、`merge_short_segments`。
- 直接使用者：[backend/app/services/subtitle_resegment_rules.py](../../../backend/app/services/subtitle_resegment_rules.py)。
- 处置：保留。

## `backend/app/services/teaching`

### [backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)、[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)；其余 28 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching/commands.py](../../../backend/app/services/teaching/commands.py)

业务/规则实现：显式教学写动作的统一命令分发，复用原操作幂等；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`execute`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)。
- 直接使用者：[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/tests/test_teaching_quiz.py](../../../backend/tests/test_teaching_quiz.py)、[backend/tests/test_teaching_quiz_pg.py](../../../backend/tests/test_teaching_quiz_pg.py)。
- 处置：保留。

### [backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)

业务/规则实现：教学材料资格核对与当前用途/权限下的正文投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`normalize_text`、`normalized_question`、`source_fingerprint`、`question_key`、`validate_candidate`、`teaching_review_input`、`validate_material`、`publish_revision`、`current_revision_available`、`may_disclose`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/services/question_exposure_service.py](../../../backend/app/services/question_exposure_service.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)、[backend/slcs/material.py](../../../backend/slcs/material.py)。
- 直接使用者：[backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)、[backend/app/services/teaching/qualification.py](../../../backend/app/services/teaching/qualification.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/scripts/content_verification_job.py](../../../backend/scripts/content_verification_job.py)、[backend/scripts/qualify_teaching_content.py](../../../backend/scripts/qualify_teaching_content.py)；其余 7 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching/content_receipts.py](../../../backend/app/services/teaching/content_receipts.py)

业务/规则实现：教学核验输入/结果的 Ed25519 收据验签；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`public_key`、`verify_receipt`。
- 直接使用者：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/services/lesson_receipts.py](../../../backend/app/services/lesson_receipts.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)、[backend/tests/test_content_receipts.py](../../../backend/tests/test_content_receipts.py)。
- 处置：保留。

### [backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)

业务/规则实现：固定任务版本下的可见学习上下文；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`resume_url`、`get_learning_context`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/schemas/learning_context.py](../../../backend/app/schemas/learning_context.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/tests/test_content_publication.py](../../../backend/tests/test_content_publication.py)、[backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)

业务/规则实现：持久聊天消息、引用、当前权限投影与回复校验；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`sources`、`owned`、`owned_chat`、`task_conversation_id`、`task_revision_id`、`task_conversation`、`associate`、`task_views`、`touch`、`project`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching/events.py](../../../backend/app/services/teaching/events.py)

业务/规则实现：教学 outbox 向学习事实的严格投影；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`deliver_pending_events`。
- 直接依赖：[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)。
- 直接使用者：[backend/app/tasks/teaching_tasks.py](../../../backend/app/tasks/teaching_tasks.py)、[backend/tests/test_teaching.py](../../../backend/tests/test_teaching.py)。
- 处置：保留。

### [backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)

业务/规则实现：服务端推导的身份、audience 和 scope 边界；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`Principal`、`require_scope`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)。
- 直接使用者：[backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)、[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/teaching/commands.py](../../../backend/app/services/teaching/commands.py)；其余 14 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)

业务/规则实现：教学候选编辑、预检、验签后发布与撤回事务；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`require_admin_actor`、`receipt_verifier`、`draft_detail`、`list_drafts`、`save_draft`、`preflight`、`PublicationInput`、`publication_input`、`VerifiedManifest`、`verify_publication`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/content_publication.py](../../../backend/app/schemas/content_publication.py)、[backend/app/schemas/pagination.py](../../../backend/app/schemas/pagination.py)；其余 4 项见机器清单。
- 直接使用者：[backend/app/api/v1/admin_teaching_content.py](../../../backend/app/api/v1/admin_teaching_content.py)、[backend/scripts/qualify_teaching_content.py](../../../backend/scripts/qualify_teaching_content.py)、[backend/tests/test_content_publication.py](../../../backend/tests/test_content_publication.py)、[backend/tests/test_content_publication_pg.py](../../../backend/tests/test_content_publication_pg.py)、[backend/tests/test_teaching_content_cli.py](../../../backend/tests/test_teaching_content_cli.py)。
- 处置：保留。

### [backend/app/services/teaching/qualification.py](../../../backend/app/services/teaching/qualification.py)

业务/规则实现：有界内容核验计划和可导入结果组装，不直接发布；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`plan`、`result_passes`、`authenticate_step`、`assemble`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)。
- 直接使用者：[backend/scripts/content_verification_job.py](../../../backend/scripts/content_verification_job.py)、[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)。
- 处置：保留。

### [backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)

业务/规则实现：确定性教学 session/item/attempt、提示、揭晓与幂等操作；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`check_write_access`、`owned_session`、`projection_target`、`answer_history_visible`、`project_session`、`get_session`、`list_sessions`、`content_catalog`、`create_session`、`create_quiz`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)；其余 6 项见机器清单。
- 直接使用者：[backend/app/api/v1/teaching.py](../../../backend/app/api/v1/teaching.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)、[backend/app/services/teaching/commands.py](../../../backend/app/services/teaching/commands.py)；其余 18 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching/streaming.py](../../../backend/app/services/teaching/streaming.py)

业务/规则实现：纯文本引用标记检查与确定性流式消息块切分；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`CitationStream`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)。
- 直接使用者：[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/tests/test_teaching_streaming.py](../../../backend/tests/test_teaching_streaming.py)、[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)。
- 处置：保留。

## `backend/app/services`

### [backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)

业务/规则实现：教学模型网关准入、预算调用、内容核验及流式排空适配；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`content_receipt_verifier`、`verify_content_receipt`、`require_gateway`、`require_content_collection`、`collect_content_receipt`、`choose_intent`、`tutor_reply`、`stream_tutor_reply`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)、[backend/app/services/teaching/content_receipts.py](../../../backend/app/services/teaching/content_receipts.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)。
- 直接使用者：[backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)、[backend/app/services/teaching/qualification.py](../../../backend/app/services/teaching/qualification.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/scripts/content_verification_job.py](../../../backend/scripts/content_verification_job.py)、[backend/tests/test_content_receipt_publication.py](../../../backend/tests/test_content_receipt_publication.py)、[backend/tests/test_content_receipts.py](../../../backend/tests/test_content_receipts.py)；其余 8 项见机器清单。
- 处置：保留。

### [backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)

业务/规则实现：持久模型运行、租约、取消、事件恢复与流式消息写入；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`summary`、`projected_cards`、`append_event`、`dispatch_run`、`start_conversation_turn`、`start_lesson_turn`、`create`、`get`、`events`、`cancel`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/lesson_learning.py](../../../backend/app/models/lesson_learning.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)；其余 14 项见机器清单。
- 直接使用者：[backend/app/api/v1/lesson_learning.py](../../../backend/app/api/v1/lesson_learning.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/tasks/teaching_tasks.py](../../../backend/app/tasks/teaching_tasks.py)、[backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)；其余 10 项见机器清单。
- 处置：保留。

### [backend/app/services/thumbnail_service.py](../../../backend/app/services/thumbnail_service.py)

业务/规则实现：下载/提取并本地化封面，复用外站域名策略；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`local_thumbnail_stems`、`find_local_video_file`、`extract_frame_thumbnail`、`download_thumbnail`、`localize_video_thumbnail`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/media_hosts.py](../../../backend/app/core/media_hosts.py)。
- 直接使用者：[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_external_meta.py](../../../backend/scripts/backfill_external_meta.py)、[backend/scripts/backfill_local_thumbnails.py](../../../backend/scripts/backfill_local_thumbnails.py)、[backend/scripts/rebackfill_video_quality.py](../../../backend/scripts/rebackfill_video_quality.py)、[backend/tests/test_thumbnail_service.py](../../../backend/tests/test_thumbnail_service.py)。
- 处置：保留。

### [backend/app/services/transcription_quality.py](../../../backend/app/services/transcription_quality.py)

业务/规则实现：转录空白、重复、时长/密度等质量门和报告；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`HallucinationCheck`、`QualityReport`、`check_transcription_quality`、`log_quality_report`、`persist_quality_report`。
- 直接依赖：[backend/app/models/video_quality_report.py](../../../backend/app/models/video_quality_report.py)。
- 直接使用者：[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/tests/test_quality_safety_net.py](../../../backend/tests/test_quality_safety_net.py)。
- 处置：保留。

## `backend/app/services/translation`

### [backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)

翻译服务入口：主备引擎、批次、并发、重试及输出检查。

- 代码入口/类型：`TranslationService`、`get_translation_service`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)、[backend/app/services/translation/engines.py](../../../backend/app/services/translation/engines.py)、[backend/app/services/translation/json_sanitizer.py](../../../backend/app/services/translation/json_sanitizer.py)。
- 直接使用者：[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/video_title.py](../../../backend/app/services/video_title.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_video_titles_zh.py](../../../backend/scripts/backfill_video_titles_zh.py)、[backend/scripts/batch_process_seeded.py](../../../backend/scripts/batch_process_seeded.py)、[backend/scripts/check_llm_provider.py](../../../backend/scripts/check_llm_provider.py)；其余 2 项见机器清单。
- 处置：保留。

### [backend/app/services/translation/engines.py](../../../backend/app/services/translation/engines.py)

业务/规则实现：内置翻译引擎的名称、端点和配置形状；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`EngineConfig`。
- 直接使用者：[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)、[backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)、[backend/tests/test_llm_provider.py](../../../backend/tests/test_llm_provider.py)。
- 处置：保留。

### [backend/app/services/translation/json_sanitizer.py](../../../backend/app/services/translation/json_sanitizer.py)

业务/规则实现：清理围栏/混合引号等模型 JSON 格式；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`sanitize_json`。
- 直接使用者：[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)。
- 处置：保留。

### [backend/app/services/translation/quality.py](../../../backend/app/services/translation/quality.py)

业务/规则实现：翻译覆盖率、长度和混合语言质量检查；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`TranslationQualityReport`、`check_translation_quality`、`log_translation_quality`、`persist_quality_report`。
- 直接依赖：[backend/app/models/video_quality_report.py](../../../backend/app/models/video_quality_report.py)。
- 直接使用者：[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_quality_safety_net.py](../../../backend/tests/test_quality_safety_net.py)。
- 处置：保留。

## `backend/app/services`

### [backend/app/services/tutor_conversations.py](../../../backend/app/services/tutor_conversations.py)

业务/规则实现：本人独立聊天、关联任务及共享运行引擎调用；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`require_capability`、`create`、`list_page`、`detail`、`patch`、`delete_chat`。
- 直接依赖：[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/dialogue.py](../../../backend/app/services/teaching/dialogue.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)、[backend/app/services/v2_access.py](../../../backend/app/services/v2_access.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)、[backend/tests/test_tutor_conversations_pg.py](../../../backend/tests/test_tutor_conversations_pg.py)。
- 处置：保留。

### [backend/app/services/v2_access.py](../../../backend/app/services/v2_access.py)

业务/规则实现：默认关闭/白名单、账号有效性与教学准入；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`require_access`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)。
- 直接使用者：[backend/app/api/v1/external_connections.py](../../../backend/app/api/v1/external_connections.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)、[backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/app/services/tutor_conversations.py](../../../backend/app/services/tutor_conversations.py)；其余 14 项见机器清单。
- 处置：保留。

### [backend/app/services/v2_schema.py](../../../backend/app/services/v2_schema.py)

业务/规则实现：缺表/缺列检测及试点惰性准入；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`existing_tables`、`existing_columns`、`has_tables`、`missing_tables`、`schema_ready`、`require_teaching_schema`、`conversation_columns_ready`、`require_conversation_schema`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)。
- 直接使用者：[backend/app/api/v1/external_connections.py](../../../backend/app/api/v1/external_connections.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)、[backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/lesson_tutor.py](../../../backend/app/services/lesson_tutor.py)；其余 10 项见机器清单。
- 处置：保留。

### [backend/app/services/video_access.py](../../../backend/app/services/video_access.py)

业务/规则实现：所有视频消费者复用的本人/官方/管理可见性规则；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`is_video_owner`、`check_video_access`、`check_video_access_by_owner`、`is_admin`、`should_use_snapshot`。
- 直接依赖：[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 直接使用者：[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)、[backend/app/api/v1/notes.py](../../../backend/app/api/v1/notes.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/subtitle_context.py](../../../backend/app/services/subtitle_context.py)、[backend/app/services/video_card.py](../../../backend/app/services/video_card.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)。
- 处置：保留。

### [backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)

业务/规则实现：视频详情、可播放状态及列表的共享缓存失效；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`invalidate_video_detail_cache`、`invalidate_video_playback_cache`、`invalidate_like_caches`、`invalidate_favorite_caches`、`invalidate_view_caches`、`invalidate_browse_cache`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)。
- 直接使用者：[backend/app/api/v1/behavior.py](../../../backend/app/api/v1/behavior.py)、[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/favorites.py](../../../backend/app/api/v1/favorites.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)、[backend/app/services/subtitle_edit_service.py](../../../backend/app/services/subtitle_edit_service.py)、[backend/app/services/video_like_service.py](../../../backend/app/services/video_like_service.py)；其余 10 项见机器清单。
- 处置：保留。

### [backend/app/services/video_card.py](../../../backend/app/services/video_card.py)

业务/规则实现：统一视频卡片 DTO，避免列表/排行/收藏各造一套字段；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`serialize_video_card`、`video_card_payload`。
- 直接依赖：[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)、[backend/app/services/video_access.py](../../../backend/app/services/video_access.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)、[backend/app/services/discovery_service.py](../../../backend/app/services/discovery_service.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)；其余 6 项见机器清单。
- 处置：保留。

### [backend/app/services/video_classification.py](../../../backend/app/services/video_classification.py)

业务/规则实现：通过受控模型生成主题和 CEFR 并校验结果；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`VideoClassificationError`、`validate_topics`、`validate_cefr`、`build_classification_prompt`、`classify_video`、`classify_video_metadata`。
- 直接依赖：[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)。
- 直接使用者：[backend/app/api/v1/browse.py](../../../backend/app/api/v1/browse.py)、[backend/app/schemas/user.py](../../../backend/app/schemas/user.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_classification.py](../../../backend/scripts/backfill_classification.py)、[backend/tests/test_video_classification.py](../../../backend/tests/test_video_classification.py)。
- 处置：保留。

### [backend/app/services/video_learning_material.py](../../../backend/app/services/video_learning_material.py)

业务/规则实现：旧服务导入名到独立 slcs.material 的兼容转发；事务所有权必须看函数，不从 service 名字假定。

- 直接依赖：[backend/slcs/material.py](../../../backend/slcs/material.py)。
- 直接使用者：[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/tests/test_lesson_learning.py](../../../backend/tests/test_lesson_learning.py)、[backend/tests/test_lesson_progress.py](../../../backend/tests/test_lesson_progress.py)、[backend/tests/test_slcs.py](../../../backend/tests/test_slcs.py)。
- 处置：保留。

### [backend/app/services/video_like_service.py](../../../backend/app/services/video_like_service.py)

业务/规则实现：点赞切换、计数与推荐信号；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`toggle_video_like`、`get_video_like_status`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/engagement.py](../../../backend/app/models/engagement.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)。
- 直接使用者：[backend/app/api/v1/favorites.py](../../../backend/app/api/v1/favorites.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)。
- 处置：保留。

### [backend/app/services/video_media.py](../../../backend/app/services/video_media.py)

业务/规则实现：无事务所有权的媒体元信息、stage、下载与转码 I/O；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`find_local_raw`、`stage_local_upload`、`cleanup_oss_raw`、`youtube_extractor_args`、`extract_video_info`、`download_video`、`is_usable_media_file`、`is_usable_local_url`、`transcode_video`、`get_video_height`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/external_meta.py](../../../backend/app/services/external_meta.py)、[backend/app/services/oss_service.py](../../../backend/app/services/oss_service.py)、[backend/app/services/youtube_cookies_service.py](../../../backend/app/services/youtube_cookies_service.py)。
- 直接使用者：[backend/app/services/video_playback.py](../../../backend/app/services/video_playback.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/check_video_media.py](../../../backend/scripts/check_video_media.py)、[backend/scripts/rebackfill_video_quality.py](../../../backend/scripts/rebackfill_video_quality.py)、[backend/tests/test_video_media.py](../../../backend/tests/test_video_media.py)、[backend/tests/test_video_playback.py](../../../backend/tests/test_video_playback.py)。
- 处置：保留。

### [backend/app/services/video_playback.py](../../../backend/app/services/video_playback.py)

业务/规则实现：本地媒体/原站嵌入的可播放与可发布判定；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`PlaybackUnavailableError`、`can_embed`、`set_renditions`、`accept_local_renditions`、`has_renditions`、`has_playback`、`require_playback`、`require_publishable`、`record_localization_failure`、`clear_localization_failure`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)。
- 直接使用者：[backend/app/services/video_publish.py](../../../backend/app/services/video_publish.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_video_playback.py](../../../backend/tests/test_video_playback.py)。
- 处置：保留。

### [backend/app/services/video_publish.py](../../../backend/app/services/video_publish.py)

业务/规则实现：发布与已审核字幕快照的共享操作；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`subtitles_from_snapshot`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/app/services/video_playback.py](../../../backend/app/services/video_playback.py)。
- 直接使用者：[backend/app/services/subtitle_context.py](../../../backend/app/services/subtitle_context.py)、[backend/app/services/video_review_service.py](../../../backend/app/services/video_review_service.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_video_playback.py](../../../backend/tests/test_video_playback.py)。
- 处置：保留。

### [backend/app/services/video_review_service.py](../../../backend/app/services/video_review_service.py)

业务/规则实现：管理员审核旧视频、冻结快照与驳回；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`approve_review`、`reject_review`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/app/services/video_publish.py](../../../backend/app/services/video_publish.py)。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)。
- 处置：保留。

### [backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)

业务/规则实现：管理员/catalog 建视频、检查 GPU 在线、触发/恢复/重试；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`seed_video`、`is_gpu_worker_online`、`start_processing`、`recover_processing`、`retry_video`、`retranslate_video`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/heartbeat.py](../../../backend/app/core/heartbeat.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)；其余 8 项见机器清单。
- 直接使用者：[backend/app/api/v1/admin.py](../../../backend/app/api/v1/admin.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/catalog_service.py](../../../backend/app/services/catalog_service.py)、[backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)。
- 处置：保留。

### [backend/app/services/video_service.py](../../../backend/app/services/video_service.py)

业务/规则实现：视频查询/详情/删除/下架/本地化用例；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`count_subtitles`、`list_public_videos`、`get_video_detail`、`get_video_status`、`list_all_videos`、`get_ugc_pending_counts`、`update_video`、`get_demo_video`、`delete_video`、`takedown_video`（其余见机器清单）。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)；其余 16 项见机器清单。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_perf_hot_paths.py](../../../backend/tests/test_perf_hot_paths.py)、[backend/tests/test_scoring.py](../../../backend/tests/test_scoring.py)、[backend/tests/test_videos.py](../../../backend/tests/test_videos.py)。
- 处置：保留。

### [backend/app/services/video_title.py](../../../backend/app/services/video_title.py)

业务/规则实现：显示用中文视频标题翻译，不改变原题身份；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`normalize_title_zh`、`translate_video_title`。
- 直接依赖：[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)。
- 直接使用者：[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_video_titles_zh.py](../../../backend/scripts/backfill_video_titles_zh.py)、[backend/tests/test_video_title.py](../../../backend/tests/test_video_title.py)。
- 处置：保留。

### [backend/app/services/video_url_guard.py](../../../backend/app/services/video_url_guard.py)

业务/规则实现：外站视频 URL 域名、私网 IP 与 DNS 稳定性检查；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`validate_video_url`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)。
- 直接使用者：[backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)、[backend/tests/test_video_url_guard.py](../../../backend/tests/test_video_url_guard.py)。
- 处置：保留。

### [backend/app/services/vocab_set_service.py](../../../backend/app/services/vocab_set_service.py)

业务/规则实现：按视频考试词建词集、本人过筛及闭环事实；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`collect_set`、`list_sets`、`get_set_detail`、`get_sieve_state`、`sieve_judge`、`mark_learned`、`unmark_learned`、`celebrate`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 8 项见机器清单。
- 直接使用者：[backend/app/api/v1/vocab_sets.py](../../../backend/app/api/v1/vocab_sets.py)、[backend/app/services/library_service.py](../../../backend/app/services/library_service.py)、[backend/tests/test_vocabulary_transactions.py](../../../backend/tests/test_vocabulary_transactions.py)、[backend/tests/test_vocabulary_transactions_pg.py](../../../backend/tests/test_vocabulary_transactions_pg.py)。
- 处置：保留。

### [backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)

业务/规则实现：词典补充、复习状态唯一写入、可选幂等日志和每日选词；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`apply_ecdict_fields`、`record_review`、`record_idempotent_review`、`mark_mastered`、`apply_review`、`review_snapshot`、`review_log_enabled`、`apply_logged_review`、`replay_review`、`enrich_word`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/lesson_learning.py](../../../backend/app/models/lesson_learning.py)；其余 10 项见机器清单。
- 直接使用者：[backend/app/api/v1/vocabulary.py](../../../backend/app/api/v1/vocabulary.py)、[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/overview_service.py](../../../backend/app/services/overview_service.py)、[backend/app/services/practice_service.py](../../../backend/app/services/practice_service.py)、[backend/app/services/study_session_service.py](../../../backend/app/services/study_session_service.py)、[backend/app/services/vocab_set_service.py](../../../backend/app/services/vocab_set_service.py)；其余 5 项见机器清单。
- 处置：保留。

### [backend/app/services/watch_progress_service.py](../../../backend/app/services/watch_progress_service.py)

业务/规则实现：保存观看位置，不把播放位置误当学习掌握；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`save_position`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 直接使用者：[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/tests/test_watch_progress_pg.py](../../../backend/tests/test_watch_progress_pg.py)。
- 处置：保留。

### [backend/app/services/word_notes.py](../../../backend/app/services/word_notes.py)

业务/规则实现：读取最合适词注、批量预热与写入；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`get_note`、`get_best_note`、`upsert_notes`、`prewarm_video_notes`。
- 直接依赖：[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/word_note.py](../../../backend/app/models/word_note.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)。
- 直接使用者：[backend/app/api/v1/words.py](../../../backend/app/api/v1/words.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/batch_process_seeded.py](../../../backend/scripts/batch_process_seeded.py)、[backend/scripts/precompute_global_word_notes.py](../../../backend/scripts/precompute_global_word_notes.py)、[backend/scripts/precompute_global_word_notes_dual.py](../../../backend/scripts/precompute_global_word_notes_dual.py)、[backend/tests/test_exam_corpus.py](../../../backend/tests/test_exam_corpus.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/app/services/youtube_cookies_service.py](../../../backend/app/services/youtube_cookies_service.py)

业务/规则实现：下载器 cookie 探测、隔离副本与受控刷新；事务所有权必须看函数，不从 service 名字假定。

- 代码入口/类型：`disposable_cookiefile`、`probe_cookies`、`refresh_cookies_from_persistent`、`ensure_cookies`、`CookiesCheckResult`、`ensure_cookies_for_pipeline`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/scripts/__init__.py](../../../backend/scripts/__init__.py)、[backend/scripts/get_youtube_cookies.py](../../../backend/scripts/get_youtube_cookies.py)。
- 直接使用者：[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/scripts/backfill_external_meta.py](../../../backend/scripts/backfill_external_meta.py)、[backend/tests/test_youtube_cookies_service.py](../../../backend/tests/test_youtube_cookies_service.py)。
- 处置：保留。

## `backend/app/slcs`

### [backend/app/slcs/__init__.py](../../../backend/app/slcs/__init__.py)

旧 app.slcs 导入路径兼容转发到独立读取器，不是第二份实现。

- 直接依赖：[backend/slcs/__init__.py](../../../backend/slcs/__init__.py)。
- 直接使用者：[backend/tests/test_slcs.py](../../../backend/tests/test_slcs.py)。
- 处置：保留。

### [backend/app/slcs/__main__.py](../../../backend/app/slcs/__main__.py)

旧 python -m app.slcs 命令入口兼容转发到独立 CLI。

- 直接依赖：[backend/slcs/cli.py](../../../backend/slcs/cli.py)。
- 处置：保留。

## `backend/app/tasks`

### [backend/app/tasks/__init__.py](../../../backend/app/tasks/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/tests/test_home_content_generation.py](../../../backend/tests/test_home_content_generation.py)、[backend/tests/test_v2_schema_gating.py](../../../backend/tests/test_v2_schema_gating.py)、[backend/tests/test_video_playback.py](../../../backend/tests/test_video_playback.py)。
- 处置：保留。

### [backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)

后台任务：异步导出、到期注销、外部意图与媒体删除重试；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`build_user_export`、`retry_media_cleanup`、`purge_deleted_accounts`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/data_export.py](../../../backend/app/models/data_export.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 9 项见机器清单。
- 直接使用者：[backend/app/api/v1/users.py](../../../backend/app/api/v1/users.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_account_deletion.py](../../../backend/tests/test_account_deletion.py)、[backend/tests/test_lesson_learning.py](../../../backend/tests/test_lesson_learning.py)、[backend/tests/test_teaching_dialogue.py](../../../backend/tests/test_teaching_dialogue.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)

后台任务：Celery 同步进程复用 async 事件循环的桥接；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`run_async`。
- 直接使用者：[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/app/tasks/home_content_tasks.py](../../../backend/app/tasks/home_content_tasks.py)、[backend/app/tasks/notification_tasks.py](../../../backend/app/tasks/notification_tasks.py)、[backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)、[backend/app/tasks/ranking_tasks.py](../../../backend/app/tasks/ranking_tasks.py)、[backend/app/tasks/reminder_tasks.py](../../../backend/app/tasks/reminder_tasks.py)；其余 2 项见机器清单。
- 处置：保留。

### [backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)

后台任务：消息队列、路由、beat 排程和任务注册；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/observability.py](../../../backend/app/core/observability.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/app/tasks/health_tasks.py](../../../backend/app/tasks/health_tasks.py)；其余 8 项见机器清单。
- 直接使用者：[backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/app/tasks/account_tasks.py](../../../backend/app/tasks/account_tasks.py)、[backend/app/tasks/home_content_tasks.py](../../../backend/app/tasks/home_content_tasks.py)、[backend/app/tasks/notification_tasks.py](../../../backend/app/tasks/notification_tasks.py)、[backend/app/tasks/pipeline_dispatch_tasks.py](../../../backend/app/tasks/pipeline_dispatch_tasks.py)；其余 9 项见机器清单。
- 配置/资源消费者：[docker-compose.yml](../../../docker-compose.yml)、[docker-compose.prod.yml](../../../docker-compose.prod.yml)、[backend/scripts/run_celery_worker.ps1](../../../backend/scripts/run_celery_worker.ps1)。
- 处置：保留。

### [backend/app/tasks/health_tasks.py](../../../backend/app/tasks/health_tasks.py)

后台任务：云 worker/beat 的线程活性心跳；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 直接依赖：[backend/app/core/heartbeat.py](../../../backend/app/core/heartbeat.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)。
- 直接使用者：[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)。
- 处置：保留。

### [backend/app/tasks/home_content_tasks.py](../../../backend/app/tasks/home_content_tasks.py)

后台任务：生成上下文→模型草稿→有条件写回与超时巡检；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`generate_home_content_draft`、`sweep_home_content_generations`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/home_content.py](../../../backend/app/models/home_content.py)、[backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)、[backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_home_content_generation.py](../../../backend/tests/test_home_content_generation.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/tasks/notification_tasks.py](../../../backend/app/tasks/notification_tasks.py)

后台任务：分页公告广播任务与重试；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`broadcast_announcement`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)、[backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)。
- 直接使用者：[backend/app/api/v1/feedback.py](../../../backend/app/api/v1/feedback.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_feedback.py](../../../backend/tests/test_feedback.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/app/tasks/pipeline_dispatch_tasks.py](../../../backend/app/tasks/pipeline_dispatch_tasks.py)

后台任务：定期补发未发送任务并告警积压；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`dispatch_pipeline_tasks`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)、[backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_internal_callback.py](../../../backend/tests/test_internal_callback.py)。
- 处置：保留。

### [backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)

后台任务：视频任务共享锁、步骤声明、恢复、超时预算和错误提交；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`Step`、`get_step_timeouts`、`PipelineCtx`、`run_steps`、`lock_ttl_seconds`、`get_pipeline_redis`、`update_progress`、`is_step_done`、`acquire_lock`、`release_lock`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/pipeline_alerting.py](../../../backend/app/services/pipeline_alerting.py)、[backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)。
- 直接使用者：[backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/app/tasks/health_tasks.py](../../../backend/app/tasks/health_tasks.py)、[backend/app/tasks/pipeline_dispatch_tasks.py](../../../backend/app/tasks/pipeline_dispatch_tasks.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_pipeline_lock_ttl.py](../../../backend/tests/test_pipeline_lock_ttl.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/app/tasks/ranking_tasks.py](../../../backend/app/tasks/ranking_tasks.py)

后台任务：定期重算首页三种榜单快照；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`snapshot_rankings`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/ranking_service.py](../../../backend/app/services/ranking_service.py)、[backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_rankings.py](../../../backend/tests/test_rankings.py)。
- 处置：保留。

### [backend/app/tasks/reminder_tasks.py](../../../backend/app/tasks/reminder_tasks.py)

后台任务：按用户本地时刻发送自愿开启的复习提醒；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`send_hourly_reminders`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/local_time.py](../../../backend/app/services/local_time.py)；其余 3 项见机器清单。
- 直接使用者：[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_local_time.py](../../../backend/tests/test_local_time.py)、[backend/tests/test_reminder_tasks.py](../../../backend/tests/test_reminder_tasks.py)。
- 处置：保留。

### [backend/app/tasks/scoring_tasks.py](../../../backend/app/tasks/scoring_tasks.py)

后台任务：单视频、热门和全量视频评分任务；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`compute_video_score_task`、`compute_top_scores`、`compute_all_scores`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/scoring_service.py](../../../backend/app/services/scoring_service.py)、[backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)。
- 直接使用者：[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/test_celery_tasks.py](../../../backend/tests/test_celery_tasks.py)、[backend/tests/test_celery_tasks_pg.py](../../../backend/tests/test_celery_tasks_pg.py)。
- 处置：保留。

### [backend/app/tasks/teaching_tasks.py](../../../backend/app/tasks/teaching_tasks.py)

后台任务：专用教学执行任务和云端巡检；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`execute_teaching_run`、`sweep_teaching_runs`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/teaching/events.py](../../../backend/app/services/teaching/events.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)、[backend/app/services/v2_schema.py](../../../backend/app/services/v2_schema.py)、[backend/app/tasks/async_helpers.py](../../../backend/app/tasks/async_helpers.py)；其余 1 项见机器清单。
- 直接使用者：[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/test_v2_schema_gating.py](../../../backend/tests/test_v2_schema_gating.py)。
- 处置：保留。

### [backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)

后台任务：云端视频 head/tail、本地化、看门狗和下载重试编排；由 Celery 注册/按任务名消费，不要求普通函数调用者。

- 代码入口/类型：`process_video`、`finalize_steps`、`finalize_video`、`watchdog_stale_pipeline`、`localize_video`、`retry_failed_downloads`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/core/media_probe.py](../../../backend/app/core/media_probe.py)、[backend/app/models/admin_setting.py](../../../backend/app/models/admin_setting.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)；其余 27 项见机器清单。
- 直接使用者：[backend/app/services/video_seed_service.py](../../../backend/app/services/video_seed_service.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/scripts/recover_video.py](../../../backend/scripts/recover_video.py)、[backend/scripts/reprocess_official_videos.py](../../../backend/scripts/reprocess_official_videos.py)、[backend/scripts/retranscribe_video.py](../../../backend/scripts/retranscribe_video.py)、[backend/scripts/seed_local_video.py](../../../backend/scripts/seed_local_video.py)；其余 5 项见机器清单。
- 处置：保留。

## `backend`

### [backend/entrypoint.sh](../../../backend/entrypoint.sh)

容器迁移所有权和启动入口；migrate-only 硬失败，普通启动错误后继续。

- 配置/资源消费者：[backend/Dockerfile.cloud](../../../backend/Dockerfile.cloud)、[docker-compose.prod.yml](../../../docker-compose.prod.yml)、[.claude/skills/deploy/SKILL.md](../../../.claude/skills/deploy/SKILL.md)。
- 处置：保留。

## `backend/migrations`

### [backend/migrations/__init__.py](../../../backend/migrations/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/migrations/env.py](../../../backend/migrations/env.py)

Alembic 迁移运行装配，取设置和完整模型 metadata，支持在线/离线。

- 代码入口/类型：`run_migrations_offline`、`do_run_migrations`、`run_async_migrations`、`run_migrations_online`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)。
- 处置：保留。

### [backend/migrations/script.py.mako](../../../backend/migrations/script.py.mako)

新迁移文件生成模板，不是可删除的旧文案。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `backend/migrations/versions`

### [backend/migrations/versions/1af3205308d9_merge_divergent_heads_phone_login_.py](../../../backend/migrations/versions/1af3205308d9_merge_divergent_heads_phone_login_.py)

数据库历史迁移 1af3205308d9，前驱 ['a9c1d2e3f4b5', 't9u0v1w2x3y4']。。负责数据/索引/约束/版本合并；具体 upgrade 定义在本文件。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/3909bc9d97cd_merge_heads.py](../../../backend/migrations/versions/3909bc9d97cd_merge_heads.py)

数据库历史迁移 3909bc9d97cd，前驱 ['d6e7f8a9b0c1', 'x5y6z7a8b9c0']。。负责数据/索引/约束/版本合并；具体 upgrade 定义在本文件。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/473b87ba4e83_add_server_default_for_community_.py](../../../backend/migrations/versions/473b87ba4e83_add_server_default_for_community_.py)

数据库历史迁移 473b87ba4e83，前驱 s8t9u0v1w2x3。。实际 upgrade：执行数据/DDL SQL UPDATE posts SET like_count = 0 WHERE like_count IS NULL；执行数据/DDL SQL UPDATE posts SET comment_count = 0 WHERE comment_count IS NULL；执行数据/DDL SQL UPDATE user_comments SET like_count = 0 WHERE like_count IS NULL；改列 posts / like_count；改列 posts / comment_count；改列 user_comments / like_count。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/80e681bd554d_initial_schema.py](../../../backend/migrations/versions/80e681bd554d_initial_schema.py)

数据库历史迁移 80e681bd554d，前驱 初始。。实际 upgrade：建表 invite_codes / id；建索引 ix_invite_codes_code / invite_codes；建表 speaking_rubrics / id；建表 users / id；建索引 ix_users_email / users；建表 daily_activities / id；建索引 ix_daily_activities_user_id / daily_activities；建表 follows / id；建索引 ix_follows_followee_id / follows；建索引 ix_follows_follower_id / follows；建表 notifications / id；建索引 ix_notifications_user_id / notifications。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/87140393fa0e_add_pending_processing_status.py](../../../backend/migrations/versions/87140393fa0e_add_pending_processing_status.py)

数据库历史迁移 87140393fa0e，前驱 f92a8f2617d9。。实际 upgrade：执行数据/DDL SQL ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'pending_processing'。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/9f2c8a7d6b10_teaching_conversation.py](../../../backend/migrations/versions/9f2c8a7d6b10_teaching_conversation.py)

数据库历史迁移 9f2c8a7d6b10，前驱 e0f1a2b3c4d5。。实际 upgrade：加列 agent_runs / response_mode；建表 teaching_messages / id；建索引 ix_teaching_messages_user_id / teaching_messages；建索引 ix_teaching_messages_session_id / teaching_messages。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a0b1c2d3e4f5_add_auto_advance_preference.py](../../../backend/migrations/versions/a0b1c2d3e4f5_add_auto_advance_preference.py)

数据库历史迁移 a0b1c2d3e4f5，前驱 k6l7m8n9o0p1。。实际 upgrade：加列 user_preferences / auto_advance_on_correct。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a1b2c3d4e5f6_add_subtitle_words.py](../../../backend/migrations/versions/a1b2c3d4e5f6_add_subtitle_words.py)

数据库历史迁移 a1b2c3d4e5f6，前驱 c4d5e6f7a8b9。。实际 upgrade：get_bind；加列 subtitles / words。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a1c2e3f4g5h6_add_comment_quality_score.py](../../../backend/migrations/versions/a1c2e3f4g5h6_add_comment_quality_score.py)

数据库历史迁移 a1c2e3f4g5h6，前驱 80e681bd554d。。实际 upgrade：加列 videos / comment_quality_score。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a2b3c4d5e6f7_add_behavior_event_id.py](../../../backend/migrations/versions/a2b3c4d5e6f7_add_behavior_event_id.py)

数据库历史迁移 a2b3c4d5e6f7，前驱 c3d4e5f6a7b8。。实际 upgrade：加列 behavior_events / event_id；建索引 uq_behavior_events_event_id / behavior_events。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a5b6c7d8e9f0_add_unique_constraint_comment_reports.py](../../../backend/migrations/versions/a5b6c7d8e9f0_add_unique_constraint_comment_reports.py)

数据库历史迁移 a5b6c7d8e9f0，前驱 473b87ba4e83。。实际 upgrade：执行数据/DDL SQL
        DELETE FROM comment_reports
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM comment_reports
            GROUP；加唯一约束 uq_comment_report_comment_reporter / comment_reports。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a7b8c9d0e1f2_add_exam_paper_bank.py](../../../backend/migrations/versions/a7b8c9d0e1f2_add_exam_paper_bank.py)

数据库历史迁移 a7b8c9d0e1f2，前驱 v1w2x3y4z5a6。。实际 upgrade：建表 exam_papers / id；建索引 ix_exam_papers_level / exam_papers；建表 exam_questions / id；建索引 ix_exam_questions_paper_id / exam_questions；加列 exam_sessions / paper_id；建索引 ix_exam_sessions_paper_id / exam_sessions；加列 exam_answers / question_id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a9b0c1d2e3f4_add_feedbacks_table.py](../../../backend/migrations/versions/a9b0c1d2e3f4_add_feedbacks_table.py)

数据库历史迁移 a9b0c1d2e3f4，前驱 k8l9m0n1o2p3。。实际 upgrade：get_bind；建表 feedbacks / id；建索引 ix_feedbacks_user_id / feedbacks；建索引 ix_feedbacks_status_created / feedbacks。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/a9c1d2e3f4b5_add_phone_login.py](../../../backend/migrations/versions/a9c1d2e3f4b5_add_phone_login.py)

数据库历史迁移 a9c1d2e3f4b5，前驱 87140393fa0e。。实际 upgrade：加列 users / phone；改列 users / email；改列 users / hashed_password；删索引 ix_users_email；建索引 uq_users_email_partial / users；建索引 uq_users_phone_partial / users；f ix_users_email。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b0c1d2e3f4a5_add_vocab_set_celebrated_at.py](../../../backend/migrations/versions/b0c1d2e3f4a5_add_vocab_set_celebrated_at.py)

数据库历史迁移 b0c1d2e3f4a5，前驱 a0b1c2d3e4f5。。实际 upgrade：加列 vocab_sets / celebrated_at。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b1c2d3e4f5a6_add_exam_tables.py](../../../backend/migrations/versions/b1c2d3e4f5a6_add_exam_tables.py)

数据库历史迁移 b1c2d3e4f5a6，前驱 a9b0c1d2e3f4。。实际 upgrade：get_bind；建表 exam_sessions / id；建索引 ix_exam_sessions_user_id / exam_sessions；建索引 ix_exam_sessions_mode / exam_sessions；建索引 ix_exam_sessions_video_id / exam_sessions；建表 exam_answers / id；建索引 ix_exam_answers_session_id / exam_answers。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b2c3d4e5f6a7_add_channels.py](../../../backend/migrations/versions/b2c3d4e5f6a7_add_channels.py)

数据库历史迁移 b2c3d4e5f6a7，前驱 a7b8c9d0e1f2。。实际 upgrade：建表 channels / id；建索引 ix_channels_slug / channels；建索引 ix_channels_upstream_channel_id / channels；加列 videos / channel_ref；加外键 fk_videos_channel_ref_channels / videos；建索引 ix_videos_channel_ref / videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b2c3d4e5f6g7_add_subtitle_resegment_snapshots.py](../../../backend/migrations/versions/b2c3d4e5f6g7_add_subtitle_resegment_snapshots.py)

数据库历史迁移 b2c3d4e5f6g7，前驱 a1b2c3d4e5f6。。实际 upgrade：get_bind；建表 subtitle_resegment_snapshots / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b2d3f4g5h6i7_add_password_changed_at.py](../../../backend/migrations/versions/b2d3f4g5h6i7_add_password_changed_at.py)

数据库历史迁移 b2d3f4g5h6i7，前驱 a1c2e3f4g5h6。。实际 upgrade：加列 users / password_changed_at；执行数据/DDL SQL UPDATE users SET password_changed_at = created_at；改列 users / password_changed_at。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b3c4d5e6f7a8_add_exam_answer_unique.py](../../../backend/migrations/versions/b3c4d5e6f7a8_add_exam_answer_unique.py)

数据库历史迁移 b3c4d5e6f7a8，前驱 a2b3c4d5e6f7。。实际 upgrade：加唯一约束 exam_answers；get_bind。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b6c7d8e9f0a1_add_fk_invite_codes_used_by.py](../../../backend/migrations/versions/b6c7d8e9f0a1_add_fk_invite_codes_used_by.py)

数据库历史迁移 b6c7d8e9f0a1，前驱 a5b6c7d8e9f0。。实际 upgrade：执行数据/DDL SQL
        UPDATE invite_codes
        SET used_by = NULL
        WHERE used_by IS NOT NULL
          AND used_by NOT IN (SELECT id FROM users；加外键 fk_invite_codes_used_by_users / invite_codes。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b7c8d9e0f1a2_event_contract_columns.py](../../../backend/migrations/versions/b7c8d9e0f1a2_event_contract_columns.py)

数据库历史迁移 b7c8d9e0f1a2，前驱 f1a2b3c4d5e6。。实际 upgrade：加列 learning_events / flow_id；加列 learning_events / source；加列 learning_events / schema_version；建索引 ix_learning_events_flow_id / learning_events；加列 behavior_events / flow_id；加列 behavior_events / schema_version；建索引 ix_behavior_events_flow_id / behavior_events。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b7c8d9e0f1g2_drop_community_tables.py](../../../backend/migrations/versions/b7c8d9e0f1g2_drop_community_tables.py)

数据库历史迁移 b7c8d9e0f1g2，前驱 z9y8x7w6v5u4。。实际 upgrade：删表 comment_likes；删表 comment_reports；删表 post_likes；删表 follows；删表 user_comments；删表 posts。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/b8e2f4a6c901_teaching_stream_blocks.py](../../../backend/migrations/versions/b8e2f4a6c901_teaching_stream_blocks.py)

数据库历史迁移 b8e2f4a6c901，前驱 9f2c8a7d6b10。。实际 upgrade：加列 teaching_messages / status；建表 teaching_message_blocks / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c0d1e2f3a4b5_add_account_deletion_and_export.py](../../../backend/migrations/versions/c0d1e2f3a4b5_add_account_deletion_and_export.py)

数据库历史迁移 c0d1e2f3a4b5，前驱 b0c1d2e3f4a5。。实际 upgrade：加列 users / deletion_requested_at；加列 users / deletion_scheduled_at；加列 users / deletion_reason；建表 data_export_tasks / id；建索引 ix_data_export_tasks_user_id / data_export_tasks；建索引 ix_data_export_tasks_user_created / data_export_tasks。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c1d2e3f4g5h6_add_learning_plan_models.py](../../../backend/migrations/versions/c1d2e3f4g5h6_add_learning_plan_models.py)

数据库历史迁移 c1d2e3f4g5h6，前驱 b7c8d9e0f1g2。。实际 upgrade：建表 user_learning_profiles / id；建索引 ix_user_learning_profiles_user_id / user_learning_profiles；建表 learning_plans / id；建索引 ix_learning_plans_user_id / learning_plans；建索引 ix_learning_plans_plan_date / learning_plans；建表 learning_plan_items / id；建索引 ix_learning_plan_items_plan_id / learning_plan_items；建索引 ix_learning_plan_items_video_id / learning_plan_items；建表 learning_events / id；建索引 ix_learning_events_user_id / learning_events；建索引 ix_learning_events_user_date / learning_events；建索引 ix_learning_events_user_type / learning_events。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c3d4e5f6a7b8_drop_redeem_and_retired_tables.py](../../../backend/migrations/versions/c3d4e5f6a7b8_drop_redeem_and_retired_tables.py)

数据库历史迁移 c3d4e5f6a7b8，前驱 q8r9s0t1u2v3。。实际 upgrade：执行数据/DDL SQL DROP TYPE IF EXISTS revokedreason；执行数据/DDL SQL DROP TYPE IF EXISTS redeemstatus；删表。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：更新必要说明/引用或生成路径。

### [backend/migrations/versions/c3d4e5f6g7h8_add_video_featured_admin_notes.py](../../../backend/migrations/versions/c3d4e5f6g7h8_add_video_featured_admin_notes.py)

数据库历史迁移 c3d4e5f6g7h8，前驱 b2d3f4g5h6i7。。实际 upgrade：加列 videos / is_featured；加列 videos / admin_notes。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c4a1b2c3d4e5_tutor_conversations.py](../../../backend/migrations/versions/c4a1b2c3d4e5_tutor_conversations.py)

数据库历史迁移 c4a1b2c3d4e5，前驱 d4e5f6a7b8c9。。实际 upgrade：建表 tutor_conversations / id；建索引 ix_tutor_conversation_user_updated / tutor_conversations；建表 tutor_conversation_tasks / id；建索引 ix_tutor_conversation_tasks_conversation_id / tutor_conversation_tasks；建索引 ix_tutor_conversation_tasks_session_id / tutor_conversation_tasks；加列 teaching_messages / conversation_id；改列 teaching_messages / conversation_id；加外键 fk_teaching_messages_conversation_id / teaching_messages；改列 teaching_messages / session_id；改列 teaching_messages / content_revision_id；改列 teaching_messages / session_revision；删约束 uq_teaching_message_sequence / teaching_messages。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c4d5e6f7a8b9_drop_daily_activities.py](../../../backend/migrations/versions/c4d5e6f7a8b9_drop_daily_activities.py)

数据库历史迁移 c4d5e6f7a8b9，前驱 w4x5y6z7a8b9。。实际 upgrade：删索引 ix_daily_activities_date；删索引 ix_daily_activities_user_id；删表 daily_activities；f ix_daily_activities_user_id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c5d6e7f8a9b0_add_behavior_events.py](../../../backend/migrations/versions/c5d6e7f8a9b0_add_behavior_events.py)

数据库历史迁移 c5d6e7f8a9b0，前驱 f0a1b2c3d4e5。。实际 upgrade：get_bind；建表 behavior_events / id；建索引 ix_behavior_events_user_server / behavior_events；建索引 ix_behavior_events_video_type / behavior_events；加列 videos / view_count。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c6d7e8f9g0h1_add_vocabulary_subtitle_id.py](../../../backend/migrations/versions/c6d7e8f9g0h1_add_vocabulary_subtitle_id.py)

数据库历史迁移 c6d7e8f9g0h1，前驱 q7r8s9t0u1v2。。实际 upgrade：加列 vocabulary / subtitle_id；建索引 ix_vocabulary_subtitle_id / vocabulary。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c8d9e0f1a2b3_exam_snapshots_and_exposures.py](../../../backend/migrations/versions/c8d9e0f1a2b3_exam_snapshots_and_exposures.py)

数据库历史迁移 c8d9e0f1a2b3，前驱 b7c8d9e0f1a2。。实际 upgrade：加列 exam_sessions / snapshot_schema_version；加列 exam_sessions / snapshot_completed_at；建表 user_question_exposures / user_id；建表 user_exposure_mapping_states / user_id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/c9d0e1f2a3b4_perf_search_indexes.py](../../../backend/migrations/versions/c9d0e1f2a3b4_perf_search_indexes.py)

数据库历史迁移 c9d0e1f2a3b4，前驱 c4a1b2c3d4e5。。实际 upgrade：建索引 ix_learning_records_user_completed_accessed / learning_records；建索引 ix_vocabulary_user_mastery_review / vocabulary；执行数据/DDL SQL CREATE EXTENSION IF NOT EXISTS pg_trgm；执行数据/DDL SQL；get_bind。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d1e2f3a4b5c6_drop_fossil_tables.py](../../../backend/migrations/versions/d1e2f3a4b5c6_drop_fossil_tables.py)

数据库历史迁移 d1e2f3a4b5c6，前驱 c0d1e2f3a4b5。。实际 upgrade：删索引 ix_learning_events_plan_id；删列 learning_events / plan_id；删表 learning_plan_items；删表 learning_plans；删表 subtitle_mergeable_updates；删表 subtitle_change_proposals；删表 video_comments；删表 video_comment_stats。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d2e3f4g5h6i7_add_vocabulary_plan_columns.py](../../../backend/migrations/versions/d2e3f4g5h6i7_add_vocabulary_plan_columns.py)

数据库历史迁移 d2e3f4g5h6i7，前驱 c1d2e3f4g5h6。。实际 upgrade：加列 vocabulary / exam_level；加列 vocabulary / first_seen_at；加列 vocabulary / correct_count。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d4e5f6a7b8c9_drop_paid_membership_chain.py](../../../backend/migrations/versions/d4e5f6a7b8c9_drop_paid_membership_chain.py)

数据库历史迁移 d4e5f6a7b8c9，前驱 b8e2f4a6c901。。实际 upgrade：删索引 ix_jinshuju_payments_status；删索引 ix_jinshuju_payments_phone；删索引 uq_jinshuju_payments_entry_token；删表 jinshuju_payments；删索引 ix_orders_order_number；删索引 ix_orders_user_id；删表 orders；删索引 ix_user_video_unlocks_user_unlocked_at；删表 user_video_unlocks；删列 admin_settings / payments_enabled；删列 admin_settings / wechat_shop_url；删列 users / plan_source。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d4e5f6g7h8i9_add_comment_count_to_videos.py](../../../backend/migrations/versions/d4e5f6g7h8i9_add_comment_count_to_videos.py)

数据库历史迁移 d4e5f6g7h8i9，前驱 c3d4e5f6g7h8。。实际 upgrade：加列 videos / comment_count。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d5e6f7a8b9c0_add_pipeline_dispatches.py](../../../backend/migrations/versions/d5e6f7a8b9c0_add_pipeline_dispatches.py)

数据库历史迁移 d5e6f7a8b9c0，前驱 b3c4d5e6f7a8。。实际 upgrade：建表 pipeline_dispatches / id；建索引 ix_pipeline_dispatches_video_id / pipeline_dispatches；建索引 ix_pipeline_dispatches_status_next / pipeline_dispatches。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d6e7f8a9b0c1_add_video_scores.py](../../../backend/migrations/versions/d6e7f8a9b0c1_add_video_scores.py)

数据库历史迁移 d6e7f8a9b0c1，前驱 c5d6e7f8a9b0。。实际 upgrade：get_bind；建表 video_scores / id；建索引 ix_video_scores_video_computed / video_scores；加列 videos / score；加列 videos / score_updated_at；建索引 ix_videos_score / videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d7e21b4c9f80_add_slcs_lessons.py](../../../backend/migrations/versions/d7e21b4c9f80_add_slcs_lessons.py)

数据库历史迁移 d7e21b4c9f80，前驱 c9d0e1f2a3b4。。实际 upgrade：建表 lessons / id；建表 lesson_revisions / id；加外键 fk_lessons_current_revision / lessons；建表 lesson_operations / id；建索引 ix_lesson_operations_actor_id / lesson_operations；建索引 ix_lesson_operations_revision_id / lesson_operations；建表 lesson_progress / user_id；建表 lesson_activities / id；建索引 ix_lesson_activities_user_time / lesson_activities。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d7e21b4c9f81_lesson_tutor_anchors.py](../../../backend/migrations/versions/d7e21b4c9f81_lesson_tutor_anchors.py)

数据库历史迁移 d7e21b4c9f81，前驱 d7e21b4c9f80。。实际 upgrade：建表 lesson_tutor_anchors / conversation_id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d7e21b4c9f82_lesson_vocabulary.py](../../../backend/migrations/versions/d7e21b4c9f82_lesson_vocabulary.py)

数据库历史迁移 d7e21b4c9f82，前驱 d7e21b4c9f81。。实际 upgrade：建表 lesson_vocabulary_sources / id；建表 vocabulary_review_log / id；建索引 ix_vocabulary_review_log_vocabulary_id / vocabulary_review_log。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d9e0f1a2b3c4_teaching_and_external_runtime.py](../../../backend/migrations/versions/d9e0f1a2b3c4_teaching_and_external_runtime.py)

数据库历史迁移 d9e0f1a2b3c4，前驱 c8d9e0f1a2b3。。实际 upgrade：建表 gateway_lifecycle_intents / id；建索引 ix_gateway_lifecycle_intents_status / gateway_lifecycle_intents；建表 external_connections / id；建索引 ix_external_connections_user_id / external_connections；建表 teaching_access_grants / user_id；建表 teaching_operations / id；建索引 ix_teaching_operations_user_id / teaching_operations；建表 exam_analysis_revisions / id；建索引 ix_exam_analysis_revisions_question_id / exam_analysis_revisions；建索引 ix_exam_analysis_revisions_question_key / exam_analysis_revisions；建索引 ix_exam_analysis_revisions_status / exam_analysis_revisions；建表 external_credentials / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/d9e0f1g2h3i4_add_weekly_reports.py](../../../backend/migrations/versions/d9e0f1g2h3i4_add_weekly_reports.py)

数据库历史迁移 d9e0f1g2h3i4，前驱 c6d7e8f9g0h1。。实际 upgrade：建表 weekly_reports / id；建索引 ix_weekly_reports_user_id / weekly_reports；建索引 ix_weekly_reports_week_start / weekly_reports。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/e0f1a2b3c4d5_content_publication.py](../../../backend/migrations/versions/e0f1a2b3c4d5_content_publication.py)

数据库历史迁移 e0f1a2b3c4d5，前驱 d9e0f1a2b3c4。。实际 upgrade：建表 teaching_content_drafts / id；建表 content_publication_operations / id；建索引 ix_content_publication_operations_actor_id / content_publication_operations；建索引 ix_content_publication_operations_target_id / content_publication_operations。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/e0f1g2h3i4j5_add_channel_is_auto.py](../../../backend/migrations/versions/e0f1g2h3i4j5_add_channel_is_auto.py)

数据库历史迁移 e0f1g2h3i4j5，前驱 d9e0f1g2h3i4。。实际 upgrade：执行数据/DDL SQL
        UPDATE videos SET channel_ref = (
            SELECT MIN(c2.id) FROM channels c2
            WHERE c2.upstream_channel_id = (
     ；执行数据/DDL SQL
        DELETE FROM channels WHERE id IN (
            SELECT c1.id FROM channels c1
            WHERE c1.upstream_channel_id IS NOT NULL
 ；删索引 ix_channels_upstream_channel_id；建索引 ix_channels_upstream_channel_id / channels；加列 channels / is_auto。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/e1m2a3i4l5r6_remove_email_auth.py](../../../backend/migrations/versions/e1m2a3i4l5r6_remove_email_auth.py)

数据库历史迁移 e1m2a3i4l5r6，前驱 3909bc9d97cd。。实际 upgrade：删表 password_reset_tokens；删索引 uq_users_email_partial；删列 users / email_verified_at；删列 users / email。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/e2f3a4b5c6d7_user_content_design.py](../../../backend/migrations/versions/e2f3a4b5c6d7_user_content_design.py)

数据库历史迁移 e2f3a4b5c6d7，前驱 d1e2f3a4b5c6。。实际 upgrade：加列 user_preferences / interest_categories；加列 vocab_sets / source_type；加列 vocab_sets / name；批量改表 vocab_sets；建表 id；建索引；建索引。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/e3f4g5h6i7j8_add_shadowing_attempts.py](../../../backend/migrations/versions/e3f4g5h6i7j8_add_shadowing_attempts.py)

数据库历史迁移 e3f4g5h6i7j8，前驱 d2e3f4g5h6i7。。实际 upgrade：建表 shadowing_attempts / id；加列 user_learning_profiles / total_shadowing_count。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/e5f6g7h8i9j0_add_user_favorites_and_notes.py](../../../backend/migrations/versions/e5f6g7h8i9j0_add_user_favorites_and_notes.py)

数据库历史迁移 e5f6g7h8i9j0，前驱 d4e5f6g7h8i9。。实际 upgrade：建表 user_favorites / id；建索引 ix_user_favorites_user_id / user_favorites；建索引 ix_user_favorites_video_id / user_favorites；建表 user_notes / id；建索引 ix_user_notes_user_id / user_notes；建索引 ix_user_notes_video_id / user_notes。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f0a1b2c3d4e5_merge_heads_resegment_video_featured.py](../../../backend/migrations/versions/f0a1b2c3d4e5_merge_heads_resegment_video_featured.py)

数据库历史迁移 f0a1b2c3d4e5，前驱 ['b2c3d4e5f6g7', 'c3d4e5f6g7h8']。。负责数据/索引/约束/版本合并；具体 upgrade 定义在本文件。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f1a2b3c4d5e6_add_media_cleanup_tasks.py](../../../backend/migrations/versions/f1a2b3c4d5e6_add_media_cleanup_tasks.py)

数据库历史迁移 f1a2b3c4d5e6，前驱 d5e6f7a8b9c0。。实际 upgrade：建表 media_cleanup_tasks / id；建索引 ix_media_cleanup_status_next / media_cleanup_tasks；建索引 ix_media_cleanup_user / media_cleanup_tasks。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f1g2h3i4j5k6_add_catalog_items.py](../../../backend/migrations/versions/f1g2h3i4j5k6_add_catalog_items.py)

数据库历史迁移 f1g2h3i4j5k6，前驱 e0f1g2h3i4j5。。实际 upgrade：建表 catalog_items / id；建索引 ix_catalog_source_upstream / catalog_items；建索引 ix_catalog_status_fit / catalog_items；建索引 ix_catalog_items_fit_score / catalog_items；建索引 ix_catalog_items_promoted_video_id / catalog_items。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f4g5h6i7j8k9_add_milestones_mastery_snapshots.py](../../../backend/migrations/versions/f4g5h6i7j8k9_add_milestones_mastery_snapshots.py)

数据库历史迁移 f4g5h6i7j8k9，前驱 e3f4g5h6i7j8。。实际 upgrade：建表 user_milestones / id；建表 mastery_snapshots / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f5g6h7i8j9k0_add_video_quality_reports.py](../../../backend/migrations/versions/f5g6h7i8j9k0_add_video_quality_reports.py)

数据库历史迁移 f5g6h7i8j9k0，前驱 e3f4g5h6i7j8。。实际 upgrade：建表 video_quality_reports / id；建索引 ix_video_quality_reports_video_id / video_quality_reports；建索引 ix_vqr_video_stage / video_quality_reports。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f6a7b8c9d0e1_add_word_levels_and_target_exam.py](../../../backend/migrations/versions/f6a7b8c9d0e1_add_word_levels_and_target_exam.py)

数据库历史迁移 f6a7b8c9d0e1，前驱 e5f6g7h8i9j0。。实际 upgrade：get_bind；加列 subtitles / word_levels；加列 user_preferences / target_exam。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/f92a8f2617d9_add_subtitle_video_id_sentence_index_.py](../../../backend/migrations/versions/f92a8f2617d9_add_subtitle_video_id_sentence_index_.py)

数据库历史迁移 f92a8f2617d9，前驱 b6c7d8e9f0a1。。实际 upgrade：建索引 ix_subtitles_video_id_sentence_index / subtitles。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/g2h3i4j5k6l7_add_video_published_at.py](../../../backend/migrations/versions/g2h3i4j5k6l7_add_video_published_at.py)

数据库历史迁移 g2h3i4j5k6l7，前驱 f1g2h3i4j5k6。。实际 upgrade：加列 videos / published_at；执行数据/DDL SQL UPDATE videos SET published_at = COALESCE(reviewed_at, created_at)；建索引 ix_videos_published_at / videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/g6h7i8j9k0l1_merge_heads_quality_milestones.py](../../../backend/migrations/versions/g6h7i8j9k0l1_merge_heads_quality_milestones.py)

数据库历史迁移 g6h7i8j9k0l1，前驱 ['f4g5h6i7j8k9', 'f5g6h7i8j9k0']。。负责数据/索引/约束/版本合并；具体 upgrade 定义在本文件。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/g7b8c9d0e1f2_add_video_practice_questions.py](../../../backend/migrations/versions/g7b8c9d0e1f2_add_video_practice_questions.py)

数据库历史迁移 g7b8c9d0e1f2，前驱 f6a7b8c9d0e1。。实际 upgrade：建表 video_practice_questions / id；建索引 ix_video_practice_questions_video_id / video_practice_questions。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/h3i4j5k6l7m8_add_vocab_sets.py](../../../backend/migrations/versions/h3i4j5k6l7m8_add_vocab_sets.py)

数据库历史迁移 h3i4j5k6l7m8，前驱 g2h3i4j5k6l7。。实际 upgrade：建表 vocab_sets / id；建索引 ix_vocab_sets_user_id / vocab_sets；建表 vocab_set_words / id；建索引 ix_vocab_set_words_set_id_position / vocab_set_words。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/h7i8j9k0l1m2_add_step_started_at.py](../../../backend/migrations/versions/h7i8j9k0l1m2_add_step_started_at.py)

数据库历史迁移 h7i8j9k0l1m2，前驱 g6h7i8j9k0l1。。实际 upgrade：get_bind；加列 videos / step_started_at。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/h8c9d0e1f2g3_add_exam_corpus.py](../../../backend/migrations/versions/h8c9d0e1f2g3_add_exam_corpus.py)

数据库历史迁移 h8c9d0e1f2g3，前驱 g7b8c9d0e1f2。。实际 upgrade：建表 exam_sentences / id；建索引 ix_exam_sentences_level / exam_sentences；建表 exam_sentence_words / id；建索引 ix_exam_sentence_words_sentence_id / exam_sentence_words；建索引 ix_exam_sentence_words_word / exam_sentence_words；建表 exam_word_freq / id；建索引 ix_exam_word_freq_word / exam_word_freq；建索引 ix_exam_word_freq_level / exam_word_freq。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/i4j5k6l7m8n9_add_video_storage_mode.py](../../../backend/migrations/versions/i4j5k6l7m8n9_add_video_storage_mode.py)

数据库历史迁移 i4j5k6l7m8n9，前驱 h3i4j5k6l7m8。。实际 upgrade：加列 videos / storage_mode；建索引 ix_videos_storage_mode / videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/i8h9c0d1e2f3_add_word_ai_notes.py](../../../backend/migrations/versions/i8h9c0d1e2f3_add_word_ai_notes.py)

数据库历史迁移 i8h9c0d1e2f3，前驱 h8c9d0e1f2g3。。实际 upgrade：建表 word_ai_notes / id；建索引 ix_word_ai_notes_word_level / word_ai_notes；建索引 ix_word_ai_notes_word_source / word_ai_notes；建索引 ix_word_ai_notes_source / word_ai_notes。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/i8j9k0l1m2n3_add_video_quality_flag.py](../../../backend/migrations/versions/i8j9k0l1m2n3_add_video_quality_flag.py)

数据库历史迁移 i8j9k0l1m2n3，前驱 h7i8j9k0l1m2。。实际 upgrade：get_bind；加列 videos / quality_flag。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/j1i2n3s4h5u6_add_jinshuju_payments.py](../../../backend/migrations/versions/j1i2n3s4h5u6_add_jinshuju_payments.py)

数据库历史迁移 j1i2n3s4h5u6，前驱 e2f3a4b5c6d7。。实际 upgrade：建表 jinshuju_payments / id；建索引 uq_jinshuju_payments_entry_token / jinshuju_payments；建索引 ix_jinshuju_payments_phone / jinshuju_payments；建索引 ix_jinshuju_payments_status / jinshuju_payments。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/j5k6l7m8n9o0_add_user_gender.py](../../../backend/migrations/versions/j5k6l7m8n9o0_add_user_gender.py)

数据库历史迁移 j5k6l7m8n9o0，前驱 i4j5k6l7m8n9。。实际 upgrade：加列 users / gender。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/j9k0l1m2n3o4_add_user_is_banned.py](../../../backend/migrations/versions/j9k0l1m2n3o4_add_user_is_banned.py)

数据库历史迁移 j9k0l1m2n3o4，前驱 i8h9c0d1e2f3。。实际 upgrade：加列 users / is_banned。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/k0l1m2n3o4p5_add_video_is_published.py](../../../backend/migrations/versions/k0l1m2n3o4p5_add_video_is_published.py)

数据库历史迁移 k0l1m2n3o4p5，前驱 j9k0l1m2n3o4。。实际 upgrade：加列 videos / is_published；执行数据/DDL SQL UPDATE videos SET is_published = is_official。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/k6l7m8n9o0p1_add_study_sessions_and_quota.py](../../../backend/migrations/versions/k6l7m8n9o0p1_add_study_sessions_and_quota.py)

数据库历史迁移 k6l7m8n9o0p1，前驱 j5k6l7m8n9o0。。实际 upgrade：建表 study_sessions / id；建索引 ix_study_sessions_user_id / study_sessions；建索引 ix_study_sessions_status / study_sessions；建索引 ix_study_sessions_user_status / study_sessions；建索引 ix_study_sessions_user_date / study_sessions；建表 study_session_items / id；建索引 ix_study_session_items_session_id / study_session_items；建索引 ix_study_session_items_vocabulary / study_session_items；加列 vocabulary / wrong_count；加列 vocabulary / last_wrong_at；加列 user_learning_profiles / daily_new_target；加列 user_learning_profiles / daily_review_target。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/k8l9m0n1o2p3_add_download_retry_fields.py](../../../backend/migrations/versions/k8l9m0n1o2p3_add_download_retry_fields.py)

数据库历史迁移 k8l9m0n1o2p3，前驱 i8j9k0l1m2n3。。实际 upgrade：get_bind；加列 videos / download_failed_at；加列 videos / download_fail_count。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/l0m1n2o3p4q5_widen_word_ai_notes_context_source.py](../../../backend/migrations/versions/l0m1n2o3p4q5_widen_word_ai_notes_context_source.py)

数据库历史迁移 l0m1n2o3p4q5，前驱 k0l1m2n3o4p5。。实际 upgrade：改列 word_ai_notes / context_source。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/m2n3o4p5q6r7_add_video_auto_publish.py](../../../backend/migrations/versions/m2n3o4p5q6r7_add_video_auto_publish.py)

数据库历史迁移 m2n3o4p5q6r7，前驱 l0m1n2o3p4q5。。实际 upgrade：加列 videos / auto_publish。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/m3n4o5p6q7r8_home_editorial_content.py](../../../backend/migrations/versions/m3n4o5p6q7r8_home_editorial_content.py)

数据库历史迁移 m3n4o5p6q7r8，前驱 j1i2n3s4h5u6。。实际 upgrade：建表 home_content_drafts / id；建索引 uq_home_content_drafts_video_id / home_content_drafts；建表 home_content_revisions / id；建索引 ix_home_content_revisions_video_id / home_content_revisions；建表 home_page_config / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：更新必要说明/引用或生成路径。

### [backend/migrations/versions/m4n5o6p7q8r9_add_home_generation_coverage.py](../../../backend/migrations/versions/m4n5o6p7q8r9_add_home_generation_coverage.py)

数据库历史迁移 m4n5o6p7q8r9，前驱 m3n4o5p6q7r8。。实际 upgrade：加列 home_content_drafts / generation_coverage。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/n3o4p5q6r7s8_add_video_review_status.py](../../../backend/migrations/versions/n3o4p5q6r7s8_add_video_review_status.py)

数据库历史迁移 n3o4p5q6r7s8，前驱 m2n3o4p5q6r7。。实际 upgrade：加列 videos / review_status；加列 videos / submitted_at；加列 videos / reviewed_by；加列 videos / reviewed_at；加列 videos / rejection_reason；加列 videos / published_snapshot；执行数据/DDL SQL UPDATE videos SET review_status = 'published' WHERE is_official = true OR is_published = true。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/n5o6p7q8r9s0_add_video_title_zh.py](../../../backend/migrations/versions/n5o6p7q8r9s0_add_video_title_zh.py)

数据库历史迁移 n5o6p7q8r9s0，前驱 m4n5o6p7q8r9。。实际 upgrade：加列 videos / title_zh。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/o4p5q6r7s8t9_add_video_like_favorite_counts.py](../../../backend/migrations/versions/o4p5q6r7s8t9_add_video_like_favorite_counts.py)

数据库历史迁移 o4p5q6r7s8t9，前驱 n3o4p5q6r7s8。。实际 upgrade：加列 videos / like_count；加列 videos / favorite_count；执行数据/DDL SQL UPDATE videos SET favorite_count = COALESCE((SELECT COUNT(*) FROM user_favorites WHERE user_favorites.video_id = videos.id), 0)；建表 video_likes / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/o6p7q8r9s0t1_add_listening_sessions.py](../../../backend/migrations/versions/o6p7q8r9s0t1_add_listening_sessions.py)

数据库历史迁移 o6p7q8r9s0t1，前驱 n5o6p7q8r9s0。。实际 upgrade：建表 listening_sessions / id；建索引 ix_listening_sessions_user_id / listening_sessions；建索引 ix_listening_sessions_video_id / listening_sessions。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/p5q6r7s8t9u0_add_show_on_homepage.py](../../../backend/migrations/versions/p5q6r7s8t9u0_add_show_on_homepage.py)

数据库历史迁移 p5q6r7s8t9u0，前驱 o4p5q6r7s8t9。。实际 upgrade：加列 videos / show_on_homepage；执行数据/DDL SQL UPDATE videos SET show_on_homepage = true WHERE is_official = true AND is_published = true。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/p6q7r8s9t0u1_add_video_unlocks_and_trial_source.py](../../../backend/migrations/versions/p6q7r8s9t0u1_add_video_unlocks_and_trial_source.py)

数据库历史迁移 p6q7r8s9t0u1，前驱 b2c3d4e5f6a7。。实际 upgrade：建表 user_video_unlocks / user_id；建索引 ix_user_video_unlocks_user_unlocked_at / user_video_unlocks；加列 users / plan_source；加列 videos / is_demo。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/p7q8r9s0t1u2_align_model_schema_drift.py](../../../backend/migrations/versions/p7q8r9s0t1u2_align_model_schema_drift.py)

数据库历史迁移 p7q8r9s0t1u2，前驱 o6p7q8r9s0t1。。实际 upgrade：get_bind；加唯一约束 uq_exam_sentence_word / exam_sentence_words；加外键 exam_sentence_words_sentence_id_fkey / exam_sentence_words；加唯一约束 uq_exam_word_freq_word_level / exam_word_freq；建索引 ix_notifications_dedup / notifications；加外键 videos_reviewed_by_fkey / videos；删约束 subtitles；加外键 subtitles_video_id_fkey / subtitles；执行数据/DDL SQL ALTER INDEX ix_vocab_video_id RENAME TO ix_vocabulary_video_id；加外键 subtitles_video_id_fkey / subtitles；建索引 ix_vocabulary_video_id / vocabulary；执行数据/DDL SQL。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/q6r7s8t9u0v1_add_missing_indexes.py](../../../backend/migrations/versions/q6r7s8t9u0v1_add_missing_indexes.py)

数据库历史迁移 q6r7s8t9u0v1，前驱 p5q6r7s8t9u0。。实际 upgrade：建索引 ix_user_comments_parent_id / user_comments；建索引 ix_posts_video_id / posts；建索引 ix_comment_reports_status / comment_reports；建索引 ix_learning_records_video_id / learning_records；建索引 ix_vocab_video_id / vocabulary；建索引 ix_daily_activities_date / daily_activities；建索引 ix_videos_homepage_status / videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/q7r8s9t0u1v2_add_subtitle_font_size_preference.py](../../../backend/migrations/versions/q7r8s9t0u1v2_add_subtitle_font_size_preference.py)

数据库历史迁移 q7r8s9t0u1v2，前驱 p6q7r8s9t0u1。。实际 upgrade：加列 user_preferences / subtitle_font_size。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/q8r9s0t1u2v3_add_query_shape_indexes.py](../../../backend/migrations/versions/q8r9s0t1u2v3_add_query_shape_indexes.py)

数据库历史迁移 q8r9s0t1u2v3，前驱 p7q8r9s0t1u2。。实际 upgrade：建索引。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/r3e4d5e6e7m8_redeem_code_lifecycle.py](../../../backend/migrations/versions/r3e4d5e6e7m8_redeem_code_lifecycle.py)

数据库历史迁移 r3e4d5e6e7m8，前驱 e1m2a3i4l5r6。。实际 upgrade：rename_table invite_codes / redeem_codes；执行数据/DDL SQL CREATE TYPE redeemstatus AS ENUM ('unused', 'redeemed', 'revoked', 'expired')；执行数据/DDL SQL CREATE TYPE revokedreason AS ENUM ('leak', 'error', 'refund')；加列 redeem_codes / status；加列 redeem_codes / revoked_reason；加列 redeem_codes / expires_at；执行数据/DDL SQL UPDATE redeem_codes SET status = 'redeemed' WHERE is_used；执行数据/DDL SQL UPDATE redeem_codes SET status = 'unused' WHERE NOT is_used；改列 redeem_codes / status；删列 redeem_codes / is_used；执行数据/DDL SQL ALTER INDEX ix_invite_codes_code RENAME TO ix_redeem_codes_code；执行数据/DDL SQL ALTER TABLE redeem_codes RENAME CONSTRAINT invite_codes_pkey TO redeem_codes_pkey。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/r7s8t9u0v1w2_add_ondelete_cascade.py](../../../backend/migrations/versions/r7s8t9u0v1w2_add_ondelete_cascade.py)

数据库历史迁移 r7s8t9u0v1w2，前驱 q6r7s8t9u0v1。。实际 upgrade：删约束 posts_video_id_fkey / posts；加外键 posts_video_id_fkey / posts；删约束 user_comments_parent_id_fkey / user_comments；加外键 user_comments_parent_id_fkey / user_comments；删约束 comment_reports_comment_id_fkey / comment_reports；加外键 comment_reports_comment_id_fkey / comment_reports；删约束 speaking_attempts_subtitle_id_fkey / speaking_attempts；加外键 speaking_attempts_subtitle_id_fkey / speaking_attempts；删约束 learning_records_video_id_fkey / learning_records；加外键 learning_records_video_id_fkey / learning_records；删约束 vocabulary_video_id_fkey / vocabulary；加外键 vocabulary_video_id_fkey / vocabulary。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/s1e2t3t4i5n6_add_admin_settings.py](../../../backend/migrations/versions/s1e2t3t4i5n6_add_admin_settings.py)

数据库历史迁移 s1e2t3t4i5n6，前驱 b1c2d3e4f5a6。。实际 upgrade：建表 admin_settings / id。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/s8t9u0v1w2x3_add_password_reset_token_lookup.py](../../../backend/migrations/versions/s8t9u0v1w2x3_add_password_reset_token_lookup.py)

数据库历史迁移 s8t9u0v1w2x3，前驱 r7s8t9u0v1w2。。实际 upgrade：加列 password_reset_tokens / token_lookup；建索引 ix_password_reset_tokens_token_lookup / password_reset_tokens。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/t2u3v4w5x6y7_add_video_external_meta.py](../../../backend/migrations/versions/t2u3v4w5x6y7_add_video_external_meta.py)

数据库历史迁移 t2u3v4w5x6y7，前驱 s1e2t3t4i5n6。。实际 upgrade：get_bind；建索引 ix_videos_yt_video_id / videos；加列 videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/t9u0v1w2x3y4_add_processing_started_at_to_videos.py](../../../backend/migrations/versions/t9u0v1w2x3y4_add_processing_started_at_to_videos.py)

数据库历史迁移 t9u0v1w2x3y4，前驱 s8t9u0v1w2x3。。实际 upgrade：加列 videos / processing_started_at。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/u2v3w4x5y6z7_add_video_standards_and_forked_from.py](../../../backend/migrations/versions/u2v3w4x5y6z7_add_video_standards_and_forked_from.py)

数据库历史迁移 u2v3w4x5y6z7，前驱 1af3205308d9。。实际 upgrade：建表 video_standards / source_url；建索引 ix_video_standards_canonical_video_id / video_standards；加列 videos / forked_from；建索引 ix_videos_forked_from / videos；建索引 ix_videos_source_url / videos。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：更新必要说明/引用或生成路径。

### [backend/migrations/versions/u3v4w5x6y7z8_add_video_score_viral_freshness.py](../../../backend/migrations/versions/u3v4w5x6y7z8_add_video_score_viral_freshness.py)

数据库历史迁移 u3v4w5x6y7z8，前驱 t2u3v4w5x6y7。。实际 upgrade：get_bind；加列 video_scores。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/v1w2x3y4z5a6_add_learning_event_ref_indexes.py](../../../backend/migrations/versions/v1w2x3y4z5a6_add_learning_event_ref_indexes.py)

数据库历史迁移 v1w2x3y4z5a6，前驱 u3v4w5x6y7z8。。实际 upgrade：建索引 ix_learning_events_video_id / learning_events；建索引 ix_learning_events_plan_id / learning_events。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/v3w4x5y6z7a8_add_subtitle_revisions.py](../../../backend/migrations/versions/v3w4x5y6z7a8_add_subtitle_revisions.py)

数据库历史迁移 v3w4x5y6z7a8，前驱 u2v3w4x5y6z7。。实际 upgrade：建表 subtitle_revisions / id；建索引 ix_subtitle_revisions_subtitle_id / subtitle_revisions；建索引 ix_subtitle_revisions_video_id / subtitle_revisions；建索引 ix_subtitle_revisions_created_at / subtitle_revisions。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：更新必要说明/引用或生成路径。

### [backend/migrations/versions/w4x5y6z7a8b9_add_proposals_and_mergeable_updates.py](../../../backend/migrations/versions/w4x5y6z7a8b9_add_proposals_and_mergeable_updates.py)

数据库历史迁移 w4x5y6z7a8b9，前驱 v3w4x5y6z7a8。。实际 upgrade：建表 subtitle_change_proposals / id；建索引 ix_scp_standard_video_id / subtitle_change_proposals；建索引 ix_scp_status / subtitle_change_proposals；建索引 ix_scp_submitted_by / subtitle_change_proposals；建索引 ix_scp_created_at / subtitle_change_proposals；建表 subtitle_mergeable_updates / id；建索引 ix_smu_fork_video_id / subtitle_mergeable_updates。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：更新必要说明/引用或生成路径。

### [backend/migrations/versions/x5y6z7a8b9c0_add_uq_learning_record_user_video.py](../../../backend/migrations/versions/x5y6z7a8b9c0_add_uq_learning_record_user_video.py)

数据库历史迁移 x5y6z7a8b9c0，前驱 w4x5y6z7a8b9。。实际 upgrade：执行数据/DDL SQL
        DELETE FROM learning_records
        WHERE ctid IN (
            SELECT ctid FROM (
                SELECT ctid,
                  ；get_bind；加唯一约束 uq_learning_record_user_video / learning_records。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

### [backend/migrations/versions/z9y8x7w6v5u4_drop_user_streak_columns.py](../../../backend/migrations/versions/z9y8x7w6v5u4_drop_user_streak_columns.py)

数据库历史迁移 z9y8x7w6v5u4，前驱 r3e4d5e6e7m8。。实际 upgrade：删列 users / streak_count；删列 users / longest_streak。不得因旧功能已下线而单删。

- 代码入口/类型：`upgrade`、`downgrade`。
- 隐式入口：Alembic revision/down_revision 迁移图。
- 处置：保留。

## `backend`

### [backend/pyproject.toml](../../../backend/pyproject.toml)

该 Python 组件的构建元数据或 lint/类型规则；具体节决定用途，不是顶层统一包。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/pytest.ini](../../../backend/pytest.ini)

pytest 收集范围、async/超时/marker 配置；测试运行器隐式读取。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/requirements-cloud.txt](../../../backend/requirements-cloud.txt)

该组件的依赖安装/约束/审计输入：requirements-cloud.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/requirements-dev.txt](../../../backend/requirements-dev.txt)

该组件的依赖安装/约束/审计输入：requirements-dev.txt；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/run_with_utf8.py](../../../backend/run_with_utf8.py)

Windows UTF-8 命令启动包装，避免本机默认编码影响应用。

- 直接依赖：[backend/app/main.py](../../../backend/app/main.py)。
- 处置：保留。

## `backend/scripts`

### [backend/scripts/__init__.py](../../../backend/scripts/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 直接使用者：[backend/app/services/youtube_cookies_service.py](../../../backend/app/services/youtube_cookies_service.py)、[backend/scripts/qualify_teaching_content.py](../../../backend/scripts/qualify_teaching_content.py)、[backend/tests/test_backfill_scripts.py](../../../backend/tests/test_backfill_scripts.py)、[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)、[backend/tests/test_lesson_receipt_signer.py](../../../backend/tests/test_lesson_receipt_signer.py)。
- 处置：保留。

### [backend/scripts/backfill_auto_channels.py](../../../backend/scripts/backfill_auto_channels.py)

按已收录视频的外站频道补作者页和关联；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)。
- 处置：保留。

### [backend/scripts/backfill_classification.py](../../../backend/scripts/backfill_classification.py)

补视频主题/CEFR，可能调用模型并写库；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`clean_dirty_difficulty`、`classify_one`、`fill_missing_difficulty`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/difficulty_service.py](../../../backend/app/services/difficulty_service.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/app/services/video_classification.py](../../../backend/app/services/video_classification.py)。
- 直接使用者：[backend/tests/test_backfill_scripts.py](../../../backend/tests/test_backfill_scripts.py)。
- 处置：保留。

### [backend/scripts/backfill_difficulty.py](../../../backend/scripts/backfill_difficulty.py)

按词难度补视频难度字段；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`compute_one`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/difficulty_service.py](../../../backend/app/services/difficulty_service.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)。
- 直接使用者：[backend/tests/test_backfill_scripts.py](../../../backend/tests/test_backfill_scripts.py)。
- 处置：保留。

### [backend/scripts/backfill_external_meta.py](../../../backend/scripts/backfill_external_meta.py)

补外站元信息，不混同本站计数；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`pass_external`、`pass_thumbnails`、`pass_speech`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/external_meta.py](../../../backend/app/services/external_meta.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/scripts/backfill_local_thumbnails.py](../../../backend/scripts/backfill_local_thumbnails.py)

下载/抽帧补本地封面；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`run`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/thumbnail_service.py](../../../backend/app/services/thumbnail_service.py)。
- 处置：保留。

### [backend/scripts/backfill_video_duration.py](../../../backend/scripts/backfill_video_duration.py)

用 ffprobe 补视频时长；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/media_probe.py](../../../backend/app/core/media_probe.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 处置：保留。

### [backend/scripts/backfill_video_titles_zh.py](../../../backend/scripts/backfill_video_titles_zh.py)

补显示用中文标题，可能调用翻译；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`backfill_one`、`backfill_all`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/app/services/video_title.py](../../../backend/app/services/video_title.py)。
- 直接使用者：[backend/tests/test_backfill_scripts.py](../../../backend/tests/test_backfill_scripts.py)。
- 处置：保留。

### [backend/scripts/backfill_vocabulary_ecdict.py](../../../backend/scripts/backfill_vocabulary_ecdict.py)

用本地词典补个人词条字段；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`backfill`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)。
- 处置：保留。

### [backend/scripts/backfill_vocabulary_subtitle.py](../../../backend/scripts/backfill_vocabulary_subtitle.py)

补词汇来源字幕引用；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`backfill`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)。
- 处置：保留。

### [backend/scripts/backfill_word_annotations.py](../../../backend/scripts/backfill_word_annotations.py)

补字幕考试词标注；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`annotate_video`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)。
- 处置：保留。

### [backend/scripts/backfill_word_levels.py](../../../backend/scripts/backfill_word_levels.py)

补逐词难度数组；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`summarize`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)。
- 直接使用者：[backend/tests/test_backfill_scripts.py](../../../backend/tests/test_backfill_scripts.py)。
- 处置：保留。

### [backend/scripts/batch_process_seeded.py](../../../backend/scripts/batch_process_seeded.py)

人工处理预置视频的翻译/注释/预热，绕过 Celery 的维护入口；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`translate_video`、`annotate_video`、`prewarm_video`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/scripts/build_exam_pdf_index.py](../../../backend/scripts/build_exam_pdf_index.py)

扫描参考 PDF 生成受控下载清单；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`sha256_of`、`split_slot`、`build_records`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/build_slcs_release.py](../../../backend/scripts/build_slcs_release.py)

按显式许可白名单组装公开发行树、wheel 与 SHA256SUMS；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`build`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/check_llm_provider.py](../../../backend/scripts/check_llm_provider.py)

列模型配置或显式调用模型 smoke；--test 不是纯本地检查；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)、[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/scripts/check_schema_drift.py](../../../backend/scripts/check_schema_drift.py)

比较 Alembic 后数据库与 ORM 的结构漂移；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/__init__.py](../../../backend/app/__init__.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)。
- 处置：保留。

### [backend/scripts/check_v2_gateway.py](../../../backend/scripts/check_v2_gateway.py)

针对独立合成网关的预算/取消/生命周期探针；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`Probe`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/check_video_media.py](../../../backend/scripts/check_video_media.py)

只用合成输入和临时目录验证 ffmpeg 媒体输出；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)。
- 处置：保留。

### [backend/scripts/content_verification_job.py](../../../backend/scripts/content_verification_job.py)

内容核验采集的本地检查点、OS 锁和不确定调用恢复；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`read_json`、`prepare`、`summary`、`execute`、`recover`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)、[backend/app/services/teaching/qualification.py](../../../backend/app/services/teaching/qualification.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)。
- 直接使用者：[backend/scripts/qualify_teaching_content.py](../../../backend/scripts/qualify_teaching_content.py)、[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)。
- 处置：保留。

### [backend/scripts/convert_guojiya_papers.py](../../../backend/scripts/convert_guojiya_papers.py)

将 guojiya 来源试题转换为站内导入格式；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`iter_papers`、`flat_questions`、`passages`、`clean_passage`、`partb_blocks`、`embedded_table_start`、`normalize_matching`、`word_bank`、`clean_partb_stem`、`q`（其余见机器清单）。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/convert_hellocet_papers.py](../../../backend/scripts/convert_hellocet_papers.py)

将 hellocet 来源试题转换为站内导入格式；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`convert_paper`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/create_admin.py](../../../backend/scripts/create_admin.py)

显式创建或配置管理员账号，会写库；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)。
- 处置：保留。

## `backend/scripts/data`

### [backend/scripts/data/languagereactor_yt_en.json](../../../backend/scripts/data/languagereactor_yt_en.json)

Language Reactor 来源的英语视频候选快照，import_catalog.py 默认输入；不是可播放媒体或线上 Video 表。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/scripts/data/lr_learning_pool.json](../../../backend/scripts/data/lr_learning_pool.json)

整理后的候选学习视频池 JSON；作为人工选材/显式导入参考，不是独立数据库或运行配置；来源权利另核对。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `backend/scripts`

### [backend/scripts/download_ecdict.py](../../../backend/scripts/download_ecdict.py)

下载参考词典到忽略的 data 目录；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/download_youtube_audio.py](../../../backend/scripts/download_youtube_audio.py)

从真实站点会话/媒体下载音频的人工工具；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`download_youtube_audio`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/fetch_xdf_papers.py](../../../backend/scripts/fetch_xdf_papers.py)

获取新东方原卷来源信息/文件的导入工具；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`parse_page`、`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/generate_exam_levels.py](../../../backend/scripts/generate_exam_levels.py)

从后端考试等级权威生成前端 TS 镜像；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`render`、`main`。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)。
- 处置：保留。

### [backend/scripts/get_youtube_cookies.py](../../../backend/scripts/get_youtube_cookies.py)

从受控浏览器登录态导出下载器 cookie，产物敏感；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`run_playwright_cmd`、`is_browser_open`、`is_youtube_logged_in`、`open_youtube_persistent`、`save_session_state`、`convert_to_netscape`、`get_cookies_from_session`、`get_cookies_with_browser`、`get_cookies_from_state_file`、`main`。
- 直接使用者：[backend/app/services/youtube_cookies_service.py](../../../backend/app/services/youtube_cookies_service.py)、[backend/scripts/refresh_youtube_cookies.py](../../../backend/scripts/refresh_youtube_cookies.py)。
- 处置：保留。

### [backend/scripts/grant_teaching_access.py](../../../backend/scripts/grant_teaching_access.py)

授予/撤销教学试点授权，会写库；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)。
- 处置：保留。

### [backend/scripts/import_catalog.py](../../../backend/scripts/import_catalog.py)

把候选视频数据导入 catalog；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`to_canonical`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/catalog_service.py](../../../backend/app/services/catalog_service.py)。
- 处置：保留。

### [backend/scripts/import_exam_papers.py](../../../backend/scripts/import_exam_papers.py)

导入结构化试卷与题目；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/exam_corpus.py](../../../backend/app/services/exam_corpus.py)。
- 处置：保留。

### [backend/scripts/ingest_exam_papers.py](../../../backend/scripts/ingest_exam_papers.py)

把真题语料写为词句/频次索引；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/exam_corpus.py](../../../backend/app/models/exam_corpus.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/exam_corpus.py](../../../backend/app/services/exam_corpus.py)。
- 处置：保留。

### [backend/scripts/inventory_orphan_media.py](../../../backend/scripts/inventory_orphan_media.py)

只读对照 DB 引用、清理队列与磁盘媒体，不删除；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`collect`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/models/data_export.py](../../../backend/app/models/data_export.py)、[backend/app/models/media_cleanup.py](../../../backend/app/models/media_cleanup.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/scripts/measure_baseline.py](../../../backend/scripts/measure_baseline.py)

导出可复现的学习/性能样本基线；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/services/measurement_service.py](../../../backend/app/services/measurement_service.py)。
- 处置：保留。

### [backend/scripts/pip_audit_gate.py](../../../backend/scripts/pip_audit_gate.py)

带期限豁免和已修陈旧项提示的依赖漏洞硬门；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`Suppression`、`Finding`、`parse_suppressions`、`lapsed_suppressions`、`run_pip_audit`、`parse_report`、`report_new_advisories`、`report_lapsed`、`report_stale`、`main`。
- 直接使用者：[backend/tests/test_pip_audit_gate.py](../../../backend/tests/test_pip_audit_gate.py)。
- 处置：保留。

### [backend/scripts/precompute_global_word_notes.py](../../../backend/scripts/precompute_global_word_notes.py)

批量预生成全局词注，调用模型并写库；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/word_note.py](../../../backend/app/models/word_note.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/word_notes.py](../../../backend/app/services/word_notes.py)。
- 处置：保留。

### [backend/scripts/precompute_global_word_notes_dual.py](../../../backend/scripts/precompute_global_word_notes_dual.py)

跨两个引擎分摊全局词注预热；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/word_note.py](../../../backend/app/models/word_note.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/word_notes.py](../../../backend/app/services/word_notes.py)。
- 处置：保留。

### [backend/scripts/prep_sms.sh](../../../backend/scripts/prep_sms.sh)

历史短信配置键迁移/权限准备工具；会改指定主机配置，不自动执行；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/production_preflight.py](../../../backend/scripts/production_preflight.py)

只读生产配置/Compose 透传检查，不连业务库；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/proxy_tunnel.ps1](../../../backend/scripts/proxy_tunnel.ps1)

开发代理的常驻 SSH 隧道；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/purge_dev_test_users.py](../../../backend/scripts/purge_dev_test_users.py)

清理测试账号的破坏性人工维护工具，先确认范围；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)。
- 处置：保留。

### [backend/scripts/purge_exam_papers.py](../../../backend/scripts/purge_exam_papers.py)

删除指定试卷及关联数据的破坏性工具；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`dump`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)。
- 处置：保留。

### [backend/scripts/qualify_teaching_content.py](../../../backend/scripts/qualify_teaching_content.py)

计划/采集真实材料核验收据并组装 manifest，不直接发布；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`inventory`、`manifests`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)、[backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)、[backend/scripts/__init__.py](../../../backend/scripts/__init__.py)；其余 1 项见机器清单。
- 直接使用者：[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)、[backend/tests/test_teaching_content_cli.py](../../../backend/tests/test_teaching_content_cli.py)。
- 处置：保留。

### [backend/scripts/rebackfill_video_quality.py](../../../backend/scripts/rebackfill_video_quality.py)

重算视频质量相关字段；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`log`、`ssh_client`、`prod_run`、`prod_sftp_put`、`prod_db`、`prod_free_disk_bytes`、`ffprobe_field`、`ffprobe_duration`、`process_one`、`main_async`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/services/thumbnail_service.py](../../../backend/app/services/thumbnail_service.py)、[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)。
- 处置：保留。

### [backend/scripts/recover_video.py](../../../backend/scripts/recover_video.py)

针对指定视频恢复/重试管线；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`recover`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)。
- 处置：保留。

### [backend/scripts/refresh_youtube_cookies.py](../../../backend/scripts/refresh_youtube_cookies.py)

在需要时刷新下载器 cookie；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`refresh_cookies`、`main`。
- 直接依赖：[backend/scripts/get_youtube_cookies.py](../../../backend/scripts/get_youtube_cookies.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/scripts/reprocess_official_videos.py](../../../backend/scripts/reprocess_official_videos.py)

重置选定视频并入队云端→GPU→尾段，不本机直接转录；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`reprocess_video`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/word_note.py](../../../backend/app/models/word_note.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)。
- 处置：保留。

### [backend/scripts/retranscribe_video.py](../../../backend/scripts/retranscribe_video.py)

指定视频的重置和重入处理队列；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`retranscribe_video`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)。
- 处置：保留。

### [backend/scripts/run_batch_driver.ps1](../../../backend/scripts/run_batch_driver.ps1)

批处理维护任务的 PowerShell 驱动；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/run_celery_worker.ps1](../../../backend/scripts/run_celery_worker.ps1)

加载后端环境启动 NSSM 云端 worker，不启动 beat；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/seed_e2e.py](../../../backend/scripts/seed_e2e.py)

向专用 e2e 库播种可播放测试视频/账号；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`seed_exam_paper`、`seed_video`、`seed_channel`、`seed_listening_video`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 处置：保留。

### [backend/scripts/seed_local_video.py](../../../backend/scripts/seed_local_video.py)

把本地素材作为管理视频入库并派发；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`seed_local_video`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)。
- 处置：保留。

### [backend/scripts/seed_official_videos.py](../../../backend/scripts/seed_official_videos.py)

人工播种官方视频来源并处理；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`seed_video`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/external_meta.py](../../../backend/app/services/external_meta.py)。
- 处置：更新必要说明/引用或生成路径。

### [backend/scripts/seed_teaching_quiz.py](../../../backend/scripts/seed_teaching_quiz.py)

仅本机合成教学题/授权播种，复用测试夹具；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)；其余 2 项见机器清单。
- 处置：保留。

### [backend/scripts/setup_pot_proxy.ps1](../../../backend/scripts/setup_pot_proxy.ps1)

下载器证明来源 token 辅助代理安装/配置；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/scripts/sign_lesson_receipt.py](../../../backend/scripts/sign_lesson_receipt.py)

独立签发方的 Ed25519 keygen/claims/sign，私钥不得在仓库；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`SignerError`、`load_private_key`、`public_pem`、`build_claims`、`sign_receipt`、`read_revision`、`main`。
- 直接使用者：[backend/tests/test_lesson_receipt_signer.py](../../../backend/tests/test_lesson_receipt_signer.py)。
- 处置：保留。

### [backend/scripts/smoke_free_access.py](../../../backend/scripts/smoke_free_access.py)

临时 SQLite/媒体验证登录免费可看和匿名拒绝；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`check`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/scripts/smoke_lesson_publication.py](../../../backend/scripts/smoke_lesson_publication.py)

真实专用库的导入/审核/签名/发布/撤回/恢复演练；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`check`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)。
- 处置：保留。

### [backend/scripts/smoke_takedown.py](../../../backend/scripts/smoke_takedown.py)

临时素材与库验证下架和历史可用性；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`check`、`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)；其余 3 项见机器清单。
- 处置：保留。

### [backend/scripts/smoke_vocab_loop.py](../../../backend/scripts/smoke_vocab_loop.py)

内存 DB 的词集收词→过筛→恢复闭环；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`check`、`main`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 1 项见机器清单。
- 处置：保留。

### [backend/scripts/test_watch_mobile.py](../../../backend/scripts/test_watch_mobile.py)

专用临时 API/DB 的手机观看回归驱动；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`seed`、`main`。
- 直接依赖：[backend/app/__init__.py](../../../backend/app/__init__.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)；其余 3 项见机器清单。
- 隐式入口：显式命令行演练/回归驱动，不由后端默认 tests/ 自动收集。
- 处置：更新必要说明/引用或生成路径。

### [backend/scripts/test_watch_postgres.py](../../../backend/scripts/test_watch_postgres.py)

建独立临时 PG 库验证观看写入竞争并清理；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`provision`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 直接使用者：[backend/scripts/test_watch_mobile.py](../../../backend/scripts/test_watch_mobile.py)。
- 隐式入口：显式命令行演练/回归驱动，不由后端默认 tests/ 自动收集。
- 处置：保留。

## `backend/slcs`

### [backend/slcs/LICENSE](../../../backend/slcs/LICENSE)

法律许可、署名与适用范围，供发行/合规消费者；不是冗余使用说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/slcs/MANIFEST.in](../../../backend/slcs/MANIFEST.in)

Python 源码发行包要随附的许可/说明/类型标记清单，由 setuptools 消费。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/slcs/NOTICE](../../../backend/slcs/NOTICE)

法律许可、署名与适用范围，供发行/合规消费者；不是冗余使用说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/slcs/README.md](../../../backend/slcs/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/slcs/__init__.py](../../../backend/slcs/__init__.py)

独立读取器的公共导出面；应用/CLI 共用，不依赖 app 包。

- 直接依赖：[backend/slcs/contract.py](../../../backend/slcs/contract.py)、[backend/slcs/material.py](../../../backend/slcs/material.py)。
- 直接使用者：[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)、[backend/app/slcs/__init__.py](../../../backend/app/slcs/__init__.py)、[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)、[docs/slcs/examples/read_example.py](../../../docs/slcs/examples/read_example.py)。
- 处置：保留。

### [backend/slcs/__main__.py](../../../backend/slcs/__main__.py)

独立 SLCS 库：公共包/命令入口；可安装 wheel 后离线使用。

- 直接依赖：[backend/slcs/cli.py](../../../backend/slcs/cli.py)。
- 处置：保留。

### [backend/slcs/cli.py](../../../backend/slcs/cli.py)

独立 SLCS 库：独立学习包校验、schema、指纹和词汇解析命令；可安装 wheel 后离线使用。

- 代码入口/类型：`CommandError`、`Parser`、`main`。
- 直接依赖：[backend/slcs/contract.py](../../../backend/slcs/contract.py)、[backend/slcs/lookup.py](../../../backend/slcs/lookup.py)、[backend/slcs/material.py](../../../backend/slcs/material.py)、[backend/slcs/stdio.py](../../../backend/slcs/stdio.py)。
- 直接使用者：[backend/app/slcs/__main__.py](../../../backend/app/slcs/__main__.py)、[backend/slcs/__main__.py](../../../backend/slcs/__main__.py)。
- 处置：保留。

### [backend/slcs/contract.py](../../../backend/slcs/contract.py)

独立 SLCS 库：SLCS 严格包模型、时间/词锚点/授权声明与指纹规则；可安装 wheel 后离线使用。

- 代码入口/类型：`tokenize`、`Media`、`TimeRange`、`Token`、`Segment`、`VocabularyEntry`、`Rights`、`Provenance`、`LearningPack`、`PackValidationError`（其余见机器清单）。
- 直接使用者：[backend/slcs/__init__.py](../../../backend/slcs/__init__.py)、[backend/slcs/cli.py](../../../backend/slcs/cli.py)、[backend/slcs/material.py](../../../backend/slcs/material.py)、[backend/slcs/stdio.py](../../../backend/slcs/stdio.py)。
- 处置：保留。

### [backend/slcs/lookup.py](../../../backend/slcs/lookup.py)

独立 SLCS 库：SLCS 词条检索、词时间与整段回退定位；可安装 wheel 后离线使用。

- 代码入口/类型：`lookup`。
- 直接依赖：[backend/slcs/material.py](../../../backend/slcs/material.py)。
- 直接使用者：[backend/slcs/cli.py](../../../backend/slcs/cli.py)、[backend/slcs/stdio.py](../../../backend/slcs/stdio.py)。
- 处置：保留。

### [backend/slcs/material.py](../../../backend/slcs/material.py)

独立 SLCS 库：把合法学习包转换为只读语境、片段与词条投影；可安装 wheel 后离线使用。

- 代码入口/类型：`VocabularyOccurrence`、`VideoLearningMaterial`、`stable_hash`、`fingerprint`、`resolve_vocabulary`、`resolve_anchor`、`load_video_material`。
- 直接依赖：[backend/slcs/contract.py](../../../backend/slcs/contract.py)。
- 直接使用者：[backend/app/services/lesson_learning.py](../../../backend/app/services/lesson_learning.py)、[backend/app/services/lessons.py](../../../backend/app/services/lessons.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)、[backend/app/services/video_learning_material.py](../../../backend/app/services/video_learning_material.py)、[backend/slcs/__init__.py](../../../backend/slcs/__init__.py)、[backend/slcs/cli.py](../../../backend/slcs/cli.py)；其余 2 项见机器清单。
- 处置：保留。

### [backend/slcs/py.typed](../../../backend/slcs/py.typed)

PEP 561 类型信息标记，通知类型检查器该安装包提供类型；无函数不等于无用。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/slcs/pyproject.toml](../../../backend/slcs/pyproject.toml)

该 Python 组件的构建元数据或 lint/类型规则；具体节决定用途，不是顶层统一包。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/slcs/requirements-mcp.lock](../../../backend/slcs/requirements-mcp.lock)

该组件的依赖安装/约束/审计输入：requirements-mcp.lock；具体消费者见构建、CI 与局部运行说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [backend/slcs/stdio.py](../../../backend/slcs/stdio.py)

独立 SLCS 库：只读取启动时指定学习包/段的离线 MCP 服务；可安装 wheel 后离线使用。

- 代码入口/类型：`serve`。
- 直接依赖：[backend/slcs/contract.py](../../../backend/slcs/contract.py)、[backend/slcs/lookup.py](../../../backend/slcs/lookup.py)、[backend/slcs/material.py](../../../backend/slcs/material.py)。
- 直接使用者：[backend/slcs/cli.py](../../../backend/slcs/cli.py)。
- 处置：保留。

## `backend/slcs_tests`

### [backend/slcs_tests/conftest.py](../../../backend/slcs_tests/conftest.py)

让安装制品测试能导入同目录测试辅助，不让源码包抢占已安装 wheel。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 __init__。行为锚点：schema_and_reference_fingerprint；documented_reference_digest_matches；schema_and_fingerprint_commands；console_script_and_offline_example。

- 代码入口/类型：`cli`、`test_schema_and_reference_fingerprint`、`test_documented_reference_digest_matches`、`test_schema_and_fingerprint_commands`、`test_console_script_and_offline_example`、`test_public_invalid_fixtures`、`test_read_and_resolve_outside_repository`、`test_distribution_is_the_installed_one`、`test_distribution_has_no_seeword_imports`。
- 直接依赖：[backend/slcs/__init__.py](../../../backend/slcs/__init__.py)。
- 直接使用者：[backend/slcs_tests/test_stdio.py](../../../backend/slcs_tests/test_stdio.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/slcs_tests/test_stdio.py](../../../backend/slcs_tests/test_stdio.py)

自动回归：只读取启动时指定学习包/段的离线 MCP 服务。行为锚点：stdio_reads_only_approved_segments。

- 代码入口/类型：`test_stdio_reads_only_approved_segments`。
- 直接依赖：[backend/slcs_tests/test_consistency.py](../../../backend/slcs_tests/test_consistency.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

## `backend/tests`

### [backend/tests/__init__.py](../../../backend/tests/__init__.py)

Python 包边界标记；供同目录模块导入和测试收集，空文件不等于无用。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [backend/tests/conftest.py](../../../backend/tests/conftest.py)

内存 SQLite/fake Redis/账号等测试夹具；PG integration 只接受明确测试连接。

- 代码入口/类型：`requires_ecdict`、`pytest_sessionfinish`、`fake_redis`、`override_get_db`、`client`、`db_session`、`test_password`、`test_user_data`、`auth_headers`、`admin_headers`。
- 直接依赖：[backend/app/__init__.py](../../../backend/app/__init__.py)、[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)；其余 6 项见机器清单。
- 直接使用者：[backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)、[backend/tests/test_account_deletion.py](../../../backend/tests/test_account_deletion.py)、[backend/tests/test_admin_quality_inspection.py](../../../backend/tests/test_admin_quality_inspection.py)、[backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)、[backend/tests/test_auth_flows.py](../../../backend/tests/test_auth_flows.py)、[backend/tests/test_auth_sms.py](../../../backend/tests/test_auth_sms.py)；其余 65 项见机器清单。
- 处置：保留。

## `backend/tests/fixtures`

### [backend/tests/fixtures/example_exam_sentences.json](../../../backend/tests/fixtures/example_exam_sentences.json)

小规模真题词句导入格式样例，供 ingest_exam_papers 的显式本地演示/验证；不作为真实语料资格证明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `backend/tests`

### [backend/tests/teaching_fixtures.py](../../../backend/tests/teaching_fixtures.py)

构造合成教学材料和签名回执的共用测试夹具，非可发布真实内容。

- 代码入口/类型：`original_candidate`、`seed_original_content`、`seed_quiz_content`。
- 直接依赖：[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)。
- 直接使用者：[backend/scripts/seed_teaching_quiz.py](../../../backend/scripts/seed_teaching_quiz.py)、[backend/tests/test_content_publication.py](../../../backend/tests/test_content_publication.py)、[backend/tests/test_content_publication_pg.py](../../../backend/tests/test_content_publication_pg.py)、[backend/tests/test_content_receipt_publication.py](../../../backend/tests/test_content_receipt_publication.py)、[backend/tests/test_content_receipts.py](../../../backend/tests/test_content_receipts.py)、[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)；其余 13 项见机器清单。
- 处置：保留。

### [backend/tests/test_account_data.py](../../../backend/tests/test_account_data.py)

自动回归：本人数据导出清单、媒体引用和可重试清理。直接覆盖 config、behavior、channel、data_export、engagement、exam_test、favorite、feedback、learning、learning_plan、listening、media_cleanup、milestone、notification、preferences、study_session、subtitle、user、user_content、video、vocab_set、__init__、account_data、account_tasks。行为锚点：export_contains_every_section_and_no_other_user；export_children_do_not_cross_users；purge_removes_user_data_and_media_but_keeps_shared_records；media_cleanup_retries_until_the_path_is_gone。

- 代码入口/类型：`media_tmp`、`test_export_contains_every_section_and_no_other_user`、`test_export_children_do_not_cross_users`、`test_purge_removes_user_data_and_media_but_keeps_shared_records`、`test_media_cleanup_retries_until_the_path_is_gone`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/data_export.py](../../../backend/app/models/data_export.py)、[backend/app/models/engagement.py](../../../backend/app/models/engagement.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)；其余 19 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_account_deletion.py](../../../backend/tests/test_account_deletion.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 config、security、behavior、data_export、learning、user、account_tasks。行为锚点：request_deletion_requires_confirm；request_deletion_schedules_30_days_and_is_idempotent；cancel_deletion_clears_fields；purge_releases_phone_and_anonymizes_behavior。

- 代码入口/类型：`media_tmp`、`test_request_deletion_requires_confirm`、`test_request_deletion_schedules_30_days_and_is_idempotent`、`test_cancel_deletion_clears_fields`、`test_purge_releases_phone_and_anonymizes_behavior`、`test_purge_keeps_not_yet_due_accounts`、`test_export_builds_zip_with_media_and_serves_once`、`test_export_status_of_other_users_task_returns_404`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/data_export.py](../../../backend/app/models/data_export.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_admin_panel.py](../../../backend/tests/test_admin_panel.py)

自动回归：管理员工作台、用户和系统设置。直接覆盖 errors、admin_setting、user、__init__、admin_service。行为锚点：TestAdminSettings；TestAdminAccounts；TestAdminUsersEnhanced；TestAdminStatsEnhanced。

- 代码入口/类型：`TestAdminSettings`、`TestAdminAccounts`、`TestAdminUsersEnhanced`、`TestAdminStatsEnhanced`、`TestAdminUserFilterValidation`、`TestAdminUserListPagination`、`TestLastAdminProtection`、`TestAdminSettingsConcurrencySafety`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/admin_setting.py](../../../backend/app/models/admin_setting.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/admin_service.py](../../../backend/app/services/admin_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_admin_quality_inspection.py](../../../backend/tests/test_admin_quality_inspection.py)

自动回归：管理员工作台、用户和系统设置。直接覆盖 video、video_quality_report。行为锚点：TestAdminQualityFilter；TestQualityReportsEndpoint。

- 代码入口/类型：`TestAdminQualityFilter`、`TestQualityReportsEndpoint`。
- 直接依赖：[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/video_quality_report.py](../../../backend/app/models/video_quality_report.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_admin_subtitle_pipeline.py](../../../backend/tests/test_admin_subtitle_pipeline.py)

自动回归：管理员工作台、用户和系统设置。直接覆盖 __init__、redis、main、learning、subtitle、subtitle_revision、user、user_content、video、video_score、subtitle_edit_service、video_seed_service。行为锚点：TestRetranslateGuards；TestRecoverRetryLockSafety；TestSeedDedupeAndLock；TestDeleteSubtitleGuard。

- 代码入口/类型：`nx_redis`、`TestRetranslateGuards`、`TestRecoverRetryLockSafety`、`TestSeedDedupeAndLock`、`TestDeleteSubtitleGuard`、`TestCreateSubtitleLock`、`TestSchemaLimits`、`TestRevisionListTotal`、`TestVideoScoreTyped`。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/subtitle_revision.py](../../../backend/app/models/subtitle_revision.py)；其余 8 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_ai_cache.py](../../../backend/tests/test_ai_cache.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 ai_service。行为锚点：enrich_caches_result_and_skips_llm_for_same_context；enrich_does_not_share_cache_across_contexts；enrich_raises_when_llm_fails。

- 代码入口/类型：`test_enrich_caches_result_and_skips_llm_for_same_context`、`test_enrich_does_not_share_cache_across_contexts`、`test_enrich_raises_when_llm_fails`。
- 直接依赖：[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_alert_service.py](../../../backend/tests/test_alert_service.py)

自动回归：站外告警及站内管理员通知降级。直接覆盖 alert_service。行为锚点：send_alert_falls_back_to_in_app_when_no_webhook；send_alert_posts_to_webhook；send_alert_returns_false_on_webhook_failure；dingtalk_sign_deterministic。

- 代码入口/类型：`test_send_alert_falls_back_to_in_app_when_no_webhook`、`test_send_alert_posts_to_webhook`、`test_send_alert_returns_false_on_webhook_failure`、`test_dingtalk_sign_deterministic`、`test_send_alert_redacts_secrets_in_the_payload`。
- 直接依赖：[backend/app/services/alert_service.py](../../../backend/app/services/alert_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_architecture_invariants.py](../../../backend/tests/test_architecture_invariants.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、errors、main、__init__。行为锚点：TestVideoProcessingIsOperatorTriggered；TestErrorsAreTypesNotProse；TestDomainErrorStatusCodes；TestAuthenticationHasOneChain。

- 代码入口/类型：`TestVideoProcessingIsOperatorTriggered`、`TestErrorsAreTypesNotProse`、`TestDomainErrorStatusCodes`、`TestAuthenticationHasOneChain`、`TestCutFeaturesStayCut`、`test_services_and_tasks_do_not_import_http_adapters`、`test_model_chat_endpoint_lives_in_exactly_one_module`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、errors、exam_test、learning_plan、listening、question_exposure、user、__init__、exam_service、listening_service、milestone_service。行为锚点：projection_failure_rolls_back_grading_then_retry_succeeds；commit_failure_or_lost_ack_can_be_retried_without_duplicate_fact；exam_event_failure_restores_claim_grades_and_exposure_for_each_mode；listening_service_refreshes_stale_state_and_never_overwrites_submitted_draft。

- 代码入口/类型：`assessment`、`post_submission`、`assert_unsubmitted`、`assert_one_fact`、`test_projection_failure_rolls_back_grading_then_retry_succeeds`、`test_commit_failure_or_lost_ack_can_be_retried_without_duplicate_fact`、`test_exam_event_failure_restores_claim_grades_and_exposure_for_each_mode`、`test_listening_service_refreshes_stale_state_and_never_overwrites_submitted_draft`、`test_listening_service_itself_enforces_ownership`、`test_listening_service_rejects_invalid_count_before_creating_session`（其余见机器清单）。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/listening.py](../../../backend/app/models/listening.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)；其余 8 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_auth.py](../../../backend/tests/test_auth.py)

自动回归：短信/密码登录、注册、续签、改密、手机号和退出。直接覆盖 __init__、security。行为锚点：TestUserProfile。

- 代码入口/类型：`TestUserProfile`。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_auth_flows.py](../../../backend/tests/test_auth_flows.py)

自动回归：短信/密码登录、注册、续签、改密、手机号和退出。直接覆盖 config、user、sms_service。行为锚点：TestRefreshToken；TestLogout；TestChangePassword；TestSessionInvalidation。

- 代码入口/类型：`TestRefreshToken`、`TestLogout`、`TestChangePassword`、`TestSessionInvalidation`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/sms_service.py](../../../backend/app/services/sms_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_auth_sms.py](../../../backend/tests/test_auth_sms.py)

自动回归：短信/密码登录、注册、续签、改密、手机号和退出。直接覆盖 config、user、sms_service。行为锚点：TestSmsRegister；TestPhoneLogin；TestSmsLoginAutoCreate；TestSmsResetPassword。

- 代码入口/类型：`TestSmsRegister`、`TestPhoneLogin`、`TestSmsLoginAutoCreate`、`TestSmsResetPassword`、`TestChangePhone`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/sms_service.py](../../../backend/app/services/sms_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_backfill_scripts.py](../../../backend/tests/test_backfill_scripts.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、video、video_cache。行为锚点：TestClassificationCacheInvalidation；TestDifficultyCacheInvalidation；TestVideoTitleBackfill；TestDirtyDifficultyScope。

- 代码入口/类型：`TestClassificationCacheInvalidation`、`TestDifficultyCacheInvalidation`、`TestVideoTitleBackfill`、`TestDirtyDifficultyScope`、`TestWordLevelsBackfill`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/scripts/__init__.py](../../../backend/scripts/__init__.py)、[backend/scripts/backfill_classification.py](../../../backend/scripts/backfill_classification.py)、[backend/scripts/backfill_difficulty.py](../../../backend/scripts/backfill_difficulty.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_behavior_api.py](../../../backend/tests/test_behavior_api.py)

自动回归：原始浏览学习行为事件。直接覆盖 database、behavior、learning、learning_plan、user、video。行为锚点：anonymous_single_event；authenticated_event_has_user_id；batch_ingest；watch_time_mirrors_learning_record。

- 代码入口/类型：`fk_enforced`、`test_anonymous_single_event`、`test_authenticated_event_has_user_id`、`test_batch_ingest`、`test_watch_time_mirrors_learning_record`、`test_complete_mirrors_view_count_and_learning_event`、`test_duplicate_complete_is_idempotent`、`test_complete_without_learning_record_does_not_inflate_view_count`、`test_complete_without_learning_record_emits_no_learning_event`、`test_single_event_with_unknown_video_id_is_stored_with_null`（其余见机器清单）。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_browse_feed.py](../../../backend/tests/test_browse_feed.py)

自动回归：主题分类与精选视频流。直接覆盖 favorite、user、video、ranking_service、video_card。行为锚点：TestFavoriteSort；TestWeeklyFavoriteSort；TestWeeklyFavoriteMatchesRankings；TestNewSortPagination。

- 代码入口/类型：`TestFavoriteSort`、`TestWeeklyFavoriteSort`、`TestWeeklyFavoriteMatchesRankings`、`TestNewSortPagination`、`TestSortCacheKeys`、`TestDurationFilter`。
- 直接依赖：[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/ranking_service.py](../../../backend/app/services/ranking_service.py)、[backend/app/services/video_card.py](../../../backend/app/services/video_card.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_cache.py](../../../backend/tests/test_cache.py)

自动回归：Redis 可降级缓存封装。直接覆盖 cache。行为锚点：TestCacheSetJsonFailOpen；TestCachedDecoratorFailOpen；cache_set_json_never_raises_for_odd_values。

- 代码入口/类型：`TestCacheSetJsonFailOpen`、`TestCachedDecoratorFailOpen`、`test_cache_set_json_never_raises_for_odd_values`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_catalog_api.py](../../../backend/tests/test_catalog_api.py)

自动回归：待收录视频候选池。直接覆盖 catalog、video、__init__、catalog_service。行为锚点：compute_fit_score_prefers_learning_suitable；import_records_is_idempotent；import_records_skips_incomplete；list_catalog_requires_admin。

- 代码入口/类型：`test_compute_fit_score_prefers_learning_suitable`、`test_import_records_is_idempotent`、`test_import_records_skips_incomplete`、`test_list_catalog_requires_admin`、`test_list_catalog_sorted_by_fit_and_paginated`、`test_list_catalog_filters`、`test_catalog_summary`、`test_get_catalog_item_and_404`、`test_mark_item_transitions`、`test_mark_item_invalid_status_422`（其余见机器清单）。
- 直接依赖：[backend/app/models/catalog.py](../../../backend/app/models/catalog.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/catalog_service.py](../../../backend/app/services/catalog_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_catalog_pg.py](../../../backend/tests/test_catalog_pg.py)

自动回归：待收录视频候选池。直接覆盖 database、security、main、catalog、user、video。行为锚点：concurrent_promote_seeds_once_and_creates_one_video；concurrent_first_promote_seeds_once_with_committing_seed。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`pg_client`、`test_concurrent_promote_seeds_once_and_creates_one_video`、`test_concurrent_first_promote_seeds_once_with_committing_seed`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/catalog.py](../../../backend/app/models/catalog.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_celery_tasks.py](../../../backend/tests/test_celery_tasks.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、video、scoring_tasks。行为锚点：compute_top_scores_scores_ready_videos。

- 代码入口/类型：`test_compute_top_scores_scores_ready_videos`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/scoring_tasks.py](../../../backend/app/tasks/scoring_tasks.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_celery_tasks_pg.py](../../../backend/tests/test_celery_tasks_pg.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、video、scoring_tasks。行为锚点：compute_top_scores_scores_ready_videos_on_pg。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`test_compute_top_scores_scores_ready_videos_on_pg`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/scoring_tasks.py](../../../backend/app/tasks/scoring_tasks.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_channel_learning.py](../../../backend/tests/test_channel_learning.py)

自动回归：从真实频道视频推导难度、学习方向和起学依据。直接覆盖 __init__、channel_learning。行为锚点：curated_profile_wins_over_noisy_tags_and_only_evidenced_accent；profile_without_evidence_does_not_invent_accent；unknown_channel_derives_directions_from_tags_and_titles；difficulty_range_uses_real_levels_and_ignores_dirty_values。

- 代码入口/类型：`test_curated_profile_wins_over_noisy_tags_and_only_evidenced_accent`、`test_profile_without_evidence_does_not_invent_accent`、`test_unknown_channel_derives_directions_from_tags_and_titles`、`test_difficulty_range_uses_real_levels_and_ignores_dirty_values`、`test_every_profile_uses_known_direction_labels`。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/channel_learning.py](../../../backend/app/services/channel_learning.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_channel_view_totals.py](../../../backend/tests/test_channel_view_totals.py)

自动回归：频道身份和展示信息。直接覆盖 channel、video、channel_service。行为锚点：channel_totals_exclude_unpublished_and_do_not_depend_on_page。

- 代码入口/类型：`test_channel_totals_exclude_unpublished_and_do_not_depend_on_page`。
- 直接依赖：[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_channels_api.py](../../../backend/tests/test_channels_api.py)

自动回归：频道列表、详情与管理员维护。直接覆盖 channel、learning、user_content、video、__init__、channel_service。行为锚点：list_channels_shows_visible_only_with_counts；channel_detail_lists_published_videos；channel_detail_unknown_slug_404；hidden_channel_detail_404。

- 代码入口/类型：`test_list_channels_shows_visible_only_with_counts`、`test_channel_detail_lists_published_videos`、`test_channel_detail_unknown_slug_404`、`test_hidden_channel_detail_404`、`test_admin_create_channel_and_auto_attach_by_upstream_id`、`test_admin_create_channel_slug_conflict_400`、`test_admin_create_channel_invalid_slug_400`、`test_admin_requires_admin_role`、`test_admin_update_and_delete_channel`、`test_admin_attach_videos_overwrites_assignment`（其余见机器清单）。
- 直接依赖：[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user_content.py](../../../backend/app/models/user_content.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/channel_service.py](../../../backend/app/services/channel_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_config_env_guard.py](../../../backend/tests/test_config_env_guard.py)

自动回归：环境配置、合法环境名与生产安全校验。直接覆盖 config。行为锚点：TestEnvValueGuard；TestSecretGuards；TestJwtSecretStrength；TestV2FeatureGuards。

- 代码入口/类型：`TestEnvValueGuard`、`TestSecretGuards`、`TestJwtSecretStrength`、`TestV2FeatureGuards`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_content_publication.py](../../../backend/tests/test_content_publication.py)

自动回归：教学可编辑候选和发布操作回执。直接覆盖 content_publication、teaching、__init__、context、principal、publication、service。行为锚点：admin_boundary_and_unverified_draft_is_not_publication；edit_conflict_replay_and_list_do_not_return_full_manifest；publication_stays_closed_without_server_receipt_verifier；publication_replay_then_withdrawal_preserves_attempt_and_restricts_context。

- 代码入口/类型：`candidate`、`draft`、`test_admin_boundary_and_unverified_draft_is_not_publication`、`test_edit_conflict_replay_and_list_do_not_return_full_manifest`、`test_publication_stays_closed_without_server_receipt_verifier`、`test_publication_replay_then_withdrawal_preserves_attempt_and_restricts_context`、`test_invalid_receipts_cannot_create_a_revision`、`test_malformed_draft_preflight_fails_safely`、`test_forged_actor_and_oversized_manifests_are_rejected`、`test_failed_commit_rolls_back_revision_and_receipt_then_retry_succeeds`（其余见机器清单）。
- 直接依赖：[backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)、[backend/app/services/teaching/publication.py](../../../backend/app/services/teaching/publication.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_content_publication_pg.py](../../../backend/tests/test_content_publication_pg.py)

自动回归：教学可编辑候选和发布操作回执。直接覆盖 database、errors、security、main、content_publication、exam_test、teaching、user、__init__、content、publication。行为锚点：concurrent_publish_is_single_effect；concurrent_drafts_share_serial_revision_numbering；edit_can_commit_during_verification_and_invalidates_prepared_proof；bank_change_while_publication_waits_is_rechecked_after_lock。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`pg_client`、`seed`、`draft`、`test_concurrent_publish_is_single_effect`、`test_concurrent_drafts_share_serial_revision_numbering`、`test_edit_can_commit_during_verification_and_invalidates_prepared_proof`、`test_bank_change_while_publication_waits_is_rechecked_after_lock`、`test_admin_revocation_during_verification_blocks_final_write`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)；其余 7 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_content_receipt_publication.py](../../../backend/tests/test_content_receipt_publication.py)

自动回归：教学材料资格核对与当前用途/权限下的正文投影。直接覆盖 config、security、teaching、user、__init__、content、teaching_gateway。行为锚点：signed_gateway_evidence_reaches_publication_without_a_true_verifier_stub。

- 代码入口/类型：`load_gateway`、`test_signed_gateway_evidence_reaches_publication_without_a_true_verifier_stub`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/content.py](../../../backend/app/services/teaching/content.py)；其余 2 项见机器清单。
- 直接使用者：[backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_content_receipts.py](../../../backend/tests/test_content_receipts.py)

自动回归：教学核验输入/结果的 Ed25519 收据验签。直接覆盖 config、__init__、content_receipts、teaching_gateway。行为锚点：public_key_authenticates_exact_observed_result；changed_claim_cannot_reuse_a_valid_signature；expiry_audience_and_policy_are_not_optional；unknown_key_wrong_signature_and_jose_headers_fail_closed。

- 代码入口/类型：`signing_key`、`signed`、`verify`、`test_public_key_authenticates_exact_observed_result`、`test_changed_claim_cannot_reuse_a_valid_signature`、`test_expiry_audience_and_policy_are_not_optional`、`test_unknown_key_wrong_signature_and_jose_headers_fail_closed`、`test_boolean_position_and_modified_review_result_are_rejected`、`test_missing_or_unbounded_tokens_do_not_pass`、`settings`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/content_receipts.py](../../../backend/app/services/teaching/content_receipts.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)、[backend/tests/teaching_fixtures.py](../../../backend/tests/teaching_fixtures.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_content_verification_job.py](../../../backend/tests/test_content_verification_job.py)

自动回归：教学材料资格核对与当前用途/权限下的正文投影。直接覆盖 __init__、config、database、errors、user、content、qualification、teaching_gateway。行为锚点：plan_has_no_receipts_or_blind_answer_and_uses_same_review_hash；invalid_material_cannot_create_a_job_or_send_content；signed_collection_is_resumable_and_does_not_publish；dispatch_guards_leave_pending_steps_untouched。

- 代码入口/类型：`setup_job`、`gateway`、`test_plan_has_no_receipts_or_blind_answer_and_uses_same_review_hash`、`test_invalid_material_cannot_create_a_job_or_send_content`、`test_signed_collection_is_resumable_and_does_not_publish`、`test_dispatch_guards_leave_pending_steps_untouched`、`test_lost_response_never_retries_and_signed_recovery_continues_remaining_steps`、`test_crashed_dispatch_and_changed_plan_are_not_silently_restarted`、`test_signed_wrong_answer_stops_further_spend_and_is_not_retried`、`test_same_family_aliases_cannot_create_a_qualified_manifest`（其余见机器清单）。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 10 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_daily_recommendation_index.py](../../../backend/tests/test_daily_recommendation_index.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 exam_test、__init__、daily_recommendation_service。行为锚点：second_preview_hits_cache_without_rescan；bank_row_count_change_invalidates_index。

- 代码入口/类型：`captured_sql`、`test_second_preview_hits_cache_without_rescan`、`test_bank_row_count_change_invalidates_index`。
- 直接依赖：[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/daily_recommendation_service.py](../../../backend/app/services/daily_recommendation_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_demo_video.py](../../../backend/tests/test_demo_video.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 video。行为锚点：TestDemoVideoEndpoint；TestDemoVideoExclusivity。

- 代码入口/类型：`TestDemoVideoEndpoint`、`TestDemoVideoExclusivity`。
- 直接依赖：[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_difficulty_service.py](../../../backend/tests/test_difficulty_service.py)

自动回归：从字幕词汇难度分布计算视频 CEFR 难度。直接覆盖 security、subtitle、user、video、difficulty_service。行为锚点：TestBeyondBasicRatio；TestComputeDifficultyFromWordLevels；compute_video_difficulty_writes_level；compute_video_difficulty_does_not_overwrite。

- 代码入口/类型：`TestBeyondBasicRatio`、`TestComputeDifficultyFromWordLevels`、`test_compute_video_difficulty_writes_level`、`test_compute_video_difficulty_does_not_overwrite`、`test_compute_video_difficulty_insufficient_data`、`test_compute_video_difficulty_no_subtitles`。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/difficulty_service.py](../../../backend/app/services/difficulty_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_discovery_api.py](../../../backend/tests/test_discovery_api.py)

自动回归：视频/字幕/频道发现、词典、订阅、收藏与每日练习。直接覆盖 security、channel、exam_test、learning、subtitle、user、user_content、video、__init__、ecdict。行为锚点：interests_roundtrip_validation_and_cache_invalidation；explicit_interests_sort_small_pools_and_empty_preferences_restore_ranking；subscriptions_and_sentence_favorites_are_persistent_idempotent_and_private；grouped_video_search_does_not_offer_an_extra_empty_page。

- 代码入口/类型：`user_id`、`content`、`test_interests_roundtrip_validation_and_cache_invalidation`、`test_explicit_interests_sort_small_pools_and_empty_preferences_restore_ranking`、`test_subscriptions_and_sentence_favorites_are_persistent_idempotent_and_private`、`test_grouped_video_search_does_not_offer_an_extra_empty_page`、`test_batch_learning_metadata_hides_unpublished_video`、`metadata_video`、`test_learning_metadata_sample_words_follow_the_home_card_rules`、`test_learning_metadata_sample_words_degrade_when_ecdict_is_unusable`（其余见机器清单）。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 4 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_download_retry.py](../../../backend/tests/test_download_retry.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、video、video_processing。行为锚点：TestRetryFailedDownloads；TestLocalizeDownloadFailure。

- 代码入口/类型：`TestRetryFailedDownloads`、`TestLocalizeDownloadFailure`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_ecdict.py](../../../backend/tests/test_ecdict.py)

自动回归：只读词典索引、词形还原与考试词标注。直接覆盖 __init__、ecdict。行为锚点：levels_of_maps_known_tags_and_filters_unknown；levels_of_dedupes；parse_exchange_extracts_inflected_forms；parse_exchange_rejects_reverse_pointer_and_type_codes。

- 代码入口/类型：`test_levels_of_maps_known_tags_and_filters_unknown`、`test_levels_of_dedupes`、`test_parse_exchange_extracts_inflected_forms`、`test_parse_exchange_rejects_reverse_pointer_and_type_codes`、`test_reverse_index_not_polluted_by_lemma_pointer_or_type_codes`、`test_lookup_resolves_inflection_via_reverse_index`、`test_lookup_strips_punctuation_and_is_case_insensitive`、`test_lookup_returns_none_for_unknown`、`test_lookup_returns_none_when_db_missing`、`test_annotate_text_keys_by_surface_form`（其余见机器清单）。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_error_envelope.py](../../../backend/tests/test_error_envelope.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 errors、main。行为锚点：TestValidationEnvelopeSurvivesNonFiniteFloats；TestUnhandledExceptionsBecomeAnEnvelope。

- 代码入口/类型：`TestValidationEnvelopeSurvivesNonFiniteFloats`、`TestUnhandledExceptionsBecomeAnEnvelope`。
- 本文件路由片段（还需 router/装配前缀）：`GET /__boom__`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/main.py](../../../backend/app/main.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exam_corpus.py](../../../backend/tests/test_exam_corpus.py)

自动回归：真题例句、词索引和词频语料。直接覆盖 __init__、ecdict、exam_corpus、word_notes。行为锚点：ingest_sentences_indexes_exam_words_and_recomputes_freq；ingest_is_idempotent；find_example_sentence_returns_match；find_example_sentence_returns_none_when_missing。

- 代码入口/类型：`ecdict_lookup`、`test_ingest_sentences_indexes_exam_words_and_recomputes_freq`、`test_ingest_is_idempotent`、`test_find_example_sentence_returns_match`、`test_find_example_sentence_returns_none_when_missing`、`test_example_sentences_for_words`、`test_gloss_endpoint_surfaces_corpus_example_and_freq`、`test_gloss_corpus_fields_null_when_empty`、`test_gloss_enrich_returns_corpus_and_note`、`test_gloss_enrich_empty_when_no_data`。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/exam_corpus.py](../../../backend/app/services/exam_corpus.py)、[backend/app/services/word_notes.py](../../../backend/app/services/word_notes.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exam_levels.py](../../../backend/tests/test_exam_levels.py)

自动回归：考试词难度排序与展示规则权威。直接覆盖 exam_levels。行为锚点：level_order_ranking；max_level_picks_highest_difficulty；display_level_returns_highest_key；display_level_target_priority。

- 代码入口/类型：`test_level_order_ranking`、`test_max_level_picks_highest_difficulty`、`test_display_level_returns_highest_key`、`test_display_level_target_priority`、`test_should_display_uses_target_as_lower_bound`、`test_target_options_exclude_collapsed_tiers`、`test_taxonomy_covers_all_keys`、`test_normalize_levels_accepts_both_historical_shapes`、`test_normalize_levels_drops_unusable_members`、`test_normalize_levels_is_total`（其余见机器清单）。
- 直接依赖：[backend/app/core/exam_levels.py](../../../backend/app/core/exam_levels.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exam_levels_generated.py](../../../backend/tests/test_exam_levels_generated.py)

自动回归：考试词难度排序与展示规则权威。行为锚点：generated_taxonomy_file_exists；generated_taxonomy_is_in_sync_with_python。

- 代码入口/类型：`test_generated_taxonomy_file_exists`、`test_generated_taxonomy_is_in_sync_with_python`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exam_pdfs.py](../../../backend/tests/test_exam_pdfs.py)

自动回归：原卷 PDF 清单与受保护下载。直接覆盖 __init__、exam_pdf_service。行为锚点：anonymous_download_requires_login；anonymous_list_requires_login；download_serves_attachment；download_accepts_query_token。

- 代码入口/类型：`fake_pdfs`、`test_anonymous_download_requires_login`、`test_anonymous_list_requires_login`、`test_download_serves_attachment`、`test_download_accepts_query_token`、`test_unknown_slug_is_404`、`test_traversal_slug_is_404`、`test_catalog_rel_path_cannot_escape_root`、`test_list_filters_by_subject_and_sorts`、`test_missing_catalog_is_empty_not_crash`。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/exam_pdf_service.py](../../../backend/app/services/exam_pdf_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exam_snapshots.py](../../../backend/tests/test_exam_snapshots.py)

自动回归：真题请求响应和作答格式。直接覆盖 errors、security、exam_test、question_exposure、user、__init__、account_data、exam_service、question_exposure_service。行为锚点：all_modes_freeze_before_bank_changes_and_deleted_question；all_modes_reject_duplicate_or_foreign_ids_and_count_omissions；missing_or_incomplete_legacy_snapshot_rejects_without_claiming；complete_legacy_daily_placeholder_is_graded_without_inventing_provenance。

- 代码入口/类型：`exam_context`、`test_all_modes_freeze_before_bank_changes_and_deleted_question`、`test_all_modes_reject_duplicate_or_foreign_ids_and_count_omissions`、`test_missing_or_incomplete_legacy_snapshot_rejects_without_claiming`、`test_complete_legacy_daily_placeholder_is_graded_without_inventing_provenance`、`test_exposure_failure_rolls_back_grade_and_submit_claim`、`test_unsubmitted_export_hides_answers_then_submitted_export_preserves_them`、`test_backfill_is_idempotent_preserves_scores_and_tracks_complete_mapping`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 4 项见机器清单。
- 直接使用者：[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exams_api.py](../../../backend/tests/test_exams_api.py)

自动回归：试卷浏览、错题、每日检查、作答与交卷。直接覆盖 exam_test、learning_plan、user。行为锚点：list_exams_shows_attempt_stats；paper_detail_does_not_leak_answers；create_and_submit_attempt_full_flow；repeat_submit_with_different_answers_keeps_first_result。

- 代码入口/类型：`seeded_paper`、`test_list_exams_shows_attempt_stats`、`test_paper_detail_does_not_leak_answers`、`test_create_and_submit_attempt_full_flow`、`test_repeat_submit_with_different_answers_keeps_first_result`、`test_submit_emits_practiced_items_learning_event`、`test_submit_foreign_session_forbidden`、`test_attempt_history_and_detail`、`test_daily_check_start`、`test_paper_list_level_filter`（其余见机器清单）。
- 直接依赖：[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 直接使用者：[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)、[backend/tests/test_exam_snapshots.py](../../../backend/tests/test_exam_snapshots.py)、[backend/tests/test_presentation_contracts.py](../../../backend/tests/test_presentation_contracts.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exams_pg.py](../../../backend/tests/test_exams_pg.py)

自动回归：试卷浏览、错题、每日检查、作答与交卷。直接覆盖 database、security、main、exam_test、learning_plan、user、__init__、exam_service。行为锚点：two_preloaded_unsubmitted_attempts_grade_once；concurrent_http_submits_return_one_result；racing_submits_with_different_payloads_keep_the_first；postgres_deleting_source_paper_preserves_frozen_grading。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`pg_client`、`test_two_preloaded_unsubmitted_attempts_grade_once`、`test_concurrent_http_submits_return_one_result`、`test_racing_submits_with_different_payloads_keep_the_first`、`test_postgres_deleting_source_paper_preserves_frozen_grading`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_exposure.py](../../../backend/tests/test_exposure.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 main。行为锚点：production_disables_docs_and_moves_metrics；development_keeps_docs_and_metrics。

- 代码入口/类型：`test_production_disables_docs_and_moves_metrics`、`test_development_keeps_docs_and_metrics`。
- 直接依赖：[backend/app/main.py](../../../backend/app/main.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_external_meta_and_speech_metrics.py](../../../backend/tests/test_external_meta_and_speech_metrics.py)

自动回归：将下载器元信息映射成可追溯来源字段。直接覆盖 subtitle、video、external_meta、subtitle_metrics_service。行为锚点：parse_external_meta_full；parse_external_meta_partial；parse_upload_date_invalid；speech_metrics_normal。

- 代码入口/类型：`test_parse_external_meta_full`、`test_parse_external_meta_partial`、`test_parse_upload_date_invalid`、`test_speech_metrics_normal`、`test_speech_metrics_insufficient_lines`、`test_speech_metrics_no_timeline`、`test_speech_metrics_punctuation_ignored`、`test_video_speech_metrics_compute_on_null`、`test_video_speech_metrics_never_overwrites_manual`、`test_video_speech_metrics_insufficient_data`（其余见机器清单）。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/external_meta.py](../../../backend/app/services/external_meta.py)、[backend/app/services/subtitle_metrics_service.py](../../../backend/app/services/subtitle_metrics_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_favorites.py](../../../backend/tests/test_favorites.py)

自动回归：视频收藏、笔记及观看元数据。直接覆盖 video。行为锚点：TestFavorites；TestNotes。

- 代码入口/类型：`TestFavorites`、`TestNotes`。
- 直接依赖：[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_favorites_pg.py](../../../backend/tests/test_favorites_pg.py)

自动回归：视频收藏、笔记及观看元数据。直接覆盖 database、security、main、favorite、user、video。行为锚点：concurrent_note_upserts_both_succeed；concurrent_note_deletes_both_succeed；concurrent_note_put_and_delete_never_fails；concurrent_note_delete_and_put_never_fails。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`pg_client`、`test_concurrent_note_upserts_both_succeed`、`test_concurrent_note_deletes_both_succeed`、`test_concurrent_note_put_and_delete_never_fails`、`test_concurrent_note_delete_and_put_never_fails`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_feedback.py](../../../backend/tests/test_feedback.py)

自动回归：用户反馈与管理员回复/公告。直接覆盖 main、feedback、notification、user、notification_tasks。行为锚点：submit_feedback_and_list_mine；submit_feedback_rejects_short_content；submit_feedback_requires_auth；admin_list_feedback。

- 代码入口/类型：`test_submit_feedback_and_list_mine`、`test_submit_feedback_rejects_short_content`、`test_submit_feedback_requires_auth`、`test_admin_list_feedback`、`test_admin_update_feedback_status_and_reply`、`test_admin_update_feedback_not_found`、`test_feedback_admin_endpoints_require_admin`、`test_admin_list_feedback_returns_typed_envelope_with_total`、`test_admin_feedback_list_is_typed_in_openapi`、`test_admin_feedback_order_has_id_tiebreaker`（其余见机器清单）。
- 直接依赖：[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/feedback.py](../../../backend/app/models/feedback.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/tasks/notification_tasks.py](../../../backend/app/tasks/notification_tasks.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_health_heartbeats.py](../../../backend/tests/test_health_heartbeats.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 heartbeat。行为锚点：healthy_heartbeats_return_200；missing_worker_heartbeat_returns_503；gpu_offline_does_not_fail_the_check；stale_beat_returns_503。

- 代码入口/类型：`test_healthy_heartbeats_return_200`、`test_missing_worker_heartbeat_returns_503`、`test_gpu_offline_does_not_fail_the_check`、`test_stale_beat_returns_503`。
- 直接依赖：[backend/app/core/heartbeat.py](../../../backend/app/core/heartbeat.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_health_monitor.py](../../../backend/tests/test_health_monitor.py)

自动回归：独立于 worker/beat 的 Web 进程健康巡检。直接覆盖 heartbeat、__init__、health_monitor、pipeline_alerting。行为锚点：healthy_system_reports_no_problems；stale_worker_is_reported；missing_heartbeats_are_stale；queue_backlog_is_reported。

- 代码入口/类型：`FakeRedis`、`test_healthy_system_reports_no_problems`、`test_stale_worker_is_reported`、`test_missing_heartbeats_are_stale`、`test_queue_backlog_is_reported`、`test_gpu_backlog_without_heartbeat_is_reported`、`test_pipeline_failure_spike_is_reported_with_video_ids`、`test_old_pipeline_failures_fall_outside_the_window`、`test_redis_failure_is_a_problem_not_a_crash`、`test_database_failure_still_reports_its_own_alert`（其余见机器清单）。
- 直接依赖：[backend/app/core/heartbeat.py](../../../backend/app/core/heartbeat.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/health_monitor.py](../../../backend/app/services/health_monitor.py)、[backend/app/services/pipeline_alerting.py](../../../backend/app/services/pipeline_alerting.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_home_content.py](../../../backend/tests/test_home_content.py)

自动回归：首页内容草稿、不可变版本、布局及生成状态。直接覆盖 errors、main、home_content、subtitle、video、__init__、home_content_service。行为锚点：fingerprint_covers_content_and_ignores_float_tails；collect_issues_reports_cross_video_and_phrase_problems；public_endpoint_needs_no_auth_and_defaults_to_null；non_admin_cannot_read_or_write_admin_home_content。

- 代码入口/类型：`make_video`、`draft_payload`、`save_draft`、`publish`、`get_state`、`public_page`、`admin_endpoint_calls`、`test_fingerprint_covers_content_and_ignores_float_tails`、`test_collect_issues_reports_cross_video_and_phrase_problems`、`test_public_endpoint_needs_no_auth_and_defaults_to_null`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/home_content.py](../../../backend/app/models/home_content.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [backend/tests/test_home_content_concurrency.py](../../../backend/tests/test_home_content_concurrency.py)

自动回归：首页内容草稿、不可变版本、布局及生成状态。直接覆盖 errors、home_content、subtitle、video、__init__、home_content_layout、home_content_service。行为锚点：generation_write_back_loses_to_admin_save_in_the_same_window；generation_write_back_succeeds_without_concurrent_edit；concurrent_draft_save_returns_409_and_keeps_the_winner；publish_with_stale_revision_is_409_and_creates_no_version。

- 代码入口/类型：`make_video`、`draft_payload`、`save_draft`、`publish`、`save_layout`、`layout_state`、`save_draft_in_other_session`、`bump_layout_revision_in_other_session`、`draft_snapshot`、`revision_versions`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/home_content.py](../../../backend/app/models/home_content.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/home_content_layout.py](../../../backend/app/services/home_content_layout.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_home_content_generation.py](../../../backend/tests/test_home_content_generation.py)

自动回归：把字幕规划为有界模型输入并严格校验生成草稿。直接覆盖 home_content、subtitle、video、ai_service、home_content_generation、home_content_service、llm_provider、__init__、celery_app、home_content_tasks。行为锚点：TestPromptContract；TestInputBudget；TestCandidateParsing；TestNormalization。

- 代码入口/类型：`subtitle_row`、`make_subtitles`、`valid_ai_payload`、`FakeAIService`、`TestPromptContract`、`TestInputBudget`、`TestCandidateParsing`、`TestNormalization`、`TestSourceChecks`、`patch_payload_validator`（其余见机器清单）。
- 直接依赖：[backend/app/models/home_content.py](../../../backend/app/models/home_content.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/home_content_generation.py](../../../backend/app/services/home_content_generation.py)、[backend/app/services/home_content_service.py](../../../backend/app/services/home_content_service.py)；其余 5 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [backend/tests/test_internal_callback.py](../../../backend/tests/test_internal_callback.py)

自动回归：独立 GPU 的共享密钥转录回调、质量门与尾段派发。直接覆盖 __init__、internal、config、database、pipeline_dispatch、subtitle、video、pipeline_dispatch_tasks。行为锚点：TestCallbackAuth；TestCallbackRedisLock；TestCallbackIdempotency；TestCallbackSuccess。

- 代码入口/类型：`callback_secret`、`redis_lock`、`redis_down`、`TestCallbackAuth`、`TestCallbackRedisLock`、`TestCallbackIdempotency`、`TestCallbackSuccess`、`TestCallbackConcurrency`、`broker_down`、`TestTailDispatchOutbox`。
- 直接依赖：[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/internal.py](../../../backend/app/api/v1/internal.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)；其余 5 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_learning.py](../../../backend/tests/test_learning.py)

自动回归：个人观看进度、词汇与学习记录。直接覆盖 learning、video。行为锚点：TestListLearningRecords；TestSaveAndGetProgress；TestSaveProgressRejectsImpossiblePositions；TestGetLearningRecord。

- 代码入口/类型：`TestListLearningRecords`、`TestSaveAndGetProgress`、`TestSaveProgressRejectsImpossiblePositions`、`TestGetLearningRecord`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)

自动回归：任务、材料、权限、草稿和恢复动作的共享上下文。直接覆盖 __init__、database、errors、teaching、user、learning_context、context、principal、service、teaching_runs。行为锚点：http_learning_journey_recovers_draft_help_and_frozen_material；readonly_external_context_never_infers_answer_from_prior_success；external_actions_intersect_scopes_and_runtime_flags；context_applies_current_rights_before_sharing_any_material。

- 代码入口/类型：`start`、`test_http_learning_journey_recovers_draft_help_and_frozen_material`、`test_readonly_external_context_never_infers_answer_from_prior_success`、`test_external_actions_intersect_scopes_and_runtime_flags`、`test_context_applies_current_rights_before_sharing_any_material`、`test_context_is_bounded_readonly_and_pins_content_not_current_question`、`test_context_cannot_read_another_user_task`、`test_completed_task_has_no_actions_and_keeps_drafts_isolated`、`test_old_context_does_not_authorize_writes_after_content_withdrawal`、`test_runtime_dispatch_receives_the_shared_model_context`。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/learning_context.py](../../../backend/app/schemas/learning_context.py)；其余 10 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_learning_context_pg.py](../../../backend/tests/test_learning_context_pg.py)

自动回归：任务、材料、权限、草稿和恢复动作的共享上下文。直接覆盖 database、teaching、__init__、context、principal、service。行为锚点：context_version_and_draft_cannot_mix_across_a_concurrent_write；rights_withdrawal_is_serialized_with_projection；two_context_readers_share_locks_without_blocking_each_other。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`seed`、`assert_blocked`、`test_context_version_and_draft_cannot_mix_across_a_concurrent_write`、`test_rights_withdrawal_is_serialized_with_projection`、`test_two_context_readers_share_locks_without_blocking_each_other`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/context.py](../../../backend/app/services/teaching/context.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)；其余 2 项见机器清单。
- 直接使用者：[backend/tests/test_content_publication_pg.py](../../../backend/tests/test_content_publication_pg.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_learning_continue.py](../../../backend/tests/test_learning_continue.py)

自动回归：个人观看进度、词汇与学习记录。直接覆盖 learning、video。行为锚点：TestContinueLearning。

- 代码入口/类型：`TestContinueLearning`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_learning_weekly_stats.py](../../../backend/tests/test_learning_weekly_stats.py)

自动回归：个人观看进度、词汇与学习记录。直接覆盖 behavior、learning、learning_plan、preferences、video、learning_event_service、local_time。行为锚点：TestWeeklyMinutes；TestAtomicDailyCounters。

- 代码入口/类型：`TestWeeklyMinutes`、`TestAtomicDailyCounters`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_lesson_learning.py](../../../backend/tests/test_lesson_learning.py)

自动回归：修订/段/词锚点的多来源收词、复习事实与导出清理。直接覆盖 config、database、errors、learning、learning_plan、lesson、lesson_learning、user、v2_runtime、__init__、dialogue、principal、teaching_gateway、teaching_runs、video_learning_material、vocabulary_service、account_tasks。行为锚点：same_word_two_revisions_and_review_replay_after_withdrawal；tutor_reuses_durable_stream_and_redacts_old_history；display_only_revision_cannot_queue_a_model_run；withdrawal_while_queued_prevents_provider_disclosure。

- 代码入口/类型：`seed`、`published_revision`、`test_same_word_two_revisions_and_review_replay_after_withdrawal`、`tutor_input`、`test_tutor_reuses_durable_stream_and_redacts_old_history`、`test_display_only_revision_cannot_queue_a_model_run`、`test_withdrawal_while_queued_prevents_provider_disclosure`、`test_retried_first_turn_replays_after_withdrawal`、`test_archived_lesson_conversation_cannot_start_a_run`、`test_postgres_concurrent_course_saves_and_review_replay`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)；其余 13 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_lesson_progress.py](../../../backend/tests/test_lesson_progress.py)

自动回归：课程级完成状态和按实际修订保存的恢复位置。直接覆盖 errors、behavior、lesson、user、__init__、lesson_progress、study_time_service、video_learning_material。行为锚点：completion_survives_a_position_save_on_another_revision；completion_while_viewing_an_older_revision_still_counts；external_link_records_explicit_completion_but_no_timer；repeated_event_returns_the_same_state_and_records_once。

- 代码入口/类型：`seed`、`complete`、`watch`、`test_completion_survives_a_position_save_on_another_revision`、`test_completion_while_viewing_an_older_revision_still_counts`、`test_external_link_records_explicit_completion_but_no_timer`、`test_repeated_event_returns_the_same_state_and_records_once`、`test_position_beyond_the_media_duration_is_rejected`、`test_course_and_video_time_are_summed_per_local_day`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/lesson.py](../../../backend/app/schemas/lesson.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_lesson_receipt_signer.py](../../../backend/tests/test_lesson_receipt_signer.py)

自动回归：课程、修订、操作、进度与学习活动。直接覆盖 config、errors、lesson_receipts。行为锚点：a_signed_receipt_is_accepted_by_the_site；claims_match_what_publish_lesson_compares；a_receipt_for_different_claims_is_rejected；a_receipt_from_a_different_key_with_a_known_kid_is_rejected。

- 代码入口/类型：`site_key`、`test_a_signed_receipt_is_accepted_by_the_site`、`test_claims_match_what_publish_lesson_compares`、`test_a_receipt_for_different_claims_is_rejected`、`test_a_receipt_from_a_different_key_with_a_known_kid_is_rejected`、`test_iat_is_backdated_so_clock_skew_does_not_break_publishing`、`test_unknown_kid_is_rejected`、`test_a_receipt_longer_than_the_site_max_age_is_rejected`、`test_a_receipt_from_another_issuer_is_rejected`、`test_missing_review_hash_is_a_signer_error_not_a_bad_token`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/lesson_receipts.py](../../../backend/app/services/lesson_receipts.py)、[backend/scripts/__init__.py](../../../backend/scripts/__init__.py)、[backend/scripts/sign_lesson_receipt.py](../../../backend/scripts/sign_lesson_receipt.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_lessons_http.py](../../../backend/tests/test_lessons_http.py)

自动回归：SLCS 课程导入、审核、签名发布、撤回和按权限读取。直接覆盖 config、lesson、user。行为锚点：pilot_gates_every_lesson_route_when_disabled；admin_routes_require_an_admin；import_and_publish_require_an_admin；import_is_idempotent_over_http。

- 代码入口/类型：`pack_text`、`enable_pilot`、`test_pilot_gates_every_lesson_route_when_disabled`、`test_admin_routes_require_an_admin`、`test_import_and_publish_require_an_admin`、`test_import_is_idempotent_over_http`、`test_import_reports_field_paths_for_an_invalid_pack`、`test_import_refuses_an_oversized_body_before_parsing`、`test_lists_only_published_and_reviewed_revisions`、`test_lesson_route_requires_a_login`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_listening_api.py](../../../backend/tests/test_listening_api.py)

自动回归：字幕句冻结的听力练习会话。直接覆盖 learning_plan、listening、subtitle、user、video、listening_service。行为锚点：listening_auth_required；catalog_excludes_offline_and_empty；draft_resume_grade_and_idempotence；restart_does_not_accumulate_pending_sessions。

- 代码入口/类型：`seed`、`test_listening_auth_required`、`test_catalog_excludes_offline_and_empty`、`test_draft_resume_grade_and_idempotence`、`test_restart_does_not_accumulate_pending_sessions`、`test_sessions_list_uses_the_standard_pagination_envelope`、`test_foreign_session_and_invalid_answers`、`test_empty_and_unpublished_cannot_start`、`test_grading`。
- 直接依赖：[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/listening.py](../../../backend/app/models/listening.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)。
- 直接使用者：[backend/tests/test_assessment_transactions.py](../../../backend/tests/test_assessment_transactions.py)、[backend/tests/test_listening_pg.py](../../../backend/tests/test_listening_pg.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_listening_grading.py](../../../backend/tests/test_listening_grading.py)

自动回归：字幕句冻结的听力练习会话。直接覆盖 listening_service。行为锚点：TestNormalizedWords；TestGrade。

- 代码入口/类型：`TestNormalizedWords`、`TestGrade`。
- 直接依赖：[backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_listening_pg.py](../../../backend/tests/test_listening_pg.py)

自动回归：字幕句冻结的听力练习会话。直接覆盖 database、learning_plan、listening、user、__init__、listening_service。行为锚点：two_stale_submissions_grade_once_and_replay_identical_results；disjoint_concurrent_drafts_merge_without_lost_answers；draft_and_submission_obey_the_same_locked_state_transition；start_waiting_for_submit_does_not_deadlock_or_delete_submitted_history。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`seed`、`race`、`test_two_stale_submissions_grade_once_and_replay_identical_results`、`test_disjoint_concurrent_drafts_merge_without_lost_answers`、`test_draft_and_submission_obey_the_same_locked_state_transition`、`test_start_waiting_for_submit_does_not_deadlock_or_delete_submitted_history`、`test_two_starts_share_one_pending_session`、`test_concurrent_submit_and_start_do_not_deadlock`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/listening.py](../../../backend/app/models/listening.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/listening_service.py](../../../backend/app/services/listening_service.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [backend/tests/test_live_video_metadata.py](../../../backend/tests/test_live_video_metadata.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 cache、video、video_cache。行为锚点：warm_detail_and_feed_follow_favorites_and_likes；detail_payload_has_no_viewer_scoped_fields；detail_invalidation_uses_sync_redis_accessor。

- 代码入口/类型：`test_warm_detail_and_feed_follow_favorites_and_likes`、`test_detail_payload_has_no_viewer_scoped_fields`、`test_detail_invalidation_uses_sync_redis_accessor`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_llm_provider.py](../../../backend/tests/test_llm_provider.py)

自动回归：供应商/模型配置目录、任务路由和兼容客户端参数。直接覆盖 config、errors、__init__、ai_service、llm_provider、engines。行为锚点：free_suffix_markers_are_detected；paid_ids_are_not_free；default_model_is_a_catalogued_free_model；free_catalog_entries_carry_provenance。

- 代码入口/类型：`test_free_suffix_markers_are_detected`、`test_paid_ids_are_not_free`、`test_default_model_is_a_catalogued_free_model`、`test_free_catalog_entries_carry_provenance`、`test_commandcode_key_wins_over_legacy_openai`、`test_empty_commandcode_key_falls_back_to_openai`、`test_no_keys_means_no_provider`、`test_custom_base_url_and_model_override_defaults`、`test_tasks_default_to_the_provider_model`、`test_task_override_wins_without_touching_other_tasks`（其余见机器清单）。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/llm_provider.py](../../../backend/app/services/llm_provider.py)、[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_local_time.py](../../../backend/tests/test_local_time.py)

自动回归：用户时区与本地日边界的唯一归一入口。直接覆盖 local_time、reminder_tasks。行为锚点：resolve_falls_back_to_east_eight；resolve_honours_explicit_timezone；local_date_is_the_users_calendar_day_not_utc；local_now_respects_an_explicit_preference。

- 代码入口/类型：`test_resolve_falls_back_to_east_eight`、`test_resolve_honours_explicit_timezone`、`test_local_date_is_the_users_calendar_day_not_utc`、`test_local_now_respects_an_explicit_preference`、`test_reminders_and_counters_share_one_basis`。
- 直接依赖：[backend/app/services/local_time.py](../../../backend/app/services/local_time.py)、[backend/app/tasks/reminder_tasks.py](../../../backend/app/tasks/reminder_tasks.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_mcp_adapter.py](../../../backend/tests/test_mcp_adapter.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 __init__、server、external_connection_service、service、v2_access。行为锚点：protocol_auth_host_origin_and_read_scope；auxiliary_submit_web_restore_replay_and_revocation。

- 代码入口/类型：`setup`、`headers`、`call`、`result`、`test_protocol_auth_host_origin_and_read_scope`、`test_auxiliary_submit_web_restore_replay_and_revocation`。
- 直接依赖：[backend/app/integrations/mcp/__init__.py](../../../backend/app/integrations/mcp/__init__.py)、[backend/app/integrations/mcp/server.py](../../../backend/app/integrations/mcp/server.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_measurement_service.py](../../../backend/tests/test_measurement_service.py)

自动回归：按固定分母和样本量计算激活、留存、事件质量与性能读模型。直接覆盖 behavior、learning_plan、pipeline_dispatch、user、video、event_contract、measurement_service。行为锚点：percentile_nearest_rank；activation_and_cohort_denominators；flow_reconciliation_and_event_versions；performance_samples_and_pipeline_backlog。

- 代码入口/类型：`test_percentile_nearest_rank`、`test_activation_and_cohort_denominators`、`test_flow_reconciliation_and_event_versions`、`test_performance_samples_and_pipeline_backlog`、`test_admin_metrics_endpoint_requires_admin_and_returns_definitions`、`test_behavior_ingest_accepts_flow_id_and_rejects_newer_schema`、`test_behavior_ingest_accepts_v3_gloss_events`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/event_contract.py](../../../backend/app/services/event_contract.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_media_access.py](../../../backend/tests/test_media_access.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 __init__、media、config、security、user、video。行为锚点：shadowing_without_token_404；shadowing_owner_token_200；shadowing_other_user_token_404；shadowing_garbage_token_404。

- 代码入口/类型：`media_dir`、`test_shadowing_without_token_404`、`test_shadowing_owner_token_200`、`test_shadowing_other_user_token_404`、`test_shadowing_garbage_token_404`、`test_shadowing_refresh_token_rejected`、`test_shadowing_other_user_dir_404_even_with_owner_token`、`test_shadowing_dotdot_prefix_does_not_skip_token_gate`、`test_shadowing_dotdot_cannot_reach_other_user_with_own_token`、`test_public_media_no_token_ok`（其余见机器清单）。
- 直接依赖：[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/media.py](../../../backend/app/api/v1/media.py)、[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_milestone_service.py](../../../backend/tests/test_milestone_service.py)

自动回归：历史掌握趋势读取和快照维护；不再颁发成就。直接覆盖 security、learning、learning_plan、milestone、user、milestone_service。行为锚点：activity_no_longer_awards_milestones_or_removes_history；mastery_snapshot_once_per_day；mastery_snapshot_different_days；mastery_trend_api。

- 代码入口/类型：`test_activity_no_longer_awards_milestones_or_removes_history`、`test_mastery_snapshot_once_per_day`、`test_mastery_snapshot_different_days`、`test_mastery_trend_api`、`test_milestones_api`、`test_profile_includes_milestones`。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/milestone.py](../../../backend/app/models/milestone.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/milestone_service.py](../../../backend/app/services/milestone_service.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_notes_api.py](../../../backend/tests/test_notes_api.py)

自动回归：本人笔记库与当前视频可用性。直接覆盖 favorite、user、video。行为锚点：TestNotesApi。

- 代码入口/类型：`TestNotesApi`。
- 直接依赖：[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_notification_transactions.py](../../../backend/tests/test_notification_transactions.py)

自动回归：本人通知记录。直接覆盖 database、notification、user、__init__、notification_service。行为锚点：rollback_never_pushes_uncommitted_notification；commit_is_visible_before_push_and_duplicate_ids_push_once；failed_commit_sends_nothing；push_failure_does_not_undo_committed_notification。

- 代码入口/类型：`seed_user`、`test_rollback_never_pushes_uncommitted_notification`、`test_commit_is_visible_before_push_and_duplicate_ids_push_once`、`test_failed_commit_sends_nothing`、`test_push_failure_does_not_undo_committed_notification`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_notifications.py](../../../backend/tests/test_notifications.py)

自动回归：通知列表、已读、偏好和鉴权 WebSocket。直接覆盖 __init__、notifications、database、notification、user、notification_service。行为锚点：TestNotificationFanout；TestListNotifications；TestUnreadCount；TestMarkAsRead。

- 代码入口/类型：`TestNotificationFanout`、`TestListNotifications`、`TestUnreadCount`、`TestMarkAsRead`、`TestMarkAllAsRead`、`TestPreferences`、`TestWebSocketPushErrorHandling`、`TestConnectionManagerListMutation`、`TestNotificationDedup`、`TestWebSocketHandshakeAuth`。
- 直接依赖：[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_openapi_contract.py](../../../backend/tests/test_openapi_contract.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 main。行为锚点：all_openapi_operation_ids_are_unique；retired_shadowing_routes_have_distinct_ids。

- 代码入口/类型：`test_all_openapi_operation_ids_are_unique`、`test_retired_shadowing_routes_have_distinct_ids`。
- 直接依赖：[backend/app/main.py](../../../backend/app/main.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_password_contract.py](../../../backend/tests/test_password_contract.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 security、user。行为锚点：TestSchemaContract；TestHashingContract；TestApiContract。

- 代码入口/类型：`TestSchemaContract`、`TestHashingContract`、`TestApiContract`。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/user.py](../../../backend/app/schemas/user.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pending_processing.py](../../../backend/tests/test_pending_processing.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 user、video。行为锚点：TestUserSubmissionNoAutoProcess；TestStartProcessing；TestWorkerStatus；TestAutoPublishSyncsReviewStatus。

- 代码入口/类型：`TestUserSubmissionNoAutoProcess`、`TestStartProcessing`、`TestWorkerStatus`、`TestAutoPublishSyncsReviewStatus`。
- 直接依赖：[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_perf_hot_paths.py](../../../backend/tests/test_perf_hot_paths.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 learning、subtitle、user、video、vocab_set、video_service。行为锚点：TestVideoDetailFastPath；TestBoundedReadModels。

- 代码入口/类型：`count_statements`、`TestVideoDetailFastPath`、`TestBoundedReadModels`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_phase1_b0_smoke.py](../../../backend/tests/test_phase1_b0_smoke.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 __init__、learning、videos、preferences、vocabulary。行为锚点：favorites_route_registered_before_dynamic_video_id；phase1_video_endpoints_registered；phase1_learning_stats_endpoints_registered；vocabulary_model_has_subtitle_id。

- 代码入口/类型：`test_favorites_route_registered_before_dynamic_video_id`、`test_phase1_video_endpoints_registered`、`test_phase1_learning_stats_endpoints_registered`、`test_vocabulary_model_has_subtitle_id`、`test_notification_prefs_defaults_include_phase1_keys`、`test_vocabulary_response_schema_includes_subtitle_id`。
- 直接依赖：[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/learning.py](../../../backend/app/api/v1/learning.py)、[backend/app/api/v1/videos.py](../../../backend/app/api/v1/videos.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/schemas/vocabulary.py](../../../backend/app/schemas/vocabulary.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pip_audit_gate.py](../../../backend/tests/test_pip_audit_gate.py)

自动回归：带期限豁免和已修陈旧项提示的依赖漏洞硬门。行为锚点：suppression_file_is_well_formed；no_suppression_is_past_its_review_date；lapsed_detection_treats_the_review_date_itself_as_valid；malformed_rows_are_rejected。

- 代码入口/类型：`test_suppression_file_is_well_formed`、`test_no_suppression_is_past_its_review_date`、`test_lapsed_detection_treats_the_review_date_itself_as_valid`、`test_malformed_rows_are_rejected`、`test_duplicate_rows_are_rejected`、`test_report_rows_are_deduped_and_keep_their_aliases`。
- 直接依赖：[backend/scripts/pip_audit_gate.py](../../../backend/scripts/pip_audit_gate.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pipeline_dispatch.py](../../../backend/tests/test_pipeline_dispatch.py)

自动回归：数据库 outbox 派发、重试、过期放弃和积压盘点。直接覆盖 pipeline_dispatch、video、__init__、celery_app。行为锚点：TestEnqueue；TestDispatchNow；TestDispatchPending；TestBacklog。

- 代码入口/类型：`sent`、`no_backoff`、`TestEnqueue`、`TestDispatchNow`、`TestDispatchPending`、`TestBacklog`、`TestPendingVideoIds`、`TestImportOrder`。
- 直接依赖：[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)、[backend/app/tasks/celery_app.py](../../../backend/app/tasks/celery_app.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pipeline_lock_ttl.py](../../../backend/tests/test_pipeline_lock_ttl.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 pipeline_helpers、video_processing。行为锚点：lock_ttl_covers_all_declared_step_budgets；lock_ttl_has_a_floor_for_tiny_budgets；refresh_lock_extends_an_existing_lock；refresh_lock_failure_is_best_effort。

- 代码入口/类型：`test_lock_ttl_covers_all_declared_step_budgets`、`test_lock_ttl_has_a_floor_for_tiny_budgets`、`test_refresh_lock_extends_an_existing_lock`、`test_refresh_lock_failure_is_best_effort`、`test_translating_stamps_step_started_at_before_llm_work`。
- 直接依赖：[backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pipeline_resume.py](../../../backend/tests/test_pipeline_resume.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、user、video。行为锚点：TestRetrySmartResume。

- 代码入口/类型：`TestRetrySmartResume`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pipeline_steps.py](../../../backend/tests/test_pipeline_steps.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 pipeline_helpers。行为锚点：TestRunSteps。

- 代码入口/类型：`TestRunSteps`。
- 直接依赖：[backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_pipeline_watchdog.py](../../../backend/tests/test_pipeline_watchdog.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、admin_setting、video、pipeline_dispatch、pipeline_helpers、video_processing。行为锚点：TestWatchdogStalePipeline；TestStepBudgets。

- 代码入口/类型：`TestWatchdogStalePipeline`、`TestStepBudgets`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/admin_setting.py](../../../backend/app/models/admin_setting.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)、[backend/app/tasks/pipeline_helpers.py](../../../backend/app/tasks/pipeline_helpers.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_presence.py](../../../backend/tests/test_presence.py)

自动回归：可见页面在线心跳。行为锚点：TestPresenceHeartbeat；TestAdminStatsNewKpis。

- 代码入口/类型：`TestPresenceHeartbeat`、`TestAdminStatsNewKpis`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_presentation_contracts.py](../../../backend/tests/test_presentation_contracts.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 exam_test、learning、user。行为锚点：training_preview_matches_rounds_without_creating_them；training_preview_excludes_active_words_from_review；catalog_filters_full_dataset_and_year_facets；catalog_uses_latest_submission_and_frozen_counts。

- 代码入口/类型：`test_training_preview_matches_rounds_without_creating_them`、`test_training_preview_excludes_active_words_from_review`、`test_catalog_filters_full_dataset_and_year_facets`、`test_catalog_uses_latest_submission_and_frozen_counts`、`test_catalog_status_and_latest_result_are_scoped_to_owner`。
- 直接依赖：[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)、[backend/tests/test_exams_api.py](../../../backend/tests/test_exams_api.py)、[backend/tests/test_study_sessions.py](../../../backend/tests/test_study_sessions.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_profile.py](../../../backend/tests/test_profile.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 user、sms_service。行为锚点：TestAvatarUpload；TestGender；TestUserNameLength；TestChangePhone。

- 代码入口/类型：`TestAvatarUpload`、`TestGender`、`TestUserNameLength`、`TestChangePhone`。
- 直接依赖：[backend/app/schemas/user.py](../../../backend/app/schemas/user.py)、[backend/app/services/sms_service.py](../../../backend/app/services/sms_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_quality_alert.py](../../../backend/tests/test_quality_alert.py)

自动回归：翻译覆盖率、长度和混合语言质量检查。直接覆盖 notification、user、notification_service。行为锚点：TestNotifyAdmins。

- 代码入口/类型：`TestNotifyAdmins`。
- 直接依赖：[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/notification_service.py](../../../backend/app/services/notification_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_quality_safety_net.py](../../../backend/tests/test_quality_safety_net.py)

自动回归：翻译覆盖率、长度和混合语言质量检查。直接覆盖 subtitle、video、video_quality_report、ecdict、transcription_quality、quality。行为锚点：TestTranscriptionQuality；TestTranslationQualityGate；TestWordLevelsPreservation；TestQualityReportPersistence。

- 代码入口/类型：`TestTranscriptionQuality`、`TestTranslationQualityGate`、`TestWordLevelsPreservation`、`TestQualityReportPersistence`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/video_quality_report.py](../../../backend/app/models/video_quality_report.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/transcription_quality.py](../../../backend/app/services/transcription_quality.py)、[backend/app/services/translation/quality.py](../../../backend/app/services/translation/quality.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [backend/tests/test_rankings.py](../../../backend/tests/test_rankings.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 cache、behavior、favorite、user、video、ranking_service、ranking_tasks。行为锚点：TestLatestRankings；TestWeeklyViewsRankings；TestWeeklyFavoritesRankings；TestWeekBoundary。

- 代码入口/类型：`TestLatestRankings`、`TestWeeklyViewsRankings`、`TestWeeklyFavoritesRankings`、`TestWeekBoundary`、`TestSnapshotRankingsTask`、`TestRankingsEndpoint`。
- 直接依赖：[backend/app/core/cache.py](../../../backend/app/core/cache.py)、[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/ranking_service.py](../../../backend/app/services/ranking_service.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_recommendations.py](../../../backend/tests/test_recommendations.py)

自动回归：首页与分类推荐接口。直接覆盖 behavior、user、video、recommendation_service。行为锚点：TestHomeFeed；TestCategoryFeed；TestDiversifyUnit；TestSplitBucketsUnit。

- 代码入口/类型：`TestHomeFeed`、`TestCategoryFeed`、`TestDiversifyUnit`、`TestSplitBucketsUnit`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/recommendation_service.py](../../../backend/app/services/recommendation_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_redaction.py](../../../backend/tests/test_redaction.py)

自动回归：token/口令连接串等外发日志脱敏。直接覆盖 redaction。行为锚点：media_token_query_is_redacted；connection_string_password_is_redacted；bearer_header_is_redacted；redaction_is_idempotent。

- 代码入口/类型：`test_media_token_query_is_redacted`、`test_connection_string_password_is_redacted`、`test_bearer_header_is_redacted`、`test_redaction_is_idempotent`、`test_redact_value_walks_nested_structures`。
- 直接依赖：[backend/app/core/redaction.py](../../../backend/app/core/redaction.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_redis_close.py](../../../backend/tests/test_redis_close.py)

自动回归：进程复用的 async Redis 连接池与关闭。直接覆盖 __init__、redis。行为锚点：close_redis_uses_close_when_aclose_missing；close_redis_prefers_aclose_when_available；close_redis_noop_when_unset。

- 代码入口/类型：`restore_redis_singleton`、`test_close_redis_uses_close_when_aclose_missing`、`test_close_redis_prefers_aclose_when_available`、`test_close_redis_noop_when_unset`。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_reminder_tasks.py](../../../backend/tests/test_reminder_tasks.py)

自动回归：按用户本地时刻发送自愿开启的复习提醒。直接覆盖 database、learning、learning_plan、notification、preferences、user、reminder_tasks。行为锚点：vocabulary_reminder_sent_when_due_words_at_reminder_hour；vocabulary_reminder_not_sent_outside_reminder_hour；vocabulary_reminder_skipped_when_no_due_words；vocabulary_reminder_respects_opt_out。

- 代码入口/类型：`test_vocabulary_reminder_sent_when_due_words_at_reminder_hour`、`test_vocabulary_reminder_not_sent_outside_reminder_hour`、`test_vocabulary_reminder_skipped_when_no_due_words`、`test_vocabulary_reminder_respects_opt_out`、`test_vocabulary_reminder_not_duplicated_on_same_day_rerun`、`test_streak_warning_sent_at_21_when_streak_at_risk`、`test_streak_warning_skipped_when_already_active_today`、`test_streak_warning_skipped_when_streak_below_two`、`test_streak_warning_respects_opt_out`、`test_streak_warning_not_sent_and_counter_reset_when_already_broken`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 1 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_response_contract.py](../../../backend/tests/test_response_contract.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 main、favorite、video。行为锚点：TestCardShapes；TestCardScopesDifferByValueNotByShape；TestErrorEnvelopeShapes；TestOpenApiResponseModels。

- 代码入口/类型：`TestCardShapes`、`TestCardScopesDifferByValueNotByShape`、`TestErrorEnvelopeShapes`、`TestOpenApiResponseModels`。
- 直接依赖：[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/schemas/video.py](../../../backend/app/schemas/video.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [backend/tests/test_retired_learning_events.py](../../../backend/tests/test_retired_learning_events.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 learning_plan、learning_event_service。行为锚点：retired_shadowing_event_does_not_write；retired_shadowing_not_in_valid_types。

- 代码入口/类型：`test_retired_shadowing_event_does_not_write`、`test_retired_shadowing_not_in_valid_types`。
- 直接依赖：[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/services/learning_event_service.py](../../../backend/app/services/learning_event_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_scoring.py](../../../backend/tests/test_scoring.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 behavior、learning、subtitle、user、video、video_score、scoring_service、video_service。行为锚点：TestScoringFactors；TestExternalFactors；TestScoringPersistence；TestPublicListOrdering。

- 代码入口/类型：`TestScoringFactors`、`TestExternalFactors`、`TestScoringPersistence`、`TestPublicListOrdering`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/video_score.py](../../../backend/app/models/video_score.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_search_d7.py](../../../backend/tests/test_search_d7.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、video、search_service。行为锚点：suggest_returns_matching_titles；suggest_prefix_match_ranks_first；suggest_excludes_unpublished_and_non_official；suggest_empty_query_returns_empty。

- 代码入口/类型：`test_suggest_returns_matching_titles`、`test_suggest_prefix_match_ranks_first`、`test_suggest_excludes_unpublished_and_non_official`、`test_suggest_empty_query_returns_empty`、`test_suggest_respects_limit`、`test_search_returns_matching_ready_video`、`test_search_excludes_unpublished_and_non_official`、`test_search_empty_query_returns_empty`、`test_search_matches_chinese_title`、`fake_redis`（其余见机器清单）。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/search_service.py](../../../backend/app/services/search_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_seed_full.py](../../../backend/tests/test_seed_full.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 video。行为锚点：TestSeedFull。

- 代码入口/类型：`TestSeedFull`。
- 直接依赖：[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_shadowing_api.py](../../../backend/tests/test_shadowing_api.py)

自动回归：退役录音功能的鉴权兼容壳，不执行跟读。直接覆盖 config。行为锚点：retired_mutation_returns_gone；retired_upload_does_not_write_files。

- 代码入口/类型：`test_retired_mutation_returns_gone`、`test_retired_upload_does_not_write_files`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_slcs.py](../../../backend/tests/test_slcs.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 video_learning_material、__init__。行为锚点：real_example_resolves_a_vocabulary_occurrence；unaligned_middle_word_falls_back_to_segment；fingerprint_ignores_json_layout_and_tracks_content_changes；two_glosses_for_one_word_span_are_rejected。

- 代码入口/类型：`document`、`test_real_example_resolves_a_vocabulary_occurrence`、`test_unaligned_middle_word_falls_back_to_segment`、`test_fingerprint_ignores_json_layout_and_tracks_content_changes`、`test_two_glosses_for_one_word_span_are_rejected`、`test_one_headword_may_describe_several_spans`、`test_fingerprint_carries_the_contract_version`、`test_token_offsets_use_unicode_code_points`、`test_invalid_pack_has_the_same_diagnostic_for_both_consumers`、`test_embedding_requires_an_official_youtube_watch_page`（其余见机器清单）。
- 直接依赖：[backend/app/services/video_learning_material.py](../../../backend/app/services/video_learning_material.py)、[backend/app/slcs/__init__.py](../../../backend/app/slcs/__init__.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_slcs_lessons.py](../../../backend/tests/test_slcs_lessons.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 config、database、errors、__init__、learning_plan、lesson、user、account_data、lesson_progress、lesson_receipts、lessons、study_time_service。行为锚点：signed_publication_is_idempotent_and_withdrawal_retains_progress。

- 代码入口/类型：`lesson_db`、`test_signed_publication_is_idempotent_and_withdrawal_retains_progress`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/__init__.py](../../../backend/app/models/__init__.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/lesson.py](../../../backend/app/models/lesson.py)；其余 9 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_sms_security.py](../../../backend/tests/test_sms_security.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 logging、sms_service。行为锚点：dev_fake_disabled_in_production；dev_fake_disabled_without_explicit_opt_in；dev_fake_enabled_in_dev；verify_requires_a_real_send_even_in_dev。

- 代码入口/类型：`prod_no_sms`、`prod_sms_ok`、`dev_no_sms`、`dev_no_sms_fake_off`、`test_dev_fake_disabled_in_production`、`test_dev_fake_disabled_without_explicit_opt_in`、`test_dev_fake_enabled_in_dev`、`test_verify_requires_a_real_send_even_in_dev`、`test_verify_rejects_fixed_code_in_production`、`test_verify_rejects_wrong_code_in_production`（其余见机器清单）。
- 直接依赖：[backend/app/core/logging.py](../../../backend/app/core/logging.py)、[backend/app/services/sms_service.py](../../../backend/app/services/sms_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_sr_service.py](../../../backend/tests/test_sr_service.py)

自动回归：错误次数分档复习调度与冻结的旧 SM-2 算法。直接覆盖 learning、sr_service、vocabulary_service。行为锚点：TestCalculateNextReview；TestReviewIntervalBands；TestApplyReviewBands；TestThreeLevelSelfRating。

- 代码入口/类型：`TestCalculateNextReview`、`TestReviewIntervalBands`、`TestApplyReviewBands`、`TestThreeLevelSelfRating`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/services/sr_service.py](../../../backend/app/services/sr_service.py)、[backend/app/services/vocabulary_service.py](../../../backend/app/services/vocabulary_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_study_sessions.py](../../../backend/tests/test_study_sessions.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 security、learning、study_session、user、local_time。行为锚点：TestRoundLifecycle；TestRoundResume；TestAnswers；TestExtraRound。

- 代码入口/类型：`TestRoundLifecycle`、`TestRoundResume`、`TestAnswers`、`TestExtraRound`、`TestRetention`、`TestTodayVisibility`。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/study_session.py](../../../backend/app/models/study_session.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/local_time.py](../../../backend/app/services/local_time.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 直接使用者：[backend/tests/test_presentation_contracts.py](../../../backend/tests/test_presentation_contracts.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_study_time_facts.py](../../../backend/tests/test_study_time_facts.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 behavior、learning、learning_plan、video。行为锚点：TestWatchTimeIngest；TestAggregationAgreement。

- 代码入口/类型：`TestWatchTimeIngest`、`TestAggregationAgreement`。
- 直接依赖：[backend/app/models/behavior.py](../../../backend/app/models/behavior.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_subtitle_edit.py](../../../backend/tests/test_subtitle_edit.py)

自动回归：英文/译文、顺序、句词时间和难度标注。直接覆盖 subtitle、video。行为锚点：TestSubtitleUpdateAuth；TestSubtitleUpdate；TestSubtitleBatchUpdate。

- 代码入口/类型：`TestSubtitleUpdateAuth`、`TestSubtitleUpdate`、`TestSubtitleBatchUpdate`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_subtitle_reorder_create_delete.py](../../../backend/tests/test_subtitle_reorder_create_delete.py)

自动回归：英文/译文、顺序、句词时间和难度标注。直接覆盖 subtitle、video。行为锚点：reorder_repairs_scrambled_indices；reorder_rejects_incomplete_payload；reorder_rejects_non_contiguous_indices；reorder_rejects_timing_overlap_in_new_order。

- 代码入口/类型：`test_reorder_repairs_scrambled_indices`、`test_reorder_rejects_incomplete_payload`、`test_reorder_rejects_non_contiguous_indices`、`test_reorder_rejects_timing_overlap_in_new_order`、`test_create_appends_subtitle_at_end`、`test_create_allows_empty_text_placeholder`、`test_create_rejects_overlap`、`test_create_rejects_invalid_timing`、`test_delete_middle_closes_gap`、`test_delete_not_found`（其余见机器清单）。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_subtitle_resegment.py](../../../backend/tests/test_subtitle_resegment.py)

自动回归：英文/译文、顺序、句词时间和难度标注。直接覆盖 learning、subtitle、subtitle_resegment_snapshot、subtitle_revision、user、user_content、video、__init__、subtitle_edit_service。行为锚点：resegment_splits_long_unsegmented_chunk；resegment_works_without_words；rollback_restores_snapshot；rollback_without_snapshot_rejected。

- 代码入口/类型：`test_resegment_splits_long_unsegmented_chunk`、`test_resegment_works_without_words`、`test_rollback_restores_snapshot`、`test_rollback_without_snapshot_rejected`、`test_resegment_preserves_favorites_revisions_vocabulary`、`test_rollback_restores_user_data_onto_original_sentences`、`test_map_interval_prefers_containing_segment`、`test_map_interval_falls_back_to_largest_overlap`、`test_map_interval_without_overlap_is_unmatched`、`test_remap_plan_marks_unmatched_and_merges_duplicates`（其余见机器清单）。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/subtitle_resegment_snapshot.py](../../../backend/app/models/subtitle_resegment_snapshot.py)、[backend/app/models/subtitle_revision.py](../../../backend/app/models/subtitle_revision.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/user_content.py](../../../backend/app/models/user_content.py)；其余 4 项见机器清单。
- 直接使用者：[backend/tests/test_subtitle_resegment_mixed.py](../../../backend/tests/test_subtitle_resegment_mixed.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_subtitle_resegment_mixed.py](../../../backend/tests/test_subtitle_resegment_mixed.py)

自动回归：英文/译文、顺序、句词时间和难度标注。直接覆盖 learning、subtitle、user_content、subtitle_resegment_rules。行为锚点：manual_cue_is_preserved_at_each_position_without_faking_word_alignment；segment_crossing_manual_and_aligned_words_does_not_claim_full_alignment；mixed_resegment_and_rollback_keep_manual_text_favorites_and_word_source。

- 代码入口/类型：`test_manual_cue_is_preserved_at_each_position_without_faking_word_alignment`、`test_segment_crossing_manual_and_aligned_words_does_not_claim_full_alignment`、`test_mixed_resegment_and_rollback_keep_manual_text_favorites_and_word_source`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user_content.py](../../../backend/app/models/user_content.py)、[backend/app/services/subtitle_resegment_rules.py](../../../backend/app/services/subtitle_resegment_rules.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)、[backend/tests/test_subtitle_resegment.py](../../../backend/tests/test_subtitle_resegment.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_subtitle_revisions.py](../../../backend/tests/test_subtitle_revisions.py)

自动回归：英文/译文、顺序、句词时间和难度标注。直接覆盖 subtitle、subtitle_revision、user、video、video_standard。行为锚点：TestEditWritesRevision；TestRollback；TestHistoryEndpoints。

- 代码入口/类型：`TestEditWritesRevision`、`TestRollback`、`TestHistoryEndpoints`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/subtitle_revision.py](../../../backend/app/models/subtitle_revision.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/video_standard.py](../../../backend/app/models/video_standard.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_subtitle_split_merge.py](../../../backend/tests/test_subtitle_split_merge.py)

自动回归：英文/译文、顺序、句词时间和难度标注。直接覆盖 subtitle、video。行为锚点：split_creates_two_parts_and_shifts_index；split_partitions_words；split_time_out_of_range_rejected；merge_combines_with_next_and_shifts_index。

- 代码入口/类型：`test_split_creates_two_parts_and_shifts_index`、`test_split_partitions_words`、`test_split_time_out_of_range_rejected`、`test_merge_combines_with_next_and_shifts_index`、`test_merge_last_subtitle_rejected`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching.py](../../../backend/tests/test_teaching.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 errors、learning_plan、question_exposure、teaching、user、__init__、admin_stats、local_time、overview_service、content、events、principal、service、v2_access。行为锚点：automatic_gate_accepts_complete_original_evidence；automatic_gate_rejects_missing_or_conflicting_proof；identity_and_score_cannot_come_from_request；initial_hint_retry_reveal_and_receipt_replay。

- 代码入口/类型：`enable`、`action`、`test_automatic_gate_accepts_complete_original_evidence`、`test_automatic_gate_rejects_missing_or_conflicting_proof`、`test_identity_and_score_cannot_come_from_request`、`test_initial_hint_retry_reveal_and_receipt_replay`、`test_unknown_history_and_cross_session_help_never_reset_initial`、`test_revision_conflict_and_changed_operation_have_no_extra_attempt`、`test_model_write_forbidden_and_external_read_does_not_leak_analysis`、`test_rights_withdrawal_reprojects_old_receipts_and_disabled_reads_work`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)；其余 11 项见机器清单。
- 直接使用者：[backend/tests/test_content_publication.py](../../../backend/tests/test_content_publication.py)、[backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)、[backend/tests/test_learning_context_pg.py](../../../backend/tests/test_learning_context_pg.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_content_cli.py](../../../backend/tests/test_teaching_content_cli.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 __init__、database、errors、content_publication、teaching、user、publication。行为锚点：inventory_quarantines_candidates_without_inventing_verification；manifest_check_is_not_publication_and_import_requires_authentic_receipts；cli_import_is_audited_replayable_and_cannot_resurrect_withdrawn_revision；cli_rejects_non_admin_actor_before_receipt_io。

- 代码入口/类型：`test_inventory_quarantines_candidates_without_inventing_verification`、`test_manifest_check_is_not_publication_and_import_requires_authentic_receipts`、`test_cli_import_is_audited_replayable_and_cannot_resurrect_withdrawn_revision`、`test_cli_rejects_non_admin_actor_before_receipt_io`、`test_malformed_manifest_entries_report_failure_without_traceback`。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 6 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_dialogue.py](../../../backend/tests/test_teaching_dialogue.py)

自动回归：导师回复、消息块、引用和页游标字段。直接覆盖 __init__、teaching_runs、database、errors、security、exam_test、teaching、user、v2_runtime、account_data、dialogue、service、teaching_gateway、v2_access、account_tasks。行为锚点：complete_learning_flow_chat_restoration_drafts_and_sse_resume；history_rights_export_retention_and_account_deletion；other_tasks_users_disabled_gate_and_cancel_do_not_publish_messages；model_history_is_bounded_and_never_includes_another_task。

- 代码入口/类型：`setup`、`model`、`create_turn`、`test_complete_learning_flow_chat_restoration_drafts_and_sse_resume`、`test_history_rights_export_retention_and_account_deletion`、`test_other_tasks_users_disabled_gate_and_cancel_do_not_publish_messages`、`test_model_history_is_bounded_and_never_includes_another_task`、`test_truncated_model_result_preserves_user_turn_without_publishing_reply`。
- 直接依赖：[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)；其余 15 项见机器清单。
- 直接使用者：[backend/tests/test_teaching_streaming.py](../../../backend/tests/test_teaching_streaming.py)、[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)、[backend/tests/test_tutor_gateway.py](../../../backend/tests/test_tutor_gateway.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_dialogue_pg.py](../../../backend/tests/test_teaching_dialogue_pg.py)

自动回归：导师回复、消息块、引用和页游标字段。直接覆盖 database、teaching、v2_runtime、teaching_dialogue、__init__、service、teaching_runs、v2_access。行为锚点：two_creators_share_one_run_and_one_user_message；obsolete_reply_never_appends_an_assistant_message。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`prepare`、`test_two_creators_share_one_run_and_one_user_message`、`test_obsolete_reply_never_appends_an_assistant_message`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/schemas/teaching_dialogue.py](../../../backend/app/schemas/teaching_dialogue.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)；其余 4 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_gateway.py](../../../backend/tests/test_teaching_gateway.py)

自动回归：教学模型网关准入、预算调用、内容核验及流式排空适配。直接覆盖 errors、__init__、teaching_gateway。行为锚点：provisions_team_membership_before_key；existing_membership_conflict_is_accepted；membership_provisioning_failure_fails_closed。

- 代码入口/类型：`test_provisions_team_membership_before_key`、`test_existing_membership_conflict_is_accepted`、`test_membership_provisioning_failure_fails_closed`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_pg.py](../../../backend/tests/test_teaching_pg.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 database、errors、teaching、__init__、principal、service、v2_access。行为锚点：concurrent_identical_start_has_one_session_and_receipt；preloaded_same_revision_two_answers_accept_only_one；cross_session_same_question_grants_initial_once。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`seed`、`start`、`test_concurrent_identical_start_has_one_session_and_receipt`、`test_preloaded_same_revision_two_answers_accept_only_one`、`test_cross_session_same_question_grants_initial_once`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/principal.py](../../../backend/app/services/teaching/principal.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_quiz.py](../../../backend/tests/test_teaching_quiz.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 errors、exam_test、question_exposure、teaching、user、__init__、commands、content、principal、service、v2_access。行为锚点：quiz_freezes_four_questions_without_leaking_answers；quiz_requires_exactly_four_usable_questions；withdrawn_material_never_enters_a_quiz；repeated_action_counts_once_and_projects_progress。

- 代码入口/类型：`enable`、`act`、`test_quiz_freezes_four_questions_without_leaking_answers`、`test_quiz_requires_exactly_four_usable_questions`、`test_withdrawn_material_never_enters_a_quiz`、`test_repeated_action_counts_once_and_projects_progress`、`test_stale_revision_is_rejected_not_silently_applied`、`test_revealing_one_question_does_not_disclose_another`、`test_quiz_answers_never_touch_the_formal_exam_tables`、`test_only_the_user_may_drive_a_quiz_action`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/exam_test.py](../../../backend/app/models/exam_test.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)；其余 8 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_quiz_pg.py](../../../backend/tests/test_teaching_quiz_pg.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 database、errors、teaching、__init__、commands、principal、service、v2_access。行为锚点：concurrent_click_on_one_action_creates_one_attempt；concurrent_quiz_creation_with_one_operation_id。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`seed`、`start_quiz`、`test_concurrent_click_on_one_action_creates_one_attempt`、`test_concurrent_quiz_creation_with_one_operation_id`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/schemas/teaching.py](../../../backend/app/schemas/teaching.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)；其余 5 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_streaming.py](../../../backend/tests/test_teaching_streaming.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 errors、security、teaching、v2_runtime、__init__、streaming、teaching_gateway、teaching_runs。行为锚点：parser_strips_markers_splits_sentences_and_keeps_unknown_brackets；parser_holds_a_marker_split_across_deltas；parser_rejects_out_of_range_markers_and_oversized_text；parser_cuts_long_unpunctuated_text_at_the_block_limit。

- 代码入口/类型：`context`、`stream_model`、`enable_streaming`、`reveal`、`run_turn`、`test_parser_strips_markers_splits_sentences_and_keeps_unknown_brackets`、`test_parser_holds_a_marker_split_across_deltas`、`test_parser_rejects_out_of_range_markers_and_oversized_text`、`test_parser_cuts_long_unpunctuated_text_at_the_block_limit`、`test_gateway_stream_reports_model_stream_and_usage`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/streaming.py](../../../backend/app/services/teaching/streaming.py)；其余 4 项见机器清单。
- 直接使用者：[backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_teaching_streaming_pg.py](../../../backend/tests/test_teaching_streaming_pg.py)

自动回归：确定性教学材料、会话、作答、提示和揭晓。直接覆盖 database、v2_runtime、__init__、service、teaching_gateway、teaching_runs、v2_access。行为锚点：cancel_mid_stream_keeps_only_committed_blocks。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`install_stream`、`test_cancel_mid_stream_keeps_only_committed_blocks`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_thumbnail_service.py](../../../backend/tests/test_thumbnail_service.py)

自动回归：下载/提取并本地化封面，复用外站域名策略。直接覆盖 config、__init__、thumbnail_service。行为锚点：sniff_detects_payload_types；download_rejects_host_outside_allowlist；localize_reuses_existing_local_file；localize_downloads_and_picks_extension_from_payload。

- 代码入口/类型：`media_dir`、`test_sniff_detects_payload_types`、`test_download_rejects_host_outside_allowlist`、`test_localize_reuses_existing_local_file`、`test_localize_downloads_and_picks_extension_from_payload`、`test_localize_failure_keeps_external_url`、`test_find_local_video_file_prefers_transcode`、`test_localize_falls_back_to_frame_extraction`、`test_localize_noop_for_local_or_missing_urls`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/thumbnail_service.py](../../../backend/app/services/thumbnail_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_translation_quality_block.py](../../../backend/tests/test_translation_quality_block.py)

自动回归：带主/备引擎和并发策略的字幕翻译。直接覆盖 subtitle、video、video_processing。行为锚点：TestTranslationQualityDecision；TestRetranslateEndpoint。

- 代码入口/类型：`TestTranslationQualityDecision`、`TestRetranslateEndpoint`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/tasks/video_processing.py](../../../backend/app/tasks/video_processing.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_translation_service.py](../../../backend/tests/test_translation_service.py)

自动回归：带主/备引擎和并发策略的字幕翻译。直接覆盖 config、__init__。行为锚点：normalize_translations_coerces_junk；translate_batch_concurrent_fans_out；translate_batch_concurrent_all_fail_returns_none；translate_batch_concurrent_partial_nulls_preserved。

- 代码入口/类型：`translation_service`、`test_normalize_translations_coerces_junk`、`test_translate_batch_concurrent_fans_out`、`test_translate_batch_concurrent_all_fail_returns_none`、`test_translate_batch_concurrent_partial_nulls_preserved`、`test_translate_batch_sequential_primary_then_fallback`、`test_translate_batch_empty_input`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/services/translation/__init__.py](../../../backend/app/services/translation/__init__.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_tutor_conversations.py](../../../backend/tests/test_tutor_conversations.py)

自动回归：本人独立聊天、关联任务及共享运行引擎调用。直接覆盖 __init__、teaching_runs、tutor、database、errors、security、teaching、user、v2_runtime、account_data、service、streaming、teaching_gateway、tutor_conversations、v2_access、v2_schema、account_tasks。行为锚点：chat_lifecycle_and_taskless_turn；general_reply_may_not_cite_or_suggest；task_turn_inside_a_chat_and_cross_task_isolation；legacy_task_endpoint_keeps_its_transcript。

- 代码入口/类型：`setup`、`model`、`test_chat_lifecycle_and_taskless_turn`、`test_general_reply_may_not_cite_or_suggest`、`test_task_turn_inside_a_chat_and_cross_task_isolation`、`test_legacy_task_endpoint_keeps_its_transcript`、`test_export_and_purge_cover_taskless_chats`、`test_conversation_runs_are_gated_and_scoped`、`test_conversation_schema_gate_returns_503`、`test_taskless_chat_streams_plain_text_without_citations`（其余见机器清单）。
- 直接依赖：[backend/app/api/v1/__init__.py](../../../backend/app/api/v1/__init__.py)、[backend/app/api/v1/teaching_runs.py](../../../backend/app/api/v1/teaching_runs.py)、[backend/app/api/v1/tutor.py](../../../backend/app/api/v1/tutor.py)、[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)；其余 19 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_tutor_conversations_pg.py](../../../backend/tests/test_tutor_conversations_pg.py)

自动回归：本人独立聊天、关联任务及共享运行引擎调用。直接覆盖 database、v2_runtime、__init__、service、teaching_runs、tutor_conversations、v2_access。行为锚点：two_creators_share_one_chat_run_and_one_user_message；deleting_a_chat_mid_run_settles_without_crashing。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`prepare`、`test_two_creators_share_one_chat_run_and_one_user_message`、`test_deleting_a_chat_mid_run_settles_without_crashing`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)、[backend/app/services/teaching/service.py](../../../backend/app/services/teaching/service.py)、[backend/app/services/teaching_runs.py](../../../backend/app/services/teaching_runs.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_tutor_gateway.py](../../../backend/tests/test_tutor_gateway.py)

自动回归：独立导师聊天生命周期及共享回合入口。直接覆盖 errors、__init__、teaching_gateway。行为锚点：invalid_model_reply_cannot_become_a_message；fresh_context_replaces_stale_sources_without_changing_model_authority。

- 代码入口/类型：`context`、`test_invalid_model_reply_cannot_become_a_message`、`test_fresh_context_replaces_stale_sources_without_changing_model_authority`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/teaching_gateway.py](../../../backend/app/services/teaching_gateway.py)、[backend/tests/test_teaching_dialogue.py](../../../backend/tests/test_teaching_dialogue.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_uploads.py](../../../backend/tests/test_uploads.py)

自动回归：上传分块限量读取，避免先全量读入再判断大小。直接覆盖 uploads。行为锚点：within_limit_returns_full_content；declared_content_length_rejects_before_any_read；declared_length_lying_small_falls_back_to_chunked_guard；missing_content_length_uses_chunked_guard。

- 代码入口/类型：`test_within_limit_returns_full_content`、`test_declared_content_length_rejects_before_any_read`、`test_declared_length_lying_small_falls_back_to_chunked_guard`、`test_missing_content_length_uses_chunked_guard`、`test_multipart_envelope_does_not_false_reject_a_max_sized_part`、`test_non_numeric_content_length_is_ignored`。
- 直接依赖：[backend/app/core/uploads.py](../../../backend/app/core/uploads.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_user_overview.py](../../../backend/tests/test_user_overview.py)

自动回归：账号、角色、封禁、改密与注销身份字段。直接覆盖 learning、learning_plan、video、local_time。行为锚点：TestUserOverview。

- 代码入口/类型：`TestUserOverview`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/local_time.py](../../../backend/app/services/local_time.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_user_preferences.py](../../../backend/tests/test_user_preferences.py)

自动回归：账号、角色、封禁、改密与注销身份字段。行为锚点：auto_advance_defaults_off_and_round_trips；preferences_update_does_not_disturb_other_fields。

- 代码入口/类型：`test_auto_advance_defaults_off_and_round_trips`、`test_preferences_update_does_not_disturb_other_fields`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_v2_account_data.py](../../../backend/tests/test_v2_account_data.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 teaching、user、v2_runtime、__init__、account_data、principal、service、v2_access、account_tasks。行为锚点：v2_export_has_only_owned_projected_facts_and_safe_runtime_summary；v2_purge_revokes_fences_and_deletes_private_children_but_keeps_gateway_intent；v2_removal_rolls_back_revocation_cancellation_and_remote_intent。

- 代码入口/类型：`test_v2_export_has_only_owned_projected_facts_and_safe_runtime_summary`、`test_v2_purge_revokes_fences_and_deletes_private_children_but_keeps_gateway_intent`、`test_v2_removal_rolls_back_revocation_cancellation_and_remote_intent`。
- 直接依赖：[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/account_data.py](../../../backend/app/services/account_data.py)、[backend/app/services/teaching/__init__.py](../../../backend/app/services/teaching/__init__.py)；其余 5 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_v2_runtime.py](../../../backend/tests/test_v2_runtime.py)

自动回归：外部凭据、访问授权、运行事件、长期消息和外部生命周期意图。直接覆盖 __init__、database、errors、v2_runtime、external_connection_service、service、teaching_runs、v2_access。行为锚点：credentials_rotated_and_revoked_without_storing_plaintext；read_scope_cannot_submit_and_password_change_invalidates_token；run_receipt_cancel_replay_and_no_duplicate_execution；event_replay_intersects_current_rights_and_cursor_retention。

- 代码入口/类型：`enable`、`start`、`test_credentials_rotated_and_revoked_without_storing_plaintext`、`test_read_scope_cannot_submit_and_password_change_invalidates_token`、`test_run_receipt_cancel_replay_and_no_duplicate_execution`、`test_event_replay_intersects_current_rights_and_cursor_retention`、`test_run_dispatch_is_idempotent_and_has_no_model_write_authority`。
- 直接依赖：[backend/app/core/__init__.py](../../../backend/app/core/__init__.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)；其余 6 项见机器清单。
- 直接使用者：[backend/tests/test_learning_context.py](../../../backend/tests/test_learning_context.py)、[backend/tests/test_mcp_adapter.py](../../../backend/tests/test_mcp_adapter.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_v2_runtime_pg.py](../../../backend/tests/test_v2_runtime_pg.py)

自动回归：外部凭据、访问授权、运行事件、长期消息和外部生命周期意图。直接覆盖 database、errors、teaching、v2_runtime、__init__、external_connection_service、service、teaching_runs、v2_access。行为锚点：revocation_waits_for_authorized_write_then_rejects_the_next_call；stale_connection_and_credential_are_refreshed_after_lock_wait；concurrent_run_operation_has_one_receipt_across_sessions；late_model_response_cannot_publish_under_obsolete_authority。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`seed`、`issued`、`wait_until_blocked`、`test_revocation_waits_for_authorized_write_then_rejects_the_next_call`、`test_stale_connection_and_credential_are_refreshed_after_lock_wait`、`test_concurrent_run_operation_has_one_receipt_across_sessions`、`test_late_model_response_cannot_publish_under_obsolete_authority`、`test_model_rights_revoked_during_key_setup_prevent_dispatch`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/external_connection_service.py](../../../backend/app/services/external_connection_service.py)；其余 5 项见机器清单。
- 直接使用者：[backend/tests/test_teaching_dialogue_pg.py](../../../backend/tests/test_teaching_dialogue_pg.py)、[backend/tests/test_teaching_streaming_pg.py](../../../backend/tests/test_teaching_streaming_pg.py)、[backend/tests/test_tutor_conversations_pg.py](../../../backend/tests/test_tutor_conversations_pg.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_v2_schema_gating.py](../../../backend/tests/test_v2_schema_gating.py)

自动回归：缺表/缺列检测及试点惰性准入。直接覆盖 errors、content_publication、question_exposure、teaching、user、v2_runtime、__init__、account_data、teaching_runs、v2_access、v2_schema、account_tasks、teaching_tasks。行为锚点：schema_ready_detects_absent_and_present_v2_tables；closed_feature_is_503_without_reading_the_grant_table；sweep_is_a_noop_without_the_v2_schema；export_omits_teaching_sections_without_the_v2_schema。

- 代码入口/类型：`test_schema_ready_detects_absent_and_present_v2_tables`、`test_closed_feature_is_503_without_reading_the_grant_table`、`test_sweep_is_a_noop_without_the_v2_schema`、`test_export_omits_teaching_sections_without_the_v2_schema`、`test_account_cleanup_is_a_noop_without_the_v2_schema`、`test_v2_table_list_matches_every_v2_model`、`test_sweep_skips_a_database_stopped_before_the_conversation_columns`、`test_conversation_columns_ready_needs_both_tables_and_columns`、`test_run_reads_answer_503_not_500_before_the_conversation_columns`。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/models/content_publication.py](../../../backend/app/models/content_publication.py)、[backend/app/models/question_exposure.py](../../../backend/app/models/question_exposure.py)、[backend/app/models/teaching.py](../../../backend/app/models/teaching.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/v2_runtime.py](../../../backend/app/models/v2_runtime.py)；其余 8 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_cache_invalidation.py](../../../backend/tests/test_video_cache_invalidation.py)

自动回归：视频详情、可播放状态及列表的共享缓存失效。直接覆盖 video_cache。行为锚点：like_drops_detail_featured_and_feed_but_not_rankings；favorite_drops_feed_but_only_weekly_favorites_ranking；view_drops_feed_but_only_weekly_views_ranking；structural_invalidation_still_clears_everything。

- 代码入口/类型：`deleted`、`detail_calls`、`test_like_drops_detail_featured_and_feed_but_not_rankings`、`test_favorite_drops_feed_but_only_weekly_favorites_ranking`、`test_view_drops_feed_but_only_weekly_views_ranking`、`test_structural_invalidation_still_clears_everything`。
- 直接依赖：[backend/app/services/video_cache.py](../../../backend/app/services/video_cache.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_classification.py](../../../backend/tests/test_video_classification.py)

自动回归：通过受控模型生成主题和 CEFR 并校验结果。直接覆盖 subtitle、video、video_classification。行为锚点：TestValidateTopics；TestValidateCefr；TestBuildPrompt；TestClassifyVideoMetadata。

- 代码入口/类型：`TestValidateTopics`、`TestValidateCefr`、`TestBuildPrompt`、`TestClassifyVideoMetadata`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/video_classification.py](../../../backend/app/services/video_classification.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_localization_pg.py](../../../backend/tests/test_video_localization_pg.py)

自动回归：视频身份、来源、状态、媒体、发布和派生指标。直接覆盖 database、security、main、pipeline_dispatch、user、video、__init__。行为锚点：concurrent_localization_claims_create_and_send_one_intent；failed_intent_insert_rolls_back_processing_claim；delayed_intent_is_abandoned_if_full_pipeline_has_taken_over。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`pg_client`、`seed`、`test_concurrent_localization_claims_create_and_send_one_intent`、`test_failed_intent_insert_rolls_back_processing_claim`、`test_delayed_intent_is_abandoned_if_full_pipeline_has_taken_over`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/main.py](../../../backend/app/main.py)、[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_media.py](../../../backend/tests/test_video_media.py)

自动回归：无事务所有权的媒体元信息、stage、下载与转码 I/O。直接覆盖 __init__、video_media。行为锚点：transcode_remuxes_without_loss_or_scales_only_when_needed；missing_or_failed_ffmpeg_never_returns_success_urls；cancellation_kills_and_reaps_child_then_propagates；unsuccessful_output_never_replaces_previous_rendition。

- 代码入口/类型：`media_config`、`Process`、`test_transcode_remuxes_without_loss_or_scales_only_when_needed`、`test_missing_or_failed_ffmpeg_never_returns_success_urls`、`test_cancellation_kills_and_reaps_child_then_propagates`、`test_unsuccessful_output_never_replaces_previous_rendition`、`test_local_artifact_validation_stays_inside_media_root`、`test_probe_timeout_kills_child_and_returns_unavailable`、`test_metadata_retry_keeps_external_fields_and_thumbnail_fallbacks`、`test_download_preserves_actual_raw_extension`（其余见机器清单）。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/video_media.py](../../../backend/app/services/video_media.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_playback.py](../../../backend/tests/test_video_playback.py)

自动回归：本地媒体/原站嵌入的可播放与可发布判定。直接覆盖 errors、redis、pipeline_dispatch、video、__init__、video_media、video_playback、video_publish、pipeline_helpers、video_processing。行为锚点：fallback_matches_only_supported_player_sources；upload_without_valid_output_cannot_complete_or_invent_url；youtube_fallback_is_playable_and_records_localization_retry；unsupported_import_without_file_never_reaches_ready。

- 代码入口/类型：`media_root`、`seed`、`artifact`、`test_fallback_matches_only_supported_player_sources`、`test_upload_without_valid_output_cannot_complete_or_invent_url`、`test_youtube_fallback_is_playable_and_records_localization_retry`、`test_unsupported_import_without_file_never_reaches_ready`、`test_resume_restores_the_real_raw_path_for_both_sources`、`test_stale_transcode_marker_requires_real_output`、`test_localization_failure_preserves_old_playable_file_and_records_attempt`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/pipeline_dispatch.py](../../../backend/app/models/pipeline_dispatch.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/pipeline_dispatch.py](../../../backend/app/services/pipeline_dispatch.py)；其余 7 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_takedown.py](../../../backend/tests/test_video_takedown.py)

自动回归：视频身份、来源、状态、媒体、发布和派生指标。直接覆盖 config、security、favorite、learning、subtitle、user、video。行为锚点：TestStorageMode；TestTakedownEffects；TestTakedownSuggestions。

- 代码入口/类型：`TestStorageMode`、`TestTakedownEffects`、`TestTakedownSuggestions`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/favorite.py](../../../backend/app/models/favorite.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_title.py](../../../backend/tests/test_video_title.py)

自动回归：显示用中文视频标题翻译，不改变原题身份。直接覆盖 __init__、video_title。行为锚点：normalize_collapses_whitespace；normalize_empty_or_missing_becomes_none；normalize_truncates_to_column_width；chinese_title_is_its_own_translation。

- 代码入口/类型：`test_normalize_collapses_whitespace`、`test_normalize_empty_or_missing_becomes_none`、`test_normalize_truncates_to_column_width`、`test_chinese_title_is_its_own_translation`、`test_translates_english_title`、`test_identical_translation_falls_back_to_source`、`test_empty_translation_returns_none`、`test_engine_failure_is_swallowed`、`test_engine_override_builds_a_dedicated_service`。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/video_title.py](../../../backend/app/services/video_title.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_unlock.py](../../../backend/tests/test_video_unlock.py)

自动回归：视频身份、来源、状态、媒体、发布和派生指标。直接覆盖 subtitle、user、video、sms_service。行为锚点：TestNoMembershipOnSignup；TestFreeDetail；TestAdminDetail；TestRetiredPaymentSurface。

- 代码入口/类型：`TestNoMembershipOnSignup`、`TestFreeDetail`、`TestAdminDetail`、`TestRetiredPaymentSurface`、`TestShadowingSentencesGate`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/sms_service.py](../../../backend/app/services/sms_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_video_url_guard.py](../../../backend/tests/test_video_url_guard.py)

自动回归：外站视频 URL 域名、私网 IP 与 DNS 稳定性检查。直接覆盖 errors、video_url_guard。行为锚点：allowed_youtube_url；allowed_bilibili_url；foreign_host_rejected；metadata_url_rejected。

- 代码入口/类型：`test_allowed_youtube_url`、`test_allowed_bilibili_url`、`test_foreign_host_rejected`、`test_metadata_url_rejected`、`test_private_ip_resolution_rejected`、`test_loopback_resolution_rejected`、`test_link_local_resolution_rejected`、`test_any_private_ip_in_set_rejected`、`test_resolve_failure_rejected`、`test_dns_rebinding_rejected`（其余见机器清单）。
- 直接依赖：[backend/app/core/errors.py](../../../backend/app/core/errors.py)、[backend/app/services/video_url_guard.py](../../../backend/app/services/video_url_guard.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_videos.py](../../../backend/tests/test_videos.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、video、__init__、video_service。行为锚点：TestPublicVideos；TestSeedVideo；TestGetVideo；TestAdminListVideos。

- 代码入口/类型：`TestPublicVideos`、`TestSeedVideo`、`TestGetVideo`、`TestAdminListVideos`、`TestAdminUpdateVideo`、`TestPublishGate`、`TestAdminDeleteVideo`、`TestAdminLocalizeVideo`、`TestAdminDemoVideoSerialization`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/video_service.py](../../../backend/app/services/video_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_videos_related.py](../../../backend/tests/test_videos_related.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 channel、video。行为锚点：TestRelatedVideos。

- 代码入口/类型：`TestRelatedVideos`。
- 直接依赖：[backend/app/models/channel.py](../../../backend/app/models/channel.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocab_celebrate.py](../../../backend/tests/test_vocab_celebrate.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、video、vocab_set。行为锚点：celebrate_requires_auth；completed_set_has_no_new_achievement；historical_set_achievement_timestamp_preserved。

- 代码入口/类型：`test_celebrate_requires_auth`、`test_completed_set_has_no_new_achievement`、`test_historical_set_achievement_timestamp_preserved`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocab_recurrence.py](../../../backend/tests/test_vocab_recurrence.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 security、learning、subtitle、user、video、recommendation_service。行为锚点：user_learning_words_returns_learning_and_reviewing；user_learning_words_empty_for_no_vocab；vocab_recurrence_boost_positive_match；vocab_recurrence_boost_no_match。

- 代码入口/类型：`test_user_learning_words_returns_learning_and_reviewing`、`test_user_learning_words_empty_for_no_vocab`、`test_vocab_recurrence_boost_positive_match`、`test_vocab_recurrence_boost_no_match`、`test_vocab_recurrence_boost_empty_vocab`、`test_vocab_recurrence_boost_multiple_videos`。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/recommendation_service.py](../../../backend/app/services/recommendation_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocab_sets.py](../../../backend/tests/test_vocab_sets.py)

自动回归：词集列表、加入学习和快速过筛操作。直接覆盖 security、learning、learning_plan、preferences、subtitle、user、video、vocab_set、__init__、ecdict。行为锚点：TestCollectSet；TestListSets；TestSetDetail；TestSieve。

- 代码入口/类型：`ecdict_only`、`TestCollectSet`、`TestListSets`、`TestSetDetail`、`TestSieve`、`TestMasteredExitsReviewQueues`、`TestUnmarkLearned`。
- 直接依赖：[backend/app/core/security.py](../../../backend/app/core/security.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/preferences.py](../../../backend/app/models/preferences.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)；其余 5 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_daily_session.py](../../../backend/tests/test_vocabulary_daily_session.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 learning。行为锚点：TestDailySession；TestDailyQuota；TestReviewPriority；TestReviewEndpoint。

- 代码入口/类型：`TestDailySession`、`TestDailyQuota`、`TestReviewPriority`、`TestReviewEndpoint`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_drill_levels.py](../../../backend/tests/test_vocabulary_drill_levels.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 learning、user、__init__、ecdict、practice_service。行为锚点：vocabulary_drill_filters_by_target_level；vocabulary_drill_falls_back_when_too_few_matches；vocabulary_drill_no_level_returns_all。

- 代码入口/类型：`test_vocabulary_drill_filters_by_target_level`、`test_vocabulary_drill_falls_back_when_too_few_matches`、`test_vocabulary_drill_no_level_returns_all`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/practice_service.py](../../../backend/app/services/practice_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_list.py](../../../backend/tests/test_vocabulary_list.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 learning。行为锚点：TestVocabularyListFilters；TestAddWordEnrichment。

- 代码入口/类型：`TestVocabularyListFilters`、`TestAddWordEnrichment`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_mastered.py](../../../backend/tests/test_vocabulary_mastered.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 learning。行为锚点：TestMarkMastered。

- 代码入口/类型：`TestMarkMastered`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_quiz.py](../../../backend/tests/test_vocabulary_quiz.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 learning、user、__init__、ecdict、practice_service。行为锚点：TestSelectDistractors；TestPosParsing；drill_builds_full_options_with_ecdict_fallback；TestSubmitPracticeResults。

- 代码入口/类型：`TestSelectDistractors`、`TestPosParsing`、`test_drill_builds_full_options_with_ecdict_fallback`、`TestSubmitPracticeResults`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)、[backend/app/services/practice_service.py](../../../backend/app/services/practice_service.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_stats.py](../../../backend/tests/test_vocabulary_stats.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 learning。行为锚点：TestVocabularyStatsDue。

- 代码入口/类型：`TestVocabularyStatsDue`。
- 直接依赖：[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_transactions.py](../../../backend/tests/test_vocabulary_transactions.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 database、learning、learning_plan、study_session、user、vocab_set、__init__、learning_event_service、local_time、milestone_service、practice_service、study_session_service、vocab_set_service、vocabulary_service。行为锚点：caller_rollback_undoes_word_event_and_profile；required_event_failure_prevents_partial_word_success；mastery_repeat_records_one_fact_and_missing_ownership_records_none；legacy_emitter_keeps_business_write_and_rolls_back_failed_projection。

- 代码入口/类型：`seed`、`fail_snapshot`、`assert_unchanged`、`test_caller_rollback_undoes_word_event_and_profile`、`test_required_event_failure_prevents_partial_word_success`、`test_mastery_repeat_records_one_fact_and_missing_ownership_records_none`、`test_legacy_emitter_keeps_business_write_and_rolls_back_failed_projection`、`test_required_emitter_rejects_invalid_or_wrong_domain_facts`、`test_training_answer_failure_rolls_back_item_round_and_word`、`test_batch_second_fact_failure_rolls_back_whole_batch`（其余见机器清单）。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/study_session.py](../../../backend/app/models/study_session.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)；其余 8 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_vocabulary_transactions_pg.py](../../../backend/tests/test_vocabulary_transactions_pg.py)

自动回归：个人词条、复习、自评、训练与观看上下文。直接覆盖 database、learning、learning_plan、study_session、user、vocab_set、__init__、local_time、practice_service、study_session_service、vocab_set_service、vocabulary_service。行为锚点：same_mastery_transition_counts_once_under_concurrency；round_answers_preserve_progress_and_count_first_answer_once；concurrent_set_closure_records_exactly_one_whole_set_fact；overlapping_batches_with_reverse_input_order_do_not_deadlock_or_lose_reviews。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`seed`、`race`、`test_same_mastery_transition_counts_once_under_concurrency`、`test_round_answers_preserve_progress_and_count_first_answer_once`、`test_concurrent_set_closure_records_exactly_one_whole_set_fact`、`test_overlapping_batches_with_reverse_input_order_do_not_deadlock_or_lose_reviews`、`test_required_review_and_learning_projection_rollback_together`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/learning_plan.py](../../../backend/app/models/learning_plan.py)、[backend/app/models/study_session.py](../../../backend/app/models/study_session.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/vocab_set.py](../../../backend/app/models/vocab_set.py)；其余 6 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_watch_baseline.py](../../../backend/tests/test_watch_baseline.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 notifications、learning、notification、subtitle、video、milestone_service、retired_features、celery_app。行为锚点：progress_clamped_and_does_not_claim_completion；save_word_uses_clicked_source_not_first_occurrence；reject_mismatched_source_without_writing；gloss_labels_hint_scope_without_new_ai。

- 代码入口/类型：`seed_source`、`test_progress_clamped_and_does_not_claim_completion`、`test_save_word_uses_clicked_source_not_first_occurrence`、`test_reject_mismatched_source_without_writing`、`test_gloss_labels_hint_scope_without_new_ai`、`test_retired_routes_auth_and_gone`、`test_hidden_notifications_and_unread_count_use_same_filter`、`test_retired_preferences_cannot_be_reenabled`、`test_retired_producers_stay_retired`、`test_old_worker_push_cannot_reintroduce_retired_badge`。
- 直接依赖：[backend/app/api/v1/notifications.py](../../../backend/app/api/v1/notifications.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/notification.py](../../../backend/app/models/notification.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/milestone_service.py](../../../backend/app/services/milestone_service.py)；其余 3 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_watch_progress_pg.py](../../../backend/tests/test_watch_progress_pg.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 database、learning、user、video、watch_progress_service。行为锚点：first_save_losing_unique_insert_still_applies_its_position；many_first_saves_have_one_record_and_consistent_percentage。需要专用 PostgreSQL；SQLite 不能证明行锁语义。

- 代码入口/类型：`test_first_save_losing_unique_insert_still_applies_its_position`、`test_many_first_saves_have_one_record_and_consistent_percentage`。
- 直接依赖：[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/models/learning.py](../../../backend/app/models/learning.py)、[backend/app/models/user.py](../../../backend/app/models/user.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/services/watch_progress_service.py](../../../backend/app/services/watch_progress_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_word_levels_column.py](../../../backend/tests/test_word_levels_column.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、types。行为锚点：column_carries_the_normalizing_type；column_ddl_is_still_plain_json；bind_writes_the_canonical_shape；empty_annotations_bind_as_null。

- 代码入口/类型：`test_column_carries_the_normalizing_type`、`test_column_ddl_is_still_plain_json`、`test_bind_writes_the_canonical_shape`、`test_empty_annotations_bind_as_null`、`test_read_normalizes_a_row_written_before_the_type_existed`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/types.py](../../../backend/app/models/types.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_word_levels_edit.py](../../../backend/tests/test_word_levels_edit.py)

自动回归：本文件列出的领域服务/接口与边界条件。直接覆盖 subtitle、video。行为锚点：TestWordLevelsUpdate；TestWordLevelsRecompute。

- 代码入口/类型：`TestWordLevelsUpdate`、`TestWordLevelsRecompute`。
- 直接依赖：[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/tests/conftest.py](../../../backend/tests/conftest.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_word_notes.py](../../../backend/tests/test_word_notes.py)

自动回归：读取最合适词注、批量预热与写入。直接覆盖 config、video、word_note、__init__、ai_service、ecdict、word_notes。行为锚点：generate_word_notes_bulk_alignment；generate_word_notes_bulk_empty_returns_empty；generate_word_notes_bulk_batches_over_15；generate_word_notes_bulk_dual_engine_fans_out。

- 代码入口/类型：`test_generate_word_notes_bulk_alignment`、`test_generate_word_notes_bulk_empty_returns_empty`、`test_generate_word_notes_bulk_batches_over_15`、`test_generate_word_notes_bulk_dual_engine_fans_out`、`test_upsert_notes_inserts_then_overwrites`、`test_get_best_note_prefers_video_specific_over_global`、`test_get_best_note_returns_none_when_missing`、`test_get_best_note_falls_back_to_surface_key_for_inflected_forms`、`test_get_best_note_priority_video_surface_beats_global_lemma`、`test_gloss_returns_preheated_db_note`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)、[backend/app/models/word_note.py](../../../backend/app/models/word_note.py)、[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ai_service.py](../../../backend/app/services/ai_service.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)；其余 2 项见机器清单。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_words_gloss.py](../../../backend/tests/test_words_gloss.py)

自动回归：点词静态词典、预生成 AI 注释和真题例句聚合。直接覆盖 __init__、ecdict。行为锚点：gloss_requires_auth；gloss_static_requires_auth；gloss_static_returns_ecdict_fields_only；gloss_returns_ecdict_static_fields。

- 代码入口/类型：`test_gloss_requires_auth`、`test_gloss_static_requires_auth`、`test_gloss_static_returns_ecdict_fields_only`、`test_gloss_returns_ecdict_static_fields`、`test_gloss_returns_empty_for_word_not_in_ecdict`、`test_target_exam_preference_roundtrip`、`test_target_exam_rejects_invalid_value`。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/ecdict.py](../../../backend/app/services/ecdict.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [backend/tests/test_youtube_cookies_service.py](../../../backend/tests/test_youtube_cookies_service.py)

自动回归：下载器 cookie 探测、隔离副本与受控刷新。直接覆盖 __init__、youtube_cookies_service。行为锚点：probe_returns_cookies_invalid_when_no_cookies_file；probe_classifies_sign_in_as_cookies_invalid；probe_other_error_classified_as_error；ensure_cookies_skips_refresh_when_probe_ok。

- 代码入口/类型：`test_probe_returns_cookies_invalid_when_no_cookies_file`、`test_probe_classifies_sign_in_as_cookies_invalid`、`test_probe_other_error_classified_as_error`、`test_ensure_cookies_skips_refresh_when_probe_ok`、`test_ensure_cookies_refreshes_then_ok`、`test_ensure_cookies_persistent_logged_out_returns_need_manual_login`、`test_ensure_cookies_refreshed_but_still_invalid_returns_need_manual_login`。
- 直接依赖：[backend/app/services/__init__.py](../../../backend/app/services/__init__.py)、[backend/app/services/youtube_cookies_service.py](../../../backend/app/services/youtube_cookies_service.py)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。
