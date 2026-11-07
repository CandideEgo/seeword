"""Streamed tutor text: citation markers and immutable block boundaries.

The streamed reply is plain text with ``[n]`` markers (1-based indices into the
trusted source cards). Markers are stripped before anything is shown or
stored, and are validated as they arrive so an out-of-range citation stops the
turn instead of being published.

This module is pure: no database, no HTTP, no clock. Block boundaries are
deterministic (sentence terminator, or 120 characters), which keeps the stored
blocks reproducible from the same token stream.
"""

from app.core.errors import AppError

TERMINATORS = frozenset("。！？!?.;；\n")
# A partial marker is at most "[digits" -- anything longer is ordinary text.
_MARKER_PREFIX_LIMIT = 6


class CitationStream:
    def __init__(
        self, source_count: int, *, max_chars: int = 1000, block_chars: int = 120, general: bool = False
    ) -> None:
        if source_count < 0:
            raise ValueError("source_count must be non-negative")
        self.source_count = source_count
        # A task-less chat has no source list: a stray marker is dropped, not
        # treated as an out-of-range citation.
        self.general = general
        self.max_chars = max_chars
        self.block_chars = block_chars
        self._buffer = ""
        self._held = ""
        self._text = ""
        self._citations: list[int] = []

    @property
    def text(self) -> str:
        return self._text

    @property
    def citations(self) -> list[int]:
        """Distinct source numbers in first-seen order."""
        return list(self._citations)

    def feed(self, delta: str) -> list[str]:
        """Consume a model delta and return any blocks completed by it."""
        if not delta:
            return []
        text = self._held + delta
        self._held = ""
        index = 0
        while index < len(text):
            char = text[index]
            if char != "[":
                self._buffer += char
                self._text += char
                index += 1
                continue
            end = text.find("]", index + 1)
            if end == -1:
                tail = text[index:]
                if len(tail) <= _MARKER_PREFIX_LIMIT and (tail[1:] == "" or tail[1:].isdigit()):
                    self._held = tail
                    index = len(text)
                    continue
                self._buffer += char
                self._text += char
                index += 1
                continue
            token = text[index + 1 : end]
            if token.isdigit():
                number = int(token)
                if self.general:
                    index = end + 1
                    continue
                if not 1 <= number <= self.source_count:
                    raise AppError(502, "AI_SERVICE_UNAVAILABLE", "导师回复引用了不存在的来源")
                if number not in self._citations:
                    self._citations.append(number)
            else:
                literal = text[index : end + 1]
                self._buffer += literal
                self._text += literal
            index = end + 1
        if len(self._text) > self.max_chars:
            raise AppError(502, "AI_SERVICE_UNAVAILABLE", "导师回复超过长度上限")
        return self._drain()

    def finish(self) -> list[str]:
        """Flush the tail. Citation requirements are the caller's decision."""
        if self._held:
            self._buffer += self._held
            self._text += self._held
            self._held = ""
        blocks = self._drain(force=True)
        if self._buffer:
            blocks.append(self._buffer)
            self._buffer = ""
        return [block for block in blocks if block.strip()]

    def _drain(self, *, force: bool = False) -> list[str]:
        blocks: list[str] = []
        while True:
            if len(self._buffer) >= self.block_chars:
                cut = self._buffer.rfind(" ", 0, self.block_chars)
                cut = cut if cut >= 20 else self.block_chars
            elif self._buffer and self._buffer[-1] in TERMINATORS:
                cut = len(self._buffer)
            elif force and self._buffer:
                cut = len(self._buffer)
            else:
                break
            block, self._buffer = self._buffer[:cut], self._buffer[cut:]
            if block.strip():
                blocks.append(block)
        return blocks
