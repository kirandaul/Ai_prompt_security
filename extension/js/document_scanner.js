/**
 * document_scanner.js — Document Upload Detection
 * 
 * Intercepts file uploads and scans documents for sensitive information
 * Works with: PDF, DOCX, XLSX, CSV, TXT
 */

class DocumentScanner {
    constructor() {
        this.apiEndpoint = 'http://localhost:3000/api/scan-document';
        this.isBlockedDocument = false;
        this.blockedDocumentFindings = [];
        this.lastScannedFile = null;
        this.init();
    }

    /**
     * Initialize document scanner
     */
    init() {
        console.log('📄 Document Scanner initialized');
        
        // Intercept file input changes
        this.interceptFileInputs();
        
        // Intercept drag/drop
        this.interceptDragDrop();
    }

    /**
     * Intercept file input element changes
     */
    interceptFileInputs() {
        document.addEventListener('change', (e) => {
            const input = e.target;
            
            // Check if it's a file input
            if (input.tagName === 'INPUT' && input.type === 'file') {
                const files = input.files;
                
                if (files && files.length > 0) {
                    for (let file of files) {
                        this.handleFileUpload(file, input);
                    }
                }
            }
        }, true);
    }

    /**
     * Intercept drag/drop events
     */
    interceptDragDrop() {
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, true);

