/**
 * critical_blocker.js — Critical Severity Blocking System
 * 
 * BLOCKS ALL SUBMISSION METHODS when sensitive data detected:
 * 1. ✅ Disable the send/submit button
 * 2. ✅ Prevent form submissions
 * 3. ✅ Block ALL Enter keys (keyboard numpad + regular)
 * 4. ✅ Show instant popup when user tries to submit
 * 5. ✅ Real-time auto-unblock when data removed
 */

class CriticalSeverityBlocker {
    constructor() {
        this.isBlocked = false;
        this.blockedFindings = [];
        this.lastScanResult = null;
        this.promptInput = null;
        this.init();
    }

    /**
     * Initialize blocking system
     */
    init() {
        console.log('🔒 Critical Severity Blocker initialized - BLOCKING ALL SUBMISSION METHODS');
        
        // Set up all blocking layers
        this.interceptFormSubmissions();
        this.interceptButtonClicks();
        this.interceptEnterKeyComplete();
        this.monitorScanResults();
    }
    
    /**
     * Monitor scan results every 300ms for auto-unblock
     */
    monitorScanResults() {
        setInterval(() => {
            if (!window.__psgLastScanResult) return;
            
            const result = window.__psgLastScanResult;
            const blockedFindings = result.findings?.filter(f => {
                const severity = f.severity;
                const severityStr = String(severity).toUpperCase();
                const action = String(f.action || '').toUpperCase();
                
                return (
                    severity >= 70 ||
                    severityStr === 'CRITICAL' ||
                    severityStr === 'HIGH' ||
                    action === 'BLOCK' ||
                    (f.decision?.severity === 'CRITICAL') ||
                    (f.decision?.severity === 'HIGH')
                );
            }) || [];
            
            if (blockedFindings.length > 0 && !this.isBlocked) {
                this.blockSubmission(blockedFindings);
            } else if (blockedFindings.length === 0 && this.isBlocked) {
                this.unblockSubmission();
            }
        }, 300);
    }

    /**
     * Block submission - disable all methods
     */
    blockSubmission(blockedFindings) {
        if (this.isBlocked) return;
        
        console.warn(`🛑 BLOCKING: ${blockedFindings.length} sensitive finding(s) detected`);
        this.isBlocked = true;
        this.blockedFindings = blockedFindings;
        
        this.disableSendButtons();
        this.addBlockingIndicators();
    }

    /**
     * Unblock submission
     */
    unblockSubmission() {
        if (!this.isBlocked) return;
        
        console.log('✅ AUTO-UNBLOCKED: Sensitive data removed');
        this.isBlocked = false;
        this.blockedFindings = [];
        
        this.enableSendButtons();
        this.removeBlockingIndicators();
        this.showSuccessMessage();
    }

    /**
     * LAYER 1: Intercept form submissions
     */
    interceptFormSubmissions() {
        document.addEventListener('submit', (e) => {
            if (!this.isBlocked) return;
            
            console.warn('🛑 FORM SUBMIT INTERCEPTED');
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            this.showPopupImmediate();
            return false;
        }, true);
    }

    /**
     * LAYER 2: Intercept button clicks
     */
    interceptButtonClicks() {
        document.addEventListener('click', (e) => {
            if (!this.isBlocked) return;
            
            const target = e.target.closest('button');
            if (!target) return;
            
            const text = target.textContent.toLowerCase();
            const ariaLabel = (target.getAttribute('aria-label') || '').toLowerCase();
            
            if (text.includes('send') || text.includes('submit') || ariaLabel.includes('send')) {
                console.warn('🛑 SEND BUTTON CLICK INTERCEPTED');
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                this.showPopupImmediate();
                return false;
            }
        }, true);
    }

    /**
     * LAYER 3: BLOCK ALL ENTER KEYS - Numpad + Keyboard
     * This is the most important one - blocks user from just pressing Enter
     */
    interceptEnterKeyComplete() {
        // Listener 1: Keydown - block immediately
        document.addEventListener('keydown', (e) => {
            if (!this.isBlocked) return;
            
            // Only care about Enter key
            if (e.key !== 'Enter') return;
            
            // Check if in prompt/textarea
            const promptInput = this.findPromptInput();
            if (!promptInput) return;
            
            const isInPrompt = this.isElementFocused(promptInput);
            const isInAnyTextarea = document.activeElement?.tagName === 'TEXTAREA' ||
                                    document.activeElement?.getAttribute?.('contenteditable') === 'true';
            
            if (!isInPrompt && !isInAnyTextarea) return;
            
            // BLOCK ANY ENTER KEY
            console.warn('🛑 ENTER KEY BLOCKED (numpad or keyboard)');
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // Show popup IMMEDIATELY
            this.showPopupImmediate();
            return false;
            
        }, true);
        
        // Listener 2: Keypress - extra layer of protection
        document.addEventListener('keypress', (e) => {
            if (!this.isBlocked) return;
            if (e.key !== 'Enter') return;
            
            const promptInput = this.findPromptInput();
            const isInPrompt = promptInput && this.isElementFocused(promptInput);
            const isInTextarea = document.activeElement?.tagName === 'TEXTAREA' ||
                                document.activeElement?.getAttribute?.('contenteditable') === 'true';
            
            if (!isInPrompt && !isInTextarea) return;
            
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
        }, true);
    }

