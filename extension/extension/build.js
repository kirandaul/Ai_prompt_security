/*
 * build.js — produce an obfuscated, distributable build in ./dist.
 *
 * HONEST NOTE: obfuscation is a speed bump, not protection. Anyone can still
 * open chrome://extensions -> Inspect, or unpack the .crx, and read/deobfuscate
 * this code. Never put API keys, secrets, or trusted logic in the extension.
 * Keep those on your backend. This step only raises the effort for casual
 * copying.
 *
 * Usage:
 *   npm install          # installs javascript-obfuscator (dev dependency)
 *   npm run obfuscate    # writes ./dist
 * Then load the ./dist folder as the unpacked extension.
 */
'use strict';

const fs = require('fs');
const path = require('path');

let JavaScriptObfuscator;
try {
    JavaScriptObfuscator = require('javascript-obfuscator');
} catch (_e) {
    console.error('javascript-obfuscator is not installed. Run: npm install');
    process.exit(1);
}

const ROOT = __dirname;
const DIST = path.join(ROOT, 'dist');

const JS_FILES = ['detection.js', 'content.js', 'background.js'];
const COPY_FILES = ['manifest.json', 'styles.css'];
const COPY_DIRS = ['icons'];

const OBFUSCATOR_OPTIONS = {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.6,
    deadCodeInjection: true,
    deadCodeInjectionThreshold: 0.3,
    stringArray: true,
    stringArrayEncoding: ['base64'],
    stringArrayThreshold: 0.75,
    identifierNamesGenerator: 'hexadecimal',
    selfDefending: false, // keep off: selfDefending can break in some page contexts
    disableConsoleOutput: false
};

function rmrf(target) {
    if (fs.existsSync(target)) fs.rmSync(target, { recursive: true, force: true });
}

function copyDir(src, dest) {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
        const s = path.join(src, entry.name);
        const d = path.join(dest, entry.name);
        if (entry.isDirectory()) copyDir(s, d);
        else fs.copyFileSync(s, d);
    }
}

function main() {
    rmrf(DIST);
    fs.mkdirSync(DIST, { recursive: true });

    for (const file of JS_FILES) {
        const src = path.join(ROOT, file);
        if (!fs.existsSync(src)) continue;
        const code = fs.readFileSync(src, 'utf8');
        const result = JavaScriptObfuscator.obfuscate(code, OBFUSCATOR_OPTIONS);
        fs.writeFileSync(path.join(DIST, file), result.getObfuscatedCode(), 'utf8');
        console.log('obfuscated', file);
    }

    for (const file of COPY_FILES) {
        const src = path.join(ROOT, file);
        if (fs.existsSync(src)) {
            fs.copyFileSync(src, path.join(DIST, file));
            console.log('copied', file);
        }
    }

    for (const dir of COPY_DIRS) {
        const src = path.join(ROOT, dir);
        if (fs.existsSync(src)) {
            copyDir(src, path.join(DIST, dir));
            console.log('copied', dir + '/');
        }
    }

    console.log('\nBuild complete -> ./dist  (load this folder as the unpacked extension)');
}

main();
