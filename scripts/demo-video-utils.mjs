import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
export const repoRoot = path.resolve(scriptsDir, "..");
export const frontendDir = path.join(repoRoot, "frontend");
export const backendDir = path.join(repoRoot, "backend");
export const artifactsDir = path.join(repoRoot, "artifacts", "demo-video");

export function requireFromFrontend(moduleName) {
  const require = createRequire(path.join(frontendDir, "package.json"));
  return require(moduleName);
}

export function parseArgs(argv = process.argv.slice(2)) {
  const args = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) {
      args._.push(item);
      continue;
    }
    const rawKey = item.slice(2);
    if (rawKey.startsWith("no-")) {
      args[rawKey.slice(3)] = false;
      continue;
    }
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) {
      args[rawKey] = true;
      continue;
    }
    args[rawKey] = next;
    index += 1;
  }
  return args;
}

export async function ensureDir(dirPath) {
  await fs.mkdir(dirPath, { recursive: true });
  return dirPath;
}

export async function writeJson(filePath, payload) {
  await ensureDir(path.dirname(filePath));
  await fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

export async function readJsonIfExists(filePath) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

export function normalizeUrl(url, fallback) {
  const value = String(url || fallback || "").trim();
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export function makeSeed(value = "") {
  if (value) {
    return String(value).replace(/[^0-9A-Za-z_-]/g, "");
  }
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return stamp;
}

export function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function apiRequest(backendUrl, apiPath, options = {}) {
  const method = options.method || (options.json ? "POST" : "GET");
  const headers = new Headers(options.headers || {});
  let body = options.body;
  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }
  const response = await fetch(`${backendUrl}${apiPath}`, { method, headers, body });
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { raw_text: text };
    }
  }
  if (!response.ok) {
    const detail = payload?.detail || payload?.message || text || response.statusText;
    throw new Error(`${method} ${apiPath} failed with ${response.status}: ${detail}`);
  }
  return payload;
}

export async function waitForEndpoint(url, options = {}) {
  const timeoutMs = Number(options.timeoutMs || 30000);
  const intervalMs = Number(options.intervalMs || 500);
  const startedAt = Date.now();
  let lastError = "";
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url, { method: options.method || "GET" });
      if (response.ok) {
        return true;
      }
      lastError = `${response.status} ${response.statusText}`;
    } catch (error) {
      lastError = error.message;
    }
    await wait(intervalMs);
  }
  throw new Error(`Endpoint did not become ready: ${url}. Last error: ${lastError}`);
}

export function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    let resolvedCommand = command;
    let resolvedArgs = args;
    if (process.platform === "win32" && ["npm", "npx", "pnpm", "yarn"].includes(command)) {
      resolvedCommand = process.env.ComSpec || "cmd.exe";
      resolvedArgs = ["/d", "/s", "/c", command, ...args];
    }
    const child = spawn(resolvedCommand, resolvedArgs, {
      cwd: options.cwd || repoRoot,
      env: { ...process.env, ...(options.env || {}) },
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    const echo = options.echo !== false;
    child.stdout?.on("data", (chunk) => {
      const text = chunk.toString();
      stdout += text;
      if (echo) process.stdout.write(text);
    });
    child.stderr?.on("data", (chunk) => {
      const text = chunk.toString();
      stderr += text;
      if (echo) process.stderr.write(text);
    });
    let timedOut = false;
    const timeout = options.timeoutMs
      ? setTimeout(() => {
          timedOut = true;
          child.kill("SIGTERM");
        }, options.timeoutMs)
      : null;
    child.on("error", (error) => {
      if (timeout) clearTimeout(timeout);
      reject(error);
    });
    child.on("close", (code) => {
      if (timeout) clearTimeout(timeout);
      if (code === 0 && !timedOut) {
        resolve({ stdout, stderr, code });
        return;
      }
      const suffix = timedOut ? " timed out" : ` exited with ${code}`;
      const error = new Error(`${command} ${args.join(" ")}${suffix}`);
      error.stdout = stdout;
      error.stderr = stderr;
      reject(error);
    });
  });
}

function escapePdfText(text) {
  return String(text)
    .replace(/[^\x20-\x7E]/g, " ")
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)");
}

export function createSimplePdfBuffer(lines) {
  const safeLines = (Array.isArray(lines) ? lines : String(lines).split(/\r?\n/))
    .map((line) => escapePdfText(line.trim()))
    .filter(Boolean)
    .slice(0, 48);
  const textOps = safeLines.map((line) => `(${line}) Tj T*`).join("\n");
  const stream = `BT\n/F1 11 Tf\n15 TL\n50 790 Td\n${textOps}\nET\n`;
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    `<< /Length ${Buffer.byteLength(stream, "ascii")} >>\nstream\n${stream}endstream`,
  ];
  let body = "%PDF-1.4\n";
  const offsets = [0];
  for (let index = 0; index < objects.length; index += 1) {
    offsets.push(Buffer.byteLength(body, "ascii"));
    body += `${index + 1} 0 obj\n${objects[index]}\nendobj\n`;
  }
  const xrefOffset = Buffer.byteLength(body, "ascii");
  body += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const offset of offsets.slice(1)) {
    body += `${String(offset).padStart(10, "0")} 00000 n \n`;
  }
  body += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;
  return Buffer.from(body, "ascii");
}

export async function latestJsonReport(defaultPath = path.join(artifactsDir, "latest-report.json")) {
  const report = await readJsonIfExists(defaultPath);
  if (!report) {
    throw new Error(`Report was not found: ${defaultPath}`);
  }
  return report;
}
