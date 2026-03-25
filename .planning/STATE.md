# Project State

## Current Phase
Phase 1: Shared Library & API Foundation — **NOT STARTED**

## Completed
- [x] Project initialization (PROJECT.md)
- [x] Domain research (4 research streams)
- [x] Requirements definition (REQUIREMENTS.md)
- [x] Roadmap creation (ROADMAP.md)
- [x] Architecture revision based on user feedback

## Next Action
Run `/gsd:plan-phase 1` to create detailed plan for Phase 1.

## Decisions Made
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | FastAPI | Built-in validation, auto-docs, OAuth2 utilities, async |
| Database | **None — flat files** | Keep same arborescence as CLI, no added complexity |
| Email | **sendemail (keep existing)** | Maintain CLI compatibility, no migration needed |
| Code sharing | **Shared Python library** | Extract from helloasso.py, imported by both CLI and web |
| File arborescence | **Same as CLI** | `invoicing/<formSlug>/*.json`, `*.pdf`, `*.mail.log` |
| Status tracking | **Filesystem-based** | .pdf exists = generated, .mail.log exists = sent |
| Config | **Keep conf.json** | Maintain CLI compatibility |
| HTTP client | httpx | Async support, drop-in replacement for requests |
| Frontend framework | **Svelte** | Lightweight, compiled, smallest bundle, no virtual DOM |
| Build tool | Vite | Standard for Svelte |
| Deployment | Single Docker container | Nginx + Gunicorn/Uvicorn + Svelte static |

## Open Questions
- HelloAsso API rate limits (undocumented)
- WeasyPrint memory behavior under batch generation
- Exact ACS brand colors for theme
- Svelte data table component choice (fewer options than React ecosystem)
