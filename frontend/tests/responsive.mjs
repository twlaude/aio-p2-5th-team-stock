import { spawn } from "node:child_process";
import { access, mkdir, rm } from "node:fs/promises";
import { createServer as createNetServer } from "node:net";
import path from "node:path";

import { chromium } from "playwright-core";

const HOST = "127.0.0.1";
const PORT = 8519;
const BASE = `http://${HOST}:${PORT}`;
const CHROME = process.env.CHROME_PATH || "/opt/google/chrome/chrome";
const SHOTS = path.resolve("tests/shots/responsive");
const ALL_VIEWPORTS = [
  { width: 320, height: 568 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 844, height: 390 },
  { width: 600, height: 1000 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
  { width: 2560, height: 1440 },
];
const requestedViewports = new Set(process.argv.slice(2));
const VIEWPORTS = ALL_VIEWPORTS.filter(({ width, height }) => (
  requestedViewports.size === 0 || requestedViewports.has(`${width}x${height}`)
));

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const log = (message) => console.log(`[TEST] ${message}`);

function pipe(stream, label) {
  stream.setEncoding("utf8");
  stream.on("data", (chunk) => {
    for (const line of chunk.split(/\r?\n/).filter(Boolean)) {
      console.log(`[TEST:${label}] ${line}`);
    }
  });
}

async function assertPortAvailable() {
  await new Promise((resolve, reject) => {
    const probe = createNetServer();
    probe.unref();
    probe.once("error", (error) => reject(new Error(`port ${PORT} is unavailable: ${error.message}`)));
    probe.listen({ host: HOST, port: PORT }, () => probe.close(resolve));
  });
}

async function waitForServer() {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try {
      if ((await fetch(BASE)).ok) return;
    } catch {
      // The dev server is still starting.
    }
    await sleep(250);
  }
  throw new Error(`dev server did not become ready at ${BASE}`);
}

