import ast
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import slcs
from slcs import PackValidationError, fingerprint, json_schema, load_pack, load_video_material, tokenize

try:
    importlib.metadata.version("slcs")
except importlib.metadata.PackageNotFoundError:  # pragma: no cover - only in a source checkout
    # The CLI checks shell out to ``python -m slcs`` from outside the checkout, so
    # this suite is meaningful only after the built wheel is installed. CI does
    # that; a plain source checkout skips with a reason instead of failing.
    pytest.skip("install the built slcs wheel to run the standalone consistency suite", allow_module_level=True)

# The release tree ships the spec under ``spec/`` and points these variables at
# it from its conftest; inside see-word the docs live in docs/slcs.
SPEC = Path(os.environ.get("SLCS_SPEC_DIR") or Path(__file__).resolve().parents[2] / "docs" / "slcs")
EXAMPLES = Path(os.environ.get("SLCS_EXAMPLES_DIR") or SPEC / "examples")
EXAMPLE = EXAMPLES / "welcome-to-wikisource.json"
REFERENCE_DIGEST = "d06cd8fa05b10e71d0030fb2e1a5569639c561d565117df91c14057f2f355ab4"


def cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "slcs", *args],
        cwd=cwd,
        capture_output=True,
        check=False,
        encoding="utf-8",
        timeout=15,
    )


def test_schema_and_reference_fingerprint():
    pack = load_pack(EXAMPLE.read_bytes())
    assert json_schema() == json.loads((SPEC / "schema.json").read_bytes())
    assert fingerprint(pack) == REFERENCE_DIGEST
    reordered = json.dumps(json.loads(EXAMPLE.read_bytes()), sort_keys=True, indent=2)
    assert fingerprint(load_pack(reordered.encode())) == REFERENCE_DIGEST


def test_documented_reference_digest_matches():
    """The spec states the reference digest for contributors; keep one source of truth."""
    readme = (SPEC / "README.md").read_text(encoding="utf-8")
    assert readme.count(REFERENCE_DIGEST) == 1


def test_schema_and_fingerprint_commands(tmp_path):
    result = cli("schema", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == json_schema()

    fingerprint_result = cli("fingerprint", str(EXAMPLE), cwd=tmp_path)
    assert fingerprint_result.returncode == 0, fingerprint_result.stderr
    assert fingerprint_result.stdout.strip() == REFERENCE_DIGEST

    structured = cli("--json", "fingerprint", str(EXAMPLE), cwd=tmp_path)
    assert structured.returncode == 0, structured.stderr
    payload = json.loads(structured.stdout)
    assert payload == {"fingerprint_version": "slcs-pack-v1", "fingerprint": REFERENCE_DIGEST}


def test_console_script_and_offline_example(tmp_path):
    """The installed entry point and the published demo script must both work."""
    executable = Path(sys.executable).with_name("slcs" + (".exe" if sys.platform == "win32" else ""))
    result = subprocess.run(
        [str(executable), "--json", "validate", str(EXAMPLE)],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["ok"]

    demo = subprocess.run(
        [sys.executable, str(EXAMPLES / "read_example.py"), str(EXAMPLE), "public domain"],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        encoding="utf-8",
        timeout=30,
    )
    assert demo.returncode == 0, demo.stderr
    assert "s03/w04 w05" in demo.stdout
    assert "公有领域" in demo.stdout


@pytest.mark.parametrize(
    ("name", "path"),
    [
        ("unknown-version.json", "/schema_version"),
        ("missing-translation.json", "/segments/0/translation"),
        ("unknown-field.json", "/extra"),
        ("duplicate-key.json", "/"),
    ],
)
def test_public_invalid_fixtures(name, path, tmp_path):
    fixture = EXAMPLES / "invalid" / name
    with pytest.raises(PackValidationError) as caught:
        load_pack(fixture.read_bytes())
    assert caught.value.path == path
    result = cli("--json", "validate", str(fixture), cwd=tmp_path)
    assert result.returncode == 1
    assert not result.stdout
    assert json.loads(result.stderr)["diagnostics"][0]["path"] == path


def test_read_and_resolve_outside_repository(tmp_path):
    material = load_video_material(EXAMPLE.read_bytes())
    assert len(material.segments) == 12
    assert len(material.vocabulary) == 7
    assert all(segment.text and segment.translation for segment in material.segments)
    valid = cli("validate", str(EXAMPLE), "--json", cwd=tmp_path)
    assert valid.returncode == 0, valid.stderr
    assert json.loads(valid.stdout)["ok"]
    resolved = cli("resolve", str(EXAMPLE), "public domain", cwd=tmp_path)
    assert resolved.returncode == 0, resolved.stderr
    result = json.loads(resolved.stdout)
    assert result["fingerprint"] == REFERENCE_DIGEST
    (occurrence,) = result["matches"]
    assert occurrence["segment_id"] == "s03"
    assert occurrence["token_ids"] == ["w04", "w05"]
    assert (occurrence["start_ms"], occurrence["end_ms"]) == (13602, 14242)
    assert "public domain" in occurrence["sentence"]
    assert "公有领域" in occurrence["translation"]
    assert tokenize("🎬 We’re café-ready!") == ((2, 7), (8, 18))
    assert cli("validate", str(tmp_path), cwd=tmp_path).returncode == 1
    assert cli("invalid-command", cwd=tmp_path).returncode == 1
    assert cli("resolve", str(EXAMPLE), "absent headword", cwd=tmp_path).returncode == 1


def test_distribution_is_the_installed_one():
    """The published tree ships sources beside its tests; refuse to test that copy."""
    if os.environ.get("SLCS_REQUIRE_INSTALLED") != "1":
        pytest.skip("only asserted from the published tree, which sets SLCS_REQUIRE_INSTALLED")
    package = Path(slcs.__file__).resolve()
    assert "site-packages" in str(package), f"tested the source copy, not the installation: {package}"


def test_distribution_has_no_seeword_imports():
    """The installed distribution (not the checkout) must not reach into SeeWord."""
    package = Path(slcs.__file__).parent
    # The published tree keeps a copy of the sources next to its tests, so the
    # assertion is "this is not the SeeWord checkout", not "this is site-packages".
    assert SPEC.parent.name != "slcs" or "site-packages" in str(package), package
    for source in package.glob("*.py"):
        text = source.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                assert (node.module or "").split(".")[0] != "app", source
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] != "app" for alias in node.names), source
        # Dynamic imports are not visible in the AST; catch the obvious forms.
        assert "__import__(" not in text, source
        assert "importlib.import_module(" not in text or "app" not in text, source
