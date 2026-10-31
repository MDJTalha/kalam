import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const webSrc = path.join(root, "apps", "web", "src");
const publicDir = path.join(root, "apps", "web", "public");

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const p = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(p) : [p];
  });
}

const files = [...walk(webSrc), ...walk(publicDir)].filter(p => /\.(tsx?|css|svg|json|md)$/i.test(p));
const violations = [];

for (const file of files) {
  const rel = path.relative(root, file).replaceAll(path.sep, "/");
  const content = fs.readFileSync(file, "utf8");

  if (/(?:Kognivon|AIVON Learning OS|Learning Intelligence)/i.test(content)) {
    const compatibility = rel === "apps/web/src/components/kognivon-brand.tsx";
    if (!compatibility) violations.push(`Legacy customer-facing identity in ${rel}`);
  }

  if (/(?:Expect\\s*<|Expect\\s+Build\\s+Assess\\s+Prove\\s+Know\\s+Act)/i.test(content)) {
    violations.push(`Competing capability-loop language in ${rel}`);
  }

  if (/(?:147AC5|63BDE8|092844)/i.test(content)) {
    violations.push(`Legacy brand color literal in ${rel}`);
  }
}

const brand = fs.readFileSync(path.join(webSrc, "components", "kalam-brand.tsx"), "utf8");
for (const token of ["#08243D", "#0878C9", "#3EA9DD", "Kalam home"]) {
  if (!brand.includes(token)) violations.push(`Canonical brand component missing expected token: ${token}`);
}

const design = fs.readFileSync(path.join(webSrc, "app", "design-system.css"), "utf8");
for (const token of ["--kalam-navy", "--kalam-blue", "--kalam-tech", "--kalam-ice", "--kalam-gold", "prefers-reduced-motion"]) {
  if (!design.includes(token)) violations.push(`Design system missing ${token}`);
}

const homepage = fs.readFileSync(path.join(webSrc, "app", "page.tsx"), "utf8");
for (const phrase of ["Build Capability.", "Prove Readiness.", "Expectation", "Capability", "Evidence", "Action", "Readiness"]) {
  if (!homepage.includes(phrase)) violations.push(`Homepage missing canonical brand narrative token: ${phrase}`);
}

if (violations.length) {
  console.error("KALAM BRAND CONTRACT: FAIL");
  for (const v of violations) console.error(" - " + v);
  process.exit(1);
}

console.log("KALAM BRAND CONTRACT: PASS");
console.log(`Scanned ${files.length} web/public source and asset files.`);