        document.addEventListener('drop', (e) => {
            if (!e.dataTransfer || !e.dataTransfer.files) return;
            
            const files = e.dataTransfer.files;
            
            if (files.length > 0) {
                for (let file of files) {
                    this.handleFileUpload(file);
                }
            }
        }, true);
    }

    /**
     * Handle file upload - read and scan
     */
    async handleFileUpload(file, inputElement = null) {
        console.log(`📄 File selected: ${file.name} (${file.size} bytes)`);
        
        // Check file size (25 MB max)
        const MAX_SIZE = 25 * 1024 * 1024;
        if (file.size > MAX_SIZE) {
            console.warn(`File too large: ${file.size} bytes`);
            this.showFileError(`File too large. Max 25 MB, got ${(file.size / 1024 / 1024).toFixed(1)} MB`);
            return;
        }
        
        // Check file type
        const fileType = this.getFileType(file.name);
        if (!['pdf', 'docx', 'xlsx', 'csv', 'txt'].includes(fileType)) {
            console.warn(`Unsupported file type: ${fileType}`);
            this.showFileError(`Unsupported file type: ${fileType}`);
            return;
        }
        
        // Read file
        const fileContent = await this.readFile(file);
        
        // Convert to base64
        const base64 = this.arrayBufferToBase64(fileContent);
        
        // Scan document
        await this.scanDocument(base64, file.name, fileType);
    }

    /**
     * Read file as array buffer
     */
    readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                resolve(e.target.result);
            };
            
            reader.onerror = () => {
                reject(new Error('Failed to read file'));
            };
            
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Convert array buffer to base64
     */
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * Get file type from filename
     */
    getFileType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        return ext || 'txt';
    }

    /**
     * Scan document via backend API
     */
    async scanDocument(base64Content, filename, fileType) {
        console.log(`Scanning document: ${filename}`);
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document: base64Content,
                    filename: filename,
                    document_type: fileType,
                    client_id: window.__psgClientId || 'unknown',
                    source: window.location.hostname
                })
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📄 Document scan result:', result);
            
            // Store result for use by blocker
            window.__psgLastDocumentScan = result;
            window.__psgLastDocumentFilename = filename;
            
            // Update UI
            this.handleScanResult(result, filename);
            
        } catch (error) {
            console.error('Document scan failed:', error);
            this.showFileError(`Failed to scan document: ${error.message}`);
        }
    }

    /**
     * Handle scan results
     */
    handleScanResult(result, filename) {
        const findings = result.findings || [];
        const totalFindings = result.totalFindings || 0;
        const severity = result.severity || 'LOW';
        const action = result.action || 'ALLOW';
        
        if (totalFindings === 0) {
            console.log('✅ Document is safe to upload');
            this.showDocumentNotification('safe', filename, 'No sensitive data found');
            this.isBlockedDocument = false;
            this.blockedDocumentFindings = [];
        } else {
            console.warn(`⚠️ Found ${totalFindings} sensitive items in document`);
            this.showDocumentNotification('warning', filename, `Found ${totalFindings} sensitive items`);
            
            // Block if HIGH or CRITICAL
            if (action === 'BLOCK' || severity === 'HIGH' || severity === 'CRITICAL') {
                this.isBlockedDocument = true;
                this.blockedDocumentFindings = findings;
                this.showDocumentBlockPopup(findings, filename);
                this.blockUploadButton();
            }
        }
    }

    /**
     * Show notification about document
     */
    showDocumentNotification(type, filename, message) {
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
            z-index: 999997;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideDown 0.3s ease;
        `;
        
        if (type === 'safe') {
            notification.style.background = '#f0fdf4';
            notification.style.color = '#22543d';
            notification.style.border = '1px solid #86efac';
            notification.innerHTML = `📄 ${filename}<br><span style="font-size: 12px; opacity: 0.8;">✅ ${message}</span>`;
        } else if (type === 'warning') {
            notification.style.background = '#fef3c7';
            notification.style.color = '#92400e';
            notification.style.border = '1px solid #fcd34d';
            notification.innerHTML = `📄 ${filename}<br><span style="font-size: 12px; opacity: 0.8;">⚠️ ${message}</span>`;
        } else {
            notification.style.background = '#fee2e2';
            notification.style.color = '#7c2d12';
            notification.style.border = '1px solid #fca5a5';
            notification.innerHTML = `📄 ${filename}<br><span style="font-size: 12px; opacity: 0.8;">❌ ${message}</span>`;
        }
        
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    /**
     * Show blocking popup for document with sensitive data
     */
    showDocumentBlockPopup(findings, filename) {
        const existing = document.getElementById('document-block-popup');
        if (existing) existing.remove();

        const findingsHTML = findings.map((f, idx) => `
            <div class="doc-finding-item">
                <span class="finding-num">${idx + 1}</span>
                <div class="finding-content">
                    <strong>${f.reason}</strong>
                    <p>${f.location || 'Document'}</p>
                </div>
            </div>
        `).join('');

        const popup = document.createElement('div');
        popup.id = 'document-block-popup';
        popup.innerHTML = `
            <div class="doc-popup-overlay">
                <div class="doc-popup-container">
                    <div class="doc-popup-header">
                        <span class="icon">🔒</span>
                        <h2>Document Blocked</h2>
                        <button class="close-btn">✕</button>
                    </div>
                    
                    <div class="doc-popup-body">
                        <p><strong>Sensitive data detected in: ${filename}</strong></p>
                        
                        <div class="doc-findings-list">
                            ${findingsHTML}
                        </div>
                        
                        <div class="doc-popup-info">
                            <p>This document contains sensitive information and cannot be uploaded.</p>
                            <p><strong>What to do:</strong></p>
                            <ul>
                                <li>Remove or redact sensitive data from the document</li>
                                <li>Save the updated document</li>
                                <li>Upload the cleaned version</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="doc-popup-footer">
                        <button class="btn-close">OK, I'll Remove It</button>
                    </div>
                </div>
            </div>
        `;
        
        popup.style.cssText = `
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
        
        // Inject styles
        if (!document.getElementById('doc-popup-styles')) {
            const style = document.createElement('style');
            style.id = 'doc-popup-styles';
            style.textContent = `
                .doc-popup-overlay { animation: fadeIn 0.2s ease; }
                
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                .doc-popup-container {
                    background: white;
                    border-radius: 12px;
                    width: 90%;
                    max-width: 450px;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.2);
                    overflow: hidden;
                }
                
                .doc-popup-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 20px 24px;
                    background: #fed7d7;
                    border-bottom: 2px solid #f56565;
                }
                
                .doc-popup-header .icon {
                    font-size: 24px;
                }
                
                .doc-popup-header h2 {
                    margin: 0;
                    color: #742a2a;
                    font-size: 18px;
                    flex: 1;
                }
                
                .doc-popup-header .close-btn {
                    background: none;
                    border: none;
                    font-size: 20px;
                    cursor: pointer;
                    color: #742a2a;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                }
                
                .doc-popup-body {
                    padding: 20px 24px;
                }
                
                .doc-popup-body p {
                    margin: 0 0 12px 0;
                    color: #2d3748;
                    font-size: 13px;
                    line-height: 1.5;
                }
                
                .doc-findings-list {
                    background: #fff5f5;
                    border-left: 4px solid #f56565;
                    padding: 12px;
                    border-radius: 4px;
                    margin: 12px 0;
                }
                
                .doc-finding-item {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 8px;
                    font-size: 12px;
                }
                
                .doc-finding-item:last-child {
                    margin-bottom: 0;
                }
                
                .finding-num {
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
                
                .finding-content {
                    flex: 1;
                }
                
                .finding-content strong {
                    color: #742a2a;
                    display: block;
                    margin-bottom: 2px;
                }
                
                .finding-content p {
                    margin: 0;
                    color: #666;
                    font-size: 11px;
                }
                
                .doc-popup-info {
                    background: #eff6ff;
                    border-left: 4px solid #667eea;
                    padding: 12px;
                    border-radius: 4px;
                }
                
                .doc-popup-info ul {
                    margin: 8px 0 0 20px;
                    padding: 0;
                    font-size: 12px;
                    color: #1e40af;
                }
                
                .doc-popup-info li {
                    margin-bottom: 4px;
                }
                
                .doc-popup-footer {
                    padding: 16px 24px;
                    background: #f7fafc;
                    border-top: 1px solid #e2e8f0;
                }
                
                .btn-close {
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
                
                .btn-close:hover {
                    background: #e53e3e;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(popup);
        
        // Event handlers
        popup.querySelector('.close-btn').onclick = () => popup.remove();
        popup.querySelector('.btn-close').onclick = () => popup.remove();
    }

    /**
     * Block upload button
     */
    blockUploadButton() {
        // Find upload buttons
        const buttons = document.querySelectorAll('[aria-label*="attach" i], [aria-label*="upload" i]');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.title = '🔒 Blocked - Remove sensitive data from document first';
        });
    }

    /**
     * Unblock upload button
     */
    unblockUploadButton() {
        const buttons = document.querySelectorAll('[aria-label*="attach" i], [aria-label*="upload" i]');
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.title = '';
        });
    }

    /**
     * Show file error
     */
    showFileError(message) {
        const error = document.createElement('div');
        error.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            background: #fee2e2;
            color: #7c2d12;
            border: 1px solid #fca5a5;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            font-weight: 500;
            z-index: 999997;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        error.textContent = `❌ ${message}`;
        
        document.body.appendChild(error);
        
        setTimeout(() => error.remove(), 5000);
    }
}

// Initialize document scanner
const documentScanner = new DocumentScanner();
