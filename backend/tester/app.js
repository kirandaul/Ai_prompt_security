/**
 * app.js — Testing dashboard core logic
 * 
 * Manages:
 * - Prompt list display and filtering
 * - Single test execution
 * - Bulk testing with progress tracking
 * - Result validation and PASS/FAIL determination
 * - Export functionality
 */

// ============================================================================
// State
// ============================================================================

let allPrompts = [];
let filteredPrompts = [];
let selectedPrompt = null;
let testResults = {};  // { promptId: result }
let isBulkRunning = false;
let bulkCancelled = false;

// ============================================================================
// DOM References
// ============================================================================

const promptList = document.getElementById('promptList');
const promptCount = document.getElementById('promptCount');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const detailsPanel = document.getElementById('detailsPanel');
const resultsPanel = document.getElementById('resultsPanel');
const runBtn = document.getElementById('runBtn');
const runAllBtn = document.getElementById('runAllBtn');
const exportBtn = document.getElementById('exportBtn');
const exportFailedBtn = document.getElementById('exportFailedBtn');
const clearBtn = document.getElementById('clearBtn');
const bulkPanel = document.getElementById('bulkPanel');
const statsCard = document.getElementById('statsCard');

// ============================================================================
// API Helpers
// ============================================================================

async function fetchDetectors() {
    try {
        const res = await fetch('/api/tester/detectors');
        if (!res.ok) throw new Error('Failed to fetch detectors');
        return await res.json();
    } catch (err) {
        console.error('Error fetching detectors:', err);
        return { detectors: [], labels: {} };
    }
}

async function scanPrompt(promptData) {
    try {
        const res = await fetch('/api/tester/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(promptData)
        });
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error('Error scanning prompt:', err);
        return { error: err.message };
    }
}

async function bulkScan(prompts) {
    try {
        // Send the prompts wrapped in the expected format
        const res = await fetch('/api/tester/bulk-scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prompts)
        });
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error('Error in bulk scan:', err);
        return { error: err.message, results: [] };
    }
}

// ============================================================================
// Prompt List Management
// ============================================================================

function renderPromptList() {
    promptList.innerHTML = '';
    
    if (filteredPrompts.length === 0) {
        promptList.innerHTML = '<div class="empty">No prompts found</div>';
        return;
    }
    
    filteredPrompts.forEach((prompt, idx) => {
        const item = document.createElement('div');
        item.className = 'prompt-item';
        if (selectedPrompt && selectedPrompt.id === prompt.id) {
            item.classList.add('selected');
        }
        
        const result = testResults[prompt.id];
        const status = result ? result.status : '';
        const statusBadge = status ? `<span class="badge ${status}">${status}</span>` : '';
        
        item.innerHTML = `
            <div class="prompt-name">#${prompt.id} ${prompt.name}</div>
            <div class="prompt-meta">
                ${statusBadge}
                <span>${prompt.category}</span> • ${prompt.expected_detector}
            </div>
        `;
        
        item.addEventListener('click', () => selectPrompt(prompt));
        promptList.appendChild(item);
    });
    
    promptCount.textContent = filteredPrompts.length;
}

function selectPrompt(prompt) {
    selectedPrompt = prompt;
    renderPromptList();
    renderDetailsPanel();
}

function filterPrompts() {
    const search = searchInput.value.toLowerCase();
    const category = categoryFilter.value;
    
    filteredPrompts = allPrompts.filter(p => {
        const matchSearch = !search || p.name.toLowerCase().includes(search) || 
                          p.prompt.toLowerCase().includes(search);
        const matchCategory = !category || p.category === category;
        return matchSearch && matchCategory;
    });
    
    renderPromptList();
}

// ============================================================================
// Details Panel
// ============================================================================

function renderDetailsPanel() {
    if (!selectedPrompt) {
        detailsPanel.innerHTML = '<div class="empty">Select a prompt to view details</div>';
        return;
    }
    
    const p = selectedPrompt;
    const result = testResults[p.id];
    
    let html = `
        <div class="detail-row">
            <div class="detail-label">ID</div>
            <div class="detail-value">${p.id}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Name</div>
            <div class="detail-value">${p.name}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Category</div>
            <div class="detail-value">${p.category}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Expected Detector</div>
            <div class="detail-value mono">${p.expected_detector}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Severity</div>
            <div class="detail-value">${p.severity || 'N/A'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Prompt Text</div>
            <div class="response-box">${escapeHtml(p.prompt)}</div>
        </div>
    `;
    
    if (result) {
        html += `
            <div class="detail-row" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--line);">
                <div class="detail-label">Test Result</div>
                <div class="detail-value" style="margin-top: 8px;">
                    <span class="badge ${result.status}">${result.status}</span>
                    <span style="font-size: 12px; color: var(--muted);">Duration: ${result.duration_ms}ms</span>
                </div>
            </div>
        `;
    }
    
    detailsPanel.innerHTML = html;
}

