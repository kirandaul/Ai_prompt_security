# Dashboard — Admin Security Console

React + Vite admin console. Login, KPIs, charts, filters, and a live newest-first
event feed. Talks only to the backend API.

## Requirements
- **Node.js 18+** (includes npm)
- The **backend** running at `http://127.0.0.1:3000` (see `../backend`).

## Install & run
```bash
cd dashboard
npm install
npm run dev
```
Open **http://localhost:5173** and log in with **admin / admin123**.

Vite proxies `/api/*` to the backend (see `vite.config.js`), so the browser makes
only same-origin calls — no CORS setup needed. If your backend runs elsewhere,
change the `target` in `vite.config.js`.

## Build for production
```bash
npm run build      # outputs static files to dist/
npm run preview    # preview the production build
```
Serve `dist/` behind any static host (and point it at your backend).

## Structure
| File | Purpose |
|---|---|
| `src/App.jsx` | Login, stat cards, filters, events table |
| `src/charts.jsx` | Dependency-free SVG charts (donut, area, bars) |
| `src/api.js` | Fetch wrappers for the backend |
| `src/styles.css` | Light theme |
| `vite.config.js` | Dev server + `/api` proxy |

## Moving to another laptop
Delete `node_modules/` before zipping to keep it small; run `npm install` on the
new machine to rebuild it.
