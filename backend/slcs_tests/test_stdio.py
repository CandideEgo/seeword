import sys

import pytest

pytest.importorskip("mcp", reason="the stdio MCP adaptor needs the optional MCP dependencies")

import anyio
from mcp import Client, StdioServerParameters, stdio_client

from test_consistency import EXAMPLE


def test_stdio_reads_only_approved_segments(tmp_path):
    async def check():
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "slcs", "mcp", "--pack", str(EXAMPLE), "--segment-id", "s03"],
            cwd=str(tmp_path),
            env={"PYTHONUTF8": "1"},
        )
        with anyio.fail_after(25):
            async with Client(stdio_client(server)) as client:
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                assert set(tools) == {"get_segment", "resolve"}
                assert all("path" not in tool.input_schema.get("properties", {}) for tool in tools.values())
                resolved = await client.call_tool("resolve", {"headword": "public domain"})
                assert not resolved.is_error
                (occurrence,) = resolved.structured_content["matches"]
                assert occurrence["token_ids"] == ["w04", "w05"]
                assert occurrence["segment_id"] == "s03"
                assert (occurrence["start_ms"], occurrence["end_ms"]) == (13602, 14242)
                blocked = await client.call_tool("get_segment", {"segment_id": "s01"})
                assert blocked.structured_content == {"available": False}

    anyio.run(check)
