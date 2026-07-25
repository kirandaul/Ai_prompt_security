/**
 * validation_tests.js — Detection Validation Test Suite
 * 
 * Runs validation tests with transparent decision explanations
 * Shows real vs. test data detection with detailed reasoning
 */

let allTests = [];
let results = {};
let categoryFilter = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Loading validation test suite...');
    await loadTests();
});

async function loadTests() {
    try {
        const res = await fetch('/test-data/detection_validation.json');
        if (!res.ok) throw new Error('Failed to load test data');
        
        const data = await res.json();
        allTests = data.test_cases;
        
        console.log(`✓ Loaded ${allTests.length} validation test cases`);
        
        // Build category filter
        const categories = [...new Set(allTests.map(t => t.category))];
        buildCategoryFilter(categories);
    } catch (err) {
        console.error('Error loading tests:', err);
        showError('Failed to load test data');
    }
}

function buildCategoryFilter(categories) {
    const filterGrid = document.getElementById('filterGrid');
    filterGrid.innerHTML = '';
    
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.textContent = cat;
        btn.onclick = () => toggleFilter(cat, btn);
        filterGrid.appendChild(btn);
    });
}

function toggleFilter(category, btn) {
    categoryFilter = categoryFilter === category ? null : category;
    
    // Update button states
    document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.remove('active');
    });
    
    if (categoryFilter) {
        btn.classList.add('active');
    }
    
    // Redraw results
    displayResults();
}

async function runTests() {
    const loading = document.getElementById('loading');
    const results_container = document.getElementById('results');
    const stats = document.getElementById('stats');
    const filterSection = document.getElementById('filterSection');
    
    loading.style.display = 'block';
    results_container.innerHTML = '';
    stats.style.display = 'none';
    filterSection.style.display = 'block';
    
    results = {};
    
    const startTime = performance.now();
    let completed = 0;
    
    try {
        for (const test of allTests) {
            const testId = test.id;
            
            // Show progress
            completed++;
            const progress = (completed / allTests.length) * 100;
            document.getElementById('progressBar').style.display = 'block';
            document.getElementById('progressFill').style.width = progress + '%';
            
            // Run test
            const result = await runSingleTest(test);
            results[testId] = result;
            
            // Log for debugging
            console.log(`[${testId}] ${test.category}: ${result.passed ? '✓ PASS' : '✗ FAIL'}`);
        }
        
        const elapsed = performance.now() - startTime;
        
        loading.style.display = 'none';
        displayResults();
        displayStats(elapsed);
        
        document.getElementById('exportBtn').style.display = 'block';
        
    } catch (err) {
        console.error('Error running tests:', err);
        loading.style.display = 'none';
        showError('Error running tests: ' + err.message);
    }
}

async function runSingleTest(test) {
    try {
        const res = await fetch('/api/tester/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: test.prompt,
                expected_detector: test.detector,
                category: test.category,
                prompt_id: test.id,
                prompt_name: test.category
            })
        });
        
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        
        const apiResult = await res.json();
        
        // Check if action matches expected
        const expectedAction = test.expectedAction?.toUpperCase() || 'ALLOW';
        const apiAction = apiResult.result?.decision?.toUpperCase() || 'ALLOW';
        
        const passed = apiResult.status === 'PASS' || 
                      (test.expectedDetection && apiResult.detectors_found.length > 0) ||
                      (!test.expectedDetection && apiResult.detectors_found.length === 0);
        
        return {
            test,
            apiResult,
            passed,
            duration_ms: apiResult.duration_ms || 0,
            detectors: apiResult.detectors_found || [],
            explanation: generateExplanation(test, apiResult)
        };
    } catch (err) {
        console.error(`Error testing case ${test.id}:`, err);
        return {
            test,
            passed: false,
            error: err.message,
            duration_ms: 0,
            detectors: [],
            explanation: 'Error running test'
        };
    }
}

function generateExplanation(test, apiResult) {
    const action = test.expectedAction?.toUpperCase() || 'ALLOW';
    const detected = apiResult.detectors_found.length > 0;
    
    let explanation = test.decision?.explanation || '';
    
    if (test.validation?.reason) {
        explanation += `\n\nValidation: ${test.validation.reason}`;
    }
    
    return explanation;
}