async function startServer() {
  await assertPortAvailable();
  const server = spawn(
    path.resolve("node_modules/.bin/vite"),
    ["--host", HOST, "--port", String(PORT), "--strictPort"],
    {
      cwd: process.cwd(),
      env: { ...process.env, VITE_API_MODE: "mock" },
      detached: true,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  pipe(server.stdout, "dev");
  pipe(server.stderr, "dev");

  const earlyExit = new Promise((_, reject) => {
    server.once("error", reject);
    server.once("exit", (code, signal) => {
      reject(new Error(`dev server exited before ready (code=${code ?? "null"}, signal=${signal ?? "null"})`));
    });
  });
  await Promise.race([waitForServer(), earlyExit]);
  log(`mock dev server ready at ${BASE}`);
  return server;
}

async function stopServer(server) {
  if (!server || server.exitCode !== null || server.signalCode !== null) return;
  const exited = new Promise((resolve) => server.once("exit", resolve));
  const kill = (signal) => {
    try {
      process.kill(-server.pid, signal);
    } catch {
      server.kill(signal);
    }
  };

  kill("SIGTERM");
  const stopped = await Promise.race([exited.then(() => true), sleep(3000).then(() => false)]);
  if (!stopped) {
    kill("SIGKILL");
    await Promise.race([exited, sleep(1000)]);
  }
  log("mock dev server stopped");
}

function watchErrors(page, label) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
  return () => {
    if (errors.length) throw new Error(`${label} browser errors:\n${errors.join("\n")}`);
  };
}

async function trackedPage(browser, label, viewport) {
  const coarse = viewport.width <= 600;
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    hasTouch: coarse,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  page.setDefaultNavigationTimeout(12000);
  return { context, page, assertClean: watchErrors(page, label), coarse };
}

const goto = (page, pathname = "/") => page.goto(`${BASE}${pathname}`, { waitUntil: "domcontentloaded" });

async function save(page, name) {
  const file = path.join(SHOTS, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  log(`saved ${path.relative(process.cwd(), file)}`);
}

async function inspectLayout(page, { checkTargets, checkEvidenceGaps }) {
  return page.evaluate(({ shouldCheckTargets, shouldCheckEvidenceGaps }) => {
    const tolerance = 2;
    const viewportWidth = document.documentElement.clientWidth;
    const describe = (element) => {
      const id = element.id ? `#${element.id}` : "";
      const classNames = (element.getAttribute("class") ?? "")
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 3)
        .map((name) => `.${name}`)
        .join("");
      return `${element.tagName.toLowerCase()}${id}${classNames}`;
    };
    const isRendered = (element) => {
      let node = element;
      while (node && node !== document.documentElement) {
        const style = getComputedStyle(node);
        if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse" || Number(style.opacity) === 0) {
          return false;
        }
        node = node.parentElement;
      }
      const rect = element.getBoundingClientRect();
      return element.getClientRects().length > 0 && rect.width > 0.5 && rect.height > 0.5;
    };
    const horizontalScrollerFor = (element) => {
      let ancestor = element.parentElement;
      while (ancestor && ancestor !== document.body) {
        const overflowX = getComputedStyle(ancestor).overflowX;
        if (/^(auto|scroll|overlay)$/.test(overflowX) && ancestor.scrollWidth > ancestor.clientWidth + 1) {
          return ancestor;
        }
        ancestor = ancestor.parentElement;
      }
      return null;
    };

    const offscreen = [];
    for (const element of document.body.querySelectorAll("*")) {
      if (!isRendered(element)) continue;
      const rect = element.getBoundingClientRect();
      const scroller = horizontalScrollerFor(element);
      if (scroller) {
        const scrollerRect = scroller.getBoundingClientRect();
        const contentLeft = rect.left - scrollerRect.left + scroller.scrollLeft;
        const contentRight = contentLeft + rect.width;
        if (contentLeft < -tolerance || contentRight > scroller.scrollWidth + tolerance) {
          offscreen.push({
            element: describe(element),
            relativeTo: describe(scroller),
            left: Math.round(contentLeft * 10) / 10,
            right: Math.round(contentRight * 10) / 10,
            limit: scroller.scrollWidth,
          });
        }
      } else if (rect.left < -tolerance || rect.right > viewportWidth + tolerance) {
        offscreen.push({
          element: describe(element),
          relativeTo: "viewport",
          left: Math.round(rect.left * 10) / 10,
          right: Math.round(rect.right * 10) / 10,
          limit: viewportWidth,
        });
      }
    }

    const smallTargets = [];
    if (shouldCheckTargets) {
      for (const element of document.querySelectorAll("button, a")) {
        if (!isRendered(element)) continue;
        const height = element.getBoundingClientRect().height;
        if (height < 44 - tolerance / 2) {
          smallTargets.push({ element: describe(element), height: Math.round(height * 10) / 10 });
        }
      }
    }

    const evidenceGaps = [];
    if (shouldCheckEvidenceGaps) {
      const container = document.querySelector(".sallae-evidence-section__subsections");
      const sections = container
        ? [...container.children].filter((element) => isRendered(element))
        : [];
      for (let index = 1; index < sections.length; index += 1) {
        const previous = sections[index - 1];
        const current = sections[index];
        const gap = current.getBoundingClientRect().top - previous.getBoundingClientRect().bottom;
        evidenceGaps.push({
          from: describe(previous),
          to: describe(current),
          gap: Math.round(gap * 10) / 10,
        });
      }
      if (sections.length < 2) {
        evidenceGaps.push({ from: "missing", to: "missing", gap: Number.POSITIVE_INFINITY });
      }
    }

    return {
      documentWidth: {
        client: viewportWidth,
        scroll: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      },
      offscreen,
      smallTargets,
      evidenceGaps,
      pointerCoarse: matchMedia("(pointer: coarse)").matches,
    };
  }, { shouldCheckTargets: checkTargets, shouldCheckEvidenceGaps: checkEvidenceGaps });
}

async function assertResponsive(page, label, { coarse, evidence = false }) {
  const layout = await inspectLayout(page, { checkTargets: coarse, checkEvidenceGaps: evidence });
  const failures = [];

  if (layout.documentWidth.scroll > layout.documentWidth.client + 1) {
    failures.push(`document overflow ${layout.documentWidth.scroll} > ${layout.documentWidth.client} + 1`);
  }
  if (layout.offscreen.length) {
    failures.push(`out-of-bounds elements ${JSON.stringify(layout.offscreen.slice(0, 12))}`);
  }
  if (coarse && !layout.pointerCoarse) {
    failures.push("viewport <=600 did not emulate pointer: coarse");
  }
  if (layout.smallTargets.length) {
    failures.push(`targets below 44px ${JSON.stringify(layout.smallTargets.slice(0, 12))}`);
  }
  const largeGaps = layout.evidenceGaps.filter(({ gap }) => gap > 48 + 0.5);
  if (largeGaps.length) {
    failures.push(`evidence subsection gaps above 48px ${JSON.stringify(largeGaps)}`);
  }
  if (failures.length) throw new Error(`${label} responsive assertions failed:\n- ${failures.join("\n- ")}`);

  const gapSummary = evidence ? `, gaps=${layout.evidenceGaps.map(({ gap }) => gap).join("/")}px` : "";
  log(`${label} passed (document=${layout.documentWidth.scroll}/${layout.documentWidth.client}px, offscreen=0, small-targets=0${gapSummary})`);
}

