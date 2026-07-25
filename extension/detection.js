/*
 * detection.js — shared detection logic for Cybage Browser Prompt Detection.
 *
 * Runs in TWO environments from the same file:
 *   - Browser (content script): attaches its API to `self.PSG`.
 *   - Node (tests): exported via module.exports.
 *
 * Detection is PLUGGABLE. Today it ships a LocalDetectionProvider (static
 * keyword rules). Later, flip PSG_CONFIG.mode to 'remote' and the exact same
 * result shape is produced by RemoteDetectionProvider, which asks your backend
 * to analyse the prompt. The rest of the extension does not change.
 */
(function (root) {
    'use strict';

    // ---- Severity model -----------------------------------------------------
    const SEVERITY_LEVELS = {
        CRITICAL: { order: 4, color: '#DC2626', backgroundColor: '#FEE2E2', borderColor: '#DC2626', icon: '🔴' },
        HIGH:     { order: 3, color: '#EA580C', backgroundColor: '#FFEDD5', borderColor: '#EA580C', icon: '🟠' },
        MEDIUM:   { order: 2, color: '#EAB308', backgroundColor: '#FEF3C7', borderColor: '#EAB308', icon: '🟡' },
        LOW:      { order: 1, color: '#3B82F6', backgroundColor: '#EFF6FF', borderColor: '#3B82F6', icon: '🔵' },
        SAFE:     { order: 0, color: '#16A34A', backgroundColor: '#DCFCE7', borderColor: '#16A34A', icon: '✅' }
    };

    const VALID_SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE'];

    // Default local rules. When you move to the API, the backend owns this list
    // instead and the extension ships with none of it.
    const DEFAULT_RULES = [
        { keyword: 'password',    severity: 'CRITICAL', reason: 'Password Detected', action: 'BLOCK' },
        { keyword: 'aws',         severity: 'HIGH',     reason: 'AWS Secret',        action: 'BLOCK' },
        { keyword: 'secret',      severity: 'HIGH',     reason: 'Secret Information', action: 'BLOCK' },
        { keyword: 'private key', severity: 'CRITICAL', reason: 'Private Key',       action: 'BLOCK' },
        { keyword: 'credit card', severity: 'CRITICAL', reason: 'Credit Card',       action: 'BLOCK' },
        { keyword: 'kiran',       severity: 'MEDIUM',   reason: 'Personal Name',     action: 'WARN'  }
    ];

    // Never scan or transmit more than this many characters. Protects against
    // pathological input and limits how much text leaves the browser in remote
    // mode.
    const MAX_SCAN_LENGTH = 20000;

    // ---- Pure helpers -------------------------------------------------------

    function severityOrder(severity) {
        const info = SEVERITY_LEVELS[severity];
        return info ? info.order : 0;
    }

    // Coerce anything (including untrusted API output) into a safe finding.
    // Strips control characters and angle brackets and caps length so a
    // malicious backend response cannot smuggle markup or huge blobs into the UI.
    function normalizeFinding(raw) {
        if (!raw || typeof raw !== 'object') return null;
        let severity = String(raw.severity || '').toUpperCase();
        if (!VALID_SEVERITIES.includes(severity)) severity = 'MEDIUM';
        const clean = value => String(value == null ? '' : value)
            .replace(/[\u0000-\u001F\u007F<>]/g, '')
            .slice(0, 200)
            .trim();
        const reason = clean(raw.reason) || 'Sensitive information';
        const keyword = clean(raw.keyword);
        const action = raw.action === 'WARN' ? 'WARN' : 'BLOCK';
        return { keyword, severity, reason, action };
    }

    function highestSeverity(findings) {
        let highest = 'SAFE';
        for (const f of findings) {
            if (severityOrder(f.severity) > severityOrder(highest)) highest = f.severity;
        }
        return highest;
    }

    function statusFor(severity) {
        return {
            CRITICAL: 'BLOCKED', HIGH: 'BLOCKED',
            MEDIUM: 'WARNING', LOW: 'WARNING', SAFE: 'SAFE'
        }[severity] || 'UNKNOWN';
    }

    function messageFor(severity) {
        return {
            CRITICAL: 'Remove sensitive information before sending.',
            HIGH: 'Remove sensitive information before sending.',
            MEDIUM: 'Review before sending. Contains potential personal information.',
            LOW: 'Consider reviewing for sensitive content.',
            SAFE: 'No sensitive information detected.'
        }[severity] || 'Unknown severity level.';
    }

    // Turn a list of findings into the canonical result object the UI consumes.
    // This is the single source of truth for result shape across all providers.
    function buildResult(rawFindings) {
        const findings = (Array.isArray(rawFindings) ? rawFindings : [])
            .map(normalizeFinding)
            .filter(Boolean);

        // De-duplicate by reason, keeping first occurrence.
        const seen = new Set();
        const deduped = [];
        for (const f of findings) {
            if (!seen.has(f.reason)) {
                seen.add(f.reason);
                deduped.push(f);
            }
        }

        if (deduped.length === 0) {
            return {
                status: 'SAFE', severity: 'SAFE', findings: [],
                allowSend: true, message: messageFor('SAFE')
            };
        }

        const severity = highestSeverity(deduped);
        return {
            status: statusFor(severity),
            severity,
            findings: deduped,
            allowSend: !['CRITICAL', 'HIGH'].includes(severity),
            message: messageFor(severity)
        };
    }

    function safeResult() {
        return { status: 'SAFE', severity: 'SAFE', findings: [], allowSend: true, message: messageFor('SAFE') };
    }

    // ---- Providers ----------------------------------------------------------

    // Static keyword matching, fully offline. No prompt ever leaves the browser.
    class LocalDetectionProvider {
        constructor(rules) {
            this.rules = Array.isArray(rules) ? rules : DEFAULT_RULES;
        }

        // Async to keep one interface with the remote provider.
        async scan(text) {
            if (!text || !text.trim()) return safeResult();
            const lower = text.toLowerCase();
            const findings = [];
            for (const rule of this.rules) {
                if (lower.includes(String(rule.keyword).toLowerCase())) {
                    findings.push({
                        keyword: rule.keyword,
                        severity: rule.severity,
                        reason: rule.reason,
                        action: rule.action
                    });
                }
            }
            return buildResult(findings);
        }
    }

    // Sends the prompt to your backend for analysis. Security notes:
    //   - Uses POST with a JSON body (never the query string), so the prompt is
    //     not written into URLs, server access logs, or browser history.
    //   - Times out via AbortController so a slow/hung backend cannot freeze UI.
    //   - On any error, falls back per config (default: local rules), so the
    //     gateway keeps working even if the backend is down.
    class RemoteDetectionProvider {
        constructor(options) {
            options = options || {};
            this.endpoint = options.endpoint;
            this.timeoutMs = options.timeoutMs || 4000;
            this.onError = options.onError || 'local'; // 'local' | 'safe' | 'block'
            this.fallback = options.fallback || new LocalDetectionProvider();
            this._fetch = options.fetchImpl || (typeof fetch !== 'undefined' ? fetch.bind(root) : null);
            // Identifies which extension install / site sent the prompt. Set by
            // content.js once the client id has been read from chrome.storage.
            this.context = options.context || {};
        }

        _errorResult(text) {
            if (this.onError === 'safe') return safeResult();
            if (this.onError === 'block') {
                return buildResult([{ severity: 'HIGH', reason: 'Detection service unavailable', action: 'BLOCK' }]);
            }
            return this.fallback.scan(text); // 'local'
        }

        async scan(text) {
            if (!text || !text.trim()) return safeResult();
            if (!this.endpoint || !this._fetch) return this._errorResult(text);

            const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
            const timer = controller ? setTimeout(() => controller.abort(), this.timeoutMs) : null;
            try {
                const res = await this._fetch(this.endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(Object.assign({ prompt: text }, this.context)),
                    signal: controller ? controller.signal : undefined
                });
                if (!res || !res.ok) return this._errorResult(text);
                const data = await res.json();
                // Accept either { findings: [...] } or a bare array of findings.
                if (data && Array.isArray(data.findings)) {
                    const res = buildResult(data.findings);
                    // Carry the backend's auto-correct text through to the UI.
                    if (typeof data.sanitized === 'string') res.sanitized = data.sanitized;
                    return res;
                }
                if (Array.isArray(data)) return buildResult(data);
                return safeResult();
            } catch (_err) {
                return this._errorResult(text);
            } finally {
                if (timer) clearTimeout(timer);
            }
        }
    }

    // ---- Configuration & engine --------------------------------------------

    // EDIT THIS to switch modes. `local` = offline keywords (default).
    // `remote` = call your backend. Endpoint must be HTTPS in production and
    // listed in manifest.json host_permissions.
    const PSG_CONFIG = {
        mode: 'remote',
        endpoint: 'http://127.0.0.1:3000/api/scan',
        timeoutMs: 4000,
        onError: 'local'
    };

    function createEngine(config) {
        const cfg = Object.assign({}, PSG_CONFIG, config || {});
        if (cfg.mode === 'remote') {
            return new RemoteDetectionProvider({
                endpoint: cfg.endpoint,
                timeoutMs: cfg.timeoutMs,
                onError: cfg.onError,
                fetchImpl: cfg.fetchImpl,
                context: cfg.context
            });
        }
        return new LocalDetectionProvider(cfg.rules);
    }

    const api = {
        SEVERITY_LEVELS,
        DEFAULT_RULES,
        MAX_SCAN_LENGTH,
        buildResult,
        normalizeFinding,
        safeResult,
        LocalDetectionProvider,
        RemoteDetectionProvider,
        createEngine,
        PSG_CONFIG
    };

    root.PSG = api;
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof self !== 'undefined' ? self : globalThis);
