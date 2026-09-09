// Run against the independently rendered draft, never the production output.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = (process.argv[2] || 'http://127.0.0.1:8920/cervical').replace(/\/$/, '');
const published = process.env.PUBLIC_WORKSHOP === '1';
const out = process.argv[3] || '/tmp/advanced-review-qa';
const data = JSON.parse(fs.readFileSync('course/research/2026-09-09-advanced/package.json', 'utf8'));
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
  const errors = [], results = [];
  await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  const go = async path => {
    await page.goto('about:blank');
    await Promise.all([page.waitForResponse(response => /\/questions(?:\.[a-f0-9]+)?\.json$/.test(response.url())), page.goto(path)]);
  };
  const check = async (name, fn) => { await fn(); results.push(name); console.log('PASS', name); };
  try {
    await go(base + '/');
    await check('draft scope, counts, provenance and noindex', async () => {
      assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'), published ? 'noindex,follow' : 'noindex,nofollow');
      assert.equal(await page.locator('article.unit').count(), 3);
      assert.equal(await page.locator('[data-question]').count(), 9);
      assert.equal(await page.locator('[data-case]').count(), 6);
      assert.match(await page.locator('.intro').innerText(), published ? /供醫療專業人員/ : /待臨床審閱/);
      assert.equal(await page.locator('.digest').textContent().then(t => t.split('：')[1].length), 64);
    });
    for (const width of [1440, 820, 390, 320]) {
      await check(`all units fit viewport ${width}`, async () => {
        await page.setViewportSize({ width, height: 1000 });
        for (const unit of data.units) {
          await page.locator(`nav a[href="#${unit.id}"]`).click();
          await page.locator(`#${unit.id}`).waitFor({ state: 'visible' });
          await page.waitForFunction(id => document.activeElement.id === id, unit.id);
          assert.equal(await page.locator('.unit:visible').count(), 1);
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
        }
        await page.screenshot({ path: `${out}/review-${width}.png`, fullPage: false });
      });
    }
    await page.setViewportSize({ width: 1440, height: 1050 });
    for (const unit of data.units) {
      await page.locator(`nav a[href="#${unit.id}"]`).click();
          await page.locator(`#${unit.id}`).waitFor({ state: 'visible' });
          await page.waitForFunction(id => document.activeElement.id === id, unit.id);
      await check(`${unit.id}: every quiz wrong, right and all rationales`, async () => {
        for (const question of unit.questions) {
          const form = page.locator(`[data-question="${question.id}"]`);
          const wrong = question.options.findIndex(option => !option.correct);
          const correct = question.options.findIndex(option => option.correct);
          await form.locator(`input[value="${wrong}"]`).check();
          await form.locator('button').click();
          await form.locator('.feedback').filter({ hasText: '本題需再核對' }).waitFor();
          assert.equal(await form.locator('.feedback p').count(), 3);
          for (const option of question.options) assert.ok((await form.locator('.feedback').innerText()).includes(option.rationale));
          await form.locator(`input[value="${correct}"]`).check();
          await form.locator('button').click();
          await form.locator('.feedback').filter({ hasText: '本題答對' }).waitFor();
        }
      });
      await check(`${unit.id}: cases, rubric and local notes`, async () => {
        for (const item of unit.cases) {
          const textarea = page.locator(`#${item.id}`);
          await textarea.fill('測試筆記：所見、限制與待補資料。');
          const section = textarea.locator('..');
          await section.locator('summary').click();
          assert.ok((await section.innerText()).includes(item.sample_report));
          assert.equal(await section.locator('details li').count(), item.rubric.length);
        }
      });
    }
    await check('answers and notes persist on reload and deep link', async () => {
      await go(base + '/#' + data.units[1].id);
      assert.ok(await page.locator('#' + data.units[1].id).isVisible());
      assert.equal(await page.locator('#' + data.units[1].cases[0].id).inputValue(), '測試筆記：所見、限制與待補資料。');
      await page.locator(`#${data.units[1].id} .feedback`).first().filter({ hasText: '本題答對' }).waitFor();
    });
    await check('back navigation and invalid hash fallback', async () => {
      await page.locator(`nav a[href="#${data.units[2].id}"]`).click();
      await page.goBack();
      assert.ok(await page.locator('#' + data.units[1].id).isVisible());
      await go(base + '/#no-such-unit');
      assert.ok(await page.locator('#' + data.units[0].id).isVisible());
    });
    await check('print includes every unit and answer rubric', async () => {
      await page.evaluate(() => { window.print = () => {}; });
      await page.locator('#print').click();
      assert.equal(await page.locator('details:not([open])').count(), 0);
      await page.emulateMedia({ media: 'print' });
      assert.equal(await page.locator('.unit:visible').count(), 3);
      await page.pdf({ path: `${out}/workshop.pdf`, format: 'A4', printBackground: true });
      await page.emulateMedia({ media: 'screen' });
    });
    await check('reset is scoped to this package and preserves unrelated progress', async () => {
      await page.evaluate(() => localStorage.setItem('unrelated-course-progress', 'keep'));
      await page.locator('#reset').click();
      assert.equal(await page.evaluate(() => localStorage.getItem('unrelated-course-progress')), 'keep');
      assert.equal(await page.locator('.feedback:not(:empty)').count(), 0);
      assert.deepEqual(await page.locator('[data-case]').evaluateAll(inputs => inputs.map(input => input.value)), ['', '', '', '', '', '']);
    });
    await check('blocked storage still permits reading and answering', async () => {
      const isolated = await browser.newContext();
      await isolated.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } }); });
      const p = await isolated.newPage();
      await p.goto(base + '/');
      await p.locator('#storage-status').filter({ hasText: '無法儲存' }).waitFor();
      const form = p.locator('[data-question]').first();
      await form.locator('input').first().check(); await form.locator('button').click();
      await form.locator('.feedback strong').waitFor();
      await isolated.close();
    });
    await check('failed questions response gives a readable recovery message', async () => {
      const isolated = await browser.newContext();
      await isolated.route('**/questions*.json', route => route.fulfill({ status: 503, body: '{}' }));
      const p = await isolated.newPage(); await p.goto(base + '/');
      await p.locator('#storage-status').filter({ hasText: '解析暫時無法載入' }).waitFor();
      assert.ok(await p.locator('.unit').first().isVisible());
      await isolated.close();
    });
    await check('without JavaScript all teaching and report examples remain readable', async () => {
      const isolated = await browser.newContext({ javaScriptEnabled: false });
      const p = await isolated.newPage(); await p.goto(base + '/');
      assert.equal(await p.locator('.unit:visible').count(), 3);
      assert.ok(await p.locator('noscript').isVisible());
      await isolated.close();
    });
    await check('source links match the package and use safe new tabs', async () => {
      const expected = data.units.flatMap(unit => unit.cases).filter(item => item.source_url).map(item => item.source_url);
      assert.deepEqual(await page.locator('.source-button').evaluateAll(links => links.map(link => link.href)), expected);
      assert.equal(await page.locator('a[target="_blank"]:not([rel*="noopener"])').count(), 0);
    });
    assert.deepEqual(errors, []);
    fs.writeFileSync(out + '/results.json', JSON.stringify({ passed: results.length, scenarios: results, errors }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
