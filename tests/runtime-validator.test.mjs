import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(root, 'index.html'), 'utf8');

function scriptContent(id) {
  const pattern = new RegExp(`<script[^>]*id=["']${id}["'][^>]*>([\\s\\S]*?)<\\/script>`, 'i');
  const match = html.match(pattern);
  assert.ok(match, `Missing inline script #${id}`);
  return match[1];
}

const schema = JSON.parse(scriptContent('protocol-schema'));
const examples = JSON.parse(scriptContent('example-bundle'));
const masterPrompt = scriptContent('master-prompt').trim();
const appCode = scriptContent('app-code');
const schemaFile = JSON.parse(readFileSync(join(root, 'skill/schemas/coordinate-image-v1.schema.json'), 'utf8'));
const promptFile = readFileSync(join(root, 'skill/MASTER_PROMPT.md'), 'utf8').trim();

assert.deepEqual(schema, schemaFile, 'Embedded schema must match the source schema.');
assert.equal(masterPrompt, promptFile, 'Embedded master prompt must match the source file.');
for (const [key, value] of Object.entries(examples)) {
  const source = JSON.parse(readFileSync(join(root, 'skill/examples', `${key}.json`), 'utf8'));
  assert.deepEqual(value, source, `Embedded example ${key} must match its source file.`);
}

