"""Build the public SLCS v0.1 release tree from this repository.

The public distribution is assembled from an explicit file list instead of
copying directories wholesale, so nothing SeeWord-only (internal audit,
roadmap, handover notes, server code) can leak into the publication by
accident. Run with ``--check`` in CI-like verification, or without it to write
a fresh tree (and, with ``--wheel``, build the distributable wheel) plus a
SHA-256 manifest.

Usage::

    python scripts/build_slcs_release.py --out ../../dist/slcs-v0.1.0
    python scripts/build_slcs_release.py --out ../../dist/slcs-v0.1.0 --wheel
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
PACKAGE = BACKEND / "slcs"
SPEC = REPO / "docs" / "slcs"
PUBLIC_TESTS = BACKEND / "slcs_tests"

PACKAGE_FILES = ("__init__.py", "__main__.py", "cli.py", "contract.py", "lookup.py", "material.py", "stdio.py")
EXAMPLE_PACK = "welcome-to-wikisource.json"
INVALID_FIXTURES = ("duplicate-key.json", "missing-translation.json", "unknown-field.json", "unknown-version.json")
PRIVATE_BLOCK = re.compile(r"<!-- seeword-only:start -->.*?<!-- seeword-only:end -->\n?", re.DOTALL)

PYPROJECT = """\
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "slcs"
version = "0.1.0"
description = "Offline reader and reference validator for SLCS v0.1 learning packs"
readme = "README.md"
requires-python = ">=3.12"
license = "Apache-2.0"
license-files = ["LICENSE", "NOTICE"]
dependencies = ["pydantic==2.13.5"]

[project.optional-dependencies]
mcp = ["mcp==2.0.0"]

[project.scripts]
slcs = "slcs.cli:main"

[tool.setuptools]
packages = ["slcs"]

[tool.setuptools.package-data]
slcs = ["py.typed"]
"""

REPO_README = """\
# SLCS — Subtitle-Linked Course Specification

SLCS is a single-file JSON contract for one video, its bilingual subtitle
segments and the vocabulary that a learner can point at inside them. This
repository holds the v0.1 specification, a reference pack, the Python
reference reader, and the offline command line and stdio MCP tools built on it.

| Path        | Contents                                                       |
| ----------- | -------------------------------------------------------------- |
| `spec/`     | The v0.1 specification and the generated JSON Schema           |
| `examples/` | The Wikisource reference pack, invalid fixtures, a reader demo |
| `slcs/`     | Python reference implementation (validator, reader, CLI, MCP)  |
| `tests/`    | Consistency tests for the installed wheel                      |
| `dist/`     | Built wheel and `SHA256SUMS`                                   |

## Install

Python 3.12. On Windows set `PYTHONUTF8=1` for every process.

```sh
python -m pip install dist/slcs-0.1.0-py3-none-any.whl
slcs validate --json examples/welcome-to-wikisource.json
slcs fingerprint examples/welcome-to-wikisource.json
slcs resolve examples/welcome-to-wikisource.json "public domain"
```

Every command exits `0` on success and `1` on an argument, read, validation or
lookup error. With `--json`, failures are written to stderr as
`{"ok": false, "diagnostics": [{"path": ..., "message": ...}]}`.

The stdio MCP adaptor is an optional extra; install it in a dedicated
environment using the pinned lock:

```sh
python -m pip install -c requirements-mcp.lock 'dist/slcs-0.1.0-py3-none-any.whl[mcp]'
slcs mcp --pack examples/welcome-to-wikisource.json --segment-id s03
```

It serves only the pack and segment IDs named at startup, exposes no path
argument to the model, and leaves the model connection to the host.

## Verify an installation

```sh
python -m pytest tests -q
```

## Licenses

See [LICENSES.md](LICENSES.md): the specification text is CC BY 4.0, the
schema, code and synthetic fixtures are Apache-2.0, and the Wikisource
reference pack is CC BY-SA 4.0.
"""

GITATTRIBUTES = """\
# SHA256SUMS pins the exact bytes of every file here. Windows checkouts default
# to CRLF, which would rewrite them and break the published manifest.
* text=auto eol=lf
*.whl binary
"""

CONFTEST = '''\
"""Test the installed wheel, not the source copy that ships beside it."""

import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
# This repository ships ``slcs/`` sources next to these tests. ``python -m
# pytest`` puts the working directory on ``sys.path``, so a plain run from the
# repository root would import that copy and would verify nothing about the
# installation. Drop it from the path; the installed distribution is then the
# only ``slcs`` that can be imported.
sys.path[:] = [entry for entry in sys.path if not entry or Path(entry).resolve() != root]
# ``tests/`` is not a package here, so the stdio test imports its sibling by
# module name; keep this directory importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("SLCS_SPEC_DIR", str(root / "spec"))
os.environ.setdefault("SLCS_EXAMPLES_DIR", str(root / "examples"))
os.environ.setdefault("SLCS_REQUIRE_INSTALLED", "1")
'''

WORKFLOW = """\
name: consistency

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  consistency:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    timeout-minutes: 10
    env:
      PYTHONUTF8: "1"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install the released wheel
        shell: bash
        run: |
          python -m pip install -c requirements-mcp.lock "dist/slcs-0.1.0-py3-none-any.whl[mcp]" \\
            pytest==8.2.0 pytest-timeout==2.4.0
          python -m pip check
      - name: Verify the recorded checksums
        shell: python
        run: |
          import hashlib, pathlib, sys
          for line in pathlib.Path("SHA256SUMS").read_text(encoding="utf-8").splitlines():
              digest, name = line.split("  ", 1)
              if hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() != digest:
                  sys.exit(f"checksum mismatch: {name}")
      - name: Run the consistency suite
        run: python -m pytest tests -q
