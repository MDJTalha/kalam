const WebSocket = globalThis.WebSocket;
const ws = new WebSocket("ws://127.0.0.1:9222/devtools/page/4865B8C4C6098F5201E00B80A4808711");
ws.addEventListener("open", () => ws.send(JSON.stringify({id:1, method:"Network.getAllCookies"})));
ws.addEventListener("message", (event) => {
  const x = JSON.parse(event.data);
  if (x.id !== 1) return;
  const out = x.result.cookies
    .filter(c => c.domain.includes("127.0.0.1") || c.domain.includes("localhost"))
    .map(c => ({name:c.name, domain:c.domain, path:c.path, expires:c.expires, httpOnly:c.httpOnly, secure:c.secure, sameSite:c.sameSite}));
  console.log(JSON.stringify(out, null, 2));
  ws.close();
});