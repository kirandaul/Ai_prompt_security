/*
 * content.js — Cybage Browser Prompt Detection UI + wiring.
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
        console.error('Cybage Browser Prompt Detection: detection.js failed to load; aborting.');
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
            
            // Get both client ID and activation key
            chrome.storage.local.get(['psg_client_id', 'psg_activation_key'], data => {
                let id = data && data.psg_client_id;
                if (!id) {
                    id = (crypto && crypto.randomUUID) ? crypto.randomUUID()
                        : 'psg-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
                    chrome.storage.local.set({ psg_client_id: id });
                }
                
                // Add context
                engine.context = { client_id: id, source, user_agent };
                
                // Add activation key if available
                if (data && data.psg_activation_key) {
                    try {
                        // Decrypt the key (using same logic as activator.js)
                        const secret = 'psg-extension-secret';
                        const encrypted = atob(data.psg_activation_key);
                        let decrypted = '';
                        for (let i = 0; i < encrypted.length; i++) {
                            decrypted += String.fromCharCode(
                                encrypted.charCodeAt(i) ^ secret.charCodeAt(i % secret.length)
                            );
                        }
                        engine.activationKey = decrypted;
                    } catch (e) {
                        console.error('Failed to decrypt activation key:', e);
                    }
                }
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
                    <span class="psg-panel-title">🔒 Cybage Browser Prompt Detection</span>
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
                    <button class="psg-add-key-btn" id="addKeyBtn" style="margin-top: 12px; width: 100%; padding: 10px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px;">🔑 Add Activation Key</button>
                </div>
            `;

            document.body.appendChild(panel);
            const closeButton = panel.querySelector('.psg-panel-close');
            if (closeButton) closeButton.addEventListener('click', () => {
                if (this.onClose) this.onClose(); else this.hidePanel();
            });
            const fixButton = panel.querySelector('.psg-fix-btn');
            if (fixButton) fixButton.addEventListener('click', () => this.applyFix());
            
            // Add Key button handler
            const addKeyButton = document.getElementById('addKeyBtn');
            if (addKeyButton) {
                addKeyButton.addEventListener('click', () => this.showAddKeyDialog());
            }

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

            // Show Add Key button ONLY when 401 Unauthorized (severity CRITICAL + "Not Authorized")
            const addKeyBtn = this.panelElement.querySelector('.psg-add-key-btn');
            if (addKeyBtn) {
                // Check if it's a 401 error by looking for "Not Authorized" in message or findings
                const messageHasUnauth = state.message && state.message.includes('Not Authorized');
                const findingsHaveUnauth = state.findings && state.findings.some(f => f.reason && f.reason.includes('Not Authorized'));
                const isUnauthorized = state.severity === 'CRITICAL' && (messageHasUnauth || findingsHaveUnauth);
                
                addKeyBtn.style.display = isUnauthorized ? 'block' : 'none';
                console.log('🔐 Button visibility:', { 
                    severity: state.severity, 
                    isUnauth: isUnauthorized,
                    display: isUnauthorized ? 'BLOCK' : 'none'
                });
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

        showAddKeyDialog() {
            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 999999;
            `;

            // Create dialog box
            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: white;
                padding: 30px;
                border-radius: 12px;
                max-width: 450px;
                width: 90%;
                box-shadow: 0 20px 50px rgba(0,0,0,0.3);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            `;

            dialog.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 40px; margin-bottom: 10px;">🔑</div>
                    <h2 style="margin: 0; color: #1f2937;">Add Activation Key</h2>
                </div>

                <div style="margin-bottom: 20px;">
                    <label style="display: block; font-size: 12px; color: #666; margin-bottom: 8px; font-weight: 600;">
                        Enter your 64-character activation key:
                    </label>
                    <input type="password" id="keyInput" placeholder="Paste your key here..." 
                        style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px; font-family: monospace; box-sizing: border-box;" />
                    <label style="display: flex; align-items: center; margin-top: 8px; font-size: 12px; color: #666; cursor: pointer;">
                        <input type="checkbox" id="showKey" style="margin-right: 6px;" />
                        Show key
                    </label>
                </div>

                <div style="margin-bottom: 20px;">
                    <button id="confirmBtn" style="width: 100%; padding: 12px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;">
                        ✅ Add Key
                    </button>
                </div>

                <div id="errorMsg" style="color: #dc2626; font-size: 12px; margin-bottom: 15px; padding: 10px; background: #fee2e2; border-radius: 6px; display: none; text-align: center;">
                </div>

                <button id="closeBtn" style="width: 100%; padding: 10px; background: #f3f4f6; color: #666; border: none; border-radius: 8px; cursor: pointer; font-size: 14px;">
                    Close
                </button>
            `;

            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            // Event handlers
            const keyInput = document.getElementById('keyInput');
            const showKeyCheckbox = document.getElementById('showKey');
            const confirmBtn = document.getElementById('confirmBtn');
            const closeBtn = document.getElementById('closeBtn');
            const errorMsg = document.getElementById('errorMsg');

            // Toggle show/hide key
            showKeyCheckbox.addEventListener('change', () => {
                keyInput.type = showKeyCheckbox.checked ? 'text' : 'password';
            });

            // Close button
            closeBtn.addEventListener('click', () => overlay.remove());
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) overlay.remove();
            });

            // Validate and save key
            const validateAndSave = () => {
                const key = keyInput.value.trim();

                // Validate: must be exactly 64 hex characters
                if (!key || key.length !== 64 || !/^[a-f0-9]{64}$/i.test(key)) {
                    errorMsg.textContent = '❌ Invalid key. Must be exactly 64 hexadecimal characters (0-9, a-f).';
                    errorMsg.style.display = 'block';
                    keyInput.style.borderColor = '#dc2626';
                    return;
                }

                // Encrypt key (XOR + Base64, same as key-prompt.js)
                const secret = 'psg-extension-secret';
                let encrypted = '';
                for (let i = 0; i < key.length; i++) {
                    encrypted += String.fromCharCode(
                        key.charCodeAt(i) ^ secret.charCodeAt(i % secret.length)
                    );
                }
                const encryptedKey = btoa(encrypted);

                // Store in chrome storage
                chrome.storage.local.set({ 'psg_activation_key': encryptedKey }, () => {
                    if (chrome.runtime.lastError) {
                        errorMsg.textContent = '❌ Failed to save key. Please try again.';
                        errorMsg.style.display = 'block';
                        return;
                    }

                    // Success
                    confirmBtn.disabled = true;
                    confirmBtn.textContent = '✅ Key saved! Reloading...';
                    confirmBtn.style.background = '#059669';

                    setTimeout(() => {
                        overlay.remove();
                        window.location.reload();
                    }, 1500);
                });
            };

            confirmBtn.addEventListener('click', validateAndSave);
            keyInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') validateAndSave();
            });

            keyInput.focus();
        }

        showAddKeyDialog() {
            // Show key input dialog (similar to key-prompt.js logic)
            const overlay = document.createElement('div');
            overlay.id = 'psg-add-key-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 999999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            `;

            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 32px;
                width: 90%;
                max-width: 450px;
                box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            `;

            dialog.innerHTML = `
                <div style="text-align: center;">
                    <div style="font-size: 40px; margin-bottom: 16px;">🔑</div>
                    <h2 style="margin: 0 0 8px 0; color: #1f2937; font-size: 20px;">Add Activation Key</h2>
                    <p style="margin: 0 0 24px 0; color: #6b7280; font-size: 14px;">
                        Enter your 64-character activation key to enable scanning
                    </p>
                </div>

                <div style="margin-bottom: 16px;">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Activation Key
                    </label>
                    <input 
                        id="psg-add-key-input"
                        type="password" 
                        placeholder="Paste your 64-character key here..."
                        style="
                            width: 100%;
                            padding: 12px;
                            border: 1px solid #d1d5db;
                            border-radius: 8px;
                            font-size: 14px;
                            font-family: monospace;
                            box-sizing: border-box;
                        "
                    />
                    <label style="display: flex; align-items: center; margin-top: 8px; font-size: 12px; color: #6b7280; cursor: pointer;">
                        <input 
                            id="psg-add-show-key"
                            type="checkbox"
                            style="margin-right: 6px; cursor: pointer;"
                        />
                        Show key
                    </label>
                </div>

                <div style="margin-bottom: 16px;">
                    <button 
                        id="psg-add-key-confirm"
                        style="
                            width: 100%;
                            padding: 12px;
                            background: linear-gradient(135deg, #059669, #10b981);
                            border: none;
                            color: white;
                            font-weight: 600;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                            transition: transform 0.15s;
                        "
                        onmouseover="this.style.transform='translateY(-2px)'"
                        onmouseout="this.style.transform='translateY(0)'"
                    >
                        ✅ Add Key
                    </button>
                </div>

                <div id="psg-add-key-error" style="
                    margin-bottom: 16px;
                    padding: 12px;
                    background: #fee2e2;
                    color: #b91c1c;
                    border: 1px solid #fca5a5;
                    border-radius: 6px;
                    font-size: 13px;
                    display: none;
                    text-align: center;
                "></div>
            `;

            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            const keyInput = document.getElementById('psg-add-key-input');
            const showKeyCheckbox = document.getElementById('psg-add-show-key');
            const confirmBtn = document.getElementById('psg-add-key-confirm');
            const errorMsg = document.getElementById('psg-add-key-error');

            showKeyCheckbox.addEventListener('change', () => {
                keyInput.type = showKeyCheckbox.checked ? 'text' : 'password';
            });

            const validateAndSave = () => {
                const key = keyInput.value.trim();
                
                if (!key || key.length !== 64 || !/^[a-f0-9]{64}$/i.test(key)) {
                    errorMsg.textContent = '❌ Invalid key format. Must be 64 hexadecimal characters.';
                    errorMsg.style.display = 'block';
                    keyInput.style.borderColor = '#fca5a5';
                    return;
                }

                // Store key (use same encryption as key-prompt.js)
                const secret = 'psg-extension-secret';
                let encrypted = '';
                for (let i = 0; i < key.length; i++) {
                    encrypted += String.fromCharCode(
                        key.charCodeAt(i) ^ secret.charCodeAt(i % secret.length)
                    );
                }
                const encryptedKey = btoa(encrypted);

                chrome.storage.local.set(
                    { 'psg_activation_key': encryptedKey },
                    () => {
                        if (chrome.runtime.lastError) {
                            errorMsg.textContent = '❌ Failed to save key. Please try again.';
                            errorMsg.style.display = 'block';
                            return;
                        }

                        // Success
                        const successMsg = document.createElement('div');
                        successMsg.style.cssText = `
                            padding: 16px;
                            background: #dcfce7;
                            color: #15803d;
                            border: 1px solid #86efac;
                            border-radius: 6px;
                            text-align: center;
                            font-weight: 600;
                            margin-bottom: 16px;
                        `;
                        successMsg.textContent = '✅ Key saved! Reloading...';
                        dialog.insertBefore(successMsg, dialog.firstChild);

                        setTimeout(() => {
                            overlay.remove();
                            window.location.reload();
                        }, 1500);
                    }
                );
            };

            confirmBtn.addEventListener('click', validateAndSave);
            keyInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') validateAndSave();
            });

            keyInput.focus();
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

    const renderCombined = () => {
        const combined = buildResult([...(lastTextResult.findings || []), ...imageFindings]);
        combined.sanitized = lastTextResult.sanitized || null;
        combined.originalText = lastTextResult.originalText || '';
        ui.updatePanel(combined);
        
        // NEW: Set global flags for critical blocker to detect CRITICAL severity
        window.__psgLastScanResult = combined;
        window.__psgLastPrompt = lastTextResult.originalText || '';
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
            console.error('Cybage Browser Prompt Detection scan error:', err);
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
    console.log('✅ Cybage Browser Prompt Detection initialized (mode-aware, document-level detection)');
})();
