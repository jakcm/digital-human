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
  'edgeTTSEstimateBoundaries',
  'edgeTTSBuildAnimItems',
].map(extractFunctionSource).join('\n');
const context = vm.createContext({});
vm.runInContext(source, context);

const parse = context.edgeTTSParseWordBoundary;
const buildVisemes = context.edgeTTSBuildVisemes;
const estimateBoundaries = context.edgeTTSEstimateBoundaries;
const buildAnimItems = context.edgeTTSBuildAnimItems;

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
assert.equal(mixed.words.length, mixed.visemes.length, 'words are split to viseme-level pseudo words so speakAudio cannot skip animation');
assert.equal(mixed.visemes.length, mixed.vtimes.length);
assert.equal(mixed.visemes.length, mixed.vdurations.length);
assert.ok(mixed.vtimes.every(Number.isFinite));
assert.ok(mixed.vdurations.every(d => d >= 60));
assert.ok(!mixed.visemes.includes(undefined));

// SpeechSynthesis fallback must produce manual TalkingHead animQueue items.
const estimated = estimateBoundaries('你好老板 hello world');
assert.ok(estimated.length >= 4, 'Chinese/English fallback boundaries should be generated');
const fallbackVisemes = buildVisemes(estimated);
const anims = buildAnimItems(fallbackVisemes, 1000);
assert.equal(anims.length, fallbackVisemes.visemes.length);
assert.ok(anims.every(a => a.template.name === 'viseme'));
assert.ok(anims.every(a => a.ts.length === 3 && a.ts.every(Number.isFinite)));
assert.ok(anims.some(a => Object.keys(a.vs).some(k => k.startsWith('viseme_'))));

const earlyAnims = buildAnimItems(fallbackVisemes, 1000, -120);
assert.equal(earlyAnims[0].ts[1], anims[0].ts[1] - 120, 'negative offset should make lip sync lead audio');
assert.ok(html.includes("id=\"cfg-lipsync-offset\""), 'UI exposes lip-sync offset tuning');
assert.ok(html.includes("utterance.onstart") && html.includes("queueLipSync('speechSynthesis-onstart')"), 'manual fallback should anchor lip-sync to SpeechSynthesis onstart');
assert.ok(html.includes("speechSynthesis-fallback-timer"), 'manual fallback keeps a safety net when onstart is blocked');

console.log('edge/browser TTS lip-sync regression tests passed');
