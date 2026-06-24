// Real Microsoft Edge verification for the LLM browser fetch path.
// Run with a Playwright install that has the Edge channel available, for example:
//   TMP=/tmp/digital-human-edge-verify && mkdir -p "$TMP" && cd "$TMP"
//   npm init -y && npm install playwright@1.61.1
//   cp /Users/admin/projects/digital-human/edge-verify-llm-fetch.mjs .
//   node edge-verify-llm-fetch.mjs
// The test uses a fake API key. Passing means Edge reaches the API and gets HTTP 401,
// rather than failing at the browser network layer with TypeError: Failed to fetch.
import { chromium } from 'playwright';

const url = 'https://jakcm.github.io/digital-human/?edge-real-verify=' + Date.now();
const browser = await chromium.launch({
  channel: 'msedge',
  headless: true,
});
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  userAgent: undefined,
});
const page = await context.newPage();

const logs = [];
const requests = [];
const responses = [];
const failures = [];
page.on('console', msg => logs.push({ type: msg.type(), text: msg.text() }));
page.on('request', req => {
  const u = req.url();
  if (u.includes('/chat/completions')) {
    const h = req.headers();
    requests.push({
      url: u,
      method: req.method(),
      headers: {
        'content-type': h['content-type'] || null,
        authorization: h.authorization ? 'present' : null,
        'http-referer': h['http-referer'] || null,
        'x-title': h['x-title'] || null,
      },
    });
  }
});
page.on('response', resp => {
  const u = resp.url();
  if (u.includes('/chat/completions')) {
    responses.push({ url: u, status: resp.status(), statusText: resp.statusText() });
  }
});
page.on('requestfailed', req => {
  const u = req.url();
  if (u.includes('/chat/completions')) {
    failures.push({ url: u, method: req.method(), failure: req.failure()?.errorText || null });
  }
});

await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForSelector('#chat-input', { timeout: 60000 });

// Configure via real DOM on the page. Use fake key: success criterion is API-level 401,
// not browser-level TypeError/Failed to fetch.
await page.locator('#settings-btn').click();
await page.locator('#cfg-llm-key').fill('not-a-real-key');
await page.locator('#cfg-llm-url').fill('https://openrouter.ai/api/v1');
await page.locator('#cfg-llm-model').fill('deepseek/deepseek-v4-flash');
await page.locator('button[onclick="saveSettings()" i]').click();

await page.locator('#chat-input').fill('Edge 实测网络请求');
await page.locator('#chat-input-area button.btn-primary').click();
await page.waitForTimeout(7000);

const messages = await page.locator('.msg').evaluateAll(nodes => nodes.slice(-5).map(n => n.textContent));
const ua = await page.evaluate(() => navigator.userAgent);
const version = await page.locator('.version-tag').textContent().catch(() => null);

const result = {
  url,
  userAgent: ua,
  version,
  requests,
  responses,
  failures,
  lastMessages: messages,
  consoleErrors: logs.filter(x => x.type === 'error').slice(-5),
  pass: requests.length > 0 && failures.length === 0 && responses.some(r => r.status === 401) && messages.some(m => /API 401/.test(m)),
};

console.log(JSON.stringify(result, null, 2));
await browser.close();

if (!result.pass) process.exit(1);
