# 候选模型网关

本目录是可选 LiteLLM 网关装配，不是全站模型调用已经统一的证明。代码拓扑、默认关闭边界与消费者见 [当前框架](../../docs/project-audit/architecture.md)。镜像 digest 与治理状态的事实源是 [image-lock.json](image-lock.json)；本轮未连接真实模型或生产主机。

| 文件组 | 用途 |
| --- | --- |
| `config.synthetic.yaml`、`provider_stub.py` | 合成供应商；配根 `docker-compose.v2-gateway.yml` 做独立验证 |
| `adapter/` | 入站输出上限/断线排空、出站 usage 补偿与可选核验收据，见 [适配器说明](adapter/README.md) |
| `config.prod.template.yaml`、`render_config.py`、`entrypoint-gateway.sh` | 将运行环境渲染成真实网关配置，不把 provider key 写入版本库 |
| `bootstrap_gateway.py` | 显式创建网关 team 与预算配置；会写远端，不是只读检查 |
| `docker-compose.gateway-host.yml` | 独立主机的网关、账本 DB、Redis 和 sidecar |
| `gateway_tunnel.sh` / `.ps1` | 网关主机主动建立反向隧道；生产容器访问宿主网桥上的受限监听 |
| `synthetic.receipts.override.yaml` | 合成收据检查的可选 override，替代旧蓝图目录中的同一配置 |

## 合成验证

以下命令在根目录运行，启动独立 synthetic 项目，不能填真实凭据：

```bash
docker compose -f docker-compose.v2-gateway.yml up -d
```

```bash
docker compose -f docker-compose.v2-gateway.yml --profile check run --rm probe
```

probe 输出在本地忽略的 `tmp/gateway-probe/`。失败/未证明项仍是失败/未证明，不得为了通过而开启 `LLM_GATEWAY_GOVERNANCE_VERIFIED`。

合成栈的 adapter 绑定 loopback 14000；网络内部服务不直接公开。它不复用业务 DB/Redis。收据 override 使用 `tmp/gateway-receipts/`，需要按 compose 的多文件规则和显式独立项目名运行。

## 真实运行边界

独立主机模式使用自己的账本 DB/Redis；备份、休眠、隧道断开、未知 usage 与跨午夜结算需要分别验收。backend 经 `teaching_gateway.require_gateway` 准入；旧翻译/词注/首页生成不自动切到此网关。

真实主机、账户和密钥路径以仓库外访问说明为准，不能沿用旧文档的地址/“当时 401”当当前事实。配置模板不证明真实容量、模型质量、预算治理或部署完成。上线/迁移/预算初始化需要单独授权。
