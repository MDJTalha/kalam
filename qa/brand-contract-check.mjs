import fs from "node:fs";
import path from "node:path";
const root = process.cwd();

function pngDimensions(buffer) {
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  if (buffer.length < 24 || !buffer.subarray(0, 8).equals(signature) || buffer.toString("ascii", 12, 16) !== "IHDR") {
    throw new Error("Invalid PNG signature or IHDR chunk");
  }
  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);
  if (!width || !height) throw new Error("PNG dimensions must be non-zero");
  return { width, height };
}
const webSrc = path.join(root, "apps", "web", "src");
const publicDir = path.join(root, "apps", "web", "public");

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const p = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(p) : [p];
  });
}

const files = [...walk(webSrc), ...walk(publicDir)].filter(p => /\.(tsx?|css|svg|json|md|webmanifest)$/i.test(p));
const violations = [];

for (const file of files) {
  const rel = path.relative(root, file).replaceAll(path.sep, "/");
  const content = fs.readFileSync(file, "utf8");

  if (/(?:Kognivon|AIVON Learning OS|Learning Intelligence)/i.test(content)) {
    const compatibility = rel === "apps/web/src/components/kognivon-brand.tsx";
    if (!compatibility) violations.push(`Legacy customer-facing identity in ${rel}`);
  }

  if (/(?:Expect\s*<|Expect\s+Build\s+Assess\s+Prove\s+Know\s+Act)/i.test(content)) {
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

function luminance(hex) {
  const rgb = hex.replace("#", "").match(/.{2}/g).map(v => parseInt(v, 16) / 255);
  const linear = rgb.map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}
function contrastRatio(foreground, background) {
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}
const contrastChecks = [
  ["Kalam Navy on white", "#08243D", "#FFFFFF"],
  ["Kalam Blue on white", "#0878C9", "#FFFFFF"],
  ["Kalam Blue hover on Ice", "#0669AE", "#EAF5FC"],
  ["Muted text on white", "#63738A", "#FFFFFF"],
  ["Muted text on Ice", "#52657A", "#EAF5FC"]
];
for (const [label, foreground, background] of contrastChecks) {
  const ratio = contrastRatio(foreground, background);
  console.log("CONTRAST " + label + ": " + ratio.toFixed(2) + ":1");
  if (ratio < 4.5) violations.push(label + " contrast is below WCAG AA normal-text threshold (" + ratio.toFixed(2) + ":1)");
}
if (!design.includes("--kalam-ice-ink: #52657A")) violations.push("Design system missing AA-safe Kalam Ice text token");

for (const stateFile of ["loading.tsx", "error.tsx", "not-found.tsx", "global-error.tsx"]) {
  if (!fs.existsSync(path.join(webSrc, "app", stateFile))) violations.push("Root route-state experience missing: " + stateFile);
}

const homepage = fs.readFileSync(path.join(webSrc, "app", "page.tsx"), "utf8");
for (const phrase of ["Build Capability.", "Prove Readiness.", "Expectation", "Capability", "Evidence", "Action", "Readiness"]) {
  if (!homepage.includes(phrase)) violations.push(`Homepage missing canonical brand narrative token: ${phrase}`);
}

const manifestPath = path.join(publicDir, "manifest.webmanifest");
if (fs.existsSync(manifestPath)) {
  const manifest = fs.readFileSync(manifestPath, "utf8");
  if (!/"theme_color"\s*:\s*"#08243D"/i.test(manifest)) {
    violations.push("PWA manifest theme_color must use Kalam Navy #08243D");
  }
}

for (const file of ["kalam-logo.svg", "kalam-symbol.svg"]) {
  const svg = fs.readFileSync(path.join(publicDir, file), "utf8");
  if (!svg.trimStart().startsWith("<svg") || !svg.includes('xmlns="http://www.w3.org/2000/svg"')) {
    violations.push(file + " must contain valid SVG source");
  }
}
const manifest = JSON.parse(fs.readFileSync(path.join(publicDir, "manifest.webmanifest"), "utf8"));
const expectedImages = new Map([
  ["kalam-app-192.png", 192],
  ["kalam-app-512.png", 512],
  ["favicon-16.png", 16],
  ["favicon-32.png", 32],
  ["apple-touch-icon.png", 180],
  ["kalam-og.png", 1200]
]);
for (const [file, size] of expectedImages) {
  try {
    const meta = pngDimensions(fs.readFileSync(path.join(publicDir, file)));
    const expectedHeight = file === "kalam-og.png" ? 630 : size;
    if (meta.width !== size || meta.height !== expectedHeight) {
      violations.push(file + " dimensions must be " + size + "x" + expectedHeight + " (found " + meta.width + "x" + meta.height + ")");
    }
  } catch (error) {
    violations.push(file + " could not be decoded: " + String(error));
  }
}
const faviconPath = path.join(root, "apps", "web", "src", "app", "favicon.ico");
try {
  const ico = fs.readFileSync(faviconPath);
  if (ico.readUInt16LE(0) !== 0 || ico.readUInt16LE(2) !== 1 || ico.readUInt16LE(4) !== 3) {
    violations.push("App favicon.ico must contain a valid three-size icon directory");
  } else {
    for (let index = 0; index < 3; index++) {
      const entry = 6 + index * 16;
      const width = ico.readUInt8(entry) || 256;
      const height = ico.readUInt8(entry + 1) || 256;
      const bytes = ico.readUInt32LE(entry + 8);
      const offset = ico.readUInt32LE(entry + 12);
      if (bytes < 24 || offset < 6 + 3 * 16 || offset + bytes > ico.length) throw new Error("ICO entry " + index + " has invalid byte bounds");
      const meta = pngDimensions(ico.subarray(offset, offset + bytes));
      if (meta.width !== width || meta.height !== height) {
        violations.push("App favicon.ico entry " + index + " is invalid");
      }
    }
  }
} catch (error) {
  violations.push("App favicon.ico could not be validated: " + String(error));
}
for (const icon of manifest.icons || []) {
  if (!fs.existsSync(path.join(publicDir, icon.src.replace(/^\//, "")))) {
    violations.push("PWA manifest icon is missing: " + icon.src);
  }
  if (!icon.purpose) violations.push("PWA manifest icon must declare purpose: " + icon.src);
}
if (manifest.background_color !== "#F4F8FC") violations.push("PWA manifest background_color must use the Kalam canvas #F4F8FC");

if (violations.length) {
  console.error("KALAM BRAND CONTRACT: FAIL");
  for (const v of violations) console.error(" - " + v);
  process.exit(1);
}

console.log("KALAM BRAND CONTRACT: PASS");
console.log(`Scanned ${files.length} web/public source and asset files.`);
