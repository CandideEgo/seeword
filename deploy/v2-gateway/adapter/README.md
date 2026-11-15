# 网关薄适配器

两个无状态 FastAPI 入口由 `app.py` 提供；账本、预算与供应商 key 属于 LiteLLM，不在业务后端复制。

```text
backend → app（入站）→ LiteLLM → shim_app（出站）→ provider
```

- 入站要求请求 `max_tokens` 不超过配置上限；SSE 增量转发。客户端断开后排空上游，让网关有机会结算。进程崩溃不在此保证内。
- 出站在供应商缺少结构化 usage 时补保守估算；已有 usage 不重新估算。估算不是供应商实际账单，错误 usage 仍需对账。
- `CONTENT_RECEIPTS_ENABLED` 默认关闭；`content_receipts.py` 固定核验提示、严格解析、签发 Ed25519 收据。不接受调用者自带 verified/model_family/任意提示冒充核验。
- 收据绑定输入摘要、kind/prompt_version、实际响应 model、模型族、结果与调用标识；签名不证明版权、内容质量、模型族独立性或实际付款。
- 具体环境名/默认值认 `app.py`、`content_receipts.py` 和上级 Compose；模型上限映射 `ADAPTER_MODEL_OUTPUT_CAPS` 不能靠放宽来增加能力。

## 运行与密钥

`Dockerfile` 使用专用非 root Python 镜像；`requirements-runtime.txt` 是运行依赖，`requirements.txt` 补测试依赖。它们不是完整传递锁，不宣称供应链全闭包已固定。

签发私钥仅挂入 adapter，后端仅持公钥；不与登录 JWT 或课程发布签名混用。模型身份映射必须有真实依据，不能改名制造两个模型族。先加新公钥，再换签发 key/kid；移除旧公钥不会自动撤回已发布内容，撤回仍走业务操作。

## 验证

工作目录 `backend/`，不连真实 provider/DB：

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m pytest ../deploy/v2-gateway/adapter/test_adapter.py ../deploy/v2-gateway/adapter/test_content_receipts.py -q
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe ../deploy/v2-gateway/adapter/check_receipts_http.py --backend-verifier app/services/teaching/content_receipts.py
```

第二条启动 loopback 合成 HTTP 链路和临时密钥，不开放业务功能。全链路治理验收另认 [上级说明](../README.md)，不继承已删除历史报告的通过结论。
