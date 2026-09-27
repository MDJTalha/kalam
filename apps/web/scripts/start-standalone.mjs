import path from "node:path";
import { cpSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const appRoot = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const distDir = process.env.NEXT_DIST_DIR || ".next";
const standaloneRoot = path.join(appRoot, distDir, "standalone", "apps", "web");
const staticSource = path.join(appRoot, distDir, "static");
const staticTarget = path.join(standaloneRoot, distDir, "static");
const publicSource = path.join(appRoot, "public");
const publicTarget = path.join(standaloneRoot, "public");

mkdirSync(path.dirname(staticTarget), { recursive: true });
cpSync(staticSource, staticTarget, { recursive: true });
cpSync(publicSource, publicTarget, { recursive: true });

const server = spawn(process.execPath, [path.join(standaloneRoot, "server.js")], {
  cwd: standaloneRoot,
  stdio: "inherit",
  env: { ...process.env, HOSTNAME: "127.0.0.1", PORT: "3000" },
});

server.on("exit", (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
