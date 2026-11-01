import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const out = path.join(process.cwd(), "apps", "web", "public");
const navy = "#08243D";
const blue = "#0878C9";
const tech = "#3EA9DD";
const ice = "#F4FAFF";

const mark = (first = navy) => `
  <g transform="translate(16 16)">
    <path fill="${first}" d="M24 12 H43 Q50 12 50 19 V141 Q50 148 43 148 H24 Q17 148 17 141 V19 Q17 12 24 12 Z"/>
    <path fill="${blue}" d="M51 77 L104 16 Q108 12 115 12 H148 Q155 12 150 18 L87 87 H51 Z"/>
    <path fill="${tech}" d="M51 86 H87 L150 142 Q155 148 148 148 H115 Q108 148 104 144 L51 95 Z"/>
  </g>`;

const symbolSvg = (first = navy, background = "none") => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192" role="img" aria-label="Kalam symbol">${background !== "none" ? `<rect width="192" height="192" rx="28" fill="${background}"/>` : ""}${mark(first)}</svg>`;
const logoSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 160" role="img" aria-label="Kalam logo">
${mark(navy)}
  <text x="184" y="112" fill="${navy}" font-family="Geist, Inter, Arial, sans-serif" font-size="104" font-weight="700" letter-spacing="-5">alam</text>
</svg>`;
const appIconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="${navy}"/>
  <g transform="translate(96 100) scale(2.3) translate(16 16)">
    <path fill="${ice}" d="M24 12 H43 Q50 12 50 19 V141 Q50 148 43 148 H24 Q17 148 17 141 V19 Q17 12 24 12 Z"/>
    <path fill="${blue}" d="M51 77 L104 16 Q108 12 115 12 H148 Q155 12 150 18 L87 87 H51 Z"/>
    <path fill="${tech}" d="M51 86 H87 L150 142 Q155 148 148 148 H115 Q108 148 104 144 L51 95 Z"/>
  </g>
</svg>`;
const faviconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="${navy}"/>
  <g transform="translate(96 100) scale(2.3) translate(16 16)">
    <path fill="${ice}" d="M24 12 H43 Q50 12 50 19 V141 Q50 148 43 148 H24 Q17 148 17 141 V19 Q17 12 24 12 Z"/>
    <path fill="${blue}" d="M51 77 L104 16 Q108 12 115 12 H148 Q155 12 150 18 L87 87 H51 Z"/>
    <path fill="${tech}" d="M51 86 H87 L150 142 Q155 148 148 148 H115 Q108 148 104 144 L51 95 Z"/>
  </g>
</svg>`;
const ogSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#F4F8FC"/>
  <rect x="0" y="0" width="18" height="630" fill="${blue}"/>
  <circle cx="1070" cy="110" r="250" fill="#EAF5FC"/>
  <circle cx="1070" cy="110" r="175" fill="none" stroke="#D7EAF7" stroke-width="2"/>
  <g transform="translate(105 116) scale(1.45)">${mark(navy)}</g>
  <text x="395" y="276" fill="${navy}" font-family="Geist, Inter, Arial, sans-serif" font-size="116" font-weight="750" letter-spacing="-5">alam</text>
  <text x="110" y="390" fill="${navy}" font-family="Geist, Inter, Arial, sans-serif" font-size="42" font-weight="700">Enterprise Workforce Capability Platform</text>
  <text x="110" y="466" fill="#52657A" font-family="Geist, Inter, Arial, sans-serif" font-size="32" font-weight="500">Build Capability. Drive Performance.</text>
  <text x="110" y="522" fill="${blue}" font-family="Geist, Inter, Arial, sans-serif" font-size="27" font-weight="650">Prove Readiness.</text>
</svg>`;

