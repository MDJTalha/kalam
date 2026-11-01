import sharp from "sharp";

const baseUrl = process.argv[2] || process.env.KALAM_BASE_URL || "http://127.0.0.1:3000";
const assets = [
  ["/kalam-logo.svg", "svg"],
  ["/kalam-symbol.svg", "svg"],
  ["/favicon.ico", "ico"],
  ["/kalam-app-192.png", "png", 192, 192],
  ["/kalam-app-512.png", "png", 512, 512],
  ["/favicon-16.png", "png", 16, 16],
  ["/favicon-32.png", "png", 32, 32],
  ["/apple-touch-icon.png", "png", 180, 180],
  ["/kalam-og.png", "png", 1200, 630],
  ["/manifest.webmanifest", "json"]
];
const removed = [
  "/kognivon-app-192.png", "/kognivon-app-512.png", "/kognivon-lockup.png",
  "/kognivon-lockup-dark.png", "/kognivon-mark.png", "/kognivon-mark-dark.png",
  "/kognivon-og.png", "/next.svg", "/vercel.svg", "/file.svg", "/globe.svg", "/window.svg"
];
const failures = [];
for (const [url, kind, width, height] of assets) {
  try {
    const response = await fetch(new URL(url, baseUrl));
    if (!response.ok) throw new Error("HTTP " + response.status);
    const body = Buffer.from(await response.arrayBuffer());
    if (kind === "svg") {
      const source = body.toString("utf8");
      if (!source.trimStart().startsWith("<svg") || !source.includes("http://www.w3.org/2000/svg")) throw new Error("response is not valid SVG source");
    } else if (kind === "png") {
      const meta = await sharp(body).metadata();
      if (meta.format !== "png" || meta.width !== width || meta.height !== height) throw new Error("expected PNG " + width + "x" + height + ", received " + meta.format + " " + meta.width + "x" + meta.height);
    } else if (kind === "ico") {
      if (body.readUInt16LE(0) !== 0 || body.readUInt16LE(2) !== 1 || body.readUInt16LE(4) !== 3) throw new Error("favicon.ico directory header is invalid");
      for (let index = 0; index < 3; index++) {
        const entry = 6 + index * 16;
        const width = body.readUInt8(entry) || 256;
        const height = body.readUInt8(entry + 1) || 256;
        const bytes = body.readUInt32LE(entry + 8);
        const offset = body.readUInt32LE(entry + 12);
        const meta = await sharp(body.subarray(offset, offset + bytes)).metadata();
        if (meta.format !== "png" || meta.width !== width || meta.height !== height) throw new Error("favicon.ico entry " + index + " is invalid");
      }
    } else {
      const manifest = JSON.parse(body.toString("utf8"));
      if (manifest.name !== "Kalam" || manifest.theme_color !== "#08243D") throw new Error("manifest identity/theme mismatch");
      for (const icon of manifest.icons || []) {
        const iconResponse = await fetch(new URL(icon.src, baseUrl));
        if (!iconResponse.ok) throw new Error("manifest icon " + icon.src + " HTTP " + iconResponse.status);
      }
    }
    console.log("PASS " + url + " (" + body.length + " bytes)");
  } catch (error) {
    failures.push({url,error:String(error)});
    console.log("FAIL " + url + ": " + String(error));
  }
}
for (const url of removed) {
  try {
    const response = await fetch(new URL(url, baseUrl));
    if (response.status !== 404) {
      failures.push({url,error:"removed asset must return 404, got " + response.status});
      console.log("FAIL " + url + " expected 404, got " + response.status);
    } else console.log("PASS removed " + url);
  } catch (error) {
    failures.push({url,error:String(error)});
  }
}
try {
  const response = await fetch(new URL("/", baseUrl));
  const html = await response.text();
  if (!response.ok || !html.includes("Kalam | Enterprise Workforce Capability Platform") || !html.includes("/kalam-logo.svg")) throw new Error("homepage title or canonical JSON-LD logo reference missing (HTTP " + response.status + ")");
  console.log("PASS / homepage brand metadata");
} catch (error) {
  failures.push({url:"/",error:String(error)});
  console.log("FAIL / " + String(error));
}
console.log("KALAM BRAND ASSET SMOKE " + (failures.length ? "FAIL" : "PASS"));
console.log(JSON.stringify({assets_checked:assets.length,removed_assets_checked:removed.length,failures},null,2));
if (failures.length) process.exitCode=1;
