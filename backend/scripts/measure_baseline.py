#!/usr/bin/env python
"""可复现的性能与留存基线（A12）。

一次命令拿到管理端同一套口径的数字，便于在改动前后用**同样的输入**对比：

    python backend/scripts/measure_baseline.py --days 7
    python backend/scripts/measure_baseline.py --days 7 --base-url http://localhost:8000 --json

数据来源：

- **RUM / 首播 / 管线积压**：直接读库（与 ``/admin/metrics/learning`` 同一个
  ``measurement_service``，不另写一套 SQL）。
- **API p95**：可选，从后端 Prometheus 暴露的
  ``http_request_duration_seconds_bucket`` 近似计算（直方图桶的线性插值，
  不是精确分位；没有 ``--base-url`` 就不出这一项，不拿 0 冒充）。

样本量、口径定义与生效版本始终随结果一起输出；样本不足时如实标注。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _prometheus_api_p95(base_url: str, metric: str = "http_request_duration_seconds") -> dict[str, float | int | None]:
    """从 Prometheus 客户端端点近似 p95（跨标签求和后线性插值）。"""
    url = f"{base_url.rstrip('/')}/metrics"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            text = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as exc:
        return {"error": f"{url} 不可读：{exc}", "p95_s": None, "samples": 0}

    buckets: dict[float, float] = {}
    count = 0.0
    for line in text.splitlines():
        if line.startswith("#") or " " not in line:
            continue
        name, _, rest = line.partition(" ")
        value_text = rest.strip().split(" ")[0]
        try:
            value = float(value_text)
        except ValueError:
            continue
        if name.startswith(f"{metric}_bucket"):
            le = name.split('le="', 1)[-1].rstrip('"}')
            if le == "+Inf":
                count = max(count, value)
            else:
                try:
                    buckets[float(le)] = buckets.get(float(le), 0.0) + value
                except ValueError:
                    continue
        elif name == f"{metric}_count":
            count = max(count, value)

    if not buckets or count <= 0:
        return {"error": f"{metric} 没有直方图样本", "p95_s": None, "samples": 0}

    target = 0.95 * count
    previous_le = 0.0
    previous_cumulative = 0.0
    for le in sorted(buckets):
        cumulative = buckets[le]
        if cumulative >= target:
            span = cumulative - previous_cumulative
            fraction = (target - previous_cumulative) / span if span > 0 else 0.0
            return {
                "p95_s": round(previous_le + (le - previous_le) * fraction, 4),
                "samples": int(count),
            }
        previous_le, previous_cumulative = le, cumulative
    return {"p95_s": None, "samples": int(count)}


def _print_human(payload: dict) -> None:
    print(f"窗口：近 {payload['days']} 天 · 口径版本 {payload['definitions']['version']}")
    performance = payload["performance"]
    print("\n[RUM] 后端 p75（最近秩法，样本 <20 仅参考）")
    for metric, sample in performance["web_vitals"].items():
        print(f"  {metric.upper():<4} p75={sample['p75']} n={sample['samples']}")
    print(f"  首播 p75={performance['first_play']['p75_ms']} ms n={performance['first_play']['samples']}")
    backlog = performance["pipeline_backlog"]
    print(f"  管线待派发={backlog['pending_dispatches']} 最久={backlog['oldest_pending_age_s']}s")
    api = payload.get("api")
    if api:
        if api.get("p95_s") is None:
            print(f"  API p95：{api.get('error', '无样本')}")
        else:
            print(f"  API p95≈{api['p95_s']}s（直方图近似，样本 {api['samples']}）")

    activation = payload["activation"]
    print("\n[激活/留存] 分母固定为入组人数")
    print(f"  24h 激活率={activation['rate']} ({activation['activated_within_24h']}/{activation['window_registered']})")
    print(f"  近 7 日活跃={payload['weekly']['active_7d']} 至少 2 天={payload['weekly']['multi_day_7d']}")

    flows = payload["event_quality"]["flows"]
    if flows:
        print("\n[事件对账] 客户端意图 vs 服务端事实")
        for flow in flows:
            print(
                f"  {flow['path']:<10} client={flow['client_distinct_flows']} "
                f"server={flow['server_facts']} loss={flow['loss_rate']} dup={flow['duplicate_intents']}"
            )
    else:
        print("\n[事件对账] 窗口内没有带 flow_id 的流程")


async def _collect(days: int) -> dict:
    from app.core.database import get_async_session_maker
    from app.services.measurement_service import learning_metrics

    async with get_async_session_maker()() as db:
        return await learning_metrics(db, days=days)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="可复现的学习/性能基线")
    parser.add_argument("--days", type=int, default=7, choices=range(7, 91), metavar="[7-90]")
    parser.add_argument("--base-url", help="后端地址，例如 http://localhost:8000；给出时附 API p95")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON（含口径定义）")
    args = parser.parse_args(argv)

    payload = asyncio.run(_collect(args.days))
    if args.base_url:
        payload["api"] = _prometheus_api_p95(args.base_url)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(payload)

    # 「基线可复现」的最低要求：有样本。全空时明确提示，不把空库当基线。
    performance = payload["performance"]
    has_samples = any(s["samples"] > 0 for s in performance["web_vitals"].values()) or (
        performance["first_play"]["samples"] > 0
    )
    if not has_samples:
        print("\n提示：RUM 样本为 0（新埋点尚未放量或窗口内没有访问）。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
