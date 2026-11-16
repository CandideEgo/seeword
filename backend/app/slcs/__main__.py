"""Backward-compatible entry point for the independent SLCS CLI."""

from slcs.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