"""


def _strip_private(text: str) -> str:
    return PRIVATE_BLOCK.sub("", text)


def _relocate(text: str) -> str:
    """Point the spec's relative links at the release layout.

    Inside the repository the spec sits beside its examples; in the published
    tree the spec is under ``spec/`` and examples, licenses and the wheel are one
    level up. Only relative links are rewritten; absolute URLs are untouched.
    """
    for name in ("examples/", "LICENSES.md"):
        text = text.replace(f"]({name}", f"](../{name}")
    # Code blocks name the demo pack, the lock file and the wheel by bare name;
    # all three live one level up from ``spec/`` in the published tree, so the
    # documented commands have to work from there.
    text = text.replace("-c requirements-mcp.lock", "-c ../requirements-mcp.lock")
    text = text.replace("./slcs-0.1.0-py3-none-any.whl", "../dist/slcs-0.1.0-py3-none-any.whl")
    return re.sub(r"(?<![/\w])welcome-to-wikisource\.json", "../examples/welcome-to-wikisource.json", text)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _copy(source: Path, target: Path) -> None:
    """Copy text as LF so the published tree is byte-identical on every host.

    This checkout sets ``core.autocrlf=true``, so files that were last written
    on Windows carry CRLF while others are LF. ``shutil.copyfile`` would publish
    whichever form happened to be on this machine, and the checksums would then
    disagree with the same tree checked out on Linux — which is exactly where
    the published CI verifies them. Binary files are copied verbatim.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    if source.suffix not in {".whl", ".png", ".ico"}:
        data = data.replace(b"\r\n", b"\n")
    target.write_bytes(data)


def _checksums(root: Path) -> list[str]:
    lines = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "SHA256SUMS" or ".git" in path.parts:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    return lines


def _assert_clean_package(root: Path) -> None:
    banned = re.compile(r"^\s*(from|import)\s+app\b", re.MULTILINE)
    for path in (root / "slcs").glob("*.py"):
        if banned.search(path.read_text(encoding="utf-8")):
            raise SystemExit(f"{path} imports SeeWord server code")


def build(out: Path, *, wheel: bool) -> None:
    if out.exists():
        raise SystemExit(f"{out} already exists; remove it first so the tree is reproducible")
    out.mkdir(parents=True)

    for name in ("LICENSE", "NOTICE", "requirements-mcp.lock", "py.typed"):
        _copy(PACKAGE / name, out / name)
    for name in PACKAGE_FILES:
        _copy(PACKAGE / name, out / "slcs" / name)
    _write(out / "pyproject.toml", PYPROJECT)
    _write(out / "README.md", REPO_README)
    _write(out / ".gitattributes", GITATTRIBUTES)

    _write(
        out / "spec" / "README.md",
        _relocate(_strip_private((SPEC / "README.md").read_text(encoding="utf-8"))),
    )
    _copy(SPEC / "schema.json", out / "spec" / "schema.json")
    _copy(SPEC / "LICENSES.md", out / "LICENSES.md")
    _copy(SPEC / "examples" / EXAMPLE_PACK, out / "examples" / EXAMPLE_PACK)
    _copy(SPEC / "examples" / "read_example.py", out / "examples" / "read_example.py")
    for name in INVALID_FIXTURES:
        _copy(SPEC / "examples" / "invalid" / name, out / "examples" / "invalid" / name)

    for name in ("test_consistency.py", "test_stdio.py"):
        _copy(PUBLIC_TESTS / name, out / "tests" / name)
    _write(out / "tests" / "conftest.py", CONFTEST)
    _write(out / ".github" / "workflows" / "consistency.yml", WORKFLOW)

    _assert_clean_package(out)
    if wheel:
        # Build in a scratch copy: setuptools writes build/ and *.egg-info into
        # the source tree, and those must not end up in the published files or
        # the checksum manifest.
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "source"
            shutil.copytree(out, source)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-deps",
                    "--wheel-dir",
                    str(Path(scratch) / "wheel"),
                    str(source),
                ],
                check=True,
            )
            (built,) = (Path(scratch) / "wheel").glob("slcs-*.whl")
            _copy(built, out / "dist" / built.name)
    _write(out / "SHA256SUMS", "\n".join(_checksums(out)) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="empty output directory for the release tree")
    parser.add_argument("--wheel", action="store_true", help="also build the wheel into dist/")
    args = parser.parse_args()
    build(args.out.resolve(), wheel=args.wheel)
    print(f"release tree written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
