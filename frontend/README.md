# ACS HelloAsso - Frontend

Web interface to manage ACS member invoices.

## Tech Stack

- **Svelte 5** with runes ($state, $derived)
- **TypeScript**
- **Vite** for build
- **TailwindCSS + DaisyUI** for styling
- **Chart.js** for charts

## Development

```bash
npm install    # install dependencies
npm run dev    # start dev server (http://localhost:5173)
```

## Production Build

```bash
npm run build    # generate files in dist/
npm run preview  # preview the build
```

## Structure

```
src/
├── components/     # Reusable components
│   ├── Layout.svelte
│   ├── Navbar.svelte
│   ├── MemberTable.svelte
│   └── ...
├── pages/          # Application pages
│   ├── Login.svelte
│   ├── Dashboard.svelte
│   ├── Members.svelte
│   └── Graphs.svelte
├── lib/            # Utilities
│   ├── api.ts      # API client
│   ├── types.ts    # TypeScript types
│   ├── constants.ts
│   └── chart-utils.ts
└── App.svelte      # Entry point + router
```

## Tests

```bash
npx vitest run  # run tests
npx vitest      # watch mode
```
