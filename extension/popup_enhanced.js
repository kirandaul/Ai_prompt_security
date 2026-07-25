/**
 * popup_enhanced.js — Enhanced detection result UI
 * 
 * Shows detailed decision explanations:
 * - What was detected?
 * - Was it real or fake?
 * - Why was it allowed/blocked?
 */

document.addEventListener('DOMContentLoaded', () => {
    loadAndDisplayResults();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('debugBtn')?.addEventListener('click', openDebugLog);
    document.getElementById('learnMore')?.addEventListener('click', (e) => {
        e.preventDefault();
        chrome.tabs.create({ url: 'https://cybage.com/security' });
    });
}

async function loadAndDisplayResults() {
    try {
        // Get the current tab and fetch its scan result
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        chrome.tabs.sendMessage(tab.id, { action: 'getScanResult' }, (response) => {
            if (response && response.result) {
                displayResults(response.result, response.scanId, response.processingTime);
            } else {
                showNoData();
            }
        });
    } catch (err) {
        console.error('Error loading results:', err);
        showNoData();
    }
}

function displayResults(result, scanId, processingTime) {
    const statusContainer = document.getElementById('status-container');
    const summaryContainer = document.getElementById('summary-container');
    const findingsContainer = document.getElementById('findings-container');

    // Display status
    const isAllowed = result.allowSend;
    const statusHtml = createStatusPanel(result, isAllowed);
    statusContainer.innerHTML = statusHtml;

    // Display summary stats
    if (result.findings && result.findings.length > 0) {
        const summaryHtml = createSummaryStats(result);
        summaryContainer.innerHTML = summaryHtml;
    }

    // Display findings
    if (result.findings && result.findings.length > 0) {
        const findingsHtml = result.findings
            .map((f, idx) => createFindingCard(f, idx))
            .join('');
        findingsContainer.innerHTML = `<div>${findingsHtml}</div>`;
    } else {
        findingsContainer.innerHTML = '';
    }

    // Update time
    document.getElementById('timeInfo').textContent = `${processingTime || 0}ms`;
}

function createStatusPanel(result, isAllowed) {
    const statusClass = isAllowed ? 'allowed' : 'blocked';
    const statusIcon = isAllowed ? '✅' : '🛑';
    const statusTitle = isAllowed ? 'SAFE TO SEND' : 'BLOCKED';
    const explanation = getStatusExplanation(result, isAllowed);

    return `
        <div class="status-panel">
            <div class="status-icon">${statusIcon}</div>
            <div class="status-title ${statusClass}">${statusTitle}</div>
            <div class="status-subtitle">${result.severity}</div>
        </div>
        <div class="decision-box ${statusClass}">
            <strong>Decision Explanation:</strong><br>
            <div style="margin-top: 8px; font-size: 12px; line-height: 1.5;">
                ${explanation}
            </div>
        </div>
    `;
}

function getStatusExplanation(result, isAllowed) {
    if (isAllowed) {
        if (!result.findings || result.findings.length === 0) {
            return 'No sensitive data detected. This prompt is safe to send to AI services.';
        } else {
            const testCount = result.findings.filter(f => f.validation?.type === 'test').length || 0;
            const fakeCount = result.findings.filter(f => f.validation?.type === 'fake').length || 0;
            
            if (testCount > 0) {
                return `${testCount} test/example value(s) detected, but not real sensitive data. Safe to send.`;
            } else if (fakeCount > 0) {
                return `${fakeCount} invalid/fake value(s) detected. Not real sensitive data, safe to send.`;
            }
        }
    } else {
        const realCount = result.findings.filter(f => f.validation?.type === 'real').length || 0;
        if (realCount > 0) {
            return `${realCount} real sensitive data detected. Blocking to protect your security and privacy.`;
        }
        return `${result.findings.length} sensitive data detection(s) found. Blocking as a precaution.`;
    }
}

function createSummaryStats(result) {
    const total = result.findings.length;
    const blocked = result.findings.filter(f => f.severity >= 70).length;
    const allowed = total - blocked;

    return `
        <div class="summary-stats">
            <div class="stat">
                <div class="stat-value">${total}</div>
                <div class="stat-label">Detections</div>
            </div>
            <div class="stat">
                <div class="stat-value">${blocked}</div>
                <div class="stat-label">Blocked</div>
            </div>
            <div class="stat">
                <div class="stat-value">${allowed}</div>
                <div class="stat-label">Allowed</div>
            </div>
        </div>
    `;
}

function createFindingCard(finding, idx) {
    const validation = finding.validation || {};
    const confidence = Math.round((finding.confidence || 0) * 100);
    
    // Determine severity class
    const severityClass = getSeverityClass(finding.severity);
    
    // Build validation tags
    let tags = '';
    if (validation.type === 'test') {
        tags += '<span class="validation-tag test">🧪 Test Data</span>';
    } else if (validation.type === 'fake') {
        tags += '<span class="validation-tag invalid">✗ Invalid</span>';
    } else if (validation.type === 'real') {
        tags += '<span class="validation-tag real">⚠️ Real Data</span>';
    }
    
    if (validation.isValid === true) {
        tags += '<span class="validation-tag valid">✓ Valid Format</span>';
    } else if (validation.isValid === false) {
        tags += '<span class="validation-tag invalid">✗ Invalid Format</span>';
    }

    // Build reason text
    const reason = validation.reason || getDefaultReason(finding.detector);

    // Truncate evidence
    const evidence = (finding.evidence || '').substring(0, 50);
    const evidenceHtml = evidence ? `<div class="evidence-box">${escapeHtml(evidence)}</div>` : '';

    return `
        <div class="finding">
            <div class="finding-header">
                <div class="detector-name">${finding.detector}</div>
                <span class="severity-badge ${severityClass}">${finding.severity}</span>
            </div>
            
            <div class="finding-detail">
                ${finding.category}
            </div>

            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${confidence}%;"></div>
            </div>

            ${tags ? `<div class="validation-tags">${tags}</div>` : ''}

            ${evidenceHtml}

            <div class="reason-text">
                <strong>Why:</strong><br>
                ${reason}
            </div>
        </div>
    `;
}

function getSeverityClass(severity) {
    if (severity >= 90) return 'severity-critical';
    if (severity >= 70) return 'severity-high';
    if (severity >= 40) return 'severity-medium';
    return 'severity-low';
}

function getDefaultReason(detector) {
    const reasons = {
        'API_KEY_DETECTOR': 'API keys grant access to third-party services and should never be shared.',
        'AWS_SECRET_DETECTOR': 'AWS credentials provide access to cloud infrastructure.',
        'CREDIT_CARD_DETECTOR': 'Payment card numbers enable financial fraud.',
        'EMAIL_DETECTOR': 'Email addresses are personally identifiable information.',
        'PHONE_DETECTOR': 'Phone numbers are personally identifiable information.',
        'PASSWORD_DETECTOR': 'Passwords grant unauthorized account access.',
        'JWT_DETECTOR': 'JWT tokens contain session data and authentication information.',
        'PRIVATE_KEY_DETECTOR': 'Private keys grant complete system access.',
        'PAN_DETECTOR': 'PAN is sensitive tax identification information.',
        'AADHAAR_DETECTOR': 'Aadhaar numbers are sensitive biometric identifiers.',
        'HEALTH_DETECTOR': 'Health information is sensitive medical data.',
        'SQL_INJECTION_DETECTOR': 'This is a malicious SQL injection attack pattern.',
        'XSS_DETECTOR': 'This is a malicious XSS attack pattern.',
        'PROMPT_INJECTION_DETECTOR': 'This is a prompt injection attack.',
        'JAILBREAK_DETECTOR': 'This attempts to bypass safety guidelines.',
    };

    return reasons[detector] || 'Sensitive information detected.';
}

function showNoData() {
    const container = document.getElementById('status-container');
    container.innerHTML = `
        <div class="no-findings">
            <div class="no-findings-icon">📄</div>
            <div class="no-findings-text">No prompt analyzed yet</div>
            <div class="no-findings-sub">Start typing in an AI prompt field</div>
        </div>
    `;
    document.getElementById('findings-container').innerHTML = '';
    document.getElementById('summary-container').innerHTML = '';
}

function openDebugLog() {
    chrome.tabs.create({ url: chrome.runtime.getURL('debug_panel.html') });
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
