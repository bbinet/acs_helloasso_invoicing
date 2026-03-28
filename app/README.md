# ACS HelloAsso - Backend API

REST API for the ACS HelloAsso dashboard.

## Tech Stack

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Jinja2** - Invoice PDF templating

## Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

The API is available at http://localhost:8000

## Structure

```
app/
├── main.py           # FastAPI app entry point
└── routes/           # API endpoints
    ├── auth.py       # Authentication (login/logout)
    ├── members.py    # Members list
    ├── invoices.py   # Invoice generation/download
    ├── emails.py     # Email sending
    ├── campaigns.py  # HelloAsso campaigns
    └── summary.py    # Activity summary

lib/
├── config.py         # Configuration loading
├── models.py         # Data models
├── helloasso_client.py  # HelloAsso API client
├── invoicing.py      # Invoice generation
└── filesystem.py     # File operations
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/members` | List members |
| POST | `/api/invoices/{id}/generate` | Generate invoice |
| GET | `/api/invoices/{id}/download` | Download invoice PDF |
| POST | `/api/emails/{id}/send` | Send invoice by email |
| POST | `/api/invoices/batch` | Batch generate invoices |
| POST | `/api/emails/batch` | Batch send emails |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONF_PATH` | Path to config file | `conf.json` |
| `DASHBOARD_PASSWORD` | Login password | `admin` |
| `SESSION_SECRET` | Session cookie secret | (dev key) |

## Tests

```bash
pytest tests/
```
