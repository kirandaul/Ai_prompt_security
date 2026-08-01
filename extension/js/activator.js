/**
 * activator.js — Extension Activation & Key Management
 * 
 * Handles:
 * 1. First-time activation (requests key from backend)
 * 2. Key storage in chrome.storage.local
 * 3. Key encryption/decryption
 * 4. Key validation and refresh
 */

class ExtensionActivator {
    constructor() {
        this.apiEndpoint = 'http://localhost:3000/api/activate';
        this.storageKey = 'psg_activation_key';
        this.extensionIdKey = 'psg_extension_id';
        this.init();
    }

    /**
     * Initialize activator on extension load
     */
    async init() {
        console.log('🔐 Extension Activator initialized');
        
        // Check if already activated
        const key = await this.getStoredKey();
        if (key) {
            console.log('✅ Extension already activated');
            return;
        }
        
        // First install - request activation
        console.log('🔐 First install detected - requesting activation key...');
        await this.requestActivation();
    }

    /**
     * Request activation key from backend
     */
    async requestActivation() {
        try {
            const hostname = await this.getHostname();
            const userAgent = navigator.userAgent;
            
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    hostname: hostname,
                    user_agent: userAgent
                })
            });

            if (!response.ok) {
                throw new Error(`Activation failed: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                // Store the activation key
                await this.storeKey(result.activation_key);
                await this.storeExtensionId(result.extension_id);
                
                console.log('✅ Extension activated successfully!');
                console.log('🔑 Activation Key stored securely');
                
                // Show success notification
                this.showActivationNotification('success', result.message);
                
                return result.activation_key;
            } else {
                throw new Error(result.message || 'Activation failed');
            }

        } catch (error) {
            console.error('❌ Activation failed:', error);
            this.showActivationNotification('error', `Activation failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get hostname using fetch to /etc/hostname or fallback
     */
    async getHostname() {
        try {
            // Try to get from localStorage first (if user provided it)
            const stored = localStorage.getItem('psg_user_hostname');
            if (stored) return stored;
            
            // Fallback: use browser-generated ID
            return `extension-${Math.random().toString(36).substr(2, 9)}`;
        } catch (error) {
            return `extension-${Date.now()}`;
        }
    }

    /**
     * Store activation key in secure storage
     */
    async storeKey(key) {
        return new Promise((resolve, reject) => {
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
    }

    /**
     * Store extension ID
     */
    async storeExtensionId(extensionId) {
        return new Promise((resolve, reject) => {
            chrome.storage.local.set(
                { [this.extensionIdKey]: extensionId },
                () => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                    } else {
                        resolve();
                    }
                }
            );
        });
    }

    /**
     * Retrieve stored activation key
     */
    async getStoredKey() {
        return new Promise((resolve) => {
            chrome.storage.local.get([this.storageKey], (result) => {
                if (result[this.storageKey]) {
                    try {
                        const decrypted = this.decryptKey(result[this.storageKey]);
                        resolve(decrypted);
                    } catch (error) {
                        console.error('Failed to decrypt key:', error);
                        resolve(null);
                    }
                } else {
                    resolve(null);
                }
            });
        });
    }

    /**
     * Get extension ID
     */
    async getExtensionId() {
        return new Promise((resolve) => {
            chrome.storage.local.get([this.extensionIdKey], (result) => {
                resolve(result[this.extensionIdKey] || null);
            });
        });
    }

    /**
     * Simple XOR encryption for key storage
     * Note: This is basic obfuscation. For production, use stronger encryption.
     */
    encryptKey(key) {
        const secret = 'psg-extension-secret'; // Static secret
        let encrypted = '';
        for (let i = 0; i < key.length; i++) {
            encrypted += String.fromCharCode(
                key.charCodeAt(i) ^ secret.charCodeAt(i % secret.length)
            );
        }
        return btoa(encrypted); // Base64 encode
    }

    /**
     * XOR decryption
     */
    decryptKey(encryptedKey) {
        try {
            const encrypted = atob(encryptedKey);
            const secret = 'psg-extension-secret';
            let decrypted = '';
            for (let i = 0; i < encrypted.length; i++) {
                decrypted += String.fromCharCode(
                    encrypted.charCodeAt(i) ^ secret.charCodeAt(i % secret.length)
                );
            }
            return decrypted;
        } catch (error) {
            throw new Error('Failed to decrypt key');
        }
    }

    /**
     * Show activation notification
     */
    showActivationNotification(type, message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            font-weight: 500;
            z-index: 999999;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        if (type === 'success') {
            notification.style.background = '#dcfce7';
            notification.style.color = '#15803d';
            notification.style.border = '1px solid #86efac';
            notification.innerHTML = `✅ ${message}`;
        } else {
            notification.style.background = '#fee2e2';
            notification.style.color = '#b91c1c';
            notification.style.border = '1px solid #fca5a5';
            notification.innerHTML = `❌ ${message}`;
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 5000);
    }

    /**
     * Check if extension is activated
     */
    async isActivated() {
        const key = await this.getStoredKey();
        return !!key;
    }
}

// Initialize on script load
const activator = new ExtensionActivator();
