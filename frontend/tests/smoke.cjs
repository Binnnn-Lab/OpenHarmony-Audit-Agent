/* Optional browser regression checks. Start scripts/serve_demo.py first. */
const puppeteer = require("puppeteer-core");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

(async () => {
  const launch = process.env.CHROME_PATH
    ? { executablePath: process.env.CHROME_PATH }
    : { channel: "chrome" };
  const browser = await puppeteer.launch({ ...launch, headless: true });
  const downloads = fs.mkdtempSync(path.join(os.tmpdir(), "oh-audit-demo-"));
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewport({ width: 1440, height: 1100 });
    await page.goto(process.env.DEMO_URL || "http://127.0.0.1:8765", {
      waitUntil: "networkidle0",
    });
    await page.emulateMediaFeatures([
      { name: "prefers-reduced-motion", value: "reduce" },
    ]);
    assert.equal(
      await page.$eval("#evidence-count", (el) => el.textContent),
      "00/ 12",
    );
    await page.click('[data-stage="6"]');
    assert.equal(
      await page.$eval("#evidence-count", (el) => el.textContent),
      "12/ 12",
    );
    assert.deepEqual(
      await page.$$eval("#findings .status", (els) =>
        els.map((el) => el.textContent),
      ),
      ["STATIC_ONLY", "REJECTED", "NEEDS_EVIDENCE"],
    );
    await page.click('[data-filter="boundary"]');
    assert.equal(
      await page.$eval("#candidate-id", (el) => el.textContent),
      "DEMO-002",
    );
    await page.click("#evidence-mini [data-evidence]");
    assert.equal(await page.$eval("#evidence-dialog", (el) => el.open), true);
    await page.keyboard.press("Escape");
    assert.equal(await page.$eval("#evidence-dialog", (el) => el.open), false);
    await page.click('nav [data-view="principles"]');
    // A deterministic result cannot compensate for missing basic evidence;
    // changing model confidence must never change a verdict.
    assert.equal(
      await page.$eval("#gate-verdict", (el) => el.textContent),
      "STATIC_ONLY",
    );
    await page.click("#gate-deterministic");
    assert.equal(
      await page.$eval("#gate-verdict", (el) => el.textContent),
      "CONFIRMED",
    );
    for (const field of ["path", "invariant", "counter"]) {
      await page.click(`#gate-${field}`);
      assert.equal(
        await page.$eval("#gate-verdict", (el) => el.textContent),
        "NEEDS_EVIDENCE",
      );
      await page.click(`#gate-${field}`);
    }
    await page.click("#gate-reject");
    assert.equal(
      await page.$eval("#gate-verdict", (el) => el.textContent),
      "REJECTED",
    );
    await page.click("#reset-lab");
    await page.$eval("#confidence", (el) => {
      el.value = 100;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    assert.equal(
      await page.$eval("#gate-verdict", (el) => el.textContent),
      "STATIC_ONLY",
    );
    await page.click('nav [data-view="evidence"]');
    assert.equal(
      await page.$$eval("#evidence-table tr", (els) => els.length),
      12,
    );
    await page.select("#evidence-filter", "DEMO-002");
    assert.equal(
      await page.$$eval("#evidence-table tr", (els) => els.length),
      4,
    );
    const client = await page.createCDPSession();
    await client.send("Page.setDownloadBehavior", {
      behavior: "allow",
      downloadPath: downloads,
    });
    await page.click("#export-json");
    await page.click('nav [data-view="report"]');
    await page.click("#export-report");
    await page.waitForFunction(() =>
      document.querySelector("#toast").textContent.includes("report"),
    );
    // Navigation and other interactions give Chromium time to flush downloads.
    await page.click('nav [data-view="workspace"]');
    await page.click("#reset");
    assert.equal(
      await page.$eval("#evidence-count", (el) => el.textContent),
      "00/ 12",
    );
    await page.click("#play");
    await page.waitForFunction(
      () => document.querySelector("#phase-value").textContent === "静态发现",
      { timeout: 6000 },
    );
    await page.click("#play");
    assert.equal(
      await page.$eval("#play", (el) => el.textContent.trim()),
      "▶ 播放审计过程",
    );
    await page.click("#next");
    assert.equal(
      await page.$eval("#phase-value", (el) => el.textContent),
      "语义审计",
    );
    await page.click("#present");
    assert.equal(
      await page.$eval("body", (el) => el.classList.contains("focus-mode")),
      true,
    );
    await page.click("#present");
    for (const width of [390, 768, 1440]) {
      await page.setViewport({ width, height: 900 });
      for (const view of ["workspace", "principles", "evidence", "report"]) {
        await page.click(`nav [data-view="${view}"]`);
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          true,
          `${view}: overflow at ${width}px`,
        );
      }
    }
    const exported = JSON.parse(
      fs.readFileSync(
        path.join(downloads, "openharmony-demo-evidence.json"),
        "utf8",
      ),
    );
    assert.equal(exported.demo, true);
    assert.equal(exported.evidence.length, 12);
    assert.equal(
      exported.decisions.some((d) => d.verdict === "CONFIRMED"),
      false,
    );
    assert.ok(
      fs
        .readFileSync(
          path.join(downloads, "openharmony-demo-report.md"),
          "utf8",
        )
        .includes("DEMO ONLY"),
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS: workflow, cases, evidence, gate rules, exports, focus mode, responsive layout and browser errors.",
    );
  } finally {
    await browser.close();
    // Only remove the unique temporary directory created above.
    fs.rmSync(downloads, { recursive: true, force: true });
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
