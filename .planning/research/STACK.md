# Technology Stack

**Project:** ACS HelloAsso Invoicing Web Dashboard
**Researched:** 2026-03-25

## Recommended Stack

### Core Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | 0.115+ | Web API framework | Built-in OAuth2 support, auto-generated Swagger docs (useful for small team), Pydantic validation, dependency injection maps cleanly to HelloAsso auth flow. 78K+ GitHub stars, fastest-growing Python API framework. |
| Uvicorn | 0.34+ | ASGI server | Default FastAPI server, production-ready with `--workers` flag |
| Pydantic | 2.x | Data validation | Already bundled with FastAPI, use for request/response models and config validation |

### Database
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite | 3.x (system) | Lightweight persistence | Zero-config, file-based, perfect for small team. Already available in Python stdlib. Stores member cache, invoice records, email send logs. |
| SQLModel | 0.0.22+ | ORM | Created by FastAPI author, unifies SQLAlchemy + Pydantic models into single class. Reduces boilerplate vs separate SQLAlchemy models + Pydantic schemas. |

### PDF Generation
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| WeasyPrint | 62+ | HTML-to-PDF | Already used in existing pipeline. Existing Jinja2 template works as-is. No reason to switch. |
| Jinja2 | 3.x | HTML templating | Already used for invoice template. FastAPI supports Jinja2 natively via `Jinja2Templates`. |

### Email
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| smtplib (stdlib) | - | SMTP client | Built-in Python, replaces `sendemail` Perl CLI. Zero dependencies. Supports TLS, attachments, HTML. |
| email (stdlib) | - | Message construction | Use modern `EmailMessage` API (not legacy MIMEText). Clean attachment handling. |

### HTTP Client
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| httpx | 0.28+ | HelloAsso API calls | Drop-in replacement for `requests` with async support. Allows using `async/await` for HelloAsso API calls while WeasyPrint runs in thread pool. Connection pooling built-in. |

### Infrastructure
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Docker | - | Deployment | Existing Docker setup, extend current Dockerfile. Single container: FastAPI serves both API and React static files. |
| python-multipart | 0.0.20+ | Form data | Required by FastAPI for form-based login endpoint |

### Frontend (for reference)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| React | 18+ | SPA dashboard | Specified in project requirements. Served as static files by FastAPI. |
| Vite | 6+ | Build tool | Fast builds, simple config, outputs static files to `dist/` for FastAPI to serve |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Framework | FastAPI | Flask | Flask lacks built-in validation, auto-docs, and OAuth2 utilities. For a pure API backend (not server-rendered HTML), FastAPI is simpler despite Flask's maturity. |
| ORM | SQLModel | SQLAlchemy direct | SQLModel eliminates duplicate model definitions (ORM model + Pydantic schema). For this small project, the reduced boilerplate matters. |
| ORM | SQLModel | Peewee | Less ecosystem support, no FastAPI integration story |
| HTTP client | httpx | requests | `requests` is sync-only. `httpx` is API-compatible but supports async. The existing code uses `requests` patterns, so migration is minimal. |
| Email | smtplib | python-emails lib | Extra dependency for no real benefit at this scale. smtplib + EmailMessage is clean enough. |
| Email | smtplib | SendGrid/Mailgun API | Overkill for a small association sending ~100 invoices/season. SMTP is simpler and free. |
| PDF | WeasyPrint | wkhtmltopdf | WeasyPrint is already integrated. wkhtmltopdf is deprecated. |
| PDF | WeasyPrint | Playwright PDF | Heavier dependency (needs browser binary). WeasyPrint is purpose-built for this. |
| HelloAsso SDK | Custom wrapper | helloasso-python (official) | The existing `helloasso.py` is simpler and does exactly what's needed. The official SDK is auto-generated and verbose. Keep custom wrapper, refactor into a service class. |
| Auth | HTTP Basic + session | Auth0/OAuth provider | Massive overkill for 3-5 volunteers. Simple username/password with session cookie is sufficient. |
| DB | SQLite | PostgreSQL | No need for a database server for ~200 member records and ~200 invoice records per season. |

## Installation

```bash
# Core dependencies
pip install fastapi uvicorn[standard] sqlmodel httpx jinja2 weasyprint python-multipart

# Dev dependencies
pip install -D pytest httpx pytest-asyncio ruff
```

### System Dependencies (for WeasyPrint)

```bash
# Debian/Ubuntu (already in existing Dockerfile)
apt-get install libpangocairo-1.0-0
```

## Key Version Notes

- **SQLModel 0.0.22+**: Supports Pydantic v2 (required for FastAPI 0.100+)
- **WeasyPrint 62+**: Current stable line, dropped Python 3.7 support
- **FastAPI 0.115+**: Stable Pydantic v2 support, improved dependency injection

## Sources

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [FastAPI SQL Databases Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [SQLModel GitHub](https://github.com/fastapi/sqlmodel)
- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/stable/)
- [HelloAsso Python SDK](https://github.com/HelloAsso/helloasso-python)
- [FastAPI vs Flask comparison (Better Stack)](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/)
- [FastAPI vs Flask comparison (Second Talent)](https://www.secondtalent.com/resources/fastapi-vs-flask/)