    /**
     * Check if element or its children are focused
     */
    isElementFocused(element) {
        if (!element) return false;
        return document.activeElement === element || element.contains(document.activeElement);
    }

    /**
     * Find prompt input element
     */
    findPromptInput() {
        const selectors = [
            '.ProseMirror[contenteditable="true"]',
            'div[role="textbox"][contenteditable="true"]',
            'textarea[name="prompt-textarea"]',
            'textarea'
        ];
        
        for (const selector of selectors) {
            const el = document.querySelector(selector);
            if (el && el.getClientRects().length > 0) return el;
        }
        return null;
    }

    /**
     * Disable send buttons
     */
    disableSendButtons() {
        const buttons = this.findAllSendButtons();
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
            btn.title = '🔒 Blocked - Sensitive data detected';
            btn.setAttribute('data-critical-blocked', 'true');
            
            // Store original handler
            if (!btn.__originalOnClick) {
                btn.__originalOnClick = btn.onclick;
            }
            
            // Override onclick
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                this.showPopupImmediate();
                return false;
            };
            
            // Override form
            if (btn.form) {
                if (!btn.form.__originalOnSubmit) {
                    btn.form.__originalOnSubmit = btn.form.onsubmit;
                }
                btn.form.onsubmit = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showPopupImmediate();
                    return false;
                };
            }
        });
    }

    /**
     * Re-enable send buttons
     */
    enableSendButtons() {
        document.querySelectorAll('[data-critical-blocked="true"]').forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
            btn.title = '';
            btn.removeAttribute('data-critical-blocked');
            
            // Restore original
            if (btn.__originalOnClick) {
                btn.onclick = btn.__originalOnClick;
            } else {
                btn.onclick = null;
            }
            
            if (btn.form && btn.form.__originalOnSubmit) {
                btn.form.onsubmit = btn.form.__originalOnSubmit;
            }
        });
    }

    /**
     * Find all send buttons
     */
    findAllSendButtons() {
        const buttons = [];
        
        document.querySelectorAll('[data-testid="send-button"]').forEach(btn => buttons.push(btn));
        document.querySelectorAll('button[aria-label*="Send" i]').forEach(btn => buttons.push(btn));
        document.querySelectorAll('button[aria-label*="send" i]').forEach(btn => buttons.push(btn));
        
        document.querySelectorAll('button').forEach(btn => {
            const text = btn.textContent.toLowerCase();
            if ((text.includes('send') || text.includes('submit')) && !btn.getAttribute('data-critical-blocked')) {
                buttons.push(btn);
            }
        });
        
        return [...new Set(buttons)];
    }

    /**
     * Show popup IMMEDIATELY (no animations, just show)
     */
    showPopupImmediate() {
        // Remove any existing popup
        const existing = document.getElementById('cannot-submit-popup');
        if (existing) existing.remove();

        const popupContainer = document.createElement('div');
        popupContainer.id = 'cannot-submit-popup';
        popupContainer.innerHTML = this.generatePopupHTML();
        popupContainer.style.cssText = `
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

        document.body.appendChild(popupContainer);

        // Add styles immediately if needed
        if (!document.getElementById('blocker-styles')) {
            this.injectStyles();
        }

        // Event handlers
        const closeBtn = popupContainer.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.onclick = () => popupContainer.remove();
        }

        const dismissBtn = popupContainer.querySelector('.btn-dismiss');
        if (dismissBtn) {
            dismissBtn.onclick = () => popupContainer.remove();
        }
    }

    /**
     * Generate popup HTML
     */
    generatePopupHTML() {
        const issuesHTML = this.blockedFindings.map((f, idx) => `
            <div class="issue-item">
                <span class="issue-num">${idx + 1}</span>
                <span class="issue-info">${f.reason} - ${this.truncate(f.evidence)}</span>
            </div>
        `).join('');

        return `
            <div class="blocker-popup">
                <div class="popup-header">
                    <span class="icon">🛑</span>
                    <h2>You can't submit like that</h2>
                    <button class="close-btn">✕</button>
                </div>
                
                <div class="popup-body">
                    <p><strong>Sensitive information detected in your message.</strong></p>
                    
                    <div class="issues-box">
                        ${issuesHTML}
                    </div>
                    
                    <div class="action-box">
                        <h3>What to do:</h3>
                        <ol>
                            <li>Remove the sensitive data from your message</li>
                            <li>Use test data or a placeholder instead</li>
                            <li>The send button will enable automatically when safe</li>
                        </ol>
                    </div>
                </div>
                
                <div class="popup-footer">
                    <button class="btn-dismiss">OK, I'll Fix It</button>
                </div>
            </div>
        `;
    }

    /**
     * Truncate text
     */
    truncate(text) {
        if (!text) return '';
        const str = String(text);
        return str.length > 30 ? str.substring(0, 27) + '...' : str;
    }

    /**
     * Inject styles
     */
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'blocker-styles';
        style.textContent = `
            .blocker-popup {
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 450px;
                box-shadow: 0 25px 50px rgba(0,0,0,0.2);
                overflow: hidden;
            }

            .popup-header {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 20px 24px;
                background: #fed7d7;
                border-bottom: 2px solid #f56565;
            }

            .popup-header .icon {
                font-size: 24px;
            }

            .popup-header h2 {
                margin: 0;
                color: #742a2a;
                font-size: 18px;
                flex: 1;
            }

            .close-btn {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #742a2a;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .popup-body {
                padding: 20px 24px;
            }

            .popup-body p {
                margin: 0 0 16px 0;
                color: #2d3748;
                font-size: 14px;
                line-height: 1.5;
            }

            .issues-box {
                background: #fff5f5;
                border-left: 4px solid #f56565;
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 16px;
            }

            .issue-item {
                display: flex;
                gap: 10px;
                margin-bottom: 6px;
                font-size: 12px;
            }

            .issue-item:last-child {
                margin-bottom: 0;
            }

            .issue-num {
                background: #f56565;
                color: white;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                font-weight: bold;
                flex-shrink: 0;
            }

            .issue-info {
                color: #742a2a;
                word-break: break-word;
            }

            .action-box {
                background: #f0fdf4;
                border-left: 4px solid #48bb78;
                padding: 12px;
                border-radius: 4px;
            }

            .action-box h3 {
                margin: 0 0 8px 0;
                color: #22543d;
                font-size: 13px;
            }

            .action-box ol {
                margin: 0;
                padding-left: 18px;
                color: #22543d;
                font-size: 12px;
            }

            .action-box li {
                margin-bottom: 4px;
                line-height: 1.4;
            }

            .action-box li:last-child {
                margin-bottom: 0;
            }

            .popup-footer {
                padding: 16px 24px;
                background: #f7fafc;
                border-top: 1px solid #e2e8f0;
            }

            .btn-dismiss {
                width: 100%;
                padding: 10px 16px;
                background: #f56565;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
            }

            .btn-dismiss:hover {
                background: #e53e3e;
            }

            @keyframes pulse-red {
                0% { box-shadow: 0 0 0 0 rgba(245, 101, 101, 0.7); }
                70% { box-shadow: 0 0 0 8px rgba(245, 101, 101, 0); }
                100% { box-shadow: 0 0 0 0 rgba(245, 101, 101, 0); }
            }

            [data-critical-blocked] {
                animation: pulse-red 2s infinite !important;
                border: 2px solid #f56565 !important;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Add visual indicators to button
     */
    addBlockingIndicators() {
        document.querySelectorAll('[data-critical-blocked="true"]').forEach(btn => {
            btn.style.borderColor = '#f56565';
            btn.style.borderWidth = '2px';
            btn.style.animation = 'pulse-red 2s infinite';
        });
    }

    /**
     * Remove visual indicators
     */
    removeBlockingIndicators() {
        document.querySelectorAll('[data-critical-blocked="true"]').forEach(el => {
            el.style.animation = 'none';
            el.style.borderColor = '';
            el.style.borderWidth = '';
        });
    }

    /**
     * Show success message
     */
    showSuccessMessage() {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #48bb78;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            font-weight: 500;
            z-index: 999998;
        `;
        toast.textContent = '✅ Critical data removed! Send button is now enabled.';
        
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
}

// Create global instance
const criticalBlocker = new CriticalSeverityBlocker();
