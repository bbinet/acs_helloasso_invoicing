# HelloAsso API V5 Research

**Researched:** 2026-03-25
**Overall confidence:** MEDIUM-HIGH (official SDK docs + WebSearch; dev portal blocked direct fetch but SDK docs are auto-generated from OpenAPI spec)

---

## 1. API Overview

**Base URLs:**
- Production: `https://api.helloasso.com/v5`
- Sandbox: `https://api.helloasso-sandbox.com/v5`
- OAuth2 tokens: `https://api.helloasso.com/oauth2/token`
- Swagger UI: `https://api.helloasso.com/v5/swagger/ui/index`

**API Version:** V5 is current and maintained. V3 is deprecated (still functional but no maintenance).

**HTTP Methods:** GET (retrieve), POST (create), PUT (update). Standard REST patterns.

---

## 2. Authentication -- OAuth2 Details

### Client Credentials Flow (current code uses this)

```
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
client_id=YOUR_ID
client_secret=YOUR_SECRET
```

Returns: `access_token` (valid ~30 minutes / 1799 seconds) + `refresh_token` (valid 30 days).

### Token Refresh Flow (CRITICAL -- current code does NOT do this)

```
POST /oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
client_id=YOUR_ID
refresh_token=YOUR_REFRESH_TOKEN
```

Returns: new `access_token` + new `refresh_token`.

### Token Rules

| Rule | Detail |
|------|--------|
| Access token validity | ~30 minutes (1799 seconds) |
| Refresh token validity | 30 days |
| Max simultaneous access tokens | 20 per API key |
| Token refresh requirement | **MUST** use refresh_token, NOT re-authenticate with client_credentials every call |
| Refresh token rotation | Each refresh returns a NEW refresh_token (old one invalidated) |

**IMPORTANT:** HelloAsso explicitly forbids generating a new access_token from client_id/client_secret on every call. The current `helloasso.py` code violates this by calling `Authenticate()` fresh each time. A dashboard must implement proper token lifecycle management.

### Authorization Code Flow (for partner/multi-org access)

For accessing private association data as a partner, an OAuth consent flow is required:
1. Generate authorization URL with redirect callback
2. User grants consent
3. Exchange authorization code for access token (with PKCE code_verifier)
4. Use token to access protected resources

This is relevant if the dashboard needs to support multiple organizations.

---

## 3. Complete Endpoint Inventory

### Currently Used by helloasso.py

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/v5/organizations/{slug}/forms/{formType}/{formSlug}/items` | GET | Fetch form items (members) with pagination |

### Available but NOT Used -- Organization Level

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v5/organizations/{slug}` | GET | Public organization info (name, logo, etc.) |
| `/v5/organizations/{slug}/formTypes` | GET | List form types where org has at least one form |
| `/v5/organizations/{slug}/forms` | GET | List all forms (with state/type filtering, pagination) |
| `/v5/organizations/{slug}/orders` | GET | All orders across all forms |
| `/v5/organizations/{slug}/items` | GET | All items across all forms |
| `/v5/organizations/{slug}/payments` | GET | All payments across all forms |

### Available but NOT Used -- Form Level

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v5/organizations/{slug}/forms/{formType}/{formSlug}/public` | GET | Detailed public form data (tiers, pricing, state) |
| `/v5/organizations/{slug}/forms/{formType}/{formSlug}/orders` | GET | Orders for a specific form |
| `/v5/organizations/{slug}/forms/{formType}/{formSlug}/payments` | GET | Payments for a specific form |
| `/v5/organizations/{slug}/forms/{formType}/action/quick-create` | POST | Create simplified form/event |

### Available but NOT Used -- Direct Entity Access

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v5/orders/{orderId}` | GET | Get specific order details |
| `/v5/orders/{orderId}/cancel` | POST | Cancel future payments (no refund) |
| `/v5/items/{itemId}` | GET | Get specific item details |
| `/v5/payments/{paymentId}` | GET | Get detailed payment info |
| `/v5/payments/{paymentId}/refund` | POST | Refund a payment |

### Available but NOT Used -- Financial

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v5/organizations/{slug}/cash-out/{cashOutId}/export` | GET | Financial transfer details (supports JSON, Excel, CSV) |

### Available but NOT Used -- Partner/Notification Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v5/partners/me/api-notifications` | PUT | Configure global webhook notification URL |
| `/v5/partners/me/api-notifications/organizations/{slug}` | PUT | Configure per-organization webhook URL |

### Available but NOT Used -- Directory/Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| Directory forms search | POST | Search forms across the platform |
| Directory organizations search | POST | Search organizations |

---

## 4. Pagination

Two pagination styles observed in the API:

### Continuation Token (used by current code)
```json
{
  "data": [...],
  "pagination": {
    "continuationToken": "abc123"
  }
}
```
Pass `continuationtoken` as query parameter for next page. Used by items endpoint.

### Page-based (available on other endpoints)
Query parameters: `pageSize`, `pageIndex`, `from`, `to`, `sortOrder`, `sortField`, `withDetails`, `userSearchKey`, `states`.

---

## 5. Payment States

**CRITICAL for dashboard correctness.** Not all payments returned are valid.

