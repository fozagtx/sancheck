import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const isWindows = process.platform === "win32";
const viteBin = resolve(ROOT, "node_modules", ".bin", isWindows ? "vite.cmd" : "vite");

const processes = [
  spawn("node", ["scripts/server.mjs", "--api-only"], {
    cwd: ROOT,
    stdio: "inherit",
    env: { ...process.env, SECCHECK_PORT: process.env.SECCHECK_PORT || "8765" }
  }),
  spawn(viteBin, ["--host", "127.0.0.1", "--port", process.env.VITE_PORT || "5173"], {
    cwd: ROOT,
    stdio: "inherit"
  })
];

function shutdown(signal) {
  for (const child of processes) {
    if (!child.killed) child.kill(signal);
  }
}

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    shutdown(signal);
    process.exit(signal === "SIGINT" ? 130 : 143);
  });
}

for (const child of processes) {
  child.on("exit", (code) => {
    if (code && code !== 0) {
      shutdown("SIGTERM");
      process.exit(code);
    }
  });
}

