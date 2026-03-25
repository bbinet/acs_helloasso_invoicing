# React Frontend Stack Research

**Project:** ACS HelloAsso Invoicing Dashboard
**Researched:** 2026-03-25
**Confidence:** HIGH (all recommendations verified across multiple sources)

---

## 1. Build Tool: Vite (not Next.js, not CRA)

**Recommendation:** Vite with `react-ts` template.

**Why Vite:**
- CRA is deprecated and unmaintained. Vite is the successor and current industry standard.
- Next.js adds SSR/SSG complexity that provides zero benefit here. This is an SPA served by a Python backend (FastAPI). There is no SEO requirement, no public-facing pages, no need for server components.
- Vite provides instant HMR, fast builds via esbuild/SWC, and native ES module serving in dev.
- Vite's dev server proxy (`server.proxy`) cleanly routes `/api/*` to FastAPI during development.

**Setup:**
```bash
npm create vite@latest frontend -- --template react-ts
```

**Vite config for FastAPI integration:**
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  },
  build: {
    outDir: 'dist',
  }
});
```

**Production deployment:** `vite build` produces a `dist/` folder. FastAPI serves this as static files using `StaticFiles` mount. Single Docker container serves both API and SPA.

**Sources:**
- [Vite docs](https://vite.dev/)
- [FastAPI + React tutorial (TestDriven.io)](https://testdriven.io/blog/fastapi-react/)
- [FastAPI and React in 2025 (joshfinnie.com)](https://www.joshfinnie.com/blog/fastapi-and-react-in-2025/)

---

## 2. UI Component Library: Mantine 7

**Recommendation:** Mantine 7.x (with `@mantine/core`, `@mantine/hooks`, `@mantine/notifications`, `@mantine/dates`).

**Why Mantine over alternatives:**

| Criterion | Mantine | Ant Design | shadcn/ui | MUI |
|-----------|---------|------------|-----------|-----|
| Best for | Small-medium dashboards | Large enterprise apps | Tailwind-native projects | Enterprise, Material Design |
| Bundle concern | Tree-shakeable | Heavy, overkill for small projects | Minimal (copy-paste) | Heavy |
| Built-in hooks | Yes (useForm, useDisclosure, etc.) | No | No | No |
| Dark mode | Built-in, one toggle | Requires extra config | Via Tailwind | Built-in |
| Docs quality | Excellent, interactive examples | Some Chinese-only sections | Good | Good but verbose |
| Customization | Deep theme + prop-level styling | Limited, requires CSS overrides | Full (own the code) | Theme system |
| Learning curve | Low | Medium | Low (if you know Tailwind) | Medium |
| Community size | Growing (28k GitHub stars) | Large (94k stars) | Fast-growing (66k stars) | Largest (94k stars) |

**Why NOT Ant Design:** Overkill for 3-5 users. Documentation has language barrier issues. Theming requires fighting CSS overrides. No built-in hooks ecosystem.

**Why NOT shadcn/ui:** Requires Tailwind CSS as a dependency (adds a technology layer). Fewer pre-built components (48 vs 120+). Copy-paste model means the team owns more maintenance burden. For a small volunteer team, batteries-included is better than assemble-it-yourself.

**Why NOT MUI:** Enterprise-weight for a small project. Material Design aesthetic may not match ACS branding goals.

**Mantine theme for ACS branding:**
```typescript
import { createTheme, MantineProvider } from '@mantine/core';

const theme = createTheme({
  primaryColor: 'blue', // Replace with ACS brand color
  fontFamily: 'Inter, sans-serif',
  // ACS-specific overrides
});

