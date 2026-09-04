import { spawn } from "node:child_process";
import { access, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const HOST = "127.0.0.1";
const PORT = 8519;
const BASE = `http://${HOST}:${PORT}`;
const CHROME = process.env.CHROME_PATH || "/opt/google/chrome/chrome";
const SHOTS = path.resolve("tests/shots");
const DESKTOP = { width: 1440, height: 960 };
const MOBILE = { width: 390, height: 844 };

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

async function waitForServer() {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try {
      if ((await fetch(BASE)).ok) {
        return;
      }
    } catch {
      await sleep(250);
    }
  }
  throw new Error(`dev server did not become ready at ${BASE}`);
}

async function startServer() {
  const server = spawn(path.resolve("node_modules/.bin/vite"), ["--host", HOST, "--port", String(PORT), "--strictPort"], {
    cwd: process.cwd(),
    env: { ...process.env, VITE_API_MODE: "mock" },
    detached: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  pipe(server.stdout, "dev");
  pipe(server.stderr, "dev");
  server.on("exit", (code, signal) => {
    if (code && code !== 0) console.log(`[TEST:dev] exited with code ${code}`);
    if (signal) console.log(`[TEST:dev] exited with signal ${signal}`);
  });
  await waitForServer();
  return server;
}

async function stopServer(server) {
  if (!server || server.exitCode !== null || server.signalCode !== null) return;
  const kill = (signal) => {
    try {
      process.kill(-server.pid, signal);
    } catch {
      server.kill(signal);
    }
  };
  kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => server.once("exit", resolve)),
    sleep(3000).then(() => kill("SIGKILL")),
  ]);
}

function watchErrors(page, label) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
  return () => {
    if (errors.length) throw new Error(`${label} console errors:\n${errors.join("\n")}`);
  };
}

async function trackedPage(browser, label, viewport = DESKTOP, reducedMotion = "no-preference") {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1, reducedMotion });
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  page.setDefaultNavigationTimeout(12000);
  return { context, page, assertClean: watchErrors(page, label) };
}

const goto = (page, pathname = "/") => page.goto(`${BASE}${pathname}`, { waitUntil: "domcontentloaded" });

async function save(page, name) {
  const file = path.join(SHOTS, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  log(`saved ${path.relative(process.cwd(), file)}`);
}

async function saveViewport(page, name) {
  const file = path.join(SHOTS, `${name}.png`);
  await page.screenshot({ path: file });
  log(`saved ${path.relative(process.cwd(), file)}`);
}

async function assertNoOverflow(page, label) {
  const widths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
  }));
  if (widths.scroll > widths.client + 1) throw new Error(`${label} horizontal overflow: ${widths.scroll} > ${widths.client}`);
}

async function assertNoInfiniteMotion(page, label) {
  const count = await page.evaluate(() => document.getAnimations().filter((animation) => animation.effect instanceof KeyframeEffect && animation.effect.getTiming().iterations === Infinity).length);
  if (count) throw new Error(`${label} has ${count} infinite animations`);
}

async function loginContext(browser, viewport = DESKTOP, reducedMotion = "no-preference") {
  const { context, page, assertClean } = await trackedPage(browser, "login-api", viewport, reducedMotion);
  await goto(page, "/login");
  await page.getByRole("button", { name: /demo001로 로그인/ }).click();
  await page.waitForURL(`${BASE}/`);
  await page.waitForFunction(() => Boolean(localStorage.getItem("sallae.auth.session")));
  assertClean();
  await page.close();
  return context;
}

async function revealCards(page) {
  const sections = page.locator(".analysis-evidence-subsection");
  for (let index = 0, count = await sections.count(); index < count; index += 1) {
    await sections.nth(index).scrollIntoViewIfNeeded();
    await page.waitForTimeout(220);
  }
}

async function idleShot(browser, viewport, name) {
  const { context, page, assertClean } = await trackedPage(browser, name, viewport);
  await goto(page);
  await page.getByRole("button", { name: "지원 20종목 보기" }).click();
  await page.getByRole("dialog", { name: "지원 기업 20개" }).waitFor();
  const count = await page.locator(".company-grid--sheet .company-grid__item").count();
  if (count !== 20) throw new Error(`${name} company sheet expected 20 items, got ${count}`);
  await page.getByLabel("지원 기업 목록 닫기").click();
  await page.waitForTimeout(200);
  if (viewport.width === MOBILE.width) await assertNoOverflow(page, name);
  await save(page, name);
  assertClean();
  await context.close();
}

