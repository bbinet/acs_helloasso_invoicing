# Feature Landscape

**Domain:** Association membership management / invoicing dashboard
**Researched:** 2026-03-25

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| View member list | Core purpose of the tool -- see who registered | Low | Already implemented in CLI (`-m txt/csv/json`) |
| Filter members by activity | Key workflow for volunteers | Low | Already implemented (`-a` flag) |
| Filter by date range | Seasonal management (saison 2023-2024, etc.) | Low | Already implemented (`-f`, `-t` flags) |
| Generate PDF invoice for a member | Core invoicing function | Medium | Already works via Makefile pipeline, needs API endpoint |
| Batch generate all invoices | Primary use case -- generate for entire season | Medium | Must run as background task (WeasyPrint is slow) |
| Send invoice by email | Completes the invoicing workflow | Medium | Replace sendemail CLI with smtplib |
| Batch send emails | Send all unsent invoices | Medium | Background task with progress tracking |
| Login/authentication | Protect member data and actions | Low | Simple auth for 3-5 users |
| View invoice status | Know which invoices were generated/sent | Low | Track in SQLite: generated, sent, error |
| French language UI | Users are French volunteers | Low | All labels, messages in French |

## Differentiators

Features that set this apart from the CLI tool. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Activity summary dashboard | At-a-glance view of registrations per activity | Low | Already computed in CLI (`-s` flag), just needs a UI |
| Invoice preview (HTML) | See invoice before generating PDF | Low | Render Jinja2 template to HTML, display in browser |
| Email delivery status | Know if emails bounced or were received | Medium | Requires tracking send results, possibly read receipts |
| Season selector | Switch between formSlugs easily | Low | Config currently hardcodes one formSlug |
| Member search | Quick find by name/email | Low | Already implemented (`-u` flag) |
| Refund detection | Flag refunded orders visually | Low | Already implemented (`-r` flag) |
| Export to CSV | Download member data for external use | Low | Already implemented in CLI, add download endpoint |
| Re-send individual email | Retry failed sends or re-send on request | Low | Simple action button per member |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Multi-tenant / multi-association support | One association (ACS), adds complexity for no benefit | Hardcode ACS context, make configurable via config file only |
| User registration / self-service | Volunteers are known, admin adds them | Seed users in config or simple admin endpoint |
| Real-time HelloAsso sync / webhooks | Volunteers check data periodically (seasonal), not real-time | Manual "refresh from HelloAsso" button with cached data |
| Payment processing | HelloAsso handles all payments | Just read payment data, never write |
| Custom invoice template editor | Template rarely changes, volunteers are not designers | Keep Jinja2 template as code, edit in repo |
| Mobile app | Small team uses desktop/laptop for admin tasks | Responsive web design is sufficient |
| Role-based access control | 3-5 users with identical needs | All authenticated users get full access |
| Internationalization (i18n) | French only, French association | Hardcode French strings |

## Feature Dependencies

```
Authentication --> All other features (gate everything behind login)
HelloAsso API wrapper --> Member list, Filters, Data dump
Data dump to DB cache --> Invoice generation, Status tracking
Invoice generation (PDF) --> Email sending
Email sending --> Email status tracking
Member list --> Activity summary (computed from member data)
```

## MVP Recommendation

Prioritize:
1. **Authentication** (gate the dashboard)
2. **Member list with filters** (core data viewing)
3. **Single invoice generation + download** (core action)
4. **Batch invoice generation** (primary workflow)
5. **Email sending** (completes the workflow)

Defer:
- **Activity summary dashboard**: Nice but not blocking -- volunteers can see this from the member list
- **Season selector**: Start with current season hardcoded, add selector later
- **Email delivery status**: Track send success/failure, but don't build bounce detection yet

## Sources

- Analysis of existing `helloasso.py` CLI capabilities
- Analysis of existing `invoicing/Makefile` pipeline
- [HelloAsso API V5 Documentation](https://api.helloasso.com/v5/)
