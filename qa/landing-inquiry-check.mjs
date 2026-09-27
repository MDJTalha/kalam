import fs from "node:fs/promises";
const tab = await (await fetch("http://127.0.0.1:9333/json/new?http://127.0.0.1:3001/", { method: "PUT" })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(resolve => ws.addEventListener("open", resolve, { once: true }));
let id = 0;
const pending = new Map();
ws.addEventListener("message", event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    message.error ? reject(new Error(message.error.message)) : resolve(message.result);
  }
});
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const requestId = ++id;
    pending.set(requestId, { resolve, reject });
    ws.send(JSON.stringify({ id: requestId, method, params }));
  });
}
await send("Page.enable");
await send("Runtime.enable");
const axe = await fs.readFile("C:/Projects/CorpLMS/node_modules/axe-core/axe.min.js", "utf8");
await send("Page.addScriptToEvaluateOnNewDocument", { source: axe });
for (const width of [390, 1440]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 900 });
  await send("Page.navigate", { url: "http://127.0.0.1:3001/" });
  await new Promise(resolve => setTimeout(resolve, 1200));
  const state = await send("Runtime.evaluate", { expression: "JSON.stringify({form:!!document.querySelector('#demo form'),overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.querySelectorAll('a[href^=\"#\"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.href)})", returnByValue: true });
  console.log("STATE " + width + " " + state.result.value);
  const audit = await send("Runtime.evaluate", { expression: "axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))))", awaitPromise: true, returnByValue: true });
  console.log("AXE " + width + " " + audit.result.value);
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
  await fs.writeFile("C:/Projects/CorpLMS/qa/landing-inquiry-" + width + ".png", Buffer.from(shot.data, "base64"));
}
ws.close();
