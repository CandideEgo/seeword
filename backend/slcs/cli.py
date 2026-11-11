"""Offline SLCS command line interface."""

import argparse
import json
import sys
from pathlib import Path
from typing import Never

from .contract import FINGERPRINT_VERSION, PackValidationError, json_schema, load_pack
from .lookup import lookup
from .material import fingerprint, load_video_material


class CommandError(ValueError):
    """Invalid command-line arguments."""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise CommandError(message)


def _parser() -> Parser:
    parser = Parser(prog="slcs")
    parser.add_argument("--json", action="store_true", help="output JSON diagnostics and results")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, description in (
        ("validate", "validate a local UTF-8 learning pack"),
        ("schema", "print the structural JSON Schema"),
        ("fingerprint", "print the canonical content fingerprint"),
        ("resolve", "find all occurrences of a headword"),
        ("mcp", "serve a selected pack over stdio MCP"),
    ):
        command = commands.add_parser(name, help=description)
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        if name in {"validate", "fingerprint", "resolve"}:
            command.add_argument("path", type=Path)
        if name == "resolve":
            command.add_argument("headword")
        if name == "mcp":
            command.add_argument("--pack", required=True, type=Path)
            command.add_argument("--segment-id", action="append", required=True)
    return parser


def _print_json(value: object, *, error: bool = False) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2), file=sys.stderr if error else sys.stdout)


def _error(path: str, message: str, structured: bool) -> int:
    if structured:
        _print_json({"ok": False, "diagnostics": [{"path": path, "message": message}]}, error=True)
    else:
        print(f"{path}: {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        args = _parser().parse_args(arguments)
    except CommandError as exc:
        return _error("/", str(exc), "--json" in arguments)

    try:
        if args.command == "schema":
            _print_json(json_schema())
        elif args.command == "mcp":
            from .stdio import serve

            serve(args.pack, set(args.segment_id))
        else:
            payload = args.path.read_bytes()
            if args.command == "resolve":
                result = lookup(load_video_material(payload), args.headword)
                if not result["matches"]:
                    return _error("/headword", "no matching vocabulary occurrence", args.json)
                _print_json(result)
            else:
                pack = load_pack(payload)
                if args.command == "validate":
                    if args.json:
                        _print_json({"ok": True, "schema_version": pack.schema_version, "lesson_id": pack.lesson_id})
                    else:
                        print(f"Valid SLCS {pack.schema_version}: {pack.lesson_id}")
                else:
                    digest = fingerprint(pack)
                    if args.json:
                        _print_json({"fingerprint_version": FINGERPRINT_VERSION, "fingerprint": digest})
                    else:
                        print(digest)
    except PackValidationError as exc:
        return _error(exc.path, exc.message, args.json)
    except (OSError, CommandError) as exc:
        return _error("/", str(exc), args.json)
    return 0
