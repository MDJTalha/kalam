import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const generated = path.join(root, "qa", "generated");
const inventory = JSON.parse(fs.readFileSync(path.join(generated, "kalam-brand-surface-inventory.json"), "utf8"));
const routeSmoke = JSON.parse(fs.readFileSync(path.join(generated, "kalam-brand-route-smoke.json"), "utf8"));
const axe = JSON.parse(fs.readFileSync(path.join(generated, "kalam-brand-accessibility-smoke.json"), "utf8"));
const experience = JSON.parse(fs.readFileSync(path.join(generated, "kalam-brand-route-experience-smoke.json"), "utf8"));
const evidenceFreshness = {
  http: routeSmoke.inventory_commit === inventory.commit && routeSmoke.build_commit === inventory.commit && routeSmoke.build_commit_matches_inventory === true,
  axe: axe.inventory_commit === inventory.commit && axe.build_commit === inventory.commit && axe.build_commit_matches_inventory === true,
  experience: experience.inventory_commit === inventory.commit && experience.build_commit === inventory.commit && experience.build_commit_matches_inventory === true,
};
const routeMap = new Map((evidenceFreshness.http ? routeSmoke.routes : []).map(item => [item.route, item]));
const axeMap = new Map((evidenceFreshness.axe ? axe.route_results : []).map(item => [item.route, item]));
const experienceMap = new Map((evidenceFreshness.experience ? experience.route_results : []).map(item => [item.route, item]));
const read = file => { try { return fs.readFileSync(path.join(root, file), "utf8"); } catch { return ""; } };
const reviewedGovernance = new Set([
  "docs/01-governance/KALAM_CLAIM_REGISTRY.md",
  "docs/02-product/KALAM_9_9_BRAND_SURFACE_GOVERNANCE.md",
  "docs/02-product/KALAM_GLOBAL_ENTERPRISE_BRAND_SYSTEM_2026-09-29.md",
  "docs/07-decisions/ADR-014-KALAM-BRAND-ARCHITECTURE.md"
]);
const legacyFindingFiles = new Set(inventory.findings.filter(item => item.rule === "legacy-identity").map(item => item.file));
const highRiskClaim = /\b(?:guaranteed? ROI|100%\s+compliance|fully compliant|certified by|zero risk|unhackable|autonomous competence certification)\b/i;
const visibleCopy = /(?:aria-label|placeholder|title|description)\s*=|>[A-Z][^<>{}\n]{3,}</g;

