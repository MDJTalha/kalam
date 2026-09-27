const WebSocket = globalThis.WebSocket;
const ws = new WebSocket("ws://127.0.0.1:9222/devtools/page/4865B8C4C6098F5201E00B80A4808711");
const routes = ["/dashboard","/dashboard/people","/dashboard/catalog","/dashboard/learning-paths","/dashboard/skills","/dashboard/assessments","/dashboard/compliance","/dashboard/analytics","/dashboard/reports","/dashboard/settings"];
let id = 0, index = 0;
function send(method, params={}) { ws.send(JSON.stringify({id:++id,method,params})); }
ws.addEventListener("open", () => { send("Page.enable"); send("Runtime.enable"); send("Page.navigate",{url:"http://127.0.0.1:3000"+routes[0]}); });
ws.addEventListener("message", async event => {
  const x=JSON.parse(event.data);
  if (x.method==="Page.loadEventFired") {
    setTimeout(()=>send("Runtime.evaluate",{expression:"location.href"}),250);
  } else if (x.id>0 && x.result?.result?.value && x.id===id) {
    console.log(routes[index]+" -> "+x.result.result.value);
    index++;
    if(index>=routes.length){ws.close();return;}
    send("Page.navigate",{url:"http://127.0.0.1:3000"+routes[index]});
  }
});