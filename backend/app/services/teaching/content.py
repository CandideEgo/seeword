"""Fail-closed, automatic content qualification and shared outbound projection.

This module validates supplied evidence. It never invents a verification report
from the legacy question bank and never calls a paid model. Real publication
requires actual source snapshots and two independent blind-answer receipts.
"""

import hashlib
import json
import re
import unicodedata
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.core.errors import AppError
from app.models.exam_test import ExamPaper, ExamQuestion
from app.models.teaching import ExamAnalysisRevision, ExamEvidence
from app.services.question_exposure_service import question_key_from_identity
from app.services.teaching.principal import require_scope
from slcs.material import stable_hash as stable_hash

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.teaching.principal import Principal

NORMALIZATION_VERSION = "unicode-nfc-lf-v1"
VERIFICATION_POLICY = "automatic-consensus-v1"


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def normalized_question(payload: dict) -> dict:
    return {
        "level": payload.get("level"),
        "year": payload.get("year"),
        "month": payload.get("month"),
        "set_no": payload.get("set_no"),
        "number": payload.get("number"),
        "question_type": payload.get("question_type"),
        "passage": normalize_text(payload.get("passage") or ""),
        "question": normalize_text(payload.get("question") or ""),
        "options": {key: normalize_text(value) for key, value in sorted((payload.get("options") or {}).items())},
        "normalization_version": NORMALIZATION_VERSION,
    }


def source_fingerprint(payload: dict, answer: str) -> str:
    return stable_hash({"question": normalized_question(payload), "answer": answer.strip().upper()})


def question_key(payload: dict) -> str:
    return question_key_from_identity(
        payload["level"], payload["year"], payload["month"], payload["set_no"], payload["number"]
    )


def _invalid(message: str) -> None:
    raise AppError(422, "VALIDATION_ERROR", message)


def validate_candidate(candidate: dict) -> dict:
    try:
        return _validate_candidate(candidate)
    except (AttributeError, KeyError, TypeError, ValueError, IndexError) as exc:
        raise AppError(422, "VALIDATION_ERROR", "候选材料结构不完整或字段类型错误") from exc


def _validate_candidate(candidate: dict) -> dict:
    checked = validate_material(candidate)
    payload, answer = checked["question_payload"], checked["correct_answer"]
    report = candidate["verification_report"]
    families: set[str] = set()
    blind_input_hash = stable_hash(payload)
    for blind in report.get("blind_answers") or []:
        order = blind.get("option_order") or []
        if sorted(order) != list("ABCD") or not isinstance(blind.get("selected_position"), int):
            _invalid("盲答必须记录选项重排映射")
        position = blind["selected_position"]
        if not 0 <= position < 4 or order[position] != answer or blind.get("input_sha256") != blind_input_hash:
            _invalid("盲答与来源答案不一致")
        if not blind.get("provider_attempt_id") or not blind.get("model_family") or not blind.get("model"):
            _invalid("缺少真实盲答调用收据")
        families.add(blind["model_family"])
    if len(families) < 2:
        _invalid("需要两个不同模型族的独立盲答")
    teaching_fingerprint = stable_hash(teaching_review_input(candidate))
    checking_families: set[str] = set()
    required_checks = {"evidence_entails_answer", "distractors_supported", "hints_non_revealing", "one_correct_option"}
    for check in report.get("teaching_checks") or []:
        checks = check.get("checks") or {}
        if (
            check.get("input_sha256") != teaching_fingerprint
            or set(checks) != required_checks
            or any(value is not True for value in checks.values())
            or not check.get("provider_attempt_id")
            or not check.get("model")
            or not check.get("model_family")
        ):
            _invalid("教学内容未通过独立语义复核")
        checking_families.add(check["model_family"])
    if len(checking_families) < 2:
        _invalid("分层提示、干扰项解释和证据需要两个模型族复核")
    return checked


def teaching_review_input(candidate: dict) -> dict:
    """One canonical input for collection and publication hashing."""
    return {
        "question": normalized_question(candidate["question_payload"]),
        "correct_answer": candidate["correct_answer"].strip().upper(),
        "option_analyses": candidate["option_analyses"],
        "hints": candidate["reviewed_hints"],
        "analysis": candidate["analysis_payload"],
        "evidence": candidate.get("evidence"),
    }


def validate_material(candidate: dict) -> dict:
    """Pre-model structure/source checks, never a publication proof."""
    try:
        qid = candidate.get("question_id")
        if qid is not None and (not isinstance(qid, str) or not 1 <= len(qid) <= 36):
            raise ValueError("invalid question id")
        return _validate_material(candidate)
    except (AttributeError, KeyError, TypeError, ValueError, IndexError) as exc:
        raise AppError(422, "VALIDATION_ERROR", "候选材料结构不完整或字段类型错误") from exc


