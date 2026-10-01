import fs from "node:fs/promises";
const tab = await (await fetch("http://127.0.0.1:9333/json/new?http://127.0.0.1:3000/", { method: "PUT" })).json();
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
for (const width of [320, 390, 768, 1440]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 900 });
  await send("Page.navigate", { url: "http://127.0.0.1:3000/" });
  await new Promise(resolve => setTimeout(resolve, 1500));
  const expression = "JSON.stringify({width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.querySelectorAll('a[href^=\"#\"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.href),cards:document.querySelectorAll('details[class*=capabilityCard]').length,questions:document.querySelectorAll('#questions details').length})";
  const state = await send("Runtime.evaluate", { expression, returnByValue: true });
  console.log("STATE " + width + " " + state.result.value);
  const audit = await send("Runtime.evaluate", { expression: "axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(x=>JSON.stringify(x.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))))", awaitPromise: true, returnByValue: true });
  console.log("AXE " + width + " " + audit.result.value);
  if (width === 390 || width === 1440) {
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
    await fs.writeFile("C:/Projects/CorpLMS/qa/landing-final-" + width + ".png", Buffer.from(shot.data, "base64"));
  }
}
const click = await send("Runtime.evaluate", { expression: "document.querySelector('details[class*=capabilityCard] summary').click(); JSON.stringify({opened:document.querySelector('details[class*=capabilityCard]').open,text:document.querySelector('details[class*=capabilityCard] .landing-module__ESXKBq__cardDetail')?.textContent})", returnByValue: true });
console.log("INTERACTION " + click.result.value);
await send("Runtime.evaluate", { expression: "document.querySelectorAll('details[class*=capabilityCard] summary')[1].focus()" });
await send("Input.dispatchKeyEvent", { type: "keyDown", key: " ", code: "Space", windowsVirtualKeyCode: 32 });
await send("Input.dispatchKeyEvent", { type: "keyUp", key: " ", code: "Space", windowsVirtualKeyCode: 32 });
await new Promise(resolve => setTimeout(resolve, 250));
const keyboard = await send("Runtime.evaluate", { expression: "JSON.stringify({open:document.querySelectorAll('details[class*=capabilityCard]')[1].open,active:document.activeElement?.tagName,summary:document.activeElement?.textContent?.slice(0,45)})", returnByValue: true });
console.log("KEYBOARD " + keyboard.result.value);
ws.close();
