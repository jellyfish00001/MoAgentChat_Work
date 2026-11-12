---
name: scaffold-graph
description: Create a new LangGraph package skeleton under server/flows/graphs/<name>/.
---

# scaffold-graph

## Steps

1. Read `.cursor/guides/graph-scaffold.md`.
2. Create `server/flows/graphs/<name>/{state,nodes,prompts,graph}.py` with `messages` state and exported `graph`.
3. Register in `server/langgraph.dev.json`（本機多流程）。**不要**改部署用的 `server/langgraph.json`，除非使用者明確要求晉升正式。
4. Do **not** generate three business graphs at once; one name per invocation.
5. Add a domain stub + pytest only if the user asked for business logic.
