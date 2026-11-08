"""Offline SLCS validation and schema generation."""

import argparse
import json
import sys
from pathlib import Path

from app.slcs import PackValidationError, json_schema, load_pack


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.slcs")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a local UTF-8 learning pack")
    validate.add_argument("path", type=Path)
    commands.add_parser("schema", help="print the structural JSON Schema")
    args = parser.parse_args()
    if args.command == "schema":
        print(json.dumps(json_schema(), ensure_ascii=False, indent=2))
        return 0
    try:
        pack = load_pack(args.path.read_bytes())
    except (OSError, PackValidationError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Valid SLCS {pack.schema_version}: {pack.lesson_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
