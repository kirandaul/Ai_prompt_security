/**
 * debug_logger.js — Detailed detection decision logging
 * 
 * Logs all detection decisions with full context:
 * - What was detected?
 * - Was it real or fake?
 * - Why was it allowed/blocked?
 * - Full validation details
 */

class DetectionDebugLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 500; // Keep last 500 logs
        this.enabled = true;
        this.loadSettings();
    }

    loadSettings() {
        // Load debug settings from storage
        chrome.storage?.local?.get(['debugEnabled', 'debugLevel'], (result) => {
            if (result.debugEnabled !== undefined) {
                this.enabled = result.debugEnabled;
            }
        });
    }

    /**
     * Log a complete detection scan result
     */
    logScan(scanId, prompt, result) {
        if (!this.enabled) return;

        const logEntry = {
            timestamp: new Date().toISOString(),
            scanId,
            promptLength: prompt.length,
            action: result.action,
            severity: result.severity,
            totalFindings: result.findings?.length || 0,
            findings: result.findings?.map(f => ({
                detector: f.detector,
                category: f.category,
                severity: f.severity,
                confidence: f.confidence,
                evidence: f.evidence,
            })) || [],
            summary: result.summary,
            decision: {
                allowSend: result.allowSend,
                reason: this.extractDecisionReason(result),
                factors: this.extractDecisionFactors(result),
            }
        };

        this.addLog(logEntry);

        // Also log to console in development
        if (this.isDevelopment()) {
            console.group(`🔍 [${scanId}] Detection Decision: ${logEntry.action}`);
            console.log('Prompt length:', prompt.length);
            console.log('Findings:', logEntry.findings);
            console.log('Decision:', logEntry.decision);
            console.groupEnd();
        }

        return logEntry;
    }

    /**
     * Log individual detector results
     */
    logDetectorResult(scanId, detector, matched, validation, decision) {
        if (!this.enabled) return;

        const logEntry = {
            timestamp: new Date().toISOString(),
            scanId,
            type: 'DETECTOR',
            detector: detector.name,
            matched,
            validation: {
                isValid: validation?.isValid,
                isReal: validation?.isReal,
                type: validation?.type, // 'real', 'fake', 'test', 'invalid'
                reason: validation?.reason,
                details: validation?.details,
            },
            decision: {
                status: decision?.status, // 'allowed', 'blocked'
                severity: decision?.severity,
                reason: decision?.reason,
                confidence: decision?.confidence,
            }
        };

        this.addLog(logEntry);

        // Console logging
        if (this.isDevelopment() && matched) {
            console.log(
                `  ✓ ${detector.name}: ${decision?.status} (${validation?.type}) - ${decision?.reason}`
            );
        }

        return logEntry;
    }

    /**
     * Log a validation check (Luhn, domain check, pattern match, etc.)
     */
    logValidation(scanId, validationType, value, result) {
        if (!this.enabled) return;

        const logEntry = {
            timestamp: new Date().toISOString(),
            scanId,
            type: 'VALIDATION',
            validationType, // 'LUHN', 'DOMAIN_CHECK', 'PATTERN_MATCH', 'ENTROPY', etc.
            result: {
                passed: result.passed,
                score: result.score,
                reason: result.reason,
                details: result.details,
            }
        };

        this.addLog(logEntry);
        return logEntry;
    }

    /**
     * Extract human-readable decision reason
     */
    extractDecisionReason(result) {
        if (result.allowSend) {
            if (result.totalFindings === 0) {
                return 'No sensitive data detected - safe to send';
            } else {
                return `${result.totalFindings} detection(s) but classified as non-risky`;
            }
        } else {
            return `${result.totalFindings} sensitive data detection(s) - blocking for safety`;
        }
    }

    /**
     * Extract decision factors for transparency
     */
    extractDecisionFactors(result) {
        const factors = [];

        result.findings?.forEach(f => {
            factors.push({
                detector: f.detector,
                reasoning: this.getDetectorReasoning(f),
                confidence: Math.round(f.confidence * 100),
                severity: f.severity,
            });
        });

        return factors;
    }

    /**
     * Get detector-specific reasoning
     */
    getDetectorReasoning(finding) {
        const detector = finding.detector;
        const category = finding.category;

        const reasoning = {
            'API_KEY_DETECTOR': 'API keys should never be shared as they grant access to services',
            'AWS_SECRET_DETECTOR': 'AWS credentials compromise cloud infrastructure security',
            'CREDIT_CARD_DETECTOR': 'Payment card numbers enable financial fraud and identity theft',
            'PASSWORD_DETECTOR': 'Passwords grant unauthorized access to accounts and systems',
            'EMAIL_DETECTOR': 'Email addresses are personally identifiable information (PII)',
            'PHONE_DETECTOR': 'Phone numbers are personally identifiable information (PII)',
            'PAN_DETECTOR': 'PAN (Permanent Account Number) is sensitive tax information',
            'AADHAAR_DETECTOR': 'Aadhaar is sensitive biometric identity information',
            'JWT_DETECTOR': 'JWT tokens contain session data and can be used for unauthorized access',
            'PRIVATE_KEY_DETECTOR': 'Private keys grant complete access to systems and data',
            'SQL_INJECTION_DETECTOR': 'SQL injection patterns are malicious attacks',
            'XSS_DETECTOR': 'XSS patterns are malicious attacks',
            'PROMPT_INJECTION_DETECTOR': 'Prompt injection attempts to manipulate AI systems',
            'JAILBREAK_DETECTOR': 'Jailbreak attempts circumvent safety guidelines',
            'HEALTH_DETECTOR': 'Health information is sensitive medical/personal data',
        };

        return reasoning[detector] || 'Sensitive information detected';
    }

    /**
     * Export logs as JSON
     */
    exportLogs(filter = null) {
        let logsToExport = this.logs;

        if (filter?.scanId) {
            logsToExport = logsToExport.filter(l => l.scanId === filter.scanId);
        }

        return JSON.stringify(logsToExport, null, 2);
    }

    /**
     * Export logs as CSV
     */
    exportLogsCSV() {
        const headers = ['Timestamp', 'Scan ID', 'Type', 'Detector', 'Matched', 'Decision', 'Reason'];
        const rows = this.logs
            .filter(l => l.type === 'DETECTOR')
            .map(l => [
                l.timestamp,
                l.scanId,
                l.type,
                l.detector || '-',
                l.matched ? 'YES' : 'NO',
                l.decision?.status || '-',
                l.decision?.reason || '-'
            ]);

        const csv = [
            headers.join(','),
            ...rows.map(r => r.map(v => `"${v}"`).join(','))
        ].join('\n');

        return csv;
    }

    /**
     * Get logs for UI display
     */
    getLogs(limit = 50) {
        return this.logs.slice(-limit);
    }

    /**
     * Get stats about detections
     */
    getStats() {
        const detectorCounts = {};
        const actionCounts = { ALLOW: 0, BLOCK: 0 };
        const severityCounts = {};

        this.logs.forEach(log => {
            // Count detectors
            if (log.detector) {
                detectorCounts[log.detector] = (detectorCounts[log.detector] || 0) + 1;
            }

            // Count actions
            if (log.decision?.status) {
                const action = log.decision.status.toUpperCase();
                actionCounts[action] = (actionCounts[action] || 0) + 1;
            }

            // Count severities
            if (log.severity) {
                severityCounts[log.severity] = (severityCounts[log.severity] || 0) + 1;
            }
        });

        return {
            totalScans: this.logs.filter(l => !l.type || l.type === 'SCAN').length,
            totalDetections: this.logs.filter(l => l.matched).length,
            detectors: detectorCounts,
            actions: actionCounts,
            severities: severityCounts,
        };
    }

    /**
     * Clear all logs
     */
    clearLogs() {
        this.logs = [];
    }

    /**
     * Internal: add log entry
     */
    addLog(entry) {
        this.logs.push(entry);

        // Trim to max size
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }

        // Persist to storage
        chrome.storage?.local?.set({ debugLogs: this.logs });
    }

    /**
     * Check if running in development
     */
    isDevelopment() {
        return chrome.runtime.getManifest().version_name?.includes('dev') || false;
    }

    /**
     * Enable/disable logging
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        chrome.storage?.local?.set({ debugEnabled: enabled });
    }

    /**
     * Open debug panel in a new tab
     */
    openDebugPanel() {
        chrome.tabs.create({
            url: chrome.runtime.getURL('debug_panel.html')
        });
    }
}

// Export for use in content/background scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DetectionDebugLogger;
}

// Create global instance
const debugLogger = new DetectionDebugLogger();
