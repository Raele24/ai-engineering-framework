# Graphify Knowledge Graph Integration (`integrations/graphify/`)

**Tool Version Verified on Host:** `graphify 0.9.48` (`graphifyy 0.9.48`)  

---

## 1. Purpose

The **AI Engineering Framework** integrates **Graphify** to transform repository code, documentation, schemas, and scripts into a persistent, queryable knowledge graph (`graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`).

Instead of grepping blindly across large directory trees and consuming thousands of context tokens, agents query the knowledge graph first.

---

## 2. Standard Commands

```bash
# Build full knowledge graph on repository root
graphify .

# Incremental update after code/doc changes (zero LLM API cost)
graphify update .

# Query the existing graph (BFS context retrieval)
graphify query "How do platform adapters synchronize with canonical rules?"

# Find shortest architectural path between two nodes
graphify path "sync_adapters.py" "core/rules"

# Explain a specific node and its relationships
graphify explain "validate.py"
```

---

## 3. Workflow Phase Integration

| Phase | Agent Role | Graphify Action |
| :--- | :--- | :--- |
| **Phase 1 (Discovery)** | `product-analyst` | Check if `graphify-out/graph.json` exists; run `graphify query` to identify affected modules |
| **Phase 4–5 (Architecture)** | `software-architect` | Inspect `graphify-out/GRAPH_REPORT.md` for god-nodes, communities, and coupling |
| **Phase 10 (Code Review)** | `code-reviewer` | Run `graphify update .` to verify the diff does not introduce unintended dependency cycles |
| **Phase 14 (Documentation)** | `implementation-engineer` | Refresh `graphify-out/` before release validation |