def _validate_material(candidate: dict) -> dict:
    """Validate a trusted importer artifact, returning a reproducible report.

    Source entries contain the actual extracted question/answer snapshot and a
    digest of that snapshot, plus a digest/address of the source artifact. A
    checkbox such as ``verified=true`` is deliberately insufficient.
    """
    payload = normalized_question(candidate.get("question_payload") or {})
    answer = str(candidate.get("correct_answer") or "").strip().upper()
    if payload["level"] != "cet4" or payload["question_type"] != "reading":
        _invalid("首批内容仅支持四级仔细阅读客观题")
    if not all(
        isinstance(payload[k], int) and not isinstance(payload[k], bool) for k in ("year", "month", "set_no", "number")
    ):
        _invalid("卷身份必须完整")
    if not (
        2000 <= payload["year"] <= 2100
        and 1 <= payload["month"] <= 12
        and 1 <= payload["set_no"] <= 3
        and 46 <= payload["number"] <= 55
    ):
        _invalid("卷身份或题号无效")
    options = payload["options"]
    if set(options) != set("ABCD") or any(not value for value in options.values()) or len(set(options.values())) != 4:
        _invalid("必须有四个完整且不同的选项")
    if answer not in options or not payload["passage"] or not payload["question"]:
        _invalid("题面或标准答案不完整")
    if (
        len(payload["passage"]) > 10000
        or len(payload["question"]) > 1000
        or any(len(v) > 1000 for v in options.values())
    ):
        _invalid("题面超过首版卡片体积限制")
    analyses = candidate.get("option_analyses") or {}
    hints = candidate.get("reviewed_hints") or []
    analysis_body = candidate.get("analysis_payload") or {}
    if (
        set(analysis_body) != {"summary"}
        or not isinstance(analysis_body["summary"], str)
        or not analysis_body["summary"].strip()
    ):
        _invalid("解析必须提供固定结构的 summary")
    if set(analyses) != set(options) or any(not isinstance(v, str) or not v.strip() for v in analyses.values()):
        _invalid("全部选项都必须有解释")
    if not candidate.get("learning_objectives") or not candidate.get("analysis_payload") or not 1 <= len(hints) <= 3:
        _invalid("考点、解析与分层提示不完整")
    body_text = json.dumps([analyses, hints, candidate.get("analysis_payload")], ensure_ascii=False)
    if len(body_text.encode()) > 14000 or re.search(
        r"这里是第\d+题|解析\.\.\.|TODO|待补充|<script|javascript:", body_text, re.I
    ):
        _invalid("占位解析、脚本或过大内容不得发布")
    for hint in hints:
        if not isinstance(hint, str) or not hint.strip() or options[answer].casefold() in hint.casefold():
            _invalid("提示不能直接包含完整正确选项")
        if re.search(r"(?:答案|answer|选项|option)\s*(?:是|为|is|:|：)?\s*[ABCD]\b", hint, re.I):
            _invalid("提示不能直接揭晓答案")
    rights = candidate.get("rights_policy") or {}
    for key in ("site_display", "model_processing", "external_redistribution"):
        if not isinstance(rights.get(key), bool):
            _invalid("必须分别声明三档材料使用范围")
    if (
        not rights["site_display"]
        or not rights.get("evidence_uri")
        or not re.fullmatch(r"[a-f0-9]{64}", rights.get("evidence_sha256", ""))
    ):
        _invalid("缺少可核验的站内使用权利依据")
    report = candidate.get("verification_report") or {}
    if report.get("policy_version") != VERIFICATION_POLICY:
        _invalid("未知的自动核验策略版本")
    fingerprint = source_fingerprint(payload, answer)
    answer_groups: set[str] = set()
    has_paper = False
    for source in report.get("sources") or []:
        snapshot = source.get("question_payload") or {}
        if normalized_question(snapshot) != payload:
            _invalid("来源题面不一致，不能仅按卷号合并")
        if not source.get("uri") or not re.fullmatch(r"[a-f0-9]{64}", source.get("artifact_sha256", "")):
            _invalid("来源必须有地址与原件指纹")
        source_answer = source.get("answer")
        if source.get("snapshot_sha256") != stable_hash(
            {"question": normalized_question(snapshot), "answer": source_answer}
        ):
            _invalid("来源快照校验失败")
        if source.get("kind") == "paper":
            has_paper = True
        if source.get("kind") == "answer":
            if source_answer != answer or not source.get("independent_group"):
                _invalid("独立来源标准答案冲突")
            answer_groups.add(source["independent_group"])
    if not has_paper or len(answer_groups) < 2:
        _invalid("需要原卷题面及至少两个独立答案来源")
    evidence = candidate.get("evidence") or []
    if not evidence:
        _invalid("缺少原文证据")
    for span in evidence:
        start, end = span.get("start"), span.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(payload["passage"]):
            _invalid("证据区间越界")
        quote = payload["passage"][start:end]
        if span.get("quote") != quote or span.get("quote_hash") != hashlib.sha256(quote.encode()).hexdigest():
            _invalid("证据摘录指纹不匹配")
    return {
        "question_payload": payload,
        "correct_answer": answer,
        "source_fingerprint": fingerprint,
        "question_key": question_key(payload),
    }


