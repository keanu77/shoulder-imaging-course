// Usage: PLAYWRIGHT_MODULE=/path/to/playwright node tests/test-course-ui.cjs http://127.0.0.1:8911 /tmp/qa
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.argv[2] || 'http://127.0.0.1:8911';
const out = process.argv[3] || '/tmp/course-ui-qa';
fs.mkdirSync(out, {recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 // Deterministic UI tests: remote video decoding and external fonts are outside this test.
 await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
 const page=await context.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const results=[];
 const check=async(name,fn)=>{await fn();results.push(name);console.log('PASS',name);};
 const ready=async()=>page.waitForFunction(()=>document.body?.dataset.tab);
 const tab=async(name)=>page.locator(`.TabNav__item[data-tab="${name}"]`).click();
 const home=async()=>page.locator('.AppHeader__brand').click();
 const data=await (await context.request.get(base+'/course.json')).json();
 const unit=data.chapters[7].units[0].id; const chapter=data.chapters[7].code;
 try {
 await page.goto(base);await ready();
 await check('homepage modality counts and grouped chapter map',async()=>{
  assert.equal(await page.locator('.Pathway').count(),data.config.nav.length);
  assert.equal(await page.locator('.CourseMap .ChapterCard').count(),data.chapters.length);
  assert.equal(await page.locator('.GlossaryPanel').count(),data.glossary?.length?1:0);
  assert.equal(await page.locator('.Hero__reviewNote').count(),data.chapters.some(ch=>ch.units.some(u=>u.review_status==='approved'))?0:1);
  assert.equal(await page.locator('meta[name="robots"]').getAttribute('content').then(x=>x.includes('noindex')), !JSON.parse(fs.readFileSync('course/course.config.json','utf8')).medical.allowIndexing);
 });
 await page.screenshot({path:out+'/desktop-home.png'});
 await check('homepage search opens matching course results',async()=>{
  await page.locator('#search').fill('MRI');
  await page.waitForFunction(()=>document.body.dataset.tab==='course');
  await page.locator('[data-reset-filters]').click();await home();
 });
 await check('direct unit link overrides saved home tab' ,async()=>{
  await page.goto(base+'/#'+unit);await ready();
  await page.waitForFunction(()=>document.body.dataset.tab==='course');
  assert.ok(await page.locator('#'+unit+' .Unit__body').isVisible());
 });
 await check('hash navigation after tab switch',async()=>{
  await home();await page.evaluate(id=>location.hash=id,data.chapters[1].units[1].id);
  await page.waitForFunction(()=>document.body.dataset.tab==='course');
  assert.ok(await page.locator('#'+data.chapters[1].units[1].id+' .Unit__body').isVisible());
 });
 await check('chapter link overrides saved player tab',async()=>{
  await tab('player');await page.goto(base+'/#'+chapter);await ready();
  await page.waitForFunction(()=>document.body.dataset.tab==='course');
  assert.ok(await page.locator('#'+chapter).evaluate(el=>el.classList.contains('is-open')));
  assert.equal(await page.locator('#ytFrame').count(),0);
 });
 await check('search, empty result, and reset',async()=>{
  await page.locator('#search').fill('zzzz-no-such-imaging-unit');
  await page.locator('#filterBlank').waitFor();
  await page.locator('[data-reset-filters]').click();
  assert.equal(await page.locator('#search').inputValue(),'');
  assert.equal(await page.locator('.Chapter:not([hidden])').count(),data.chapters.length);
 });
 await check('modality navigation clears conflicting search',async()=>{
  await page.locator('#search').fill('zzzz-no-such-imaging-unit');await page.locator('#filterBlank').waitFor();
  await home();await page.locator('.Pathway').last().click();
  assert.equal(await page.locator('#search').inputValue(),'');
  assert.ok(await page.locator('#'+data.config.nav.at(-1).chapters[0]).isVisible());
 });
 await check('browser back restores previous chapter',async()=>{
  await home();await page.locator('.Pathway').first().click();
  await home();await page.locator('.Pathway').nth(1).click();
  await page.goBack();
  await page.waitForFunction(code=>location.hash==='#'+code&&document.body.dataset.tab==='course',data.config.nav[0].chapters[0]);
  assert.ok(await page.locator('#'+data.config.nav[0].chapters[0]).isVisible());
 });
 await check('player opens paused and explicit choice plays',async()=>{
  await tab('player');assert.equal(await page.locator('#ytFrame').count(),1);
  assert.ok((await page.locator('#ytFrame').getAttribute('src')).includes('autoplay=0'));
  await page.locator('.PlaylistItem').nth(1).click();
  assert.ok((await page.locator('#ytFrame').getAttribute('src')).includes('autoplay=1'));
 });
 const selected=await page.locator('#ytFrame').getAttribute('src');
 await check('player restores selected video after leaving',async()=>{
  await tab('course');assert.equal(await page.locator('#ytFrame').count(),0);await tab('player');
  assert.equal(await page.locator('#ytFrame').getAttribute('src'),selected.replace('autoplay=1','autoplay=0'));
 });
 await check('player reload remains paused',async()=>{
  await page.goto(base+'/?tab=player');await ready();
  assert.ok((await page.locator('#ytFrame').getAttribute('src')).includes('autoplay=0'));
 });
 await check('explicit video deep link plays selected video',async()=>{
  const video=data.chapters[0].units[0].drills[0].url.split('v=')[1];
  await page.goto(base+'/#play='+video);await ready();
  assert.ok((await page.locator('#ytFrame').getAttribute('src')).includes(video));
  assert.ok((await page.locator('#ytFrame').getAttribute('src')).includes('autoplay=1'));
 });
 await check('completion persists and updates map',async()=>{
  await page.goto(base+'/#'+unit);await ready();
  await page.locator('#'+unit+' [data-action="toggle-done"]').click();
  await home();assert.match(await page.locator('.ContinueCard__progressHead').innerText(),new RegExp('1 / '+data.meta.units));
  await page.reload();await ready();assert.match(await page.locator('.ContinueCard__progressHead').innerText(),new RegExp('1 / '+data.meta.units));
 });
 await check('all rendered icon references exist',async()=>{
  const missing=await page.evaluate(()=>[...new Set([...document.querySelectorAll('use')].map(el=>el.getAttribute('href')).filter(id=>id?.startsWith('#')&&!document.getElementById(id.slice(1))))]);
  assert.deepEqual(missing,[]);
 });
 for(const width of [1440,1024,821,820,768,767,390,360,320]) {
  await page.setViewportSize({width,height:1000});await home();
  await check(`home and course fit ${width}px`,async()=>{
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   // Compact 課程 / 影片 labels: preserve actual hit targets and visibility below.
   assert.equal(await page.locator('.TabNav__label:visible').count(),2);
   for (const item of await page.locator('.TabNav__item').all()) {
     const box=await item.boundingBox();assert.ok(box.width>=44&&box.height>=44);
     assert.ok(await item.evaluate(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}));
   }
   const bounds=await page.locator('.CourseGuide').boundingBox();assert.ok(bounds.x>=0&&bounds.x+bounds.width<=width+1);
   await page.screenshot({path:out+`/home-${width}.png`});
   await page.locator('.Pathway').last().click();
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:out+`/course-${width}.png`});
   await tab('player');
   assert.ok(await page.locator('#ytFrame').isVisible());
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:out+`/player-${width}.png`});
   assert.equal(await page.locator('body').getAttribute('data-tab'),'player');
  });
 }
 await check('dark theme preserves navigation',async()=>{
  await home();await page.locator('#themeToggle').click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.screenshot({path:out+'/dark-mobile.png'});
 });
 const segmentItem=data.chapters.flatMap(ch=>ch.units.flatMap(u=>u.drills||[])).find(d=>d.segments?.length);
 if(segmentItem) await check('existing segment notes still render and seek',async()=>{
   const vid=segmentItem.url.split('v=')[1];await page.goto(base+'/#play='+vid);await ready();
   assert.equal(await page.locator('.Segment').count(),segmentItem.segments.length);
   const jump=page.locator('[data-seek]').first();const second=await jump.getAttribute('data-seek');await jump.click();
   assert.ok((await page.locator('#ytFrame').getAttribute('src')).includes('start='+second));
 });
 await check('course data failure provides retry and recovers',async()=>{
   const failed=route=>route.fulfill({status:503,body:'unavailable'});
   await context.route('**/course.json*',failed);await page.goto(base);await page.locator('#retryCourse').waitFor();
   await context.unroute('**/course.json*',failed);await Promise.all([page.waitForNavigation(),page.locator('#retryCourse').click()]);await ready();
   assert.equal(await page.locator('.Chapter').count(),data.chapters.length);
 });
 await check('no uncaught browser errors' ,async()=>assert.deepEqual(errors,[]));
 fs.writeFileSync(out+'/results.json',JSON.stringify({base,passed:results.length,results,errors},null,2)+'\n');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
