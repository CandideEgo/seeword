"""Pure, deterministic review diff for validated immutable SLCS packs.

Segment/token identities are scoped exactly as the pack anchors are; vocabulary
has no ID in v0.1, so its stable identity is its segment + ordered token span.
Paths name stable keys, never list offsets. No persistence, authorization or IO.
"""

from copy import deepcopy


def _pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def diff_lesson_packs(before: dict, after: dict) -> dict:
    changes: list[dict] = []

    def emit(category, path, old, new, kind="modified"):
        if old != new:
            changes.append(
                {"category": category, "kind": kind, "path": path, "before": deepcopy(old), "after": deepcopy(new)}
            )

    def fields(category, path, old, new):
        for key in sorted(old.keys() | new.keys()):
            left, right = old.get(key), new.get(key)
            if isinstance(left, dict) and isinstance(right, dict):
                fields(category, f"{path}/{_pointer(key)}", left, right)
            else:
                emit(category, f"{path}/{_pointer(key)}", left, right)

    def keyed(category, path, old_items, new_items, key, compare):
        old = {key(item): item for item in old_items}
        new = {key(item): item for item in new_items}
        for identity in sorted(old.keys() | new.keys()):
            item_path = f"{path}/{_pointer(identity)}"
            if identity not in old:
                emit(category, item_path, None, new[identity], "added")
            elif identity not in new:
                emit(category, item_path, old[identity], None, "removed")
            else:
                compare(item_path, old[identity], new[identity])
        emit(category, f"{path}/@order", list(map(key, old_items)), list(map(key, new_items)))

    def tokens(segment):
        # Character offsets alone can remain unchanged while the anchored word
        # changes. Include the resolved word so that this impact is inspectable.
        return [
            {**token, "text": segment["text"][token["start_char"] : token["end_char"]]} for token in segment["tokens"]
        ]

    def segment(path, old, new):
        for field, category in (
            ("text", "original"),
            ("translation", "translation"),
            ("start_ms", "timing"),
            ("end_ms", "timing"),
            ("speaker", "metadata"),
        ):
            emit(category, f"{path}/{field}", old.get(field), new.get(field))
        keyed("anchors", f"{path}/tokens", tokens(old), tokens(new), lambda item: item["id"], token)

    def token(path, old, new):
        for field in ("start_char", "end_char", "text", "timing"):
            emit("timing" if field == "timing" else "anchors", f"{path}/{field}", old.get(field), new.get(field))

    fields(
        "metadata",
        "",
        {key: value for key, value in before.items() if key not in {"segments", "vocabulary", "media", "provenance"}},
        {key: value for key, value in after.items() if key not in {"segments", "vocabulary", "media", "provenance"}},
    )
    fields("media", "/media", before["media"], after["media"])
    fields("provenance", "/provenance", before["provenance"], after["provenance"])
    keyed("segments", "/segments", before["segments"], after["segments"], lambda item: item["id"], segment)
    keyed(
        "vocabulary",
        "/vocabulary",
        before["vocabulary"],
        after["vocabulary"],
        lambda item: item["segment_id"] + ":" + ",".join(item["token_ids"]),
        lambda path, old, new: fields("vocabulary", path, old, new),
    )
    return {"impacts": sorted({change["category"] for change in changes}), "changes": changes}
