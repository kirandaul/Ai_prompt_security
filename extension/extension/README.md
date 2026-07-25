# Extension — AI Prompt Security Gateway

Chrome extension (Manifest V3) that monitors ChatGPT & Claude prompts, detects
sensitive data, blocks the send button, offers one-click auto-fix, and scans
images (screenshots) too.

## Requirements
- Google Chrome (or any Chromium browser).
- The **backend** running at `http://127.0.0.1:3000` (see `../backend`).
- *(Optional, for tests/obfuscation only)* Node.js 18+.

## Install / run
1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top-right).
3. Click **Load unpacked** and select this `extension/` folder.
4. Open ChatGPT or Claude and start typing. When you change the backend URL,
   edit `PSG_CONFIG.endpoint` in `detection.js` and reload the extension.

After any code change: `chrome://extensions` → **reload ↻** → refresh the AI tab.

## Files
| File | Purpose |
|---|---|
| `manifest.json` | Extension config (MV3), permissions, matched sites |
| `detection.js` | Detection interface (local + remote providers, config) |
| `content.js` | On-page UI, prompt/image capture, auto-fix, send-blocking |
| `styles.css` | Panel + button styling |
| `background.js` | Minimal service worker |
| `tests/` | Node test suite for the detection logic |
| `build.js` | Optional obfuscated build → `dist/` |

## Optional: tests & obfuscated build (needs Node)
```bash
npm test          # run the detection test suite (node --test)
npm install       # only needed for the obfuscator
npm run obfuscate # writes ./dist (load that instead, for a "protected" build)
```

## Config
`detection.js` → `PSG_CONFIG`:
- `mode`: `'remote'` (use backend) or `'local'` (offline keyword fallback).
- `endpoint`: backend scan URL (default `http://127.0.0.1:3000/api/scan`).
- For production, use an **HTTPS** endpoint and add it to `host_permissions` in
  `manifest.json`.
