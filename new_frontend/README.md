# Frontend — Adaptive Learning Platform

Next.js 16 App Router frontend. Proxies all API requests to the FastAPI backend via `next.config.mjs` rewrites.

## Setup

```bash
npm install
```

No `.env` file needed for local dev — the proxy defaults to `http://localhost:8001`.

### Environment variable

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_PROXY_TARGET` | `http://localhost:8001` | Backend URL for API proxy |

Only needed if backend runs on a non-default host/port.

## Development

```bash
npm run dev    # http://localhost:3000
```

All `/auth/*`, `/query/*`, `/chat/*`, `/courses/*`, etc. are rewritten to the backend automatically. No CORS configuration needed.

## Build

```bash
npm run build    # output: .next/standalone
npm run start    # requires Node.js server.js
```

Build ignores TypeScript errors (`ignoreBuildErrors: true` in `next.config.mjs`).

## Lint

```bash
npm run lint     # eslint with next/core-web-vitals
```

## Key architecture notes

- **Auth store**: zustand with localStorage persistence (`uniauth` key). Login sends `application/x-www-form-urlencoded`, not JSON.
- **API client**: `src/lib/api/client.ts` — axios instance, auto-attaches Bearer token, redirects to `/` on 401.
- **CSS**: Custom properties in `globals.css` + per-page CSS modules. No Tailwind.
- **Next.js 16**: Has breaking changes from earlier versions. See `node_modules/next/dist/docs/` before modifying framework code.