async function loginState(browser, viewport, prefix) {
  const label = `${prefix}-login`;
  const { context, page, assertClean, coarse } = await trackedPage(browser, label, viewport);
  try {
    await goto(page, "/login");
    await page.getByRole("heading", { name: "누구로 들어갈까요?" }).waitFor();
    await page.waitForTimeout(250);
    await assertResponsive(page, label, { coarse });
    await save(page, label);
    assertClean();
  } finally {
    await context.close();
  }
}

async function loadingState(browser, viewport, prefix) {
  const label = `${prefix}-loading`;
  const { context, page, assertClean, coarse } = await trackedPage(browser, label, viewport);
  try {
    await goto(page, "/?scenario=slow");
    await page.locator(".loading-block").waitFor();
    await page.waitForTimeout(180);
    await assertResponsive(page, label, { coarse });
    await save(page, label);
    assertClean();
  } finally {
    await context.close();
  }
}

async function revealEvidence(page, label) {
  const sections = page.locator(".sallae-evidence-section__subsections > section");
  const count = await sections.count();
  if (count !== 4) throw new Error(`${label} expected 4 evidence subsections, got ${count}`);
  for (let index = 0; index < count; index += 1) {
    await sections.nth(index).scrollIntoViewIfNeeded();
    await page.waitForTimeout(180);
  }
  await page.waitForFunction(() => (
    document.querySelectorAll(".analysis-evidence-subsection--visible").length === 3
    && Boolean(document.querySelector(".analysis-gap--visible"))
  ));
  // Measure the real grid spacing only after every card's staggered reveal
  // transition has finished; zoom and a busy CI host can alter wall-clock timing.
  await page.waitForFunction(() => (
    [...document.querySelectorAll(".analysis-gap, .analysis-evidence-subsection")].every((element) => (
      element.getAnimations().every((animation) => !["pending", "running"].includes(animation.playState))
    ))
  ));
  await page.waitForTimeout(50);
}

async function resultState(browser, viewport, prefix) {
  const label = `${prefix}-result`;
  const { context, page, assertClean, coarse } = await trackedPage(browser, label, viewport);
  try {
    await goto(page, "/login");
    await page.getByRole("button", { name: /demo001로 로그인/ }).click();
    await page.waitForURL(`${BASE}/`);
    await page.waitForFunction(() => Boolean(localStorage.getItem("sallae.auth.session")));
    await page.getByLabel("기업명 또는 종목코드 6자리").fill("삼성전자");
    await page.getByRole("button", { name: /살펴보기/ }).click();
    const why = page.getByRole("button", { name: "왜 이렇게 판단했나요?" });
    await why.waitFor();
    await why.click();
    await revealEvidence(page, label);
    await assertResponsive(page, label, { coarse, evidence: true });
    await save(page, label);
    assertClean();
  } finally {
    await context.close();
  }
}

async function runViewport(browser, viewport) {
  const prefix = `${viewport.width}x${viewport.height}`;
  log(`${prefix} matrix started`);
  await loginState(browser, viewport, prefix);
  await loadingState(browser, viewport, prefix);
  await resultState(browser, viewport, prefix);
  log(`${prefix} matrix completed`);
}

async function main() {
  if (VIEWPORTS.length === 0) {
    throw new Error(`no matching viewport; choose from ${ALL_VIEWPORTS.map(({ width, height }) => `${width}x${height}`).join(", ")}`);
  }
  await access(CHROME);
  await rm(SHOTS, { recursive: true, force: true });
  await mkdir(SHOTS, { recursive: true });

  let server;
  let browser;
  try {
    server = await startServer();
    browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--no-sandbox"] });
    for (const viewport of VIEWPORTS) {
      await runViewport(browser, viewport);
    }
    log(`responsive matrix completed: ${VIEWPORTS.length} viewports x 3 states`);
  } finally {
    if (browser) await browser.close();
    await stopServer(server);
  }
}

main().catch((error) => {
  const detail = error instanceof Error ? error.stack : String(error);
  for (const line of detail.split(/\r?\n/)) console.error(`[TEST] ${line}`);
  process.exitCode = 1;
});