| State | Meaning | Show in dashboard? |
|-------|---------|-------------------|
| `Authorized` | Payment accepted and validated | YES -- this is a confirmed payment |
| `Refused` | Payment refused (typically by bank) | Show as failed |
| `Unknow` (sic) | Unresolved status | Show as pending/warning |
| `Registered` | Offline payment (cash, check) | YES -- manual entry |
| `Refunded` | Payment fully refunded | Show with refund indicator |
| `Refunding` | Refund in progress | Show as pending refund |
| `Contested` | User disputed with their bank (chargeback) | Show as disputed/alert |

**Dashboard must filter by state.** The current CLI uses refund operations to detect refunds, but the proper approach is to check `payment.state`.

---

## 6. Webhooks / Notifications

### Event Types

| eventType | Trigger | Payload contains |
|-----------|---------|-----------------|
| `Order` | New order created | Payer info, items array, payments, total amounts |
| `Payment` | Payment processed | Payer info, order reference, payment receipt URL, cashout state |
| `Form` | Form/campaign created or updated | Organization details, tier pricing, form type, state |
| `Organization` | Organization-level changes | Organization details |

### Payload Structure

```json
{
  "data": { /* event-specific content */ },
  "eventType": "Order|Payment|Form|Organization",
  "metadata": {
    "key": "value"
  }
}
```

### Configuration

Two levels:
1. **Global (partner-level):** `PUT /v5/partners/me/api-notifications`
2. **Per-organization:** `PUT /v5/partners/me/api-notifications/organizations/{slug}`
3. **Back-office:** Manual configuration in HelloAsso admin UI

### Retry Behavior

If webhook delivery fails (non-200 response):
- Formula: `min(48h, 3 * 2^attempt)` seconds
- Starts at 3 seconds
- Up to 16 retries
- Maximum delay between retries: ~27 hours (capped at 48h)
- Must return HTTP 200 to acknowledge receipt

### Implications for Dashboard

Webhooks enable real-time updates without polling. For a membership dashboard:
- `Order` webhook = new member registered
- `Payment` webhook = payment confirmed/failed
- `Form` webhook = form configuration changed

**Recommendation:** Implement webhook receiver endpoint to get real-time membership notifications instead of polling the items endpoint.

---

## 7. Data Model

### Core Entities (hierarchy)

```
Organization
  |-- Form (type: MemberShip, Event, Donation, CrowdFunding, MonthlyDonation)
       |-- Order (a contributor action; can be free or paid)
            |-- Item (individual line items in an order; e.g., membership tier + options)
            |-- Payment (one or more payments per order; installments possible)
                 |-- RefundOperation (refund records on a payment)
```

### Key Fields per Entity

**Item** (what current code fetches):
- `id`, `name`, `user` (firstName, lastName), `payer` (email), `order` (date, id)
- `payments[]` (with `refundOperations[]`)
- `customFields[]` (name/answer pairs -- e.g., company, phone)
- `options[]` (selected activities/options)
- `amount`, `state`, `type`

**Order:**
- `id`, `date`, `formSlug`, `formType`, `organizationSlug`
- `payer` (firstName, lastName, email, address)
- `items[]`, `payments[]`
- `amount` (totalAmount, vat, discount)

**Payment:**
- `id`, `date`, `amount`, `state` (Authorized/Refused/Refunded/etc.)
- `paymentReceiptUrl`
- `cashOutState`, `paymentMeans` (Card, etc.)
- `refundOperations[]`

---

## 8. Rate Limits

### What is documented

- Max 20 simultaneous valid access tokens per API key
- Must use refresh tokens (not re-authenticate each time)
- Access token valid 30 minutes

### What is NOT documented

- No explicit requests-per-minute or requests-per-second limit found
- No documented burst limits
- No documented response headers for rate limit tracking (X-RateLimit-* etc.)

**Confidence: LOW** on the absence of rate limits. HelloAsso may enforce undocumented limits. For a dashboard, implement:
- Token caching and refresh (mandatory)
- Request debouncing/throttling (defensive)
- Response caching for frequently accessed data

---

## 9. Official Python SDKs

### Option 1: `helloasso-python` (RECOMMENDED -- current, auto-generated from OpenAPI)

```bash
pip install helloasso-python
```

- Python 3.8+
- Auto-generated from OpenAPI spec (216 doc files covering all endpoints and models)
- Uses Authlib for OAuth2
- Pre-built API classes: AnnuaireApi, CheckoutApi, CommandesApi, FormulairesApi, OrganisationApi, PaiementsApi, PartenairesApi, TagsApi, UtilisateursApi, VersementsApi, ListeDeValeursApi, ReusFiscauxApi

**Usage:**
```python
import helloasso_python

configuration = helloasso_python.Configuration(host="https://api.helloasso.com/v5")
configuration.access_token = "your_access_token"

with helloasso_python.ApiClient(configuration) as api_client:
    api = helloasso_python.CommandesApi(api_client)
    orders = api.organizations_organization_slug_forms_form_type_form_slug_orders_get(
        organization_slug="acs-savoie-technolac",
        form_type="MemberShip",
        form_slug="inscription-acs-saison-2023-2024"
    )
```

