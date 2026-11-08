import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const root = process.cwd();
const baseUrl = process.argv[2] || process.env.KALAM_BASE_URL || "http://127.0.0.1:3000";
const inventory = JSON.parse(fs.readFileSync(path.join(root, "qa", "generated", "kalam-brand-surface-inventory.json"), "utf8"));
const allRoutes = process.argv.includes("--all");
const requestedRoutes = process.argv.slice(3).filter(value => value !== "--all");
const routes = allRoutes
  ? [...new Set(inventory.page_metadata.map(item => item.route))]
      .map(route => route.replace(/:id/g, "audit-sample").replace(/:tenant/g, "demo").replace(/:code/g, "audit-sample"))
  : requestedRoutes.length ? requestedRoutes
  : ["/", "/clients", "/contact-sales", "/free-trial", "/guided-evaluation", "/implementation", "/integrations", "/login", "/pricing", "/trust", "/forgot-password", "/reset-password", "/dashboard", "/unknown-brand-audit-route"];
const cdpBase = process.env.KALAM_CDP_URL || "http://127.0.0.1:9333";
let buildCommit = null;
try {
  const response = await fetch(new URL("/", baseUrl));
  buildCommit = response.headers.get("x-kalam-build-commit");
} catch {}
const axePath = require.resolve("axe-core/axe.min.js");
const axeSource = fs.readFileSync(axePath, "utf8");
const outputPath = path.join(root, "qa", "generated", "kalam-brand-accessibility-smoke.json");

const targetResponse = await fetch(cdpBase + "/json/new?about:blank", { method: "PUT" });
if (!targetResponse.ok) throw new Error("Could not create Chrome DevTools target: " + targetResponse.status);
const target = await targetResponse.json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.addEventListener("open", resolve, { once: true });
  ws.addEventListener("error", reject, { once: true });
});

let nextId = 0;
const pending = new Map();
ws.addEventListener("message", event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const item = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) item.reject(new Error(message.error.message));
    else item.resolve(message.result);
  }
});

function send(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression, awaitPromise = false) {
  const response = await send("Runtime.evaluate", {
    expression, awaitPromise, returnByValue: true, userGesture: true
  });
  if (response.exceptionDetails) {
    throw new Error(response.exceptionDetails.text || "Browser evaluation failed");
  }
  return response.result?.value;
}

async function waitForLoad() {
  const start = Date.now();
  while (Date.now() - start < 20000) {
    try {
      const state = await evaluate("document.readyState");
      if (state === "complete") return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error("Timed out waiting for page load");
}

await send("Page.enable");
await send("Runtime.enable");
const results = [];

try {
  for (const route of routes) {
    const url = new URL(route, baseUrl).href;
    try {
      await send("Page.navigate", { url });
      await waitForLoad();
      await new Promise(resolve => setTimeout(resolve, 700));
      await evaluate("(()=>{const s=document.createElement('script');s.textContent=" + JSON.stringify(axeSource) + ";document.documentElement.appendChild(s);return true})()");
      const result = await evaluate(
        "axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22a','wcag22aa']}}).then(r=>({url:location.href,title:document.title,violations:r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,description:v.description,node_count:v.nodes.length,nodes:v.nodes.slice(0,10).map(n=>({target:n.target,summary:(n.failureSummary||'').slice(0,260),html:(n.html||'').slice(0,1200)}))})),passes:r.passes.length,incomplete:r.incomplete.length}))",
        true
      );
      results.push({ route, result: "SCANNED", ...result });
      console.log(route + " violations=" + result.violations.length + " passes=" + result.passes);
    } catch (error) {
      results.push({ route, result: "SCAN_ERROR", error: String(error) });
      console.log(route + " SCAN_ERROR " + String(error));
    }
  }
} finally {
  try { await send("Page.close"); } catch {}
  ws.close();
}

const violations = results.flatMap(item => item.violations || []);
const summary = {
  tested_at: new Date().toISOString(),
  base_url: baseUrl,
  inventory_commit: inventory.commit,
  inventory_working_tree: inventory.working_tree,
  build_commit: buildCommit,
  build_commit_matches_inventory: buildCommit === inventory.commit,
  axe_core: JSON.parse(fs.readFileSync(require.resolve("axe-core/package.json"), "utf8")).version,
  standard: "WCAG 2.2 A/AA automated rules",
  routes_requested: routes.length,
  routes_scanned: results.filter(item => item.result === "SCANNED").length,
  scan_errors: results.filter(item => item.result === "SCAN_ERROR").length,
  total_violation_instances: violations.reduce((sum, item) => sum + item.node_count, 0),
  unique_violation_rules: [...new Set(violations.map(item => item.id))],
  route_results: results,
  limitations: [
    "Automated axe results are not a complete WCAG conformance audit.",
    "Keyboard-only, screen-reader, zoom/reflow, cognitive and manual interaction checks remain required.",
    "Protected routes may render redirects or access states when no authenticated session is supplied.",
    "Findings must be triaged for context and severity before being treated as defects."
  ]
};
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2) + "\n");
console.log("KALAM ACCESSIBILITY SMOKE");
console.log(JSON.stringify({
  routes_scanned: summary.routes_scanned,
  scan_errors: summary.scan_errors,
  violation_instances: summary.total_violation_instances,
  unique_rules: summary.unique_violation_rules,
  output: path.relative(root, outputPath)
}, null, 2));
if (summary.scan_errors > 0 || !summary.build_commit_matches_inventory) process.exitCode = 1;