function App() {
  return (
    <MantineProvider theme={theme}>
      {/* app */}
    </MantineProvider>
  );
}
```

**Key Mantine packages:**
- `@mantine/core` -- All UI components (Button, Modal, TextInput, Select, Tabs, etc.)
- `@mantine/hooks` -- Utility hooks (useMediaQuery, useDisclosure, useClipboard, useDebouncedValue)
- `@mantine/notifications` -- Toast/notification system for action feedback
- `@mantine/dates` -- DatePicker, DateRangePicker for date filtering (uses dayjs)
- `@tabler/icons-react` -- Recommended icon set for Mantine

**Sources:**
- [Mantine docs](https://mantine.dev/)
- [Makers Den: React UI libs 2025](https://makersden.io/blog/react-ui-libs-2025-comparing-shadcn-radix-mantine-mui-chakra)
- [Subframe: Ant Design vs Mantine 2025](https://www.subframe.com/tips/ant-design-vs-mantine-162ef)
- [Dev.to: Why I Chose Mantine](https://dev.to/saltorgil/why-i-chose-mantine-as-my-react-ui-library-34nm)

---

## 3. Data Table: Mantine React Table (MRT)

**Recommendation:** `mantine-react-table` v2.x

**What it is:** A fully-featured data grid built on TanStack Table v8, styled with Mantine components. It is a fork of Material React Table adapted for Mantine. MIT licensed.

**Why MRT instead of raw TanStack Table:**
- TanStack Table is headless (no UI). You would need to wire up Mantine components manually for every feature (pagination controls, filter inputs, sort indicators, etc.).
- MRT provides all of this out of the box while still exposing the full TanStack Table API for customization.
- Consistent Mantine styling without any extra work.

**Why MRT instead of Mantine DataTable:**
- MRT has richer built-in features: column filtering, global search, row selection, column reordering/resizing, row expansion.
- MRT is built on TanStack Table, which is the most widely-used React table engine.

**Features needed for this project:**
| Feature | MRT Support | Notes |
|---------|-------------|-------|
| Sorting | Built-in | Click column headers |
| Column filtering | Built-in | Per-column filter inputs |
| Global search | Built-in | Search across all columns |
| Pagination | Built-in | Client-side or server-side |
| Row selection | Built-in | Checkboxes for bulk actions |
| Column visibility | Built-in | Toggle columns on/off |
| Row actions | Built-in | Action buttons per row (generate invoice, send email) |
| Export to CSV | Via custom toolbar button | Easy to add |

**Data size consideration:** The HelloAsso membership lists are small (likely < 1000 members per season). Client-side pagination, sorting, and filtering are perfectly adequate. No need for server-side table state.

**Example usage:**
```typescript
import { MantineReactTable, useMantineReactTable } from 'mantine-react-table';

const columns = [
  { accessorKey: 'lastName', header: 'Nom' },
  { accessorKey: 'firstName', header: 'Prenom' },
  { accessorKey: 'email', header: 'Email' },
  { accessorKey: 'activities', header: 'Activites' },
  { accessorKey: 'orderDate', header: 'Date' },
  { accessorKey: 'refunded', header: 'Rembourse', Cell: ({ cell }) => cell.getValue() ? 'Oui' : 'Non' },
];

const table = useMantineReactTable({
  columns,
  data: members,
  enableRowSelection: true,
  enableColumnFilters: true,
  enableGlobalFilter: true,
  enablePagination: true,
});

return <MantineReactTable table={table} />;
```

**Sources:**
- [Mantine React Table docs](https://www.mantine-react-table.com/)
- [MRT GitHub](https://github.com/KevinVandy/mantine-react-table)
- [TanStack Table docs](https://tanstack.com/table/latest)

---

## 4. Server State Management: TanStack Query v5

**Recommendation:** `@tanstack/react-query` v5.x

**Why TanStack Query (not Redux, not Zustand, not raw useEffect):**
- All application data comes from the FastAPI backend. There is minimal client-only state (maybe a selected season, dark mode toggle). This is a server-state-dominant application.
- TanStack Query handles caching, background refetching, deduplication, loading/error states, and retry logic out of the box.
- Eliminates the need for manual `useEffect` + `useState` + loading/error boilerplate (reduces code by ~85% per the docs).
- No need for Redux or Zustand because there is no complex client state to manage.

**Key patterns for this project:**

```typescript
// Query keys with parameters
const memberKeys = {
  all: ['members'] as const,
  list: (season: string) => ['members', season] as const,
  detail: (id: string) => ['members', id] as const,
};

// Fetch members for a season
function useMembers(season: string) {
  return useQuery({
    queryKey: memberKeys.list(season),
    queryFn: () => api.getMembers(season),
    staleTime: 5 * 60 * 1000, // 5 minutes -- data changes infrequently
  });
}

