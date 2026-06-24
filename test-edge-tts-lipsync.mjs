import fs from 'node:fs';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');

function extractFunctionSource(name) {
  const marker = `function ${name}`;
  const start = html.indexOf(marker);
  if (start === -1) throw new Error(`Function ${name} not found`);
  const braceStart = html.indexOf('{', start);
  let depth = 0;
  for (let i = braceStart; i < html.length; i++) {
    const ch = html[i];
    if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) return html.slice(start, i + 1);
    }
  }
  throw new Error(`Function ${name} source not closed`);
}

const source = [
  'edgeTTSParseWordBoundary',
  'edgeTTSVisemeForToken',
  'edgeTTSTokenizeForVisemes',
  'edgeTTSBuildVisemes',
].map(extractFunctionSource).join('\n');
const context = vm.createContext({});
vm.runInContext(source, context);

const parse = context.edgeTTSParseWordBoundary;
const buildVisemes = context.edgeTTSBuildVisemes;

function edgeMessage(body) {
  return `X-RequestId:test\r\nPath:audio.metadata\r\nContent-Type:application/json\r\n\r\n${JSON.stringify(body)}`;
}

function assertBoundary(msg, expected) {
  assert.deepEqual(JSON.parse(JSON.stringify(parse(msg))), expected);
}

// Current Edge Read Aloud protocol wraps boundaries inside { Metadata: [...] } and uses Type/Data keys.
assertBoundary(edgeMessage({
  Metadata: [{
    Type: 'WordBoundary',
    Data: { Offset: 5750000, Duration: 2000000, text: { Text: 'for', Length: 3 } }
  }]
}), { word: 'for', startMs: 575, durMs: 200 });

assertBoundary(edgeMessage({
  Metadata: [{
    Type: 'WordBoundary',
    Data: { Offset: 1200000, Duration: 1800000, text: { Text: '你好', Length: 2 } }
  }]
}), { word: '你好', startMs: 120, durMs: 180 });

// Legacy flat/nested formats should keep working.
assertBoundary(edgeMessage({
  type: 'WordBoundary',
  Data: { Offset: 3000000, Duration: 1500000, text: { Text: 'legacy' } }
}), { word: 'legacy', startMs: 300, durMs: 150 });

assertBoundary(edgeMessage({
  type: 'wordBoundary',
  Text: 'flat',
  Offset: 1000000,
  Duration: 500000,
}), { word: 'flat', startMs: 100, durMs: 50 });

// Sentence metadata must not be treated as a word.
assert.equal(parse(edgeMessage({
  Metadata: [{
    Type: 'SentenceBoundary',
    Data: { Offset: 0, Duration: 1000000, text: { Text: 'hello world' } }
  }]
})), null);

const mixed = buildVisemes([
  { word: '你好', startMs: 0, durMs: 300 },
  { word: 'hello', startMs: 300, durMs: 500 },
]);
assert.ok(mixed.visemes.length >= 4, 'mixed Chinese/English text should produce explicit visemes');
assert.equal(mixed.visemes.length, mixed.vtimes.length);
assert.equal(mixed.visemes.length, mixed.vdurations.length);
assert.ok(mixed.vtimes.every(Number.isFinite));
assert.ok(mixed.vdurations.every(d => d >= 60));
assert.ok(!mixed.visemes.includes(undefined));

console.log('edge TTS lip-sync regression tests passed');