await fs.promises.writeFile(path.join(out, "kalam-logo.svg"), logoSvg.trim() + "\n");
await fs.promises.writeFile(path.join(out, "kalam-symbol.svg"), symbolSvg().trim() + "\n");
await sharp(Buffer.from(appIconSvg)).resize(192, 192).png().toFile(path.join(out, "kalam-app-192.png"));
await sharp(Buffer.from(appIconSvg)).resize(512, 512).png().toFile(path.join(out, "kalam-app-512.png"));
await sharp(Buffer.from(faviconSvg)).resize(16, 16).png().toFile(path.join(out, "favicon-16.png"));
await sharp(Buffer.from(faviconSvg)).resize(32, 32).png().toFile(path.join(out, "favicon-32.png"));
const faviconImages = await Promise.all([16, 32, 48].map(size => sharp(Buffer.from(faviconSvg)).resize(size, size).png().toBuffer()));
const icoHeader = Buffer.alloc(6 + faviconImages.length * 16);
icoHeader.writeUInt16LE(0, 0);
icoHeader.writeUInt16LE(1, 2);
icoHeader.writeUInt16LE(faviconImages.length, 4);
let icoOffset = icoHeader.length;
for (let index = 0; index < faviconImages.length; index++) {
  const size = [16, 32, 48][index];
  const entry = 6 + index * 16;
  icoHeader.writeUInt8(size === 256 ? 0 : size, entry);
  icoHeader.writeUInt8(size === 256 ? 0 : size, entry + 1);
  icoHeader.writeUInt8(0, entry + 2);
  icoHeader.writeUInt8(0, entry + 3);
  icoHeader.writeUInt16LE(1, entry + 4);
  icoHeader.writeUInt16LE(32, entry + 6);
  icoHeader.writeUInt32LE(faviconImages[index].length, entry + 8);
  icoHeader.writeUInt32LE(icoOffset, entry + 12);
  icoOffset += faviconImages[index].length;
}
const appIconDir = path.join(process.cwd(), "apps", "web", "src", "app");
await fs.promises.writeFile(path.join(appIconDir, "favicon.ico"), Buffer.concat([icoHeader, ...faviconImages]));
await sharp(Buffer.from(faviconSvg)).resize(180, 180).png().toFile(path.join(out, "apple-touch-icon.png"));
await sharp(Buffer.from(ogSvg)).png().toFile(path.join(out, "kalam-og.png"));

const expected = new Map([
  ["kalam-app-192.png", 192], ["kalam-app-512.png", 512],
  ["favicon-16.png", 16], ["favicon-32.png", 32],
  ["apple-touch-icon.png", 180], ["kalam-og.png", 1200]
]);
for (const [name, width] of expected) {
  const meta = await sharp(path.join(out, name)).metadata();
  if (meta.width !== width || meta.height !== (name === "kalam-og.png" ? 630 : width)) {
    throw new Error(name + " has unexpected dimensions " + meta.width + "x" + meta.height);
  }
  console.log(name + ": " + meta.width + "x" + meta.height);
}
const ico = await fs.promises.readFile(path.join(appIconDir, "favicon.ico"));
if (ico.readUInt16LE(0) !== 0 || ico.readUInt16LE(2) !== 1 || ico.readUInt16LE(4) !== 3) throw new Error("favicon.ico directory header is invalid");
for (let index = 0; index < 3; index++) {
  const entry = 6 + index * 16;
  const width = ico.readUInt8(entry) || 256;
  const height = ico.readUInt8(entry + 1) || 256;
  const bytes = ico.readUInt32LE(entry + 8);
  const offset = ico.readUInt32LE(entry + 12);
  const meta = await sharp(ico.subarray(offset, offset + bytes)).metadata();
  if (meta.format !== "png" || meta.width !== width || meta.height !== height) throw new Error("favicon.ico image entry " + index + " is invalid");
  console.log("favicon.ico entry: " + width + "x" + height);
}
for (const name of ["kalam-logo.svg", "kalam-symbol.svg"]) {
  const svg = await fs.promises.readFile(path.join(out, name), "utf8");
  if (!svg.startsWith("<svg") || !svg.includes('xmlns="http://www.w3.org/2000/svg"')) throw new Error(name + " is not valid SVG source");
  console.log(name + ": valid SVG source (" + Buffer.byteLength(svg) + " bytes)");
}
console.log("KALAM BRAND ASSET REBUILD: PASS");