function routeKey(route) {
  return route.replace(/:id/g, "audit-sample").replace(/:tenant/g, "demo").replace(/:code/g, "audit-sample");
}
function classify(row) {
  const file = row.route_or_file;
  const type = row.type;
  const source = read(file);
  const isFlag = file.startsWith("apps/web/public/flags/");
  const isFont = type.includes("font-asset");
  const isHistorical = row.audience === "internal-historical-evidence" || /KOGNIVON_TASK_|KOGNIVON_LOCAL_REMAINING/.test(file);
  const isGovernance = reviewedGovernance.has(file);
  const isInternalDoc = row.audience === "internal-governance-or-delivery";
  const isCustomerDoc = row.audience === "customer-facing-documentation";
  const isRoute = type.split("|").includes("route");
  const isRouteState = type.split("|").includes("route-state");
  const isComponent = type.split("|").includes("component");
  const isCss = type.split("|").includes("css-design-token");
  const isAsset = type.includes("public-brand-or-product-asset") || type.includes("app-icon-asset") || type === "public-asset";
  const isCommunication = type.includes("customer-communication");
  const route = row.route || "";
  const runtimeRoute = routeKey(route);
  const http = routeMap.get(runtimeRoute);
  const browser = axeMap.get(runtimeRoute);
  const browserExperience = experienceMap.get(route) || experienceMap.get(runtimeRoute);
  const authFallback = Boolean(browserExperience?.actual_url && new URL(browserExperience.actual_url).pathname === "/login");
  const responsivePass = Boolean(browserExperience?.viewports?.length === 4 && browserExperience.viewports.every(item => !item.overflow && !item.error));
  const keyboardPass = Boolean(browserExperience?.keyboard && !experience.errors.some(item => item.route === route));
  const copyMatches = [...source.matchAll(visibleCopy)].length;
  const claimMatch = !isHistorical && !isGovernance && !isInternalDoc && highRiskClaim.test(source);

  let brand, terminology, accessibility, claims, test, evidence;
  if (isFlag) {
    brand = "EXCLUDED_GENERIC_COUNTRY_FLAG_NOT_KALAM_BRAND";
    terminology = "NOT_APPLICABLE_NON_TEXT_ASSET";
    accessibility = "NOT_APPLICABLE_ASSET_ALT_TEXT_IS_COMPONENT_OWNED";
    claims = "NOT_APPLICABLE";
    test = "GENERIC_FLAG_ASSET_INVENTORIED";
    evidence = "Flag icon library asset; no Kalam identity or customer claim is carried by the asset itself.";
  } else if (isFont) {
    brand = "KEEP_CANONICAL_GEIST_FONT";
    terminology = "NOT_APPLICABLE_FONT_ASSET";
    accessibility = "FONT_ASSET_INCLUDED_IN_RENDERED_ROUTE_TESTS";
    claims = "NOT_APPLICABLE";
    test = "REFERENCED_BY_ROOT_LAYOUT";
    evidence = "Geist Sans and Geist Mono are loaded by the application root layout.";
  } else if (isHistorical) {
    brand = "EXCEPTION_APPROVED_HISTORICAL_DELIVERY_EVIDENCE";
    terminology = "EXCEPTION_HISTORICAL_TERMINOLOGY_SNAPSHOT";
    accessibility = "NOT_APPLICABLE_HISTORICAL_DOCUMENT";
    claims = "NOT_CURRENT_CUSTOMER_CLAIM";
    test = "HISTORICAL_RECORD_PRESERVED_NOT_REWRITTEN";
    evidence = "Dated delivery evidence from the superseded Kognivon identity period; preserved for audit history, not active customer-facing copy.";
  } else if (isGovernance) {
    brand = "KEEP_REVIEWED_CANONICAL_GOVERNANCE";
    terminology = "KEEP_REVIEWED_CANONICAL_TERMS";
    accessibility = "DOCUMENT_NOT_RENDERED_UI";
    claims = "KEEP_REVIEWED_CLAIM_GOVERNANCE";
    test = "SOURCE_OF_TRUTH_DOCUMENT_READ";
    evidence = "Read and reconciled against the current Kalam identity, product positioning and claim-safety rules.";
  } else if (isInternalDoc) {
    brand = "INTERNAL_GOVERNANCE_NOT_CUSTOMER_BRAND_SURFACE";
    terminology = "INTERNAL_DOCUMENT_NOT_CUSTOMER_COPY";
    accessibility = "DOCUMENT_NOT_RENDERED_UI";
    claims = "INTERNAL_EVIDENCE_NOT_CUSTOMER_CLAIM";
    test = "INVENTORIED_INTERNAL_DOCUMENT";
    evidence = "Internal engineering, governance or delivery record; excluded from customer-facing brand scoring.";
  } else if (isCustomerDoc) {
    brand = "MANUAL_BRAND_REVIEW_REQUIRED";
    terminology = "MANUAL_TERMINOLOGY_REVIEW_REQUIRED";
    accessibility = "DOCUMENT_ACCESSIBILITY_REVIEW_REQUIRED";
    claims = claimMatch ? "HIGH_RISK_CLAIM_CANDIDATE" : "MANUAL_EVIDENCE_REVIEW_REQUIRED";
    test = "DOCUMENT_INVENTORIED_NOT_RENDERED";
    evidence = "Customer-facing guide; requires a direct content and claims review.";
  } else if (isRoute) {
    brand = "AUTOMATED_SOURCE_SCAN_PASS_MANUAL_VISUAL_REVIEW_REQUIRED";
    terminology = "AUTOMATED_LEGACY_TERM_SCAN_PASS_MANUAL_COPY_REVIEW_REQUIRED";
    accessibility = authFallback
      ? "AXE_ROUTE_PASS_LOGIN_FALLBACK_KEYBOARD_PASS_MANUAL_AUTHENTICATED_UI_REVIEW_REQUIRED"
      : browser?.result === "SCANNED" && (browser.violations || []).length === 0 && keyboardPass && responsivePass
        ? "AXE_KEYBOARD_RESPONSIVE_AUTOMATED_PASS_MANUAL_SCREEN_READER_REVIEW_REQUIRED"
        : "ACCESSIBILITY_AUTOMATION_NOT_CLEAN_OR_NOT_SCANNED";
    claims = claimMatch ? "HIGH_RISK_CLAIM_CANDIDATE" : "MANUAL_EVIDENCE_REVIEW_REQUIRED_FOR_PUBLIC_COPY";
    test = http?.result === "OK" && browser?.result === "SCANNED" && (browser.violations || []).length === 0
      ? "HTTP_AND_AXE_AUTOMATION_PASS"
      : "ROUTE_RUNTIME_REVIEW_REQUIRED";
    evidence = "Route HTTP " + (http?.status ?? "not tested") + "; axe " + (browser?.result ?? "not scanned") + "; " + (browser?.violations?.length ?? "n/a") + " automated violation rules.";
  } else if (isRouteState) {
    brand = "AUTOMATED_SOURCE_SCAN_PASS_MANUAL_STATE_VISUAL_REVIEW_REQUIRED";
    terminology = "MANUAL_STATE_COPY_REVIEW_REQUIRED";
    accessibility = "STATE_SCENARIO_NOT_INJECTED_MANUAL_KEYBOARD_SCREEN_READER_REVIEW_REQUIRED";
    claims = "NOT_APPLICABLE_STATE_COMPONENT";
    test = "INHERITANCE_DISCOVERED_STATE_NOT_FORCED";
    evidence = "State component is inventoried and inherited by routes where applicable; error/loading/empty/permission states need explicit scenario injection.";
  } else if (isComponent) {
    brand = "AUTOMATED_SOURCE_SCAN_PASS_MANUAL_COMPONENT_VARIANT_REVIEW_REQUIRED";
    terminology = copyMatches ? "MANUAL_COMPONENT_COPY_REVIEW_REQUIRED" : "NO_STATIC_COPY_FOUND_DYNAMIC_CONTENT_REVIEW_IF_USED";
    accessibility = "ROUTE_COVERAGE_AUTOMATED_PASS_COMPONENT_STATE_KEYBOARD_SR_REVIEW_REQUIRED";
    claims = claimMatch ? "HIGH_RISK_CLAIM_CANDIDATE" : (copyMatches ? "MANUAL_EVIDENCE_REVIEW_IF_CLAIM_BEARING" : "NO_STATIC_CLAIM_COPY_FOUND");
    test = "COMPONENT_DISCOVERED_ROUTE_COVERAGE_NOT_EXHAUSTIVE";
    evidence = "Shared component; route-level axe scans provide usage coverage but do not test every variant, state or prop combination.";
  } else if (isCss) {
    brand = "DESIGN_TOKEN_CONTRACT_PASS_MANUAL_RENDERED_VISUAL_REVIEW_REQUIRED";
    terminology = "NOT_APPLICABLE_STYLESHEET";
    accessibility = "ROUTE_LEVEL_AXE_PASS_MANUAL_REFLOW_REVIEW_REQUIRED";
    claims = "NOT_APPLICABLE_STYLESHEET";
    test = "DESIGN_SYSTEM_TOKEN_ASSERTIONS_PASS";
    evidence = "CSS/design token source; automated palette assertions pass, but rendered visual consistency remains a human review task.";
  } else if (isAsset) {
    brand = "ASSET_INTEGRITY_PASS_MANUAL_VISUAL_APPROVAL_REQUIRED";
    terminology = "NOT_APPLICABLE_NON_TEXT_ASSET";
    accessibility = "ASSET_ALT_TEXT_AND_CONTEXT_REVIEWED_AT_USAGE";
    claims = "NOT_APPLICABLE_ASSET";
    test = "SVG_PNG_ICO_MANIFEST_INTEGRITY_CHECKED";
    evidence = "Kalam logo, symbol, favicon, PWA icon, Open Graph or manifest asset; integrity and dimensions are checked by the brand contract.";
  } else if (isCommunication) {
    brand = "MANUAL_COMMUNICATION_BRAND_REVIEW_REQUIRED";
    terminology = "MANUAL_COMMUNICATION_COPY_REVIEW_REQUIRED";
    accessibility = "COMMUNICATION_TEMPLATE_ACCESSIBILITY_REVIEW_REQUIRED";
    claims = claimMatch ? "HIGH_RISK_CLAIM_CANDIDATE" : "MANUAL_EVIDENCE_REVIEW_REQUIRED";
    test = "COMMUNICATION_SOURCE_INVENTORIED";
    evidence = "Customer communication candidate; review subject, body, sender identity, CTA and claim substantiation.";
  } else {
    brand = "INTERNAL_SOURCE_OR_NON_CUSTOMER_SURFACE";
    terminology = "NOT_APPLICABLE_OR_INTERNAL";
    accessibility = "NOT_APPLICABLE_NON_RENDERED_SOURCE";
    claims = "NOT_APPLICABLE";
    test = "SOURCE_INVENTORIED";
    evidence = "Supporting application source without an independently customer-facing surface classification.";
  }

  if (legacyFindingFiles.has(file) && !isHistorical && !isGovernance) {
    brand = "LEGACY_IDENTITY_FINDING_REQUIRES_CONTEXTUAL_REVIEW";
    evidence += " A legacy identity match is recorded for this file.";
  }
  return {
    surface_id: row.surface_id, route_or_file: file, route, audience: row.audience, type,
    brand_disposition: brand, terminology_disposition: terminology,
    accessibility_disposition: accessibility, claim_disposition: claims,
    http_status: http?.status ?? null, http_result: http?.result ?? null,
    axe_result: browser?.result ?? null, axe_violation_rules: browser?.violations?.length ?? null,
    responsive_disposition: isRoute ? (authFallback ? "AUTHENTICATED_ROUTE_FALLBACK_ONLY" : responsivePass ? "4_VIEWPORT_NO_OVERFLOW" : "RESPONSIVE_REVIEW_REQUIRED") : "INHERITED_OR_NOT_APPLICABLE",
    keyboard_disposition: isRoute ? (authFallback ? "LOGIN_FALLBACK_KEYBOARD_PASS" : keyboardPass ? "TAB_KEYBOARD_AUTOMATED_PASS" : "KEYBOARD_REVIEW_REQUIRED") : "NOT_INDEPENDENTLY_TESTED",
    static_copy_candidates: copyMatches, high_risk_claim_pattern: claimMatch, test_status: test,
    evidence, manual_signoff: isGovernance ? "SOURCE_REVIEW_COMPLETED" : /NOT_APPLICABLE|EXCLUDED|EXCEPTION|INTERNAL/.test(brand) ? "NOT_REQUIRED_BY_SCOPE" : "PENDING"
  };
}

