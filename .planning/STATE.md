# Project State

## Current Phase
Phase 1: API Foundation — **NOT STARTED**

## Completed
- [x] Project initialization (PROJECT.md)
- [x] Domain research (4 research streams)
- [x] Requirements definition (REQUIREMENTS.md)
- [x] Roadmap creation (ROADMAP.md)

## Next Action
Run `/gsd:plan-phase 1` to create detailed plan for Phase 1 (API Foundation).

## Decisions Made
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | FastAPI | Built-in validation, auto-docs, OAuth2 utilities, async |
| ORM | SQLModel | Unifies SQLAlchemy + Pydantic, same author as FastAPI |
| Database | SQLite | Perfect for ~200 members/season, zero-config |
| HTTP client | httpx | Async support, drop-in replacement for requests |
| Email | smtplib (stdlib) | Zero dependencies, replaces sendemail Perl CLI |
| Frontend framework | React + TypeScript | User requirement |
| Build tool | Vite | Industry standard, CRA deprecated, Next.js overkill |
| UI library | Mantine 7 | Best for small dashboards, built-in hooks, great DX |
| Data table | Mantine React Table | TanStack Table + Mantine styling |
| Server state | TanStack Query v5 | Standard for API data fetching |
| Deployment | Single Docker container | Nginx + Gunicorn/Uvicorn + React static |

## Open Questions
- HelloAsso API rate limits (undocumented)
- WeasyPrint memory behavior under batch generation
- Exact ACS brand colors for theme