function displayResults() {
    const container = document.getElementById('results');
    const noResults = document.getElementById('noResults');
    
    const testIds = Object.keys(results);
    
    if (testIds.length === 0) {
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    container.innerHTML = '';
    
    testIds.forEach(id => {
        const result = results[id];
        const test = result.test;
        
        // Apply filter
        if (categoryFilter && test.category !== categoryFilter) {
            return;
        }
        
        const card = createResultCard(result);
        container.appendChild(card);
    });
}

function createResultCard(result) {
    const test = result.test;
    const decision = test.decision || {};
    const validation = test.validation || {};
    
    const card = document.createElement('div');
    card.className = 'result-card';
    
    const statusClass = result.passed ? 'status-pass' : 'status-fail';
    const statusText = result.passed ? '✓ PASS' : '✗ FAIL';
    
    const severityClass = `severity-${(decision.severity || 'LOW').toLowerCase()}`;
    const severityBadge = `<span class="decision-severity ${severityClass}">${decision.severity || 'NONE'}</span>`;
    
    let validationBadges = '';
    if (validation.isTestCard !== undefined) {
        validationBadges += `<span class="validation-badge ${validation.isTestCard ? 'badge-test' : 'badge-real'}">
            ${validation.isTestCard ? '🧪 Test' : '⚠️ Real'}
        </span>`;
    }
    if (validation.luhnValid !== undefined) {
        validationBadges += `<span class="validation-badge ${validation.luhnValid ? 'badge-valid' : 'badge-invalid'}">
            ${validation.luhnValid ? '✓' : '✗'} Luhn
        </span>`;
    }
    if (validation.isFakeDomain !== undefined) {
        validationBadges += `<span class="validation-badge ${validation.isFakeDomain ? 'badge-test' : 'badge-real'}">
            ${validation.isFakeDomain ? '🧪 Test' : '⚠️ Real'}
        </span>`;
    }
    if (validation.isTestValue !== undefined) {
        validationBadges += `<span class="validation-badge ${validation.isTestValue ? 'badge-test' : 'badge-real'}">
            ${validation.isTestValue ? '🧪 Test' : '⚠️ Real'}
        </span>`;
    }
    if (validation.isPlaceholder !== undefined) {
        validationBadges += `<span class="validation-badge ${validation.isPlaceholder ? 'badge-test' : 'badge-real'}">
            ${validation.isPlaceholder ? '📝 Placeholder' : '⚙️ Production'}
        </span>`;
    }
    if (validation.isTestToken !== undefined) {
        validationBadges += `<span class="validation-badge ${validation.isTestToken ? 'badge-test' : 'badge-real'}">
            ${validation.isTestToken ? '🧪 Test' : '🔒 Real'}
        </span>`;
    }
    
    const detectorText = result.detectors.length > 0 
        ? result.detectors.join(', ')
        : '(none)';
    
    card.innerHTML = `
        <div class="result-header">
            <div class="result-id">Test #${test.id} — ${test.category}</div>
            <div class="result-status ${statusClass}">${statusText}</div>
        </div>
        <div class="result-body">
            <div class="result-field">
                <div class="field-label">📝 Type</div>
                <div class="field-value">${test.type}</div>
            </div>
            
            <div class="result-field">
                <div class="field-label">💬 Prompt</div>
                <div class="field-value code">${escapeHtml(test.prompt.substring(0, 100))}${test.prompt.length > 100 ? '...' : ''}</div>
            </div>
            
            <div class="result-field">
                <div class="field-label">🔍 Detectors Found</div>
                <div class="field-value">${detectorText}</div>
            </div>
            
            <div class="result-field">
                <div class="field-label">✓ Expected Action</div>
                <div class="field-value" style="font-weight: bold; color: ${test.expectedAction === 'ALLOW' ? '#48bb78' : '#f56565'};">
                    ${test.expectedAction}
                </div>
            </div>
            
            ${validationBadges ? `
            <div class="result-field">
                <div class="field-label">🔎 Validation</div>
                <div class="field-value" style="margin-top: 5px;">${validationBadges}</div>
            </div>
            ` : ''}
            
            <div class="reason-box">
                <strong>Decision Explanation:</strong><br>
                ${escapeHtml(decision.explanation || 'No explanation available')}
            </div>
            
            <div class="decision-box">
                ${severityBadge}
                <div style="font-size: 12px; color: #666; margin-top: 5px;">
                    <strong>Confidence:</strong> ${Math.round((decision.confidence || 0) * 100)}%<br>
                    <strong>Time:</strong> ${result.duration_ms}ms
                </div>
            </div>
        </div>
    `;
    
    return card;
}

function displayStats(elapsed) {
    const stats = document.getElementById('stats');
    const testIds = Object.keys(results);
    const passed = testIds.filter(id => results[id].passed).length;
    const failed = testIds.length - passed;
    
    document.getElementById('totalTests').textContent = testIds.length;
    document.getElementById('passedTests').textContent = passed;
    document.getElementById('failedTests').textContent = failed;
    document.getElementById('passPct').textContent = testIds.length > 0 ? 
        Math.round((passed / testIds.length) * 100) : 0;
    document.getElementById('failPct').textContent = testIds.length > 0 ? 
        Math.round((failed / testIds.length) * 100) : 0;
    document.getElementById('avgTime').textContent = 
        Math.round(elapsed / testIds.length) + 'ms';
    
    stats.style.display = 'grid';
}

function clearResults() {
    results = {};
    document.getElementById('results').innerHTML = '';
    document.getElementById('stats').style.display = 'none';
    document.getElementById('progressBar').style.display = 'none';
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('noResults').style.display = 'block';
    document.getElementById('exportBtn').style.display = 'none';
    document.getElementById('filterSection').style.display = 'none';
}

function exportResults() {
    const testIds = Object.keys(results);
    const passed = testIds.filter(id => results[id].passed);
    const failed = testIds.filter(id => !results[id].passed);
    
    let csv = 'Test ID,Category,Type,Status,Detector,Expected Action,Detected,Duration MS\n';
    
    testIds.forEach(id => {
        const result = results[id];
        const test = result.test;
        const detectors = result.detectors.join('|') || 'NONE';
        
        csv += `${test.id},"${test.category}","${test.type}","${result.passed ? 'PASS' : 'FAIL'}","${test.detector}","${test.expectedAction}","${detectors}",${result.duration_ms}\n`;
    });
    
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = `validation-results-${Date.now()}.csv`;
    link.click();
}

function showError(message) {
    const container = document.getElementById('results');
    container.innerHTML = `<div style="background: #fed7d7; color: #742a2a; padding: 20px; border-radius: 8px; margin-top: 20px;">
        <strong>❌ Error:</strong> ${message}
    </div>`;
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

// Debug logging
window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);
});