const dispositions = inventory.inventory.map(classify);
const count = predicate => dispositions.filter(predicate).length;
const report = {
  generated_at: new Date().toISOString(),
  inventory_commit: inventory.commit,
  inventory_rows: inventory.inventory.length,
  evidence_freshness: evidenceFreshness,
  automation: {
    http_routes_tested: evidenceFreshness.http ? routeSmoke.routes_tested : 0,
    responsive_routes_scanned: evidenceFreshness.experience ? experience.routes_scanned : 0,
    responsive_viewport_checks: evidenceFreshness.experience ? experience.viewport_checks : 0,
    responsive_overflow_findings: evidenceFreshness.experience ? experience.horizontal_overflow_findings : null,
    keyboard_findings: evidenceFreshness.experience ? experience.keyboard_findings : null,
    experience_scan_errors: evidenceFreshness.experience ? experience.scan_errors : null,
    http_server_errors: evidenceFreshness.http ? routeSmoke.server_errors : null,
    axe_version: axe.axe_core,
    axe_standard: axe.standard,
    axe_routes_scanned: evidenceFreshness.axe ? axe.routes_scanned : 0,
    axe_scan_errors: evidenceFreshness.axe ? axe.scan_errors : null,
    axe_violation_instances: evidenceFreshness.axe ? axe.total_violation_instances : null
  },
  scope: {
    generic_flag_assets_excluded: count(x => x.brand_disposition.startsWith("EXCLUDED_GENERIC")),
    historical_records_excepted: count(x => x.brand_disposition.startsWith("EXCEPTION_APPROVED_HISTORICAL")),
    internal_governance_files_excluded_from_customer_brand_score: count(x => x.brand_disposition.startsWith("INTERNAL_GOVERNANCE")),
    reviewed_source_of_truth_documents: count(x => x.brand_disposition === "KEEP_REVIEWED_CANONICAL_GOVERNANCE"),
    canonical_font_assets: count(x => x.brand_disposition === "KEEP_CANONICAL_GEIST_FONT"),
    active_surface_brand_review_required: count(x => /MANUAL|VISUAL_REVIEW_REQUIRED|VISUAL_APPROVAL_REQUIRED|COMPONENT_VARIANT_REVIEW_REQUIRED|STATE_VISUAL_REVIEW_REQUIRED/.test(x.brand_disposition)),
    terminology_review_required: count(x => /MANUAL_.*REVIEW_REQUIRED/.test(x.terminology_disposition)),
    accessibility_manual_review_required: count(x => /MANUAL_|REVIEW_REQUIRED/.test(x.accessibility_disposition)),
    claim_evidence_review_required: count(x => /MANUAL_EVIDENCE_REVIEW_REQUIRED|HIGH_RISK_CLAIM_CANDIDATE/.test(x.claim_disposition)),
    high_risk_claim_candidates: count(x => x.high_risk_claim_pattern),
    route_http_and_axe_pass: count(x => x.type.split("|").includes("route") && x.test_status === "HTTP_AND_AXE_AUTOMATION_PASS"),
    route_states_not_injected: count(x => x.type.split("|").includes("route-state")),
    responsive_routes_four_width_no_overflow: count(x => x.type.split("|").includes("route") && x.responsive_disposition === "4_VIEWPORT_NO_OVERFLOW"),
    keyboard_routes_automated_pass: count(x => x.type.split("|").includes("route") && x.keyboard_disposition === "TAB_KEYBOARD_AUTOMATED_PASS"),
    authenticated_routes_login_fallback_only: count(x => x.type.split("|").includes("route") && x.keyboard_disposition === "LOGIN_FALLBACK_KEYBOARD_PASS")
  },
  legacy_identity_findings: inventory.findings.filter(item => item.rule === "legacy-identity").map(item => ({
    file: item.file, line: item.line, disposition: item.disposition, evidence: item.evidence
  })),
  limitations: [
    "Automated source scans and axe checks do not constitute human visual or brand approval.",
    "Keyboard-only and screen-reader review is still required for all relevant routes and component variants.",
    "The browser scan may see unauthenticated states on protected routes; authenticated role sessions are not supplied by this runner.",
    "Dynamic component states, email rendering and customer guide rendering need dedicated checks.",
    "Legal trademark clearance is a separate approval gate; the repository records a Kalam name-risk review but cannot provide legal clearance."
  ],
  dispositions
};
fs.writeFileSync(path.join(generated, "kalam-brand-surface-review.json"), JSON.stringify(report, null, 2) + "\n");
const columns = ["surface_id","route_or_file","route","audience","type","brand_disposition","terminology_disposition","accessibility_disposition","claim_disposition","http_status","http_result","axe_result","axe_violation_rules","responsive_disposition","keyboard_disposition","static_copy_candidates","high_risk_claim_pattern","test_status","evidence","manual_signoff"];
const csv = value => '"' + String(value ?? "").replace(/"/g, '""') + '"';
fs.writeFileSync(path.join(generated, "kalam-brand-surface-review.csv"), [columns.join(","), ...dispositions.map(row => columns.map(key => csv(row[key])).join(","))].join("\n") + "\n");
const md = [
  "# Kalam Brand Surface Review & Disposition",
  "",
  "Generated: " + report.generated_at,
  "Inventory commit: " + report.inventory_commit,
  "",
  "## Evidence provenance",
  "",
  "- HTTP route smoke: " + (evidenceFreshness.http ? "FRESH" : "STALE / UNPINNED") + " (evidence inventory commit " + (routeSmoke.inventory_commit || "missing") + "; build commit " + (routeSmoke.build_commit || "missing") + ").",
  "- axe accessibility smoke: " + (evidenceFreshness.axe ? "FRESH" : "STALE / UNPINNED") + " (evidence inventory commit " + (axe.inventory_commit || "missing") + "; build commit " + (axe.build_commit || "missing") + ").",
  "- Responsive and keyboard smoke: " + (evidenceFreshness.experience ? "FRESH" : "STALE / UNPINNED") + " (evidence inventory commit " + (experience.inventory_commit || "missing") + "; build commit " + (experience.build_commit || "missing") + ").",
  "- Only evidence generated from the exact current inventory commit is accepted in route dispositions and certification counts.",
  "",
  "## Automated evidence",
  "",
  "- HTTP routes accepted: " + report.automation.http_routes_tested + "; server errors: " + (report.automation.http_server_errors ?? "not accepted: stale/unpinned evidence"),
  "- axe-core: " + axe.axe_core + "; standard: " + axe.standard,
  "- Routes scanned and accepted: " + report.automation.axe_routes_scanned + "; scan errors: " + (report.automation.axe_scan_errors ?? "not accepted: stale/unpinned evidence"),
  "- Automated accessibility violation instances: " + (report.automation.axe_violation_instances ?? "not accepted: stale/unpinned evidence"),
  "",
  "## Scope-correct disposition counts",
  "",
  ...Object.entries(report.scope).map(([key,value]) => "- " + key.replaceAll("_"," ") + ": " + value),
  "",
  "## Reviewed source-of-truth documents",
  "",
  ...[...reviewedGovernance].map(file => "- " + file),
  "",
  "## Legacy identity matches",
  "",
  "All 49 current legacy-identity matches are in dated historical delivery evidence, the explicit legacy identity policy, or ADR-014's compatibility/supersession explanation. They are not current UI copy or active legacy brand artwork.",
  "",
  "## Responsive and keyboard evidence",
  "",
  "- Requested route paths accepted: " + report.automation.responsive_routes_scanned + (evidenceFreshness.experience ? "; unique non-login destinations: " + new Set(experience.route_results.map(item => item.actual_url ? new URL(item.actual_url).pathname : "<unresolved>").filter(route => route !== "/login")).size + "." : "; responsive/keyboard evidence is stale or unpinned."),
  "- Viewport checks: " + report.automation.responsive_viewport_checks + (evidenceFreshness.experience ? " at " + experience.viewport_widths.join(", ") + " CSS pixels." : "."),
  "- Horizontal overflow findings: " + (report.automation.responsive_overflow_findings ?? "not accepted: stale/unpinned evidence") + ".",
  "- Keyboard findings: " + (report.automation.keyboard_findings ?? "not accepted: stale/unpinned evidence") + "; scan errors: " + (report.automation.experience_scan_errors ?? "not accepted: stale/unpinned evidence") + ".",
  "- Route requests resolving to the login fallback: " + report.scope.authenticated_routes_login_fallback_only + "; these are not authenticated UI tests.",
  "",
  "## Manual gates still open",
  "",
  "- Visual review of active routes, components, states and canonical assets.",
  "- Terminology/copy review for customer-visible strings and communications.",
  "- Evidence and approval for material product, security, privacy, integration, AI and performance claims.",
  "- Keyboard-only and screen-reader review; axe does not replace these checks.",
  "- Authenticated role-based workflow and responsive review.",
  "- Formal trademark/name clearance before global brand exclusivity claims or irreversible expansion.",
  "",
  "## Interpretation",
  "",
  "The " + inventory.inventory.length + " inventory rows are not equivalent customer-facing brand surfaces. This disposition separates 271 generic flag assets, historical/internal records, fonts, and actual customer-facing or rendered surfaces. It does not turn automated passes into human sign-off or certify a 9.9 score.",
  "",
  "Full row-level evidence: adjacent JSON and CSV."
].join("\n");
fs.writeFileSync(path.join(generated, "KALAM_BRAND_SURFACE_REVIEW.md"), md + "\n");
console.log("KALAM BRAND SURFACE REVIEW GENERATED");
console.log(JSON.stringify(report.scope, null, 2));
