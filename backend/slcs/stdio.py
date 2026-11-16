"""Read-only stdio MCP adapter for one explicitly selected pack."""

from pathlib import Path

from .contract import FINGERPRINT_VERSION, PackValidationError
from .lookup import lookup
from .material import load_video_material


def serve(pack: Path, segment_ids: set[str]) -> None:
    try:
        from mcp.server import MCPServer
        from mcp.types import ToolAnnotations
    except ModuleNotFoundError:
        raise PackValidationError("/", "install the optional MCP dependencies to use stdio") from None

    material = load_video_material(pack.read_bytes())
    selected = {segment.id: segment for segment in material.segments if segment.id in segment_ids}
    if not selected or selected.keys() != segment_ids:
        raise PackValidationError("/segment_id", "select one or more segment IDs from the chosen pack")

    server = MCPServer("SLCS")
    # Keyword names must be the pydantic FIELD names (snake_case). The model
    # also accepts the camelCase wire aliases at runtime (populate_by_name), but
    # mypy only sees the field names — camelCase is a `call-arg` type error, and
    # `mypy app/` reaches this file through app/slcs/__main__ → slcs.cli.
    readonly = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)

    @server.tool(annotations=readonly)
    def resolve(headword: str) -> dict[str, object]:
        """Find the word in the approved subtitle segments of the selected pack."""
        return lookup(material, headword, segment_ids)

    @server.tool(annotations=readonly)
    def get_segment(segment_id: str) -> dict[str, object]:
        """Read the bilingual original sentence for an approved segment ID."""
        segment = selected.get(segment_id)
        if segment is None:
            return {"available": False}
        return {
            "available": True,
            "lesson_id": material.lesson_id,
            "fingerprint_version": FINGERPRINT_VERSION,
            "fingerprint": material.source_fingerprint,
            "segment_id": segment.id,
            "sentence": segment.text,
            "translation": segment.translation,
            "start_ms": segment.start_ms,
            "end_ms": segment.end_ms,
        }

    server.run(transport="stdio")
