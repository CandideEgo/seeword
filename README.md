# SeeWord

视频双语字幕点读、词汇复习与试卷学习站；支持固定修订课程包及实验性的受控第三方学习接口。

## 当前边界

- **根代码许可尚未转换，对外贡献接收尚未开放。** 大纲选择的 AGPL-3.0-only 与 DCO 1.1 是待实施方向，不是已经生效的授权；以当前 [LICENSE](LICENSE) 为准。独立 SLCS 包保留自己的许可。
- P1–P5 本地工程不等于 P0 或任何阶段正式验收通过。权利核对、真实听校、学习者及独立接入者证据仍需分别验收。
- 登录用户免费；不恢复会员收费、解锁额度或已退役功能。源码不附官方语料、私人词典、签名私钥或生产配置。

## 入口

- [自托管安装与升级](docs/self-hosting.md)：无模型 production 基础配置、账号首建、课程发布、生命周期 worker 与独立 beat、localhost smoke。
- [项目审计](docs/project-audit/README.md) 与 [架构](docs/project-audit/architecture.md)：当前框架及服务边界。
- [开发大纲](docs/seeword-open-source-development-outline-2026-11-13.md) 与 [P0 工作记录](docs/open-learning/p0-worklog.md)：本轮实施授权及尚未通过的验收门。
- [实验性学习接口](docs/open-learning/api.md)：固定引用、窄授权、本人确认及 REST/MCP 参考调用。
- [SLCS 说明](docs/slcs/README.md)：课程包格式、指纹与独立读取器。
- [贡献准备规则](CONTRIBUTING.md)：代码与内容分域、DCO 预备流程；尚未开放接收。

本地开发使用 Python 3.12、Next.js 16 / React 19。根目录没有 package.json；后端与前端分别遵守 [后端规则](backend/CLAUDE.md)、[前端规则](frontend/CLAUDE.md)。
