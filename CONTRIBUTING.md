# Contributing to HostPulse

Thanks for helping. Keep changes small and testable.

## Before you code

1. Read the [README](README.md) quickstart.
2. Skim the architecture graph: [`docs/graphify/`](docs/graphify/) — especially god nodes in `GRAPH_REPORT.md`.
3. If you use an AI coding agent in a **fork**, point it at `docs/graphify/` (see that folder’s README) so it shares the same map as upstream.

## Dev loop

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
ruff check bin tests
```

Windows EXE smoke: `.\scripts\verify_local.ps1` (optional `-BuildExe`).

## PR norms

- Commits and PR titles in **English**
- Prefer extending `bin/plat.py` for OS-specific probes — keep `engine.py` portable
- Report / schema changes: update [`docs/SCHEMA.md`](docs/SCHEMA.md) when the JSON contract moves

## License

By contributing you agree your work is MIT-licensed like the rest of the project.
