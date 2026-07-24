# HostPulse architecture graph (graphify)

This folder is the **checked-in knowledge map** of the HostPulse repository. It is for:

- **Contributors** — onboard faster (modules, call paths, communities)
- **Coding agents / AI in forks** — query architecture without re-reading the whole tree

Generated with [graphify](https://github.com/safishamsi/graphify) (`graphifyy`). Local caches stay in gitignored `graphify-out/`; **this `docs/graphify/` copy is the shared source of truth for humans and agents.**

## Contents

| File | Purpose |
|------|---------|
| [`GRAPH_REPORT.md`](GRAPH_REPORT.md) | Audit report: communities, god nodes, suggested questions |
| [`graph.json`](graph.json) | Full graph (nodes/edges) — GraphRAG / agent tools |
| [`graph.html`](graph.html) | Interactive visualization (open in a browser) |
| [`labels.json`](labels.json) | Community id → human label |

## For contributors

1. Skim **God Nodes** and community labels in `GRAPH_REPORT.md`.
2. Open `graph.html` locally when exploring unfamiliar areas.
3. Prefer changing code along existing communities (engine / reporter / plat / orchestrator) instead of inventing parallel paths.
4. After large structural changes (new package layout, major adapters), rebuild the graph and refresh this folder (see below).

## For AI agents (including forks)

**Before exploring the codebase for architecture questions**, prefer this graph:

1. Read `docs/graphify/GRAPH_REPORT.md` (god nodes + communities).
2. If `graphify` CLI is available and a local `graphify-out/graph.json` exists, run:
   ```bash
   graphify query "How does the GUI start an audit and produce HTML?"
   graphify path "HostPulseEngine" "ReportGenerator"
   ```
3. Otherwise load `docs/graphify/graph.json` and answer from nodes/edges (`source_file`, relations `calls` / `references` / `conceptually_related_to`).
4. Treat `EXTRACTED` edges as ground truth; treat `INFERRED` / `AMBIGUOUS` as hypotheses to verify in source.
5. Do **not** invent imports or call edges that are not in the graph or the files.

Suggested starter questions (also listed in the report):

- How do GUI and CLI share `run_audit`?
- Where do Windows-only APIs live relative to `plat`?
- What stamps `schema_version` onto results before the reporter runs?

### Fork setup (one-time)

```bash
pip install graphifyy   # or: uv tool install graphifyy
# optional: copy checked-in graph into working cache
mkdir -p graphify-out
cp docs/graphify/graph.json graphify-out/graph.json
cp docs/graphify/GRAPH_REPORT.md graphify-out/GRAPH_REPORT.md
```

Point your agent docs (`CLAUDE.md`, Cursor rules, etc.) at **`docs/graphify/`** so every fork shares the same map.

## Rebuild (maintainers)

From the repo root (after installing `graphifyy`):

```bash
# Full rebuild via agent skill /graphify .   OR structural-only:
python -c "from pathlib import Path; import graphify"  # ensure installed
# Prefer the project /graphify skill for a full pipeline.
# Then publish:
mkdir -p docs/graphify
cp graphify-out/GRAPH_REPORT.md docs/graphify/
cp graphify-out/graph.json docs/graphify/
cp graphify-out/graph.html docs/graphify/
cp graphify-out/.graphify_labels.json docs/graphify/labels.json
```

Commit updates to `docs/graphify/` when architecture changes materially (new modules, renamed packages, major adapter splits).

## Graph health note

The last build reported some **dangling-endpoint edges** from AST/semantic merge (type-annotation `references` collapsing). The graph remains usable for navigation; prefer `calls` edges and file-backed nodes when tracing execution.