// Generate invoice (mutation)
function useGenerateInvoice() {
  return useMutation({
    mutationFn: (memberId: string) => api.generateInvoice(memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
}
```

**v5-specific notes:**
- `isLoading` was renamed to `isPending` for "no data yet" state.
- `onSuccess`/`onError` callbacks removed from `useQuery` -- handle side effects in the component or with global handlers.
- Requires React 18+.
- Use `queryOptions()` helper for reusable, type-safe query definitions.

**Sources:**
- [TanStack Query docs](https://tanstack.com/query/latest)
- [TanStack Query v5 migration guide](https://tanstack.com/query/v5/docs/framework/react/guides/migrating-to-v5)
- [rtcamp React data fetching best practices](https://rtcamp.com/handbook/react-best-practices/data-loading/)

---

## 5. Forms & Validation: React Hook Form + Zod

**Recommendation:** `react-hook-form` v7 + `zod` v3 + `@hookform/resolvers`

**Why this combination:**
- React Hook Form is lightweight, minimal re-renders, excellent TypeScript support.
- Zod provides TypeScript-native schema validation with `z.infer<typeof schema>` for automatic type inference. No need to write types AND validation rules separately.
- `@hookform/resolvers` bridges the two with `zodResolver`.
- This is the dominant pattern in the React ecosystem in 2025-2026.

**Forms needed in this project:**
| Form | Fields | Validation |
|------|--------|------------|
| Season selector | formSlug dropdown | Required |
| Filter controls | activity, date range, refund toggle | Optional, date format validation |
| Email send confirmation | recipient email, subject override (optional) | Email format |
| Settings/config | SMTP settings, API credentials | Required fields, URL format |

**Example:**
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const emailSchema = z.object({
  to: z.string().email('Adresse email invalide'),
  subject: z.string().min(1, 'Le sujet est requis'),
});

type EmailForm = z.infer<typeof emailSchema>;

function SendEmailForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<EmailForm>({
    resolver: zodResolver(emailSchema),
  });
  // ...
}
```

**Note:** Mantine also has `@mantine/form` (useForm hook). For this project, either works. Mantine's useForm is simpler but less powerful. React Hook Form + Zod is better if you want schema reuse with the backend or have complex validation. Given the forms in this project are simple, Mantine's built-in `useForm` is also acceptable. **Recommendation: start with Mantine useForm for simplicity; switch to RHF+Zod only if validation needs grow.**

**Sources:**
- [React Hook Form docs](https://react-hook-form.com/)
- [Zod docs](https://zod.dev/)
- [Contentful: Zod + RHF guide](https://www.contentful.com/blog/react-hook-form-validation-zod/)
- [freeCodeCamp: Zod + RHF](https://www.freecodecamp.org/news/react-form-validation-zod-react-hook-form/)

---

## 6. PDF Preview in Browser

**Recommendation:** `react-pdf` v10.x (by wojtekmaj) for inline preview, with iframe fallback.

**How it works in this project:**
1. User clicks "Generate Invoice" for a member.
2. Frontend calls `POST /api/invoices/{memberId}/generate` which triggers WeasyPrint server-side.
3. Backend returns the PDF as a blob (or a URL to the generated PDF).
4. Frontend displays it inline using `react-pdf` or opens in a new tab.

**react-pdf setup:**
```typescript
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

function InvoicePreview({ pdfUrl }: { pdfUrl: string }) {
  return (
    <Document file={pdfUrl}>
      <Page pageNumber={1} />
    </Document>
  );
}
```

**Known gotchas:**
- **Worker setup:** PDF.js requires a web worker. The import path can be tricky with Vite. Must configure via `pdfjs.GlobalWorkerOptions.workerSrc`. Test this early.
- **Module execution order:** Setting workerSrc in a separate file (like main.tsx) may be overwritten. Configure it in the same file that renders PDF components.
- **CSS imports:** Must import AnnotationLayer.css and TextLayer.css for proper rendering.

**Simpler alternative:** For this project, an `<iframe src={pdfUrl} />` or `<object>` tag may be sufficient. The browser's built-in PDF viewer handles single-page invoices perfectly. No extra dependency needed. Reserve `react-pdf` for cases where you need custom UI around the PDF (zoom controls, page navigation).

**Recommendation:** Start with `<iframe>` for PDF preview. It is zero-dependency and works for single-page invoices. Add `react-pdf` only if you need embedded preview within a Mantine Modal with custom controls.

**Sources:**
- [react-pdf GitHub](https://github.com/wojtekmaj/react-pdf)
- [react-pdf npm](https://www.npmjs.com/package/react-pdf)
- [Nutrient: React PDF viewer guide](https://www.nutrient.io/blog/how-to-build-a-reactjs-pdf-viewer-with-react-pdf/)

---

## 7. Internationalization: react-i18next (French-first)

**Recommendation:** `react-i18next` + `i18next` + `i18next-browser-languagedetector`

**Approach:** French as default language, English as fallback. All UI strings externalized to JSON translation files from the start, even if only French is provided initially. This makes adding languages trivial later.

**Setup:**
```typescript
// src/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import fr from './locales/fr/translation.json';
import en from './locales/en/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
      en: { translation: en },
    },
    fallbackLng: 'fr', // French is the default, not English
    interpolation: { escapeValue: false },
  });

export default i18n;
```

**Translation file structure:**
```
src/
  locales/
    fr/
      translation.json   # {"members.title": "Liste des adherents", ...}
    en/
      translation.json   # {"members.title": "Member List", ...}
```

**Usage in components:**
```typescript
import { useTranslation } from 'react-i18next';

function MemberList() {
  const { t } = useTranslation();
  return <h1>{t('members.title')}</h1>;
}
```

**Practical note for this project:** Given the small scope and French-only audience, an alternative is to simply hardcode French strings directly in components and skip i18n entirely. This is the simplest approach. However, externalizing strings from day one with react-i18next adds minimal overhead and makes the codebase cleaner (no string literals scattered in JSX). **Recommendation: use react-i18next from the start.** The setup is 15 minutes, and it enforces good habits.

**Sources:**
- [react-i18next docs](https://react.i18next.com/)
- [Phrase: React localization with i18next](https://phrase.com/blog/posts/localizing-react-apps-with-i18next/)
- [Dev.to: i18n React app 2025 edition](https://dev.to/anilparmar/how-to-add-internationalization-i18n-to-a-react-app-using-i18next-2025-edition-3hkk)

---

## 8. Routing: React Router DOM v7

**Recommendation:** `react-router-dom` v7.x

**Routes for this project:**
```
/                  --> Dashboard / overview (redirect to /members)
/members           --> Member list with filters (main view)
/members/:id       --> Member detail (or use modal from list)
/invoices          --> Invoice management / status view
/statistics        --> Activity summaries and stats
/settings          --> Season selector, config display
```

**Note:** For a simple dashboard, 3-5 routes suffice. Most interaction happens on the member list page with modals for details and actions. Do not over-engineer routing.

---

## 9. Project Structure

```
frontend/
  src/
    api/                    # API client functions
      client.ts             # Axios/fetch wrapper with base URL
      members.ts            # Member API calls
      invoices.ts           # Invoice API calls
      emails.ts             # Email API calls
    components/
      layout/               # AppShell, Header, Sidebar
      members/              # MemberTable, MemberDetail, MemberFilters
      invoices/             # InvoicePreview, InvoiceActions
      common/               # Reusable components
    hooks/                  # Custom hooks (useMembers, useInvoice, etc.)
    locales/
      fr/translation.json
      en/translation.json
    pages/                  # Route-level components
      MembersPage.tsx
      InvoicesPage.tsx
      StatisticsPage.tsx
    theme/                  # Mantine theme config, ACS branding
    types/                  # TypeScript interfaces (Member, Invoice, etc.)
    App.tsx
    main.tsx
    i18n.ts
  public/
    logo.svg                # ACS logo
  index.html
  vite.config.ts
  tsconfig.json
  package.json
```

---

## 10. Full Installation Command

```bash
# Scaffold project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Mantine UI
npm install @mantine/core @mantine/hooks @mantine/notifications @mantine/dates dayjs

# Icons
npm install @tabler/icons-react

# Data table
npm install mantine-react-table

# Server state
npm install @tanstack/react-query

# Forms (start with Mantine useForm; add these later if needed)
# npm install react-hook-form zod @hookform/resolvers

# Routing
npm install react-router-dom

# Internationalization
npm install i18next react-i18next i18next-browser-languagedetector

# HTTP client
npm install axios

# Dev tools
npm install -D @tanstack/react-query-devtools
```

**Estimated `node_modules` size:** ~150-200MB (typical for a React project with these dependencies).
**Estimated production bundle:** ~300-500KB gzipped (acceptable for an internal tool).

---

## 11. Summary Decision Matrix

| Decision | Choice | Confidence | Rationale |
|----------|--------|------------|-----------|
| Build tool | Vite | HIGH | Industry standard, CRA dead, Next.js overkill |
| UI library | Mantine 7 | HIGH | Best fit for small dashboards, great DX, built-in hooks |
| Data table | Mantine React Table | HIGH | TanStack Table + Mantine styling, batteries included |
| Server state | TanStack Query v5 | HIGH | Standard for API data, no complex client state |
| Forms | Mantine useForm (start), RHF+Zod (if needed) | HIGH | Keep it simple for simple forms |
| PDF preview | iframe (start), react-pdf (if needed) | MEDIUM | Simplest approach first |
| i18n | react-i18next | HIGH | Minimal overhead, good habit, French-first |
| Routing | React Router DOM v7 | HIGH | Standard SPA routing |
| HTTP client | Axios | HIGH | Interceptors, cleaner API than fetch |
| Icons | Tabler Icons | HIGH | Mantine's recommended icon set |
