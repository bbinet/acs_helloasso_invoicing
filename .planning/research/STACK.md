# Technology Stack

**Project:** ACS HelloAsso Invoicing Dashboard
**Researched:** 2026-03-25

## Recommended Stack

### Build Tool & Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Vite | 6.x | Build tool & dev server | Industry standard for React SPAs. Instant HMR, fast builds. CRA is deprecated. Next.js is overkill -- this is an SPA served by Python, not an SSR app. |
| React | 18.x | UI framework | Stable, massive ecosystem. React 19 is available but 18 is safer for library compatibility. |
| TypeScript | 5.5+ | Type safety | Required for Zod integration, better DX with Mantine and TanStack |

### UI Component Library
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Mantine | 7.x | Component library | Best fit for small dashboards. Built-in hooks (useForm, useDisclosure), dark mode, excellent docs. Less bloated than Ant Design. More batteries-included than shadcn/ui. |
| @mantine/core | 7.x | Core components | Buttons, modals, inputs, layouts, navigation |
| @mantine/hooks | 7.x | Utility hooks | useMediaQuery, useDisclosure, useClipboard, etc. |
| @mantine/notifications | 7.x | Toast notifications | For email sent/failed feedback, invoice generation status |
| @tabler/icons-react | latest | Icons | Mantine's recommended icon set |

### Data Table
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| mantine-react-table | 2.x | Data grid | Built on TanStack Table v8, styled with Mantine. Provides sorting, filtering, pagination, row selection out of the box. No need to wire TanStack Table manually. MIT licensed. |

### Server State Management
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| @tanstack/react-query | 5.x | API data fetching & caching | Handles caching, deduplication, background refetch, loading/error states. Eliminates manual useEffect fetching. The standard for React server state. |

### Forms & Validation
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| react-hook-form | 7.x | Form state management | Minimal re-renders, great TypeScript support, lightweight |
| zod | 3.x | Schema validation | TypeScript-native type inference with z.infer. Schemas reusable on backend. |
| @hookform/resolvers | 3.x | Zod-RHF bridge | Connects Zod schemas to react-hook-form validation |

### PDF Preview
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| react-pdf | 10.x | PDF viewer in browser | MIT licensed, based on PDF.js, most popular React PDF viewer. Display server-generated PDFs inline. |

### Internationalization
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| react-i18next | latest | i18n framework | Industry standard for React i18n. Supports French-first with English fallback. Hooks-based API (useTranslation). |
| i18next | latest | i18n core | Core library used by react-i18next |
| i18next-browser-languagedetector | latest | Language detection | Auto-detect browser language preference |

### Routing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| react-router-dom | 7.x | Client-side routing | Standard SPA routing. Pages: members list, member detail, invoice generation, email management, statistics |

### Development Tools
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| ESLint | 9.x | Linting | Code quality enforcement |
| Prettier | 3.x | Formatting | Consistent code style |
| @tanstack/react-query-devtools | 5.x | Query debugging | Inspect cache state during development |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Build tool | Vite | Next.js | SSR/SSG unnecessary; SPA served by FastAPI. Next.js adds complexity (file-based routing, server components) with no benefit here. |
| Build tool | Vite | CRA | Deprecated. Slow builds. No longer maintained. |
| UI library | Mantine | Ant Design | Overkill for small project. Docs have Chinese-only sections. Harder to customize. No built-in hooks. |
| UI library | Mantine | shadcn/ui | Requires Tailwind (extra dependency). Fewer pre-built components (48 vs 120+). Copy-paste model means more maintenance for a small team. |
| UI library | Mantine | Material UI | Heavier bundle, enterprise-oriented, less cohesive hooks ecosystem |
| Data table | mantine-react-table | AG Grid | Commercial license for advanced features. Overkill for this use case. |
| Data table | mantine-react-table | Mantine DataTable | Less feature-rich than MRT for filtering/sorting/pagination |
| State mgmt | TanStack Query | Redux/Zustand | No complex client state to manage. All data comes from API. TanStack Query handles server state perfectly. |
| Forms | RHF + Zod | Formik + Yup | Formik has more re-renders, Yup has weaker TypeScript inference |
| PDF | react-pdf | @react-pdf-viewer | Commercial license required |
| i18n | react-i18next | FormatJS/react-intl | react-i18next has better ecosystem, more tutorials, simpler API |

## Installation

```bash
# Scaffold
npm create vite@latest frontend -- --template react-ts
cd frontend

# Core UI
npm install @mantine/core @mantine/hooks @mantine/notifications @tabler/icons-react

# Data table
npm install mantine-react-table

# Server state
npm install @tanstack/react-query

# Forms & validation
npm install react-hook-form zod @hookform/resolvers

# Routing
npm install react-router-dom

# PDF preview
npm install react-pdf

# Internationalization
npm install i18next react-i18next i18next-browser-languagedetector

# Dev dependencies
npm install -D @tanstack/react-query-devtools @types/react @types/react-dom
```

## Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'  // Proxy to FastAPI in dev
    }
  },
  build: {
    outDir: 'dist',  // FastAPI serves this in production
  }
});
```

## Sources

- [Vite docs](https://vite.dev/)
- [Mantine docs](https://mantine.dev/)
- [Mantine React Table](https://www.mantine-react-table.com/)
- [TanStack Query docs](https://tanstack.com/query/latest)
- [React Hook Form docs](https://react-hook-form.com/)
- [Zod docs](https://zod.dev/)
- [react-pdf GitHub](https://github.com/wojtekmaj/react-pdf)
- [react-i18next docs](https://react.i18next.com/)
- [Makers Den: React UI libs comparison 2025](https://makersden.io/blog/react-ui-libs-2025-comparing-shadcn-radix-mantine-mui-chakra)
- [Subframe: Ant Design vs Mantine 2025](https://www.subframe.com/tips/ant-design-vs-mantine-162ef)
