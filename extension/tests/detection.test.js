'use strict';

const test = require('node:test');
const assert = require('node:assert');
const PSG = require('../detection.js');

const local = new PSG.LocalDetectionProvider();

// ---- Local keyword detection -------------------------------------------------

test('empty prompt is SAFE and allowed', async () => {
    const r = await local.scan('');
    assert.equal(r.severity, 'SAFE');
    assert.equal(r.allowSend, true);
    assert.deepEqual(r.findings, []);
});

test('whitespace-only prompt is SAFE', async () => {
    const r = await local.scan('   \n  ');
    assert.equal(r.severity, 'SAFE');
});

test('benign prompt is SAFE', async () => {
    const r = await local.scan('write a poem about the ocean');
    assert.equal(r.severity, 'SAFE');
    assert.equal(r.allowSend, true);
});

test('ChatGPT screenshot case: "my aws pasowrd is" is detected and BLOCKED', async () => {
    const r = await local.scan('my aws pasowrd is');
    // "aws" matches (HIGH). "pasowrd" is misspelled so it does NOT match "password".
    assert.equal(r.severity, 'HIGH');
    assert.equal(r.status, 'BLOCKED');
    assert.equal(r.allowSend, false);
    assert.ok(r.findings.some(f => f.reason === 'AWS Secret'));
});

test('password is CRITICAL and blocked', async () => {
    const r = await local.scan('my password is hunter2');
    assert.equal(r.severity, 'CRITICAL');
    assert.equal(r.allowSend, false);
});

test('personal name is MEDIUM warning but still allowed', async () => {
    const r = await local.scan('hello kiran how are you');
    assert.equal(r.severity, 'MEDIUM');
    assert.equal(r.status, 'WARNING');
    assert.equal(r.allowSend, true);
});

test('detection is case-insensitive', async () => {
    const r = await local.scan('MY AWS PASSWORD');
    assert.equal(r.severity, 'CRITICAL'); // password wins over aws
    assert.equal(r.allowSend, false);
});

test('multi-word keyword "credit card" matches', async () => {
    const r = await local.scan('here is my credit card number');
    assert.ok(r.findings.some(f => f.reason === 'Credit Card'));
    assert.equal(r.severity, 'CRITICAL');
});

test('highest severity wins across multiple matches', async () => {
    const r = await local.scan('this secret is also my password');
    assert.equal(r.severity, 'CRITICAL'); // password (CRITICAL) > secret (HIGH)
    assert.ok(r.findings.length >= 2);
});

test('duplicate reasons are de-duplicated', async () => {
    const r = await local.scan('password password password');
    const passwordFindings = r.findings.filter(f => f.reason === 'Password Detected');
    assert.equal(passwordFindings.length, 1);
});

// ---- normalizeFinding: hardening untrusted (API) output ----------------------

test('normalizeFinding strips angle brackets to prevent markup injection', () => {
    const f = PSG.normalizeFinding({ severity: 'HIGH', reason: '<img src=x onerror=alert(1)>' });
    assert.ok(!f.reason.includes('<'));
    assert.ok(!f.reason.includes('>'));
});

test('normalizeFinding coerces unknown severity to MEDIUM', () => {
    const f = PSG.normalizeFinding({ severity: 'BOGUS', reason: 'x' });
    assert.equal(f.severity, 'MEDIUM');
});

test('normalizeFinding caps reason length', () => {
    const f = PSG.normalizeFinding({ severity: 'LOW', reason: 'a'.repeat(9999) });
    assert.ok(f.reason.length <= 200);
});

test('buildResult ignores malformed findings', () => {
    const r = PSG.buildResult([null, 42, 'nope', { severity: 'HIGH', reason: 'ok' }]);
    assert.equal(r.findings.length, 1);
    assert.equal(r.severity, 'HIGH');
});

// ---- Remote provider ---------------------------------------------------------

function mockFetch(response, { throwError = false } = {}) {
    const calls = [];
    const fn = async (url, opts) => {
        calls.push({ url, opts });
        if (throwError) throw new Error('network down');
        return {
            ok: true,
            json: async () => response
        };
    };
    fn.calls = calls;
    return fn;
}

test('remote provider maps {findings:[...]} into a result', async () => {
    const fetchImpl = mockFetch({ findings: [{ severity: 'CRITICAL', reason: 'API Key' }] });
    const remote = new PSG.RemoteDetectionProvider({ endpoint: 'https://api.test/scan', fetchImpl });
    const r = await remote.scan('some prompt');
    assert.equal(r.severity, 'CRITICAL');
    assert.equal(r.findings[0].reason, 'API Key');
});

test('remote provider sends the prompt in the POST body, never the URL', async () => {
    const fetchImpl = mockFetch({ findings: [] });
    const remote = new PSG.RemoteDetectionProvider({ endpoint: 'https://api.test/scan', fetchImpl });
    await remote.scan('super secret prompt text');
    const call = fetchImpl.calls[0];
    assert.equal(call.opts.method, 'POST');
    assert.ok(!call.url.includes('super')); // not leaked in URL
    assert.ok(call.opts.body.includes('super secret prompt text'));
});

test('remote provider falls back to local rules on network error (onError:local)', async () => {
    const fetchImpl = mockFetch(null, { throwError: true });
    const remote = new PSG.RemoteDetectionProvider({ endpoint: 'https://api.test/scan', fetchImpl, onError: 'local' });
    const r = await remote.scan('my password is x');
    assert.equal(r.severity, 'CRITICAL'); // local rules caught it
});

test('remote provider fails safe when configured (onError:safe)', async () => {
    const fetchImpl = mockFetch(null, { throwError: true });
    const remote = new PSG.RemoteDetectionProvider({ endpoint: 'https://api.test/scan', fetchImpl, onError: 'safe' });
    const r = await remote.scan('my password is x');
    assert.equal(r.severity, 'SAFE');
});

test('remote provider fails closed when configured (onError:block)', async () => {
    const fetchImpl = mockFetch(null, { throwError: true });
    const remote = new PSG.RemoteDetectionProvider({ endpoint: 'https://api.test/scan', fetchImpl, onError: 'block' });
    const r = await remote.scan('anything');
    assert.equal(r.allowSend, false);
});

test('remote provider returns SAFE for empty input without calling fetch', async () => {
    const fetchImpl = mockFetch({ findings: [] });
    const remote = new PSG.RemoteDetectionProvider({ endpoint: 'https://api.test/scan', fetchImpl });
    const r = await remote.scan('');
    assert.equal(r.severity, 'SAFE');
    assert.equal(fetchImpl.calls.length, 0);
});

// ---- Engine factory ----------------------------------------------------------

test('createEngine follows the configured default mode (remote)', () => {
    const engine = PSG.createEngine();
    assert.ok(engine instanceof PSG.RemoteDetectionProvider);
});

test('createEngine builds a local provider when mode is local', () => {
    const engine = PSG.createEngine({ mode: 'local' });
    assert.ok(engine instanceof PSG.LocalDetectionProvider);
});

test('createEngine builds a remote provider when mode is remote', () => {
    const engine = PSG.createEngine({ mode: 'remote', endpoint: 'https://api.test/scan' });
    assert.ok(engine instanceof PSG.RemoteDetectionProvider);
});
