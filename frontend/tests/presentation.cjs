const puppeteer = require("puppeteer-core");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const os = require("node:os");
const { pathToFileURL } = require("node:url");

(async () => {
  const isolated = fs.mkdtempSync(path.join(os.tmpdir(), 'oh-recording-'));
  const entry = path.join(isolated, 'recording.html');
  const portable = path.resolve(__dirname, '../../deliverables/03-recording-demo.html');
  assert.equal(fs.readFileSync(portable,'utf8'),fs.readFileSync(path.resolve(__dirname,'../demo.html'),'utf8'));
  fs.copyFileSync(portable,entry);
  const browser = await puppeteer.launch({
    headless: true,
    ...(process.env.CHROME_PATH
      ? { executablePath: process.env.CHROME_PATH }
      : { channel: "chrome" }),
  });
  try {
    const page = await browser.newPage();
    const errors = [],
      remoteRequests = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("request", (request) => {
      if (/^https?:/.test(request.url())) remoteRequests.push(request.url());
    });
    await page.setViewport({ width: 1440, height: 1000 });
    await page.emulateMediaFeatures([
      { name: "prefers-reduced-motion", value: "reduce" },
    ]);
    await page.goto(
      pathToFileURL(entry).href,
    );
    const text = (selector) => page.$eval(selector, (el) => el.textContent);
    const choose = (number) => page.click(`[data-chapter="${number - 1}"]`);
    assert.equal(await page.$$eval(".slide.active", (els) => els.length), 1);
    await page.click('.top [data-reading="guide"]');
    assert.equal(await page.$eval('#reading-dialog',el=>el.open),true);
    assert.match(await text('#reading-content'),/Python 3.10/);
    await page.keyboard.press('PageDown');
    assert.equal(await text('#chapter-number'),'01 / 08');
    await page.keyboard.press('Escape');
    assert.equal(await page.$eval('#reading-dialog',el=>el.open),false);
    await page.click('.top [data-reading="speech"]');
    assert.equal(await page.$$eval('#reading-content h2',els=>els.length),8);
    await page.click('#reading-content nav a:last-child');
    assert.equal(await text('#chapter-number'),'01 / 08');
    await page.click('#close-reading');
    assert.equal(await page.$$eval('a[href]',els=>els.every(el=>el.getAttribute('href').startsWith('#'))),true);
    assert.equal(await page.$$eval('script[src],link[rel="stylesheet"],img[src]',els=>els.length),0);
    await choose(2);
    assert.match(await text("#flow-left-data"), /CodeQL required: no/);
    await page.click('[data-flow="roles"]');
    assert.match(await text("#flow-right-data"), /DEMO-001 \/ r1/);
    await page.click('[data-flow="call"]');
    await page.click('#flow-return');
    assert.match(await text("#flow-right-data"), /DEMO-E01/);
    assert.equal(await page.$eval('#flow-return',el=>el.disabled),true);
    await page.click('[data-flow="checkpoint"]');
    await page.click('#flow-save');
    assert.match(await text("#flow-right-data"), /已中断/);
    await page.click('#flow-resume');
    assert.match(await text("#flow-right-data"), /可继续/);
    assert.match(await text("#flow-right-data"), /DEMO-E01/);
    assert.match(await text("#flow-right-data"), /DEMO-001 \/ r1/);
    await page.click('[data-flow="map"]');
    assert.equal(await page.$eval('#system-map',el=>el.hidden),false);
    await choose(1);
    await page.click("#jump-case");
    assert.equal(await text("#case-kicker"), "STEP 01 / 05");
    for (let i = 2; i <= 5; i++) {
      await page.click("#next");
      assert.equal(await text("#case-kicker"), `STEP 0${i} / 05`);
      assert.equal(await text("#chapter-number"), "03 / 08");
    }
    assert.match(await text("#paper-content"), /STATIC_ONLY/);
    await page.click("#next");
    assert.equal(await text("#chapter-number"), "04 / 08");
    assert.match(await text("#input-result"), /违反容量/);
    assert.match(await text("#domain-result"), /n = 65/);
    for (const n of [32,64,96]) {
      await page.click(`[data-length="${n}"]`);
      assert.equal(await page.$eval('#length',el=>Number(el.value)),n);
    }
    const setLength = async (n) =>
      page.$eval(
        "#length",
        (el, value) => {
          el.value = value;
          el.dispatchEvent(new Event("input", { bubbles: true }));
        },
        n,
      );
    for (const n of [0, 32, 64]) {
      await setLength(n);
      assert.match(await text("#input-result"), /满足容量/);
      assert.match(await text("#domain-result"), /n = 65/);
    }
    for (const n of [65, 256]) {
      await setLength(n);
      assert.match(await text("#input-result"), /违反容量/);
    }
    await page.click("#guard");
    assert.match(await text("#input-result"), /阻断/);
    assert.match(await text("#domain-result"), /无满足危险条件/);
    await setLength(64);
    assert.match(await text("#input-result"), /满足容量/);
    // Arrow keys inside the range must remain input controls, not navigate slides.
    await page.focus("#length");
    await page.keyboard.press("ArrowLeft");
    assert.equal(await text("#chapter-number"), "04 / 08");
    await page.click("#prev");
    assert.equal(await text("#case-kicker"), "STEP 05 / 05");
    await page.click("#prev");
    assert.equal(await text("#case-kicker"), "STEP 04 / 05");
    await choose(5);
    for (const key of ["needs", "static", "confirmed", "rejected"]) {
      await page.click(`[data-verdict="${key}"]`);
      assert.equal(
        await page.$eval(`[data-verdict="${key}"]`, (el) =>
          el.getAttribute("aria-pressed"),
        ),
        "true",
      );
    }
    await choose(6);
    await page.click("#cycle-next");
    assert.match(await text("#cycle-kicker"), /REGRESSION/);
    await page.$eval('[data-cycle="2"]', (el) => el.focus());
    await page.keyboard.press("Enter");
    assert.match(await text("#cycle-kicker"), /REUSE/);
    await page.click("#notes-toggle");
    assert.equal(await page.$eval("#notes", (el) => el.hidden), false);
    await page.keyboard.press("Escape");
    assert.equal(await page.$eval("#notes", (el) => el.hidden), true);
    await choose(1);
    await page.click("#auto");
    await page.waitForFunction(
      () => document.querySelector("#chapter-number").textContent === "02 / 08",
      { timeout: 12000 },
    );
    await page.click("#auto");
    assert.equal(
      await page.$eval("#auto", (el) => el.getAttribute("aria-pressed")),
      "false",
    );
    for (const width of [390, 768, 1440]) {
      await page.setViewport({ width, height: 900 });
      for (let i = 1; i <= 8; i++) {
        await choose(i);
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          true,
          `chapter ${i} overflow at ${width}`,
        );
        assert.equal(
          await page.$$eval(".slide.active", (els) => els.length),
          1,
        );
      }
    }
    await page.click("#restart");
    assert.equal(await text("#chapter-number"), "01 / 08");
    assert.equal(await page.$eval("#guard", (el) => el.checked), false);
    assert.equal(await page.$eval("#length", (el) => el.value), "96");
    assert.deepEqual(errors, []);
    assert.deepEqual(remoteRequests, []);
    console.log(
      "PASS: isolated single-file HTML, embedded guide and 8-page speech, presets, 8 chapters, 5 case steps, constraint boundaries, 4 verdicts, feedback, keyboard, autoplay, reset, responsive layout; no remote requests or browser errors.",
    );
  } finally {
    await browser.close();
    fs.unlinkSync(entry);
    fs.rmdirSync(isolated);
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