// ============================================================================
// Results Panel
// ============================================================================

function renderResultsPanel(result) {
    if (!result) {
        resultsPanel.innerHTML = '<div class="empty">Run a test to see results</div>';
        return;
    }
    
    if (result.error) {
        resultsPanel.innerHTML = `<div class="error">Error: ${result.error}</div>`;
        return;
    }
    
    const r = result.result || {};
    const findings = r.findings || [];
    
    let html = `
        <div class="summary">
            <div class="summary-card">
                <div class="summary-label">Severity</div>
                <div class="summary-value">${r.severity || 'UNKNOWN'}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Action</div>
                <div class="summary-value">${r.action || 'UNKNOWN'}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Findings</div>
                <div class="summary-value">${findings.length}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Duration</div>
                <div class="summary-value">${result.duration_ms}ms</div>
            </div>
        </div>
    `;
    
    if (findings.length > 0) {
        html += '<div style="margin-top: 16px;"><h3 style="margin: 0 0 12px; font-size: 14px;">Findings</h3>';
        findings.forEach(f => {
            html += `
                <div class="finding-item ${f.severity}">
                    <div style="font-weight: 600;">${f.reason}</div>
                    <div style="font-size: 12px; margin-top: 4px; opacity: 0.8;">
                        ${f.category} • Confidence: ${(f.confidence * 100).toFixed(0)}% • Evidence: ${f.evidence}
                    </div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += '<div style="margin-top: 16px; padding: 16px; background: #f8fafc; border-radius: 8px; text-align: center; color: var(--muted);">No findings detected</div>';
    }
    
    html += `
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--line);">
            <h3 style="margin: 0 0 8px; font-size: 12px; color: var(--muted); text-transform: uppercase;">Full API Response</h3>
            <div class="response-box">${escapeHtml(JSON.stringify(r, null, 2))}</div>
        </div>
    `;
    
    resultsPanel.innerHTML = html;
}

// ============================================================================
// Testing Logic
// ============================================================================

async function runSingleTest() {
    if (!selectedPrompt) {
        alert('Please select a prompt first');
        return;
    }
    
    runBtn.disabled = true;
    resultsPanel.innerHTML = '<div style="text-align: center; color: var(--muted);"><div class="spinner"></div> Running test...</div>';
    
    const result = await scanPrompt({
        prompt: selectedPrompt.prompt,
        prompt_id: selectedPrompt.id,
        prompt_name: selectedPrompt.name,
        category: selectedPrompt.category,
        expected_detector: selectedPrompt.expected_detector
    });
    
    testResults[selectedPrompt.id] = result;
    renderDetailsPanel();
    renderResultsPanel(result);
    renderPromptList();
    
    runBtn.disabled = false;
}

async function runAllTests() {
    if (filteredPrompts.length === 0) {
        alert('No prompts to run');
        return;
    }
    
    if (!confirm(`Run ${filteredPrompts.length} tests? This may take a while.`)) {
        return;
    }
    
    isBulkRunning = true;
    bulkCancelled = false;
    runBtn.disabled = true;
    runAllBtn.disabled = true;
    exportBtn.disabled = true;
    bulkPanel.style.display = 'block';
    
    const prompts = filteredPrompts.map(p => ({
        prompt: p.prompt,
        prompt_id: p.id,
        prompt_name: p.name,
        category: p.category,
        expected_detector: p.expected_detector
    }));
    
    const result = await bulkScan(prompts);
    
    if (result.error) {
        alert(`Error: ${result.error}`);
    } else {
        // Store all results
        (result.results || []).forEach(r => {
            testResults[r.prompt_id] = r;
        });
        
        // Update UI
        const total = result.total || 0;
        const passed = result.passed || 0;
        const failed = total - passed;
        const rate = total > 0 ? Math.round((passed / total) * 100) : 0;
        
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressText').textContent = `${total}/${total}`;
        document.getElementById('progressStatus').textContent = 'Completed';
        document.getElementById('bulkTotal').textContent = total;
        document.getElementById('bulkPassed').textContent = passed;
        document.getElementById('bulkFailed').textContent = failed;
        document.getElementById('bulkRate').textContent = `${rate}%`;
        
        renderPromptList();
        renderStats();
        
        setTimeout(() => {
            statsCard.style.display = 'block';
        }, 500);
    }
    
    isBulkRunning = false;
    runBtn.disabled = false;
    runAllBtn.disabled = false;
    exportBtn.disabled = false;
}

// ============================================================================
// Statistics
// ============================================================================

function renderStats() {
    const results = Object.values(testResults);
    if (results.length === 0) return;
    
    const total = results.length;
    const passed = results.filter(r => r.status === 'PASS').length;
    const failed = results.filter(r => r.status === 'FAIL').length;
    
    const byCategory = {};
    const bySeverity = {};
    
    results.forEach(r => {
        const cat = r.category || 'UNKNOWN';
        byCategory[cat] = (byCategory[cat] || 0) + 1;
    });
    
    let html = `
        <div class="stat">
            <div class="stat-label">Total Tests</div>
            <div class="stat-value">${total}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Passed</div>
            <div class="stat-value" style="color: var(--safe);">${passed}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Failed</div>
            <div class="stat-value" style="color: var(--crit);">${failed}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value">${total > 0 ? Math.round((passed / total) * 100) : 0}%</div>
        </div>
    `;
    
    Object.entries(byCategory).forEach(([cat, count]) => {
        html += `
            <div class="stat">
                <div class="stat-label">${cat}</div>
                <div class="stat-value">${count}</div>
            </div>
        `;
    });
    
    document.getElementById('statsGrid').innerHTML = html;
}

// ============================================================================
// Export
// ============================================================================

function exportResults() {
    const results = Object.values(testResults).map(r => ({
        id: r.prompt_id,
        name: r.prompt_name,
        category: r.category,
        expected_detector: r.expected_detector,
        status: r.status,
        detectors_found: r.detectors_found,
        severity: r.result?.severity,
        findings_count: r.result?.findings?.length || 0,
        duration_ms: r.duration_ms
    }));
    
    const data = {
        timestamp: new Date().toISOString(),
        total_tests: results.length,
        passed: results.filter(r => r.status === 'PASS').length,
        failed: results.filter(r => r.status === 'FAIL').length,
        results: results
    };
    
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `detector-test-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function exportFailedTests() {
    const failedResults = Object.values(testResults)
        .filter(r => r.status === 'FAIL')
        .map(r => ({
            id: r.prompt_id,
            name: r.prompt_name,
            category: r.category,
            expected_detector: r.expected_detector,
            detectors_found: r.detectors_found,
            prompt: allPrompts.find(p => p.id === r.prompt_id)?.prompt || 'N/A',
            severity: r.result?.severity,
            findings: r.result?.findings || [],
            duration_ms: r.duration_ms
        }));
    
    if (failedResults.length === 0) {
        alert('No failed tests to export');
        return;
    }
    
    // Generate text report
    let text = `FAILED TEST CASES REPORT\n`;
    text += `========================\n\n`;
    text += `Generated: ${new Date().toISOString()}\n`;
    text += `Total Failed: ${failedResults.length}\n\n`;
    
    failedResults.forEach((test, idx) => {
        text += `\n${'='.repeat(80)}\n`;
        text += `TEST ${idx + 1}: #${test.id} - ${test.name}\n`;
        text += `${'='.repeat(80)}\n\n`;
        
        text += `Category: ${test.category}\n`;
        text += `Expected Detector: ${test.expected_detector}\n`;
        text += `Detectors Found: ${test.detectors_found.join(', ') || 'NONE'}\n`;
        text += `Severity: ${test.severity}\n`;
        text += `Findings Count: ${test.findings.length}\n`;
        text += `Duration: ${test.duration_ms}ms\n\n`;
        
        text += `PROMPT:\n`;
        text += `-------\n`;
        text += test.prompt + '\n\n';
        
        if (test.findings.length > 0) {
            text += `FINDINGS:\n`;
            text += `---------\n`;
            test.findings.forEach((f, i) => {
                text += `${i + 1}. ${f.reason} (${f.severity})\n`;
                text += `   Category: ${f.category}\n`;
                text += `   Confidence: ${f.confidence}\n`;
                text += `   Evidence: ${f.evidence}\n`;
            });
            text += '\n';
        }
    });
    
    // Download text file
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `failed-test-cases-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    alert(`Exported ${failedResults.length} failed test cases`);
}

function clearResults() {
    if (!confirm('Clear all test results?')) return;
    testResults = {};
    bulkPanel.style.display = 'none';
    statsCard.style.display = 'none';
    renderPromptList();
    renderDetailsPanel();
    renderResultsPanel(null);
}

// ============================================================================
// Utilities
// ============================================================================

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ============================================================================
// Event Listeners
// ============================================================================

runBtn.addEventListener('click', runSingleTest);
runAllBtn.addEventListener('click', runAllTests);
exportBtn.addEventListener('click', exportResults);
exportFailedBtn.addEventListener('click', exportFailedTests);
clearBtn.addEventListener('click', clearResults);

searchInput.addEventListener('input', filterPrompts);
categoryFilter.addEventListener('change', filterPrompts);

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Load prompts
    if (typeof window.PROMPTS !== 'undefined' && Array.isArray(window.PROMPTS)) {
        allPrompts = window.PROMPTS;
        filteredPrompts = [...allPrompts];
        renderPromptList();
        
        // Select first prompt
        if (allPrompts.length > 0) {
            selectPrompt(allPrompts[0]);
        }
    } else {
        promptList.innerHTML = '<div class="error">Failed to load prompts. Check browser console.</div>';
    }
});
