import { createReadStream, existsSync, statSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DIST = join(ROOT, "dist");
const PORT = Number(process.env.SECCHECK_PORT || "8765");
const API_ONLY = process.argv.includes("--api-only");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon"
};

const server = createServer(async (request, response) => {
  try {
    if (request.url === "/api/scan" && request.method === "POST") {
      await handleScan(request, response);
      return;
    }

    if (API_ONLY) {
      sendJson(response, 404, { error: "Not found" });
      return;
    }

    await serveStatic(request, response);
  } catch (error) {
    sendJson(response, 500, {
      error: error instanceof Error ? error.message : "Server error"
    });
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`seccheck API listening on http://127.0.0.1:${PORT}`);
});

async function handleScan(request, response) {
  const body = await readBody(request, 1024 * 1024);
  let payload;

  try {
    payload = JSON.parse(body || "{}");
  } catch {
    sendJson(response, 400, { error: "Invalid JSON." });
    return;
  }

  const url = typeof payload.url === "string" ? payload.url.trim() : "";
  if (!url) {
    sendJson(response, 400, { error: "URL is required." });
    return;
  }

  const options = payload.options || {};
  const args = ["-m", "seccheck", "scan", url, "--format", "json"];

  if (options.allowPrivate) args.push("--allow-private");
  if (options.threatIntel === false) args.push("--no-threat-intel");
  if (options.domainAge === false) args.push("--no-domain-age");

  const result = await runPython(args);
  if (result.code !== 0 && result.code !== 2) {
    sendJson(response, 500, {
      error: result.stderr || "Scanner failed.",
      exitCode: result.code
    });
    return;
  }

  let scannerPayload;
  try {
    scannerPayload = JSON.parse(result.stdout);
  } catch {
    sendJson(response, 500, {
      error: "Scanner returned invalid JSON.",
      stdout: result.stdout.slice(0, 1000)
    });
    return;
  }

  const report = scannerPayload.reports?.[0];
  if (!report) {
    sendJson(response, 500, { error: "Scanner returned no report." });
    return;
  }

  sendJson(response, 200, { report });
}

function runPython(args) {
  return new Promise((resolveRun) => {
    const child = spawn("python3", args, {
      cwd: ROOT,
      env: {
        ...process.env,
        PYTHONPATH: [join(ROOT, "src"), process.env.PYTHONPATH].filter(Boolean).join(":")
      },
      stdio: ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
    }, 45000);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      resolveRun({ code, stdout, stderr });
    });
  });
}

async function serveStatic(request, response) {
  const url = new URL(request.url || "/", "http://127.0.0.1");
  const pathname = decodeURIComponent(url.pathname);
  const requestedPath = pathname === "/" ? "/index.html" : pathname;
  const candidate = normalize(join(DIST, requestedPath));

  if (!candidate.startsWith(DIST + sep) && candidate !== DIST) {
    sendJson(response, 403, { error: "Forbidden" });
    return;
  }

  const filePath = existsSync(candidate) && statSync(candidate).isFile() ? candidate : join(DIST, "index.html");

  if (!existsSync(filePath)) {
    sendJson(response, 404, { error: "Build not found. Run npm run build." });
    return;
  }

  response.writeHead(200, {
    "Content-Type": MIME[extname(filePath)] || "application/octet-stream"
  });
  createReadStream(filePath).pipe(response);
}

function readBody(request, maxBytes) {
  return new Promise((resolveBody, reject) => {
    let body = "";
    let size = 0;

    request.on("data", (chunk) => {
      size += chunk.length;
      if (size > maxBytes) {
        reject(new Error("Request body is too large."));
        request.destroy();
        return;
      }
      body += chunk.toString("utf8");
    });

    request.on("end", () => resolveBody(body));
    request.on("error", reject);
  });
}

function sendJson(response, status, payload) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload));
}

