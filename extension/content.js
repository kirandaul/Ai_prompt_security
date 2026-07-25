/*
 * content.js — Prompt Security Gateway UI + wiring.
 *
 * Detection logic lives in detection.js (loaded first via the manifest and
 * exposed on `self.PSG`). This file only:
 *   - reads the visible prompt text on ChatGPT / Claude,
 *   - asks the detection engine (local rules today, backend API later),
 *   - renders the result panel and enables/disables the send button.
 *
 * Rendering is XSS-safe: all dynamic text goes through textContent, never
 * innerHTML — important because in "remote" mode the finding text comes from
 * the backend and must be treated as untrusted.
 */
(function () {
    'use strict';

    if (!self.PSG) {
        console.error('Prompt Security Gateway: detection.js failed to load; aborting.');
        return;
    }

    const { SEVERITY_LEVELS, createEngine, MAX_SCAN_LENGTH, buildResult, PSG_CONFIG } = self.PSG;

    // The engine reads PSG_CONFIG (mode: 'local' | 'remote'). Switch modes by
    // editing detection.js — no changes needed here.
    const engine = createEngine();

    // Give this browser install a stable anonymous id so the backend can tell
    // WHICH extension/browser a prompt came from (not a real identity — add
    // login for that). Stored in chrome.storage.local, persists across reloads.
    (function initClientContext() {
        const source = location.hostname;          // chatgpt.com / claude.ai
        const user_agent = navigator.userAgent;    // browser/OS (real OS hostname
                                                    // is not exposed to web pages)
        try {
            if (!chrome || !chrome.storage || !chrome.storage.local) {
                engine.context = { source, user_agent };
                return;
            }
            chrome.storage.local.get(['psg_client_id'], data => {
                let id = data && data.psg_client_id;
                if (!id) {
                    id = (crypto && crypto.randomUUID) ? crypto.randomUUID()
                        : 'psg-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
                    chrome.storage.local.set({ psg_client_id: id });
                }
                engine.context = { client_id: id, source, user_agent };
            });
        } catch (_e) {
            engine.context = { source, user_agent };
        }
    })();

    // ---- UI -----------------------------------------------------------------
    class SecurityUI {
        constructor() {
            this.panelId = 'psg-security-panel';
            this.panelElement = null;
            this.currentState = null;
        }

        createPanel() {
            const existing = document.getElementById(this.panelId);
            if (existing) {
                this.panelElement = existing;
                return existing;
            }

            const panel = document.createElement('div');
            panel.id = this.panelId;
            panel.className = 'psg-panel psg-panel-safe psg-fixed-panel';
            // Static shell only — no dynamic/untrusted data in this markup.
            panel.innerHTML = `
                <button class="psg-panel-close" aria-label="Close security panel">×</button>
                <div class="psg-panel-header">
                    <span class="psg-panel-title">🔒 Prompt Security Gateway</span>
                </div>
                <div class="psg-panel-content">
                    <div class="psg-status-row">
                        <span class="psg-label">Severity:</span>
                        <span class="psg-severity-value psg-severity-safe">✅ SAFE</span>
                    </div>
                    <div class="psg-status-row">
                        <span class="psg-label">Status:</span>
                        <span class="psg-status-value">OK</span>
                    </div>
                    <div class="psg-findings"></div>
                    <div class="psg-recommendation">
                        <span class="psg-rec-label">Recommendation:</span>
                        <span class="psg-rec-text"></span>
                    </div>
                    <button class="psg-fix-btn" style="display:none">✨ Auto-fix &amp; replace</button>
                </div>
            `;

            document.body.appendChild(panel);
            const closeButton = panel.querySelector('.psg-panel-close');
            if (closeButton) closeButton.addEventListener('click', () => {
                if (this.onClose) this.onClose(); else this.hidePanel();
            });
            const fixButton = panel.querySelector('.psg-fix-btn');
            if (fixButton) fixButton.addEventListener('click', () => this.applyFix());

            this.panelElement = panel;
            return panel;
        }

        // Replace the sensitive value(s) in the live prompt box with the
        // backend's sanitized text (e.g. the phone number becomes
        // "[REDACTED:Phone Number]") so the user can send a safe version.
        applyFix() {
            const sanitized = this.currentSanitized;
            if (!sanitized) return;
            const el = findPromptInput();
            if (!el) return;
            el.focus();

            if ('value' in el) {                       // <textarea>
                el.value = sanitized;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                return;
            }

            // contenteditable / ProseMirror (ChatGPT + Claude).
            const selectAll = () => {
                const sel = window.getSelection();
                sel.removeAllRanges();
                const range = document.createRange();
                range.selectNodeContents(el);
                sel.addRange(range);
            };

            selectAll();
            document.execCommand('insertText', false, sanitized);

            // Some editors (notably ChatGPT's) mangle a multi-word insertText and
            // keep only the last chunk. Verify and, if wrong, retry via a paste
            // event — which ProseMirror inserts atomically as one block.
            setTimeout(() => {
                const norm = s => (s || '').replace(/\s+/g, ' ').trim();
                if (norm(el.innerText) !== norm(sanitized)) {
                    selectAll();
                    try {
                        const dt = new DataTransfer();
                        dt.setData('text/plain', sanitized);
                        el.dispatchEvent(new ClipboardEvent('paste', {
                            clipboardData: dt, bubbles: true, cancelable: true,
                        }));
                    } catch (_e) { /* older browsers */ }
                }
            }, 50);
        }

        updatePanel(state) {
            this.currentState = state;

            // Only show the panel when there is something to report; keep it
            // hidden when the prompt is safe/empty (no auto popup on load).
            if (!state.findings || state.findings.length === 0) {
                this.hidePanel();
                this.enableSend();
                return;
            }

            // Re-create the panel if it was closed or removed from the DOM, so
            // later detections still surface (fixes "only worked the first time").
            if (!this.panelElement || !document.body.contains(this.panelElement)) {
                this.panelElement = null;
                this.createPanel();
            }

            const levelInfo = SEVERITY_LEVELS[state.severity] || SEVERITY_LEVELS.MEDIUM;
            const sev = state.severity.toLowerCase();

            this.panelElement.className = `psg-panel psg-panel-${sev} psg-fixed-panel`;
            this.panelElement.style.backgroundColor = levelInfo.backgroundColor;
            this.panelElement.style.borderColor = levelInfo.borderColor;

            const severityEl = this.panelElement.querySelector('.psg-severity-value');
            if (severityEl) {
                severityEl.textContent = `${levelInfo.icon} ${state.severity}`;
                severityEl.style.color = levelInfo.color;
                severityEl.className = `psg-severity-value psg-severity-${sev}`;
            }

            const statusEl = this.panelElement.querySelector('.psg-status-value');
            if (statusEl) {
                statusEl.textContent = state.status;
                statusEl.style.color = levelInfo.color;
            }

            // Build findings with DOM APIs + textContent — never innerHTML with
            // finding text (which may come from the backend and be untrusted).
            const findingsEl = this.panelElement.querySelector('.psg-findings');
            if (findingsEl) {
                findingsEl.textContent = '';
                for (const finding of state.findings) {
                    const item = document.createElement('span');
                    const fsev = String(finding.severity || 'medium').toLowerCase();
                    item.className = `psg-finding-item psg-finding-${fsev}`;
                    item.textContent = `• ${finding.reason}`;
                    findingsEl.appendChild(item);
                }
            }

            const recEl = this.panelElement.querySelector('.psg-rec-text');
            if (recEl) {
                recEl.textContent = state.message;
                recEl.style.color = levelInfo.color;
            }

            // Offer the auto-fix button when the backend returned a sanitized
            // version that differs from what the user typed.
            this.currentSanitized = state.sanitized || null;
            const fixBtn = this.panelElement.querySelector('.psg-fix-btn');
            if (fixBtn) {
                const currentText = state.originalText || '';
                const canFix = this.currentSanitized && this.currentSanitized !== currentText;
                fixBtn.style.display = canFix ? 'block' : 'none';
            }

            if (state.allowSend) {
                this.enableSend();
            } else {
                this.disableSend();
            }
        }

        hidePanel() {
            if (this.panelElement && this.panelElement.parentNode) {
                this.panelElement.parentNode.removeChild(this.panelElement);
            }
            this.panelElement = null;
        }

        _findSendButton() {
            // Re-query every time — ChatGPT/Claude re-render the send button, so
            // a cached reference goes stale and enabling/disabling stops working.
            const selectors = [
                'button[data-testid="send-button"]',
                'button[aria-label*="Send" i]',
                'button[type="submit"]'
            ];
            for (const selector of selectors) {
                const btn = document.querySelector(selector);
                if (btn) return btn;
            }
            return null;
        }

        enableSend() {
            const btn = this._findSendButton();
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('psg-button-disabled');
                btn.title = '';
            }
        }

        disableSend() {
            const btn = this._findSendButton();
            if (btn) {
                btn.disabled = true;
                btn.classList.add('psg-button-disabled');
                btn.title = 'Cannot send: Contains sensitive information';
            }
        }
    }

    // ---- Prompt detection / wiring -----------------------------------------
    const promptSelectors = [
        '.ProseMirror[contenteditable="true"]',
        'div[role="textbox"][contenteditable="true"]',
        'textarea[name="prompt-textarea"]',
        'textarea'
    ];

    const isVisible = node =>
        node && node.getClientRects().length > 0 && window.getComputedStyle(node).visibility !== 'hidden';

    const findPromptInput = () => {
        for (const selector of promptSelectors) {
            for (const node of document.querySelectorAll(selector)) {
                if (isVisible(node)) return node;
            }
        }
        return null;
    };

    const isInsidePrompt = node => {
        if (!node || node.nodeType !== 1) return false;
        for (const selector of promptSelectors) {
            if (node.closest && node.closest(selector)) return true;
        }
        return false;
    };

    const getPromptText = el => {
        if (!el) return '';
        const raw = ('value' in el) ? (el.value || '') : (el.innerText || el.textContent || '');
        return raw.length > MAX_SCAN_LENGTH ? raw.slice(0, MAX_SCAN_LENGTH) : raw;
    };

    const ui = new SecurityUI();
    let debounceTimer = null;
    let scanSeq = 0;        // race guard: only the latest scan may update the UI
    let lastScanned = null; // last prompt text we actually sent to the engine
    let lastTextResult = { findings: [], sanitized: null, originalText: '' };
    let imageFindings = []; // findings from the last scanned image (if sensitive)

    // Merge the current text findings with any image findings into ONE panel.
    const renderCombined = () => {
        const combined = buildResult([...(lastTextResult.findings || []), ...imageFindings]);
        combined.sanitized = lastTextResult.sanitized || null;
        combined.originalText = lastTextResult.originalText || '';
        ui.updatePanel(combined);
    };

    const scanAndUpdate = async () => {
        // Always read from whichever prompt box is currently visible, rather
        // than one element captured at load (ChatGPT re-renders its composer).
        const promptInput = findPromptInput();
        const text = promptInput ? getPromptText(promptInput) : '';

        // KEY GUARD: only call the backend when the text actually changed.
        // Otherwise idle ticks / re-renders would re-send the same prompt.
        if (text === lastScanned) return;
        lastScanned = text;

        const seq = ++scanSeq;
        try {
            const result = await engine.scan(text);
            if (seq === scanSeq) {
                lastTextResult = {
                    findings: result.findings || [],
                    sanitized: result.sanitized || null,
                    originalText: text,
                };
                renderCombined();
            }
        } catch (err) {
            console.error('Prompt Security Gateway scan error:', err);
        }
    };

    // ---- Image scanning (OCR on the backend) --------------------------------
    const imageEndpoint = (engine.endpoint || (PSG_CONFIG && PSG_CONFIG.endpoint) || '')
        .replace(/\/scan$/, '/scan-image');
    const imageScanEnabled = PSG_CONFIG && PSG_CONFIG.mode === 'remote' && imageEndpoint;

    const scanImageBlob = blob => {
        if (!imageScanEnabled || !blob) return;
        if (blob.size > 8 * 1024 * 1024) return; // 8 MB cap
        const reader = new FileReader();
        reader.onload = () => {
            const payload = Object.assign({ image: reader.result }, engine.context || {});
            fetch(imageEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
                .then(r => r.json())
                .then(data => {
                    imageFindings = (data && Array.isArray(data.findings)) ? data.findings : [];
                    renderCombined();
                })
                .catch(() => { /* backend unavailable — ignore */ });
        };
        reader.readAsDataURL(blob);
    };

    const handleImages = fileList => {
        if (!fileList) return;
        for (const f of fileList) {
            if (f && f.type && f.type.indexOf('image/') === 0) scanImageBlob(f);
        }
    };

    document.addEventListener('paste', e => {
        const items = e.clipboardData && e.clipboardData.items;
        if (!items) return;
        for (const it of items) {
            if (it.type && it.type.indexOf('image/') === 0) {
                const blob = it.getAsFile();
                if (blob) scanImageBlob(blob);
            }
        }
    }, true);
    document.addEventListener('drop', e => {
        handleImages(e.dataTransfer && e.dataTransfer.files);
    }, true);
    document.addEventListener('change', e => {
        const t = e.target;
        if (t && t.tagName === 'INPUT' && t.type === 'file') handleImages(t.files);
    }, true);

    // Closing the panel dismisses any image warning and re-checks the text only.
    ui.onClose = () => {
        imageFindings = [];
        lastScanned = null;
        ui.hidePanel();
        scanAndUpdate();
    };

    // Debounced path: a burst of typing collapses into ONE scan after a short
    // pause. 250ms keeps the panel feeling instant without scanning mid-word.
    const scheduleScan = () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(scanAndUpdate, 250);
    };

    // Document-level capture listeners catch typing/pasting in ANY prompt box
    // on either site and survive composer re-renders. This is the ONLY thing
    // that reacts to user input — no DOM-wide MutationObserver, which used to
    // fire thousands of times while ChatGPT streamed its reply and froze the UI.
    const onDocEvent = event => {
        if (isInsidePrompt(event.target)) scheduleScan();
    };
    document.addEventListener('input', onDocEvent, true);
    document.addEventListener('paste', onDocEvent, true);

    // Lightweight safety tick (composer appearing, box cleared after send).
    // The text-change guard makes idle ticks essentially free — no API call
    // unless the prompt actually changed.
    setInterval(scheduleScan, 1500);

    scanAndUpdate();
    console.log('✅ Prompt Security Gateway initialized (mode-aware, document-level detection)');
})();
