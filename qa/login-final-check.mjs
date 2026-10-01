import fs from "node:fs/promises";
const tab = await (await fetch("http://127.0.0.1:9336/json/new?http://127.0.0.1:3000/login", { method: "PUT" })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let id = 0; const pending = new Map();
ws.addEventListener("message", e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result);
  }
});
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const requestId = ++id; pending.set(requestId, { resolve, reject });
    ws.send(JSON.stringify({ id: requestId, method, params }));
  });
}
await send("Page.enable"); await send("Runtime.enable");
const axe = await fs.readFile("C:/Projects/CorpLMS/node_modules/axe-core/axe.min.js", "utf8");
await send("Page.addScriptToEvaluateOnNewDocument", { source: axe });for (const width of [320, 390, 768, 1440]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 900 });
  await send("Page.navigate", { url: "http://127.0.0.1:3000/login" });
  await new Promise(r => setTimeout(r, 1200));
  const state = await send("Runtime.evaluate", { expression:
    "JSON.stringify({overflow:document.documentElement.scrollWidth>innerWidth,title:document.querySelector('h2')?.textContent,org:!!document.querySelector('#login-organization'),email:!!document.querySelector('#login-email'),password:!!document.querySelector('#login-password'),oldBrand:document.body.innerText.includes('Learning intelligence')})",
    returnByValue: true });
  console.log("STATE " + width + " " + state.result.value);
  const audit = await send("Runtime.evaluate", { expression:
    "axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))))",
    awaitPromise: true, returnByValue: true });
  console.log("AXE " + width + " " + audit.result.value);
  if (width === 390 || width === 1440) {
    const shot = await send("Page.captureScreenshot", { format:"png", captureBeyondViewport:true });
    await fs.writeFile("C:/Projects/CorpLMS/qa/login-final-" + width + ".png", Buffer.from(shot.data, "base64"));
  }
}
ws.close();