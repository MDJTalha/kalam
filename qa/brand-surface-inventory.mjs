import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const web = path.join(root, "apps", "web");
const src = path.join(web, "src");
const app = path.join(src, "app");
const components = path.join(src, "components");
const publicDir = path.join(web, "public");
const docs = path.join(root, "docs");
const qa = path.join(root, "qa");
const outputDir = path.join(qa, "generated");

const exists = p => fs.existsSync(p);
const rel = p => path.relative(root, p).split(path.sep).join("/");
const walk = dir => {
  if (!exists(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(file) : [file];
  });
};
const read = file => {
  try { return fs.readFileSync(file, "utf8"); } catch { return ""; }
};
const unique = values => [...new Set(values)].sort();
const extensions = /\.(?:tsx?|jsx?|css|scss|svg|json|md|mdx|html|txt|ya?ml|webmanifest)$/i;
const allFiles = unique([
  ...walk(src), ...walk(publicDir), ...walk(docs),
  ...walk(path.join(root, "emails")), ...walk(path.join(root, "notifications")),
  ...walk(path.join(web, "emails")), ...walk(path.join(web, "notifications"))
].filter(file => extensions.test(file)));

const routeFiles = allFiles.filter(file => file.startsWith(app + path.sep) && /(?:^|[\\/])page\.(?:tsx?|jsx?)$/i.test(file));
const routeStateFiles = allFiles.filter(file => file.startsWith(app + path.sep) && /(?:^|[\\/])(?:loading|error|not-found|global-error)\.(?:tsx?|jsx?)$/i.test(file));
const componentFiles = allFiles.filter(file => file.startsWith(components + path.sep));
const cssFiles = allFiles.filter(file => /\.(?:css|scss)$/i.test(file));
const assetFiles = allFiles.filter(file => file.startsWith(publicDir + path.sep));
const metadataFiles = allFiles.filter(file => /(?:metadata|manifest|sitemap|robots|opengraph|twitter|schema|structured)/i.test(path.basename(file)));
const communicationFiles = allFiles.filter(file => /(?:email|notification|template|message|marketing|transactional|communication)/i.test(file));
const customerDocs = allFiles.filter(file => file.startsWith(docs + path.sep) && /\.(?:md|mdx|html|txt)$/i.test(file));

const routePath = file => {
  let value = path.relative(app, path.dirname(file)).split(path.sep).join("/");
  value = value === "." ? "/" : "/" + value;
  value = value.replace(/\([^/]+\)\/?/g, "").replace(/\/+/g, "/").replace(/\[([^\]]+)\]/g, ":$1");
  return value;
};
const statesByDir = new Map();
for (const file of routeStateFiles) {
  const dir = path.dirname(file);
  const state = path.basename(file).replace(/\.(?:tsx?|jsx?)$/i, "");
  const list = statesByDir.get(dir) || [];
  list.push(state);
  statesByDir.set(dir, list);
}

const inventory = [];
function add(file, type, extra = {}) {
  const relative = rel(file);
  const audience = relative.includes("/dashboard/") ? "authenticated-user"
    : relative.startsWith("docs/") ? "internal-or-customer-documentation"
    : relative.includes("/public/") ? "public" : "public-or-shared";
  inventory.push({
    surface_id: relative.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase(),
    route_or_file: relative, route: extra.route || "", audience, type,
    states: extra.states || "not-applicable",
    brand_status: "NEEDS_MANUAL_REVIEW",
    terminology_status: "NEEDS_MANUAL_REVIEW",
    accessibility_status: type === "route" || type === "component" ? "NEEDS_VERIFICATION" : "REVIEW_IF_APPLICABLE",
    claim_status: "NEEDS_CLAIM_REVIEW",
    test_status: "NO_SURFACE_SPECIFIC_EVIDENCE_RECORDED",
    evidence: "Inventory discovery only; automated detection is not certification.",
    owner: "UNASSIGNED"
  });
}
for (const file of routeFiles) add(file, "route", {route:routePath(file),states:(statesByDir.get(path.dirname(file)) || ["default"]).join(",")});
for (const file of routeStateFiles) add(file, "route-state", {route:routePath(file),states:path.basename(file).replace(/\.(?:tsx?|jsx?)$/i,"")});
for (const file of componentFiles) add(file, "component");
for (const file of cssFiles) add(file, "css-design-token");
for (const file of assetFiles) add(file, "public-brand-or-product-asset");
for (const file of metadataFiles) add(file, "metadata-structured-data");
for (const file of communicationFiles) add(file, "customer-communication");
for (const file of customerDocs) add(file, "customer-facing-or-governance-document");
for (const file of allFiles.filter(f => f.startsWith(src + path.sep) && !inventory.some(row => row.route_or_file === rel(f)))) {
  if (/layout\.(?:tsx?|jsx?)$/i.test(file)) add(file, "layout-shell");
  else if (/\.(?:tsx?|jsx?)$/i.test(file)) add(file, "application-source");
}

const patterns = [
  ["legacy-identity", /Kognivon|AIVON Learning OS|Learning Intelligence/gi],
  ["obsolete-slogan", /Expect\s*<|Expect\s+Build\s+Assess\s+Prove\s+Know\s+Act/gi],
  ["legacy-color", /#(?:147AC5|63BDE8|092844)\b/gi],
  ["placeholder-language", /\b(?:coming soon|lorem ipsum|TODO: replace|placeholder text)\b/gi],
  ["unsupported-claim-candidate", /\b(?:guaranteed? ROI|100%\s+compliance|fully compliant|certified by|zero risk|unhackable|autonomous competence certification)\b/gi],
  ["brand-capitalization", /\bkalam\b/g]
];
const findings = [];
for (const file of allFiles.filter(f => f.startsWith(src + path.sep) || f.startsWith(publicDir + path.sep) || f.startsWith(docs + path.sep))) {
  const content = read(file);
  const lines = content.split(/\r?\n/);
  for (const [rule, regex] of patterns) {
    regex.lastIndex = 0;
    let match;
    while ((match = regex.exec(content)) !== null) {
      const line = content.slice(0, match.index).split("\n").length;
      findings.push({
        rule, file:rel(file), line, match:match[0],
        disposition:rule === "legacy-identity" ? "CLASSIFY_COMPATIBILITY_HISTORY_FIXTURE_OR_CUSTOMER_FACING"
          : rule === "brand-capitalization" ? "REVIEW_CONTEXT_NOT_AUTOMATIC_FAILURE" : "REVIEW_AND_RECORD_DISPOSITION",
        evidence:(lines[line - 1] || "").trim().slice(0,180)
      });
      if (match[0].length === 0) regex.lastIndex++;
    }
  }
}

const pageMetadata = routeFiles.map(file => {
  const text = read(file);
  const layout = path.join(path.dirname(file), "layout.tsx");
  const rootLayout = path.join(app, "layout.tsx");
  const pattern = /\bexport\s+(?:const|async\s+function)\s+metadata\b|\bexport\s+const\s+generateMetadata\b/;
  const own = pattern.test(text);
  const inherited = (exists(layout) && pattern.test(read(layout))) || (exists(rootLayout) && pattern.test(read(rootLayout)));
  return {route:routePath(file),file:rel(file),metadata:own ? "PAGE_LEVEL" : inherited ? "INHERITED_LAYOUT_POSSIBLE" : "NOT_DETECTED_STATIC_REVIEW_REQUIRED"};
});

let commit = "unknown";
try { commit = execFileSync("git", ["rev-parse","HEAD"], {encoding:"utf8"}).trim(); } catch {}
const summary = {
  generated_at:new Date().toISOString(), commit,
  counts:{
    discovery_files:allFiles.length,routes:routeFiles.length,route_state_files:routeStateFiles.length,
    components:componentFiles.length,css_design_files:cssFiles.length,public_assets:assetFiles.length,
    metadata_candidates:metadataFiles.length,communication_candidates:communicationFiles.length,
    customer_documentation_files:customerDocs.length,inventory_rows:inventory.length,automated_findings:findings.length
  },
  limitations:[
    "Discovery inventory is not a manual brand disposition.",
    "Regex findings require contextual classification; matches are not automatically defects.",
    "Static metadata detection cannot prove rendered metadata or inheritance correctness.",
    "Dead links/actions, interaction behavior, visual quality, responsive behavior, accessibility and claims require dedicated verification.",
    "No 9.9 score or 100% certification is inferred from this report."
  ],
  inventory,findings,page_metadata:pageMetadata
};

fs.mkdirSync(outputDir,{recursive:true});
fs.writeFileSync(path.join(outputDir,"kalam-brand-surface-inventory.json"),JSON.stringify(summary,null,2)+"\n");
const csvEscape = value => '"' + String(value ?? "").replace(/"/g,'""') + '"';
const columns = ["surface_id","route_or_file","route","audience","type","states","brand_status","terminology_status","accessibility_status","claim_status","test_status","evidence","owner"];
fs.writeFileSync(path.join(outputDir,"kalam-brand-surface-inventory.csv"),
  [columns.join(","),...inventory.map(row=>columns.map(key=>csvEscape(row[key])).join(","))].join("\n")+"\n");
const report = [
  "# Kalam Brand Surface Inventory","",
  "Generated: "+summary.generated_at,"Commit: "+summary.commit,"",
  "## Discovery counts","",
  ...Object.entries(summary.counts).map(([key,value])=>"- "+key+": "+value),
  "","## Metadata review","","| Route | Metadata detection | Source |","|---|---|---|",
  ...pageMetadata.map(row=>"| "+row.route+" | "+row.metadata+" | "+row.file+" |"),
  "","## Limitations","",...summary.limitations.map(item=>"- "+item),"",
  "Full row-level inventory and findings are in the adjacent JSON and CSV files.",""
].join("\n");
fs.writeFileSync(path.join(outputDir,"KALAM_BRAND_SURFACE_INVENTORY.md"),report);
console.log("KALAM BRAND SURFACE INVENTORY GENERATED");
console.log(JSON.stringify(summary.counts,null,2));
console.log("Output: "+path.relative(root,outputDir));
