/**
 * key-prompt.js — Extension Key Input Dialog
 * 
 * Shows on first load if no key is stored.
 * User must enter activation key before extension can work.
 */

class KeyPromptDialog {
    constructor() {
        this.storageKey = 'psg_activation_key';
        this.init();
    }

    /**
     * Initialize - check if key exists, show dialog if not
     */
    async init() {
        const hasKey = await this.checkKeyExists();
        
        if (!hasKey) {
            console.log('🔐 No activation key found - showing input dialog');
            this.showKeyInputDialog();
        }
    }

    /**
     * Check if activation key is already stored
     */
    async checkKeyExists() {
        return new Promise((resolve) => {
            try {
                chrome.storage.local.get([this.storageKey], (result) => {
                    const hasKey = !!result[this.storageKey];
                    resolve(hasKey);
                });
            } catch (e) {
                resolve(false);
            }
        });
    }

    /**
     * Show modal dialog for key input
     */
    showKeyInputDialog() {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.id = 'psg-key-prompt-overlay';
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

        // Create dialog
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
                <div style="font-size: 40px; margin-bottom: 16px;">🔐</div>
                <h2 style="margin: 0 0 8px 0; color: #1f2937; font-size: 20px;">Activate Extension</h2>
                <p style="margin: 0 0 24px 0; color: #6b7280; font-size: 14px;">
                    Enter your activation key to enable the extension
                </p>
            </div>

            <div style="margin-bottom: 16px;">
                <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                    Activation Key
                </label>
                <input 
                    id="psg-key-input"
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
                        id="psg-show-key"
                        type="checkbox"
                        style="margin-right: 6px; cursor: pointer;"
                    />
                    Show key
                </label>
            </div>

            <div style="margin-bottom: 16px;">
                <button 
                    id="psg-activate-btn"
                    style="
                        width: 100%;
                        padding: 12px;
                        background: linear-gradient(135deg, #6366f1, #8b5cf6);
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
                    🔓 Activate
                </button>
            </div>

            <div id="psg-error-msg" style="
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

            <div style="text-align: center; font-size: 12px; color: #9ca3af;">
                <p style="margin: 0 0 8px 0;">Don't have a key?</p>
                <p style="margin: 0;">
                    Contact your administrator at
                    <br/>
                    <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">http://localhost:3000</code>
                </p>
            </div>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        // Setup event listeners
        const keyInput = document.getElementById('psg-key-input');
        const showKeyCheckbox = document.getElementById('psg-show-key');
        const activateBtn = document.getElementById('psg-activate-btn');
        const errorMsg = document.getElementById('psg-error-msg');

        // Toggle password visibility
        showKeyCheckbox.addEventListener('change', () => {
            keyInput.type = showKeyCheckbox.checked ? 'text' : 'password';
        });

        // Activate button
        activateBtn.addEventListener('click', () => this.validateAndStore(keyInput, errorMsg, overlay));

        // Enter key
        keyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateAndStore(keyInput, errorMsg, overlay);
            }
        });

        // Focus input
        keyInput.focus();
    }

    /**
     * Validate key format and store
     */
    async validateAndStore(keyInput, errorMsg, overlay) {
        const key = keyInput.value.trim();

        // Validate format (64 hex chars)
        if (!key || key.length !== 64 || !/^[a-f0-9]{64}$/i.test(key)) {
            errorMsg.textContent = '❌ Invalid key format. Must be 64 hexadecimal characters.';
            errorMsg.style.display = 'block';
            keyInput.style.borderColor = '#fca5a5';
            return;
        }

        // Store key
        try {
            await new Promise((resolve, reject) => {
                chrome.storage.local.set(
                    { [this.storageKey]: this.encryptKey(key) },
                    () => {
                        if (chrome.runtime.lastError) {
                            reject(chrome.runtime.lastError);
                        } else {
                            resolve();
                        }
                    }
                );
            });

            // Success
            errorMsg.textContent = '';
            errorMsg.style.display = 'none';
            keyInput.style.borderColor = '#d1d5db';

            // Show success message
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
            successMsg.textContent = '✅ Activation key saved! Reloading page...';
            keyInput.parentElement.parentElement.insertBefore(successMsg, keyInput.parentElement);

            // Remove dialog and reload
            setTimeout(() => {
                overlay.remove();
                window.location.reload();
            }, 1500);
        } catch (e) {
            errorMsg.textContent = '❌ Failed to save key. Please try again.';
            errorMsg.style.display = 'block';
        }
    }

    /**
     * Encrypt key for storage (XOR + Base64)
     */
    encryptKey(key) {
        const secret = 'psg-extension-secret';
        let encrypted = '';
        for (let i = 0; i < key.length; i++) {
            encrypted += String.fromCharCode(
                key.charCodeAt(i) ^ secret.charCodeAt(i % secret.length)
            );
        }
        return btoa(encrypted);
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new KeyPromptDialog();
    });
} else {
    new KeyPromptDialog();
}
