import fs from "node:fs/promises";
const tab = await (await fetch("http://127.0.0.1:9333/json/new?http://127.0.0.1:3000/contact-sales", { method: "PUT" })).json();
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
for (const width of [390, 768, 1440]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 900 });
  await send("Page.navigate", { url: "http://127.0.0.1:3000/contact-sales" });
  await new Promise(resolve => setTimeout(resolve, 1900));
  const state = await send("Runtime.evaluate", { expression: "JSON.stringify({title:document.title,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,header:getComputedStyle(document.querySelector('header')).position,form:!!document.querySelector('form'),h1:document.querySelector('h1')?.textContent})", returnByValue: true });
  console.log("STATE " + width + " " + state.result.value);
  const audit = await send("Runtime.evaluate", { expression: "axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))))", awaitPromise: true, returnByValue: true });
  console.log("AXE " + width + " " + audit.result.value);
  if (true) {
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
    await fs.writeFile("C:/Projects/CorpLMS/qa/contact-sales-" + width + ".png", Buffer.from(shot.data, "base64"));
  }
}
ws.close();