async def publish_revision(
    db: "AsyncSession",
    candidate: dict,
    *,
    verify_receipt: Callable[[dict], Awaitable[bool]] | None = None,
) -> ExamAnalysisRevision:
    """Internal importer only: do not expose a user-supplied verification API."""
    checked = validate_candidate(candidate)
    if verify_receipt is None:
        raise AppError(503, "SERVICE_UNAVAILABLE", "真实网关核验收据验证器尚未接入，内容保持未发布")
    for receipt in [
        *candidate["verification_report"]["blind_answers"],
        *candidate["verification_report"]["teaching_checks"],
    ]:
        if not await verify_receipt(receipt):
            _invalid("盲答收据无法在模型网关验证")
    qid = candidate.get("question_id")
    if not qid:
        raise AppError(422, "VALIDATION_ERROR", "发布必须绑定当前题库题目")
    if qid:
        await db.execute(
            select(ExamQuestion.id, ExamPaper.id)
            .join(ExamPaper, ExamPaper.id == ExamQuestion.paper_id)
            .where(ExamQuestion.id == qid)
            .with_for_update(of=[ExamQuestion.id, ExamPaper.id])
        )
        # Check after locking: an importer may have committed while we waited.
        current = await _current_payload(db, qid)
        if current is None or source_fingerprint(*current) != checked["source_fingerprint"]:
            raise AppError(409, "CONTENT_REVISION_MISMATCH", "题库来源与核验内容不匹配")
    latest = await db.scalar(
        select(func.max(ExamAnalysisRevision.revision_no)).where(
            ExamAnalysisRevision.question_key == checked["question_key"]
        )
    )
    revision = ExamAnalysisRevision(
        **checked,
        question_id=qid,
        revision_no=(latest or 0) + 1,
        normalization_version=NORMALIZATION_VERSION,
        learning_objectives=candidate["learning_objectives"],
        option_analyses=candidate["option_analyses"],
        reviewed_hints=candidate["reviewed_hints"],
        analysis_payload=candidate["analysis_payload"],
        rights_policy=candidate["rights_policy"],
        verification_report=candidate["verification_report"],
        verification_method="automatic_consensus",
        status="auto_verified",
    )
    db.add(revision)
    await db.flush()
    for span in candidate["evidence"]:
        db.add(
            ExamEvidence(
                revision_id=revision.id,
                material_key=revision.question_key,
                source_revision=revision.source_fingerprint,
                start=span["start"],
                end=span["end"],
                quote_hash=span["quote_hash"],
                kind=span.get("kind", "answer_support"),
            )
        )
    await db.flush()
    return revision


async def _current_payload(db: "AsyncSession", question_id: str) -> tuple[dict, str] | None:
    row = (
        await db.execute(
            select(ExamQuestion, ExamPaper)
            .join(ExamPaper, ExamPaper.id == ExamQuestion.paper_id)
            .where(ExamQuestion.id == question_id)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        return None
    q, p = row
    return {
        "level": p.level,
        "year": p.year,
        "month": p.month,
        "set_no": p.set_no,
        "number": q.number,
        "question_type": q.question_type,
        "passage": q.passage,
        "question": q.question,
        "options": q.options,
    }, q.answer


async def current_revision_available(db: "AsyncSession", revision: ExamAnalysisRevision) -> bool:
    if revision.status != "auto_verified" or not revision.question_id:
        return False
    current = await _current_payload(db, revision.question_id)
    return current is not None and source_fingerprint(*current) == revision.source_fingerprint


def may_disclose(revision: ExamAnalysisRevision, principal: "Principal", target: str) -> bool:
    permission = {"site": "site_display", "model": "model_processing", "external": "external_redistribution"}.get(
        target
    )
    if permission is None or revision.rights_policy.get(permission) is not True:
        return False
    return revision.status == "auto_verified"


async def project_content(
    db: "AsyncSession", revision: ExamAnalysisRevision, principal: "Principal", *, disclosed=False, target="site"
) -> dict:
    """Current rights intersect disclosure and current external scopes on every read."""
    require_scope(principal, "teaching:read")
    if not may_disclose(revision, principal, target):
        return {"restricted": True, "code": "CONTENT_RESTRICTED"}
    payload = revision.question_payload
    result = {
        "question_key": revision.question_key,
        "question_type": payload["question_type"],
        "passage": payload["passage"],
        "question": payload["question"],
        "options": payload["options"],
        "source_url": "/practice/exams",
    }
    analysis_scope = principal.actor != "external_agent" or "teaching:analysis:read" in principal.granted_scopes
    if disclosed and analysis_scope:
        result.update(
            correct_answer=revision.correct_answer,
            option_analyses=revision.option_analyses,
            analysis=revision.analysis_payload,
        )
        evidence = (
            await db.execute(
                select(ExamEvidence).where(ExamEvidence.revision_id == revision.id).order_by(ExamEvidence.start)
            )
        ).scalars()
        result["quotes"] = [
            {"start": e.start, "end": e.end, "quote": payload["passage"][e.start : e.end]} for e in evidence
        ]
    return result