async function loadingShot(browser) {
  const { context, page, assertClean } = await trackedPage(browser, "desktop-loading");
  await goto(page, "/?scenario=slow");
  await page.locator(".loading-block").waitFor();
  await page.waitForTimeout(650);
  await save(page, "desktop-loading");
  assertClean();
  await context.close();
}

async function guestShot(browser, gate) {
  const name = gate ? "desktop-gate" : "desktop-guest";
  const { context, page, assertClean } = await trackedPage(browser, name);
  await goto(page);
  await page.getByLabel("기업명 또는 종목코드 6자리").fill("삼성전자");
  await page.getByRole("button", { name: /살펴보기/ }).click();
  await page.getByRole("button", { name: "왜 이렇게 판단했나요?" }).waitFor();
  await page.waitForTimeout(1900);
  const ambient = await page.locator(".result-ambient__topic").count();
  if (ambient < 6) throw new Error(`${name} expected ambient topics around one-liner, got ${ambient}`);
  if (gate) {
    await page.getByRole("button", { name: "왜 이렇게 판단했나요?" }).click();
    await page.getByText("회원가입이 필요합니다!").waitFor();
  }
  await save(page, name);
  assertClean();
  await context.close();
}

async function loginShot(browser) {
  const { context, page, assertClean } = await trackedPage(browser, "desktop-login");
  await goto(page, "/login");
  await page.getByRole("heading", { name: "누구로 들어갈까요?" }).waitFor();
  await page.waitForTimeout(450);
  await save(page, "desktop-login");
  assertClean();
  await context.close();
}

async function memberShot(browser, viewport, name, pathname = "/") {
  const context = await loginContext(browser, viewport);
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const assertClean = watchErrors(page, name);
  await goto(page, pathname);
  if (pathname === "/") {
    await page.getByLabel("기업명 또는 종목코드 6자리").fill("삼성전자");
    await page.getByRole("button", { name: /살펴보기/ }).click();
  }
  await page.getByText("커뮤니티 반응").first().waitFor();
  await page.getByRole("button", { name: "왜 이렇게 판단했나요?" }).click();
  await revealCards(page);
  await page.locator(".analysis-personal-card").scrollIntoViewIfNeeded();
  await page.waitForTimeout(1100);
  if (viewport.width === MOBILE.width) await assertMobileMember(page, name);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(120);
  await save(page, name);
  assertClean();
  await context.close();
}

async function partialShot(browser) {
  const context = await loginContext(browser);
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const assertClean = watchErrors(page, "desktop-partial");
  await goto(page, "/?scenario=partial");
  await page.getByText("커뮤니티 데이터를 못 가져왔어요").waitFor();
  await revealCards(page);
  await page.locator(".analysis-personal-card").scrollIntoViewIfNeeded();
  await page.waitForTimeout(1100);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(120);
  await save(page, "desktop-partial");
  assertClean();
  await context.close();
}

async function communityShot(browser) {
  const context = await loginContext(browser);
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const assertClean = watchErrors(page, "desktop-community");
  await goto(page);
  await page.getByLabel("기업명 또는 종목코드 6자리").fill("삼성전자");
  await page.getByRole("button", { name: /살펴보기/ }).click();
  await page.getByRole("button", { name: "왜 이렇게 판단했나요?" }).click();
  await page.locator("#evidence-community").scrollIntoViewIfNeeded();
  await page.waitForTimeout(900);
  const topicChips = await page.locator(".analysis-evidence-topic").count();
  if (topicChips < 8) throw new Error(`desktop-community expected topic chips, got ${topicChips}`);
  await saveViewport(page, "desktop-community");
  assertClean();
  await context.close();
}

async function assertMobileMember(page, label) {
  await assertNoOverflow(page, label);
  const layout = await page.evaluate(() => {
    const tracks = (selector) => {
      const node = document.querySelector(selector);
      return node ? getComputedStyle(node).gridTemplateColumns.split(" ").filter(Boolean).length : 0;
    };
    const peek = document.querySelector(".analysis-peek-mascot");
    const visibleTopics = document.querySelectorAll(".result-ambient__topic").length;
    return { gauges: tracks(".sallae-evidence-section__gauges"), sections: document.querySelectorAll(".analysis-evidence-subsection").length, visibleTopics, peekWidth: peek ? Math.round(peek.getBoundingClientRect().width) : 0 };
  });
  if (layout.gauges !== 1 || layout.sections !== 3 || layout.visibleTopics > 6 || layout.peekWidth !== 64) {
    throw new Error(`${label} mobile layout mismatch: ${JSON.stringify(layout)}`);
  }
}

