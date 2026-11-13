"""A small offline SLCS client. Install the SLCS wheel before running it."""

import argparse
from pathlib import Path

from slcs import load_video_material, resolve_vocabulary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack", type=Path)
    parser.add_argument("headword")
    args = parser.parse_args()
    material = load_video_material(args.pack.read_bytes())
    for segment in material.segments:
        print(f"{segment.id} [{segment.start_ms}, {segment.end_ms}) ms")
        print(segment.text)
        print(segment.translation)
    for entry in resolve_vocabulary(material, args.headword):
        print(f"{entry.segment_id}/{' '.join(entry.token_ids)} [{entry.start_ms}, {entry.end_ms}) ms")
        print(f"{entry.text} — {entry.gloss}")


if __name__ == "__main__":
    main()
