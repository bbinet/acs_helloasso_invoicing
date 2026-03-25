# Comparison: FastAPI vs Flask

**Context:** Choosing a Python web framework for wrapping existing HelloAsso invoicing CLI into a web API
**Recommendation:** FastAPI because it provides built-in validation, auto-docs, OAuth2 utilities, and async support -- all of which this project needs -- with less total code than Flask + extensions.

## Quick Comparison

| Criterion | FastAPI | Flask |
|-----------|---------|-------|
| API documentation | Built-in (Swagger UI + ReDoc) | Manual or Flask-RESTX extension |
| Request validation | Built-in (Pydantic) | Manual or Marshmallow extension |
| OAuth2 support | Built-in utilities | Flask-Login + manual implementation |
| Async support | Native (ASGI) | Limited (WSGI, needs workarounds) |
| Performance | ~20K req/s (Uvicorn) | ~4-5K req/s (Gunicorn) |
| Maturity | 6 years, 78K GitHub stars | 15 years, 68K GitHub stars |
| Learning curve | Moderate (type hints required) | Low (minimal boilerplate) |
| Extension ecosystem | Growing, fewer extensions | Massive, mature ecosystem |
| ORM integration | SQLModel (same author) | Flask-SQLAlchemy (mature) |
| Static file serving | Starlette StaticFiles | Built-in |
| Background tasks | Built-in BackgroundTasks | Celery (external) or custom |
| Type safety | Enforced via Pydantic | Optional |

## Detailed Analysis

### FastAPI
**Strengths:**
- Auto-generated Swagger UI is immediately useful for a small team -- volunteers can test API endpoints without writing code
- Pydantic validation catches bad data at the boundary (e.g., invalid date filters, missing fields)
- `Depends()` dependency injection is perfect for injecting authenticated HelloAsso service instances
- Native async means HelloAsso API calls (I/O-bound) don't block other requests
- `BackgroundTasks` handles batch PDF generation without external task queue
- Built-in OAuth2 utilities simplify both HelloAsso token management and dashboard auth
- SQLModel (by same author) eliminates the model duplication problem

**Weaknesses:**
- Requires type hints everywhere (minor learning curve for contributors)
- Younger ecosystem -- fewer battle-tested extensions than Flask
- ASGI server (Uvicorn) is less familiar than WSGI (Gunicorn) to some

**Best for:** API-first backends, projects that benefit from auto-documentation, async I/O workloads

### Flask
**Strengths:**
- Simpler mental model -- "just functions that return responses"
- 15 years of extensions for every conceivable need (Flask-Login, Flask-Admin, Flask-Mail, Flask-WeasyPrint)
- Flask-WeasyPrint extension specifically handles the "server requesting its own templates" problem
- More tutorials, Stack Overflow answers, and community resources
- Easier onboarding for Python beginners

**Weaknesses:**
- No built-in validation -- need Marshmallow or manual checks
- No auto-generated API docs without Flask-RESTX (which adds its own complexity)
- WSGI is synchronous by default -- HelloAsso API calls block the worker
- Background tasks require Celery or RQ (external dependencies, operational overhead)
- Would need Flask-Login + Flask-Session + manual JWT for auth (multiple extensions)

**Best for:** Server-rendered HTML apps, quick prototypes, projects that need mature extensions

## Recommendation

**Choose FastAPI** for this project because:

1. **This is an API backend**, not a server-rendered HTML app. FastAPI is purpose-built for this.
2. **Auto-generated docs** are a free feature that helps volunteers understand and test the API.
3. **Async HelloAsso calls** are valuable -- the API has pagination and can be slow. Non-blocking I/O means the dashboard stays responsive.
4. **Built-in BackgroundTasks** handles batch PDF generation without needing Celery/Redis infrastructure.
5. **Pydantic validation** catches input errors early and produces clear error messages.
6. **SQLModel** unifies the data model -- one class serves as both the database model and the API response model.
7. The team is building something new (not maintaining existing Flask code), so there's no migration cost.

The only scenario where Flask would be better: if the volunteers maintaining this code are Flask experts and have never used FastAPI. Given that the current code is a CLI script (no web framework experience), this is not the case.

## Sources

- [FastAPI vs Flask (Better Stack)](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/)
- [FastAPI vs Flask (Second Talent)](https://www.secondtalent.com/resources/fastapi-vs-flask/)
- [FastAPI vs Flask (Strapi)](https://strapi.io/blog/fastapi-vs-flask-python-framework-comparison)
- [FastAPI vs Flask 2026 (Medium)](https://medium.com/@muhammadshakir4152/fastapi-vs-flask-the-deep-comparison-every-python-developer-needs-in-2026-334ccf9abfa8)
- [Framework Comparison 2026 (dasroot.net)](https://dasroot.net/posts/2026/02/python-flask-fastapi-django-framework-comparison-2026/)
