import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const baseUrl = process.argv[2] || process.env.KALAM_BASE_URL || "http://127.0.0.1:3000";
const inventoryPath = path.join(root, "qa", "generated", "kalam-brand-surface-inventory.json");
const outputPath = path.join(root, "qa", "generated", "kalam-brand-route-smoke.json");
const timeoutMs = Number(process.env.KALAM_ROUTE_SMOKE_TIMEOUT_MS || 15000);
const concurrency = 8;

if (!fs.existsSync(inventoryPath)) {
  console.error("Missing generated surface inventory. Run node qa/brand-surface-inventory.mjs first.");
  process.exit(2);
}

const inventory = JSON.parse(fs.readFileSync(inventoryPath, "utf8"));
const routes = [...new Set(inventory.page_metadata.map(item => item.route))];
const paths = routes.map(route =>
  route.replace(/:id/g, "audit-sample").replace(/:tenant/g, "demo").replace(/:code/g, "audit-sample")
);

async function check(pathname) {
  try {
    const response = await fetch(new URL(pathname, baseUrl), {
      redirect: "manual",
      signal: AbortSignal.timeout(timeoutMs)
    });
    return {
      route: pathname,
      status: response.status,
      location: response.headers.get("location"),
      result: response.status >= 500 ? "SERVER_ERROR"
        : response.status >= 400 ? "CLIENT_RESPONSE_REVIEW"
        : response.status >= 300 ? "REDIRECT"
        : "OK"
    };
  } catch (error) {
    return { route: pathname, status: null, result: "REQUEST_ERROR", error: String(error) };
  }
}

const results = [];
for (let index = 0; index < paths.length; index += concurrency) {
  results.push(...await Promise.all(paths.slice(index, index + concurrency).map(check)));
}

const statusDistribution = {};
for (const result of results) {
  const key = result.status === null ? "request_error" : String(result.status);
  statusDistribution[key] = (statusDistribution[key] || 0) + 1;
}
const serverErrors = results.filter(result => result.result === "SERVER_ERROR" || result.result === "REQUEST_ERROR");
const summary = {
  tested_at: new Date().toISOString(),
  base_url: baseUrl,
  inventory_commit: inventory.commit,
  inventory_working_tree: inventory.working_tree,
  routes_discovered: routes.length,
  routes_tested: results.length,
  status_distribution: statusDistribution,
  successful_responses: results.filter(result => result.result === "OK").length,
  redirects: results.filter(result => result.result === "REDIRECT").length,
  client_responses_requiring_review: results.filter(result => result.result === "CLIENT_RESPONSE_REVIEW").length,
  server_errors: serverErrors.length,
  result: serverErrors.length === 0 && results.length === routes.length ? "PASS" : "FAIL",
  limitations: [
    "HTTP smoke only; does not verify authenticated business workflows or data correctness.",
    "Dynamic identifiers use a non-production sample value.",
    "A 3xx response is recorded, not assumed to be a defect.",
    "Visual, responsive and assistive-technology verification remains separate."
  ],
  routes: results
};

fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2) + "\n");
console.log("KALAM ROUTE SMOKE " + summary.result);
console.log(JSON.stringify({
  routes_tested: summary.routes_tested,
  status_distribution: summary.status_distribution,
  server_errors: summary.server_errors,
  output: path.relative(root, outputPath)
}, null, 2));
if (summary.result !== "PASS") process.exit(1);