async function smoke(browser, pathname, text, label) {
  const { context, page, assertClean } = await trackedPage(browser, label);
  await goto(page, pathname);
  await page.getByText(text).waitFor();
  assertClean();
  await context.close();
  log(`smoke ok ${label}`);
}

async function mobileGateAndLogin(browser) {
  const gate = await trackedPage(browser, "mobile-gate", MOBILE);
  await goto(gate.page);
  await gate.page.getByLabel("기업명 또는 종목코드 6자리").fill("삼성전자");
  await gate.page.getByRole("button", { name: /살펴보기/ }).click();
  await gate.page.getByRole("button", { name: "왜 이렇게 판단했나요?" }).click();
  await gate.page.getByText("회원가입이 필요합니다!").waitFor();
  await assertNoOverflow(gate.page, "mobile-gate");
  const fits = await gate.page.evaluate(() => {
    const rect = document.querySelector(".guest-gate__card")?.getBoundingClientRect();
    return Boolean(rect && rect.left >= -1 && rect.right <= document.documentElement.clientWidth + 1);
  });
  if (!fits) throw new Error("mobile gate card overflows viewport");
  gate.assertClean();
  await gate.context.close();
  log("mobile gate layout ok");

  const login = await trackedPage(browser, "mobile-login", MOBILE);
  await goto(login.page, "/login");
  const columns = await login.page.evaluate(() => getComputedStyle(document.querySelector(".login-page__users")).gridTemplateColumns.split(" ").filter(Boolean).length);
  if (columns !== 2) throw new Error(`mobile login expected 2 columns, got ${columns}`);
  await assertNoOverflow(login.page, "mobile-login");
  login.assertClean();
  await login.context.close();
  log("mobile login layout ok");
}

async function reducedMotion(browser) {
  const loading = await trackedPage(browser, "reduced-motion", DESKTOP, "reduce");
  await goto(loading.page, "/?scenario=slow");
  await loading.page.locator(".loading-block").waitFor();
  const doneCount = await loading.page.locator(".loading-block__done").count();
  if (doneCount !== 4) throw new Error(`reduced-motion loading expected 4 done chips, got ${doneCount}`);
  await assertNoInfiniteMotion(loading.page, "reduced-motion-loading");
  loading.assertClean();
  await loading.context.close();

  const context = await loginContext(browser, DESKTOP, "reduce");
  const page = await context.newPage();
  const assertClean = watchErrors(page, "reduced-motion-member");
  await goto(page, "/?scenario=partial");
  await page.getByText("커뮤니티 데이터를 못 가져왔어요").waitFor();
  await assertNoInfiniteMotion(page, "reduced-motion-member");
  assertClean();
  await context.close();
  log("reduced-motion ok");
}

async function main() {
  await access(CHROME);
  await rm(SHOTS, { recursive: true, force: true });
  await mkdir(SHOTS, { recursive: true });
  const server = await startServer();
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--no-sandbox"] });
  try {
    await idleShot(browser, DESKTOP, "desktop-idle");
    await loadingShot(browser);
    await guestShot(browser, false);
    await guestShot(browser, true);
    await loginShot(browser);
    await memberShot(browser, DESKTOP, "desktop-member");
    await communityShot(browser);
    await partialShot(browser);
    await idleShot(browser, MOBILE, "mobile-idle");
    await memberShot(browser, MOBILE, "mobile-member");
    await smoke(browser, "/?scenario=unsupported", "아직 NAVER 분석은 제공하지 않아요", "desktop-unsupported");
    await smoke(browser, "/?scenario=error", "일시적으로 분석 데이터를 가져오지 못했어요.", "desktop-error");
    await mobileGateAndLogin(browser);
    await reducedMotion(browser);
    log("shots and E2E checks completed");
  } finally {
    await browser.close();
    await stopServer(server);
  }
}

main().catch((error) => {
  console.error(`[TEST] ${error instanceof Error ? error.stack : String(error)}`);
  process.exitCode = 1;
});