**Limitation:** Does NOT handle token refresh automatically. You must implement OAuth2 lifecycle with Authlib separately.

### Option 2: `helloasso-apiv5` (LEGACY -- archived Nov 2024)

```bash
pip install helloasso-apiv5
```

- Python 3.6-3.10
- **Archived** as of November 2024
- DOES handle token refresh automatically (built-in)
- Simpler API: `api.call("organizations/{slug}")` style
- Supports custom token getter/setter functions for persistence

**Key advantage:** Automatic token management including refresh. But archived and no longer maintained.

### Option 3: Direct `requests` (current approach)

The existing code uses raw `requests`. This works but:
- No token refresh (violates HelloAsso TOS)
- No retry logic
- No model validation
- Manual URL construction

### Recommendation for Dashboard

Use `helloasso-python` (official, current) but wrap it with proper OAuth2 token lifecycle management using Authlib. The legacy SDK's auto-refresh is tempting but it is archived and limited to Python 3.10.

---

## 10. Sandbox Environment

HelloAsso provides a full sandbox for testing:
- API: `https://api.helloasso-sandbox.com/v5`
- OAuth: `https://api.helloasso-sandbox.com/oauth2/token`
- Separate credentials needed (register at sandbox portal)

**Use for:** Dashboard development and testing without affecting production data.

---

## 11. Gaps in Current helloasso.py Code

| Gap | Impact | Fix Priority |
|-----|--------|-------------|
| No token refresh | Violates HelloAsso policy; tokens may be revoked | HIGH |
| Only uses items endpoint | Misses payment details, order info, form listing | MEDIUM |
| No payment state filtering | May show unvalidated payments | HIGH |
| No error handling on API calls | Silent failures | HIGH |
| Hardcoded to single form | Cannot browse across forms/seasons | MEDIUM |
| No webhook support | Must poll for updates | LOW (for CLI, HIGH for dashboard) |
| No pagination safety | Could loop forever if API changes | LOW |

---

## 12. Key Considerations for Dashboard

### What the API Enables

1. **Multi-form/multi-season view:** `/organizations/{slug}/forms` lists all forms, then fetch items per form
2. **Payment tracking:** Dedicated payment endpoints with state filtering
3. **Real-time updates:** Webhooks for Order/Payment/Form events
4. **Refund management:** `POST /payments/{id}/refund` for processing refunds
5. **Financial overview:** Cash-out export endpoints for accounting
6. **Organization info:** Public org details for dashboard branding

### What the API Does NOT Provide

- No bulk export endpoint (must paginate through results)
- No GraphQL or flexible query language
- No real-time streaming (webhooks are push, not stream)
- No member profile endpoint (members are items on forms, not first-class entities)
- No cross-organization aggregation (unless using partner flow)

### Architecture Implications

- **Backend required:** OAuth2 token management, webhook receiver, and API key security all require a server-side component. Cannot be a pure client-side SPA.
- **Caching layer recommended:** API has no documented rate limits but token constraints suggest they want minimal calls. Cache form data, member lists, etc.
- **Webhook receiver:** Needs a publicly accessible HTTPS endpoint. Consider a lightweight webhook ingestion service.
- **Multi-season support:** The `formSlug` changes each season (e.g., `inscription-acs-saison-2023-2024`). Dashboard should allow selecting/comparing across seasons.

---

## Sources

- [HelloAsso Developer Portal](https://dev.helloasso.com/)
- [HelloAsso API Swagger](https://api.helloasso.com/v5/swagger/ui/index)
- [HelloAsso Webhook Documentation](https://dev.helloasso.com/docs/notifications-webhook)
- [HelloAsso Authentication Guide](https://dev.helloasso.com/docs/getting-started)
- [HelloAsso Payment States](https://dev.helloasso.com/docs/status-des-paiements)
- [HelloAsso Payment Validation](https://dev.helloasso.com/docs/validation-de-vos-paiements)
- [helloasso-python SDK (GitHub)](https://github.com/HelloAsso/helloasso-python)
- [helloasso-python-legacy SDK (GitHub)](https://github.com/HelloAsso/helloasso-python-legacy)
- [helloasso-python SDK - CommandesApi docs](https://github.com/HelloAsso/helloasso-python/blob/main/docs/CommandesApi.md)
- [helloasso-python SDK - PaiementsApi docs](https://github.com/HelloAsso/helloasso-python/blob/main/docs/PaiementsApi.md)
- [helloasso-python SDK - FormulairesApi docs](https://github.com/HelloAsso/helloasso-python/blob/main/docs/FormulairesApi.md)
- [helloasso-python SDK - OrganisationApi docs](https://github.com/HelloAsso/helloasso-python/blob/main/docs/OrganisationApi.md)
- [Node Notification Handler Sample (GitHub)](https://github.com/HelloAsso/node-notification-handler-sample)
- [HelloAsso API Introduction](https://dev.helloasso.com/docs/introduction-%C3%A0-lapi-de-helloasso)
- [helloasso-apiv5 on PyPI](https://pypi.org/project/helloasso-apiv5/)
