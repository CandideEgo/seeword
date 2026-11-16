# SLCS Python reader

This package validates v0.1 learning packs, reads their bilingual subtitles,
and resolves vocabulary occurrences to word IDs and millisecond ranges.

```sh
python -m pip install .
slcs validate --json /path/to/learning-pack.json
slcs resolve /path/to/learning-pack.json "public domain"
```

To use stdio MCP, install the optional dependencies in a dedicated Python 3.12
environment with `python -m pip install -c requirements-mcp.lock '.[mcp]'`.
Configure the host to run `slcs mcp --pack /path/to/learning-pack.json --segment-id s03`,
using the environment's executable and the segment IDs approved for the host.
The host manages its own model connection.
