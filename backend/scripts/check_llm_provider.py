"""Audit / smoke-test the configured LLM provider (Command Code by default).

The provider and its model catalog live in ``app/services/llm_provider.py``;
this script is the ops view of that config. Three explicit modes so a CI job
can run the offline summary without touching the network:

    cd backend && python scripts/check_llm_provider.py            # 配置摘要（不联网）
    cd backend && python scripts/check_llm_provider.py --list      # 拉 /models + 免费目录对账
    cd backend && python scripts/check_llm_provider.py --test      # 真实冒烟（聊天/JSON/翻译/首页）

Exit codes: 0 success, 1 smoke failure or catalog mismatch, 2 misconfigured
provider. Keys are always masked in the output.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Make `app` importable when run as `python scripts/check_llm_provider.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.llm_provider import (
    TASK_EDITORIAL,
    TASK_TRANSLATION,
    TASK_WORD_NOTES,
    audit_free_catalog,
    list_remote_models,
    provider_summary,
    resolve_model,
    resolve_provider,
)

TRANSLATION_SAMPLES = [
    "The future of work is already here.",
    "Many of us spend hours commuting every day.",
    "Could you speak more slowly, please?",
]


def _print_summary(summary: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    print("== LLM provider ==")
    if not summary.get("configured"):
        print(f"  未配置：{summary.get('reason')}")
        print("  在 backend/.env 设置 COMMANDCODE_API_KEY（或 OPENAI_API_KEY）后重试。")
        return
    for key in ("provider", "api", "base_url", "api_key", "model", "timeout_seconds", "zdr"):
        print(f"  {key:<16}= {summary[key]}")
    print("  == 任务 → 模型 ==")
    for task, model in summary["tasks"].items():
        print(f"  {task:<16}  {model}")
    print("  == 免费模型目录（价格页口径，2026-10-20）==")
    for model in summary["free_models"]:
        print(f"  - {model}")


async def _run_list(as_json: bool) -> int:
    provider = resolve_provider()
    if provider is None:
        print("未配置 provider，无法拉取 /models。", file=sys.stderr)
        return 2
    print(f"== GET {provider.models_url} ==")
    try:
        remote = await list_remote_models(provider)
    except Exception as exc:  # httpx errors carry enough text; keep the script simple
        print(f"拉取模型列表失败：{exc}", file=sys.stderr)
        return 1
    free = [spec for spec in remote if spec.free]
    print(f"  模型总数：{len(remote)}；免费标记：{len(free)}")
    for spec in free:
        extra = []
        if spec.context_window:
            extra.append(f"ctx={spec.context_window}")
        if spec.zdr:
            extra.append("ZDR")
        if spec.daily_limit:
            extra.append(f"日限 {spec.daily_limit}")
        print(f"  - {spec.id}  {' '.join(extra)}".rstrip())
    audit = audit_free_catalog(remote)
    if audit["missing"]:
        print("  [WARN] 目录里的免费模型已不在网关列表中（促销可能已下线，请换默认模型）：", file=sys.stderr)
        for model in audit["missing"]:
            print(f"    - {model}", file=sys.stderr)
    if audit["uncatalogued_free"]:
        print("  [INFO] 网关新增了未登记的免费模型：")
        for model in audit["uncatalogued_free"]:
            print(f"    - {model}")
    if as_json:
        print(
            json.dumps(
                {
                    "total": len(remote),
                    "free": [spec.id for spec in free],
                    "missing": audit["missing"],
                    "uncatalogued_free": audit["uncatalogued_free"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 1 if audit["missing"] else 0


async def _run_smoke() -> int:
    # Imported here so `--list` works even if the SDK/service stack is borked.
    from app.services.ai_service import AIService
    from app.services.translation import TranslationService

    failures = 0
    service = AIService()
    if service.client is None:
        print("AIService 未配置客户端（缺 COMMANDCODE_API_KEY / OPENAI_API_KEY）。", file=sys.stderr)
        return 2

    async def timed(label: str, coro) -> object | None:
        nonlocal failures
        t0 = time.monotonic()
        try:
            result = await coro
        except Exception as exc:
            failures += 1
            print(f"  [FAIL] {label}: {exc}")
            return None
        print(f"  [OK]   {label}  {time.monotonic() - t0:.1f}s")
        return result

    print("== 冒烟：AIService 普通聊天 ==")
    chat = await timed(
        f"chat_json default ({resolve_model(task='default')})",
        service.chat_json(
            'Return a JSON object with exactly one key "ok" whose value is true.',
            "Say ok.",
        ),
    )
    if isinstance(chat, dict):
        print(f"     -> {chat}")

    print("== 冒烟：AIService 词注释（JSON 对象，task=word_notes）==")
    notes = await timed(
        f"chat_json word_notes ({resolve_model(task=TASK_WORD_NOTES)})",
        service.chat_json(
            'You are an English tutor for Chinese learners. Return a JSON object {"notes": '
            '[{"word": ..., "contextual_note": ..., "pitfalls": ..., "knowledge": ...}]} '
            "with exactly one entry for the input word. Keep Chinese compact.",
            "Word: run (She runs a company)",
            task=TASK_WORD_NOTES,
        ),
    )
    if isinstance(notes, dict):
        print(f"     -> {json.dumps(notes, ensure_ascii=False)[:300]}")

    print("== 冒烟：首页编辑草稿（JSON 对象，task=editorial）==")
    draft = await timed(
        f"chat_json editorial ({resolve_model(task=TASK_EDITORIAL)})",
        service.chat_json(
            "你是英语学习站的中文编辑。根据字幕资料输出 JSON 对象，字段："
            "headline（不超过 32 字）、dek（不超过 80 字）、topic_label。只输出 JSON。",
            "资料：<subtitles>She runs a small company. I have never been to London.</subtitles>",
            task=TASK_EDITORIAL,
        ),
    )
    if isinstance(draft, dict):
        print(f"     -> {json.dumps(draft, ensure_ascii=False)[:300]}")

    print("== 冒烟：字幕翻译（TranslationService，task=translation）==")
    translator = TranslationService()
    print(f"     引擎={translator.engine_name} 批次={translator.effective_batch_size}")
    translated = await timed(
        f"translate_batch ({len(TRANSLATION_SAMPLES)} 句，模型 {resolve_model(task=TASK_TRANSLATION)})",
        translator.translate_batch(list(TRANSLATION_SAMPLES)),
    )
    if isinstance(translated, list):
        if len(translated) != len(TRANSLATION_SAMPLES) or any(item is None for item in translated):
            failures += 1
            print(f"  [FAIL] 翻译结果不完整：{translated}")
        else:
            for src, dst in zip(TRANSLATION_SAMPLES, translated, strict=True):
                print(f"     {src}\n       -> {dst}")

    if failures:
        print(f"\n冒烟失败 {failures} 项。", file=sys.stderr)
        return 1
    print("\n冒烟全部通过。")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="审查/冒烟 LLM provider（默认 Command Code）")
    parser.add_argument("--list", action="store_true", help="拉取实时 /models 并和免费模型目录对账")
    parser.add_argument("--test", action="store_true", help="真实冒烟：聊天 / 词注释 / 首页草稿 / 翻译")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出摘要与列表")
    args = parser.parse_args()

    summary = provider_summary()
    _print_summary(summary, as_json=args.json and not (args.list or args.test))
    if not summary.get("configured"):
        return 2

    code = 0
    if args.list:
        code = await _run_list(args.json)
    if args.test:
        print()
        code = max(code, await _run_smoke())
    if not args.list and not args.test:
        print("\n（未联网。加 --list 拉模型列表，加 --test 做真实冒烟。）")
    return code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