for (const forbidden of ['innerHTML', 'eval(', 'new Function', 'fetch(', 'XMLHttpRequest', 'document.write']) {
  assert.equal(appCode.includes(forbidden), false, `App must not use ${forbidden}`);
}
assert.equal(/https?:\/\//.test(appCode), false, 'App code must not depend on remote URLs.');

const sandbox = { console };
vm.createContext(sandbox);
vm.runInContext(appCode, sandbox, { filename: 'index.html:app-code' });
const CIE = sandbox.CoordinateImageEngine;
assert.ok(CIE, 'App must expose CoordinateImageEngine for tests.');
CIE.setEmbeddedData(schema, examples, masterPrompt);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function fakeCanvas(width = 100, height = 100) {
  const calls = { fill: 0, stroke: 0, fillRect: 0, text: 0, path: 0 };
  const gradient = {
    addColorStop(offset, color) {
      assert.equal(typeof offset, 'number');
      assert.ok(offset >= 0 && offset <= 1);
      assert.equal(typeof color, 'string');
    }
  };
  const ctx = {
    canvas: { width, height },
    globalAlpha: 1,
    fillStyle: '', strokeStyle: '', lineWidth: 1, lineCap: 'butt', lineJoin: 'miter',
    shadowColor: 'transparent', shadowBlur: 0, shadowOffsetX: 0, shadowOffsetY: 0,
    font: '', textAlign: 'left', textBaseline: 'alphabetic',
    imageSmoothingEnabled: true, imageSmoothingQuality: 'low',
    save() {}, restore() {}, setTransform() {}, clearRect() {},
    fillRect() { calls.fillRect += 1; },
    beginPath() { calls.path += 1; },
    moveTo() {}, lineTo() {}, quadraticCurveTo() {}, bezierCurveTo() {},
    arc() {}, ellipse() {}, rect() {}, closePath() {},
    fill() { calls.fill += 1; }, stroke() { calls.stroke += 1; },
    fillText() { calls.text += 1; }, strokeText() { calls.text += 1; },
    setLineDash(values) { assert.ok(Array.isArray(values)); },
    translate() {}, rotate() {}, scale() {},
    createLinearGradient() { return gradient; },
    createRadialGradient() { return gradient; }
  };
  const canvas = { width, height, getContext: () => ctx };
  ctx.canvas = canvas;
  return { canvas, ctx, calls };
}

function expectInvalid(label, mutate, matcher) {
  const doc = clone(examples['simple-diagram']);
  mutate(doc);
  const errors = CIE.validateDocument(doc);
  assert.ok(errors.length > 0, `${label}: expected validation errors`);
  if (matcher) {
    const text = errors.map(CIE.formatErrorShort).join('\n');
    assert.match(text, matcher, `${label}: diagnostics were not helpful`);
  }
}

assert.equal(CIE.parseJsonInput('```json\n{"a":1}\n```').a, 1, 'A single fenced JSON block should be accepted.');
assert.throws(() => CIE.parseJsonInput('{"protocol":'), /JSON syntax error/, 'Malformed JSON should produce a syntax error.');
assert.equal(CIE.parsePathData('m 1 2 l 3 4 c 1 0 2 0 3 1 q 1 1 2 0 z').length, 5, 'Relative path grammar should parse.');
assert.throws(() => CIE.parsePathData('M 0 0 L 1 1 2 2'), /explicit command letter/, 'Implicit path repetition must be rejected.');
assert.throws(() => CIE.parsePathData('M 0 0 A 10 10 0 0 1 20 20'), /restricted grammar/, 'SVG arcs must be rejected.');

for (const [key, doc] of Object.entries(examples)) {
  const errors = CIE.validateDocument(doc);
  assert.equal(errors.length, 0, `${key} should pass runtime validation: ${errors.map(CIE.formatErrorShort).join('; ')}`);
  const fake = fakeCanvas();
  const info = CIE.renderDocument(doc, fake.canvas, { scale: 1 });
  assert.equal(info.logicalWidth, doc.canvas.width);
  assert.equal(info.logicalHeight, doc.canvas.height);
  assert.ok(fake.calls.fillRect >= 1, `${key} should paint a background`);
  assert.ok(fake.calls.fill + fake.calls.stroke + fake.calls.text > 0, `${key} should draw at least one element`);
}

const icon = fakeCanvas();
const scaled = CIE.renderDocument(examples['app-icon'], icon.canvas, { scale: 2 });
assert.equal(scaled.width, 1024);
assert.equal(scaled.height, 1024);
assert.throws(() => CIE.renderDocument({ protocol: 'coordinate-image-v1', canvas: { width: 100, height: 100, background: '#fff' }, elements: [{ id: 'x', type: 'oval' }] }, fakeCanvas().canvas), /validation/, 'Rendering an invalid document must fail.');

expectInvalid('missing required fields', (doc) => delete doc.canvas, /Missing required property "canvas"/);
expectInvalid('unsupported element type', (doc) => { doc.elements[0].type = 'iframe'; }, /Unsupported element type/);
expectInvalid('invalid color', (doc) => { doc.canvas.background = 'red'; }, /hex color|String does not match|allowed form/i);
expectInvalid('out-of-range dimensions', (doc) => { doc.canvas.width = 9000; }, /at most 4096/);
expectInvalid('excessive element count', (doc) => {
  doc.elements = Array.from({ length: 1001 }, (_, i) => ({ id: `r${i}`, type: 'rectangle', x: 0, y: 0, width: 1, height: 1, fill: '#000' }));
}, /at most 1000 items|element count/);
expectInvalid('unknown root property', (doc) => { doc.unexpected = true; }, /Unknown property/);
expectInvalid('dangling gradient', (doc) => { doc.canvas.background = { gradient: 'missing' }; }, /not defined/);
expectInvalid('non-finite number', (doc) => { doc.canvas.width = Number('1e999'); }, /finite/);
expectInvalid('canvas area', (doc) => { doc.canvas.width = 4096; doc.canvas.height = 4096; }, /Canvas area/);
expectInvalid('duplicate id', (doc) => { doc.elements[0].id = 'duplicate'; doc.elements[1].id = 'duplicate'; }, /Duplicate element id/);
expectInvalid('malformed path', (doc) => {
  doc.elements = [{ id: 'path', type: 'path', d: 'M 0 0 L 10 10 20 20', stroke: '#fff', strokeWidth: 1 }];
}, /explicit command letter/);
expectInvalid('too many text lines', (doc) => {
  doc.elements = [{ id: 'text', type: 'text', x: 1, y: 2, text: Array(33).fill('line').join('\n'), fill: '#000' }];
}, /exceeds 32 lines/);
expectInvalid('deep nesting', (doc) => {
  let node = { id: 'leaf', type: 'rectangle', x: 0, y: 0, width: 1, height: 1, fill: '#000' };
  for (let i = 0; i < 9; i += 1) node = { id: `group${i}`, type: 'group', children: [node] };
  doc.elements = [node];
}, /nesting exceeds/);

console.log(`Runtime tests passed: ${Object.keys(examples).length} examples, schema checks, invalid-document checks, path grammar, and Canvas render calls.`);
