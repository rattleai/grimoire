#!/usr/bin/env node
/**
 * Smoke-test the Rattle MCP server over its real stdio transport.
 *
 * This is not a unit test — it spawns the server exactly the way Claude Code,
 * Cursor and Claude Desktop spawn it, and drives it with real JSON-RPC frames.
 * It asserts the four things whose failure would be silent in production:
 *
 *   1. It completes an MCP handshake and advertises its tools.
 *   2. Endpoint discovery works against the bundled OpenAPI spec, and returns
 *      paths that are directly usable by rattle_request (no /api/v1 doubling).
 *   3. It is READ-ONLY by default. A write must be refused when
 *      RATTLE_MCP_ALLOW_WRITES is unset — a live CPQ tenant is not a sandbox.
 *   4. It refuses to read outside the bundle (path traversal).
 *
 * Runs with no network and no API key.
 */

import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const REQUESTS = [
  { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18" } },
  { jsonrpc: "2.0", id: 2, method: "tools/list" },
  { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "rattle_api_search", arguments: { query: "options", limit: 5 } } },
  { jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "rattle_knowledge_get", arguments: { ref: "skills/rattle-configurator/SKILL.md" } } },
  { jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "rattle_request", arguments: { method: "POST", path: "products", body: { name: "should-never-be-created" } } } },
  { jsonrpc: "2.0", id: 6, method: "tools/call", params: { name: "rattle_knowledge_get", arguments: { ref: "../../../../etc/passwd" } } },
];

function run() {
  return new Promise((resolve, reject) => {
    const env = { ...process.env, RATTLE_API_KEY: "rk_test_smoke" };
    delete env.RATTLE_MCP_ALLOW_WRITES; // the whole point of check 3

    const proc = spawn("node", [path.join(ROOT, "mcp", "server.mjs")], {
      env,
      stdio: ["pipe", "pipe", "inherit"],
    });

    let out = "";
    proc.stdout.on("data", (d) => (out += d));
    proc.on("error", reject);
    proc.on("close", () => {
      const byId = new Map();
      for (const line of out.split("\n").filter((l) => l.trim())) {
        const msg = JSON.parse(line);
        byId.set(msg.id, msg);
      }
      resolve(byId);
    });

    for (const req of REQUESTS) proc.stdin.write(JSON.stringify(req) + "\n");
    proc.stdin.end();
  });
}

const failures = [];
const check = (label, ok, detail = "") => {
  console.log(`${ok ? "  ok  " : "  FAIL"}  ${label}${detail && !ok ? ` — ${detail}` : ""}`);
  if (!ok) failures.push(label);
};

const res = await run();
const payload = (id) => JSON.parse(res.get(id).result.content[0].text);

console.log("Rattle MCP server — smoke test\n");

// 1. handshake
const init = res.get(1)?.result;
check("handshake returns serverInfo + protocolVersion", !!init?.serverInfo && !!init?.protocolVersion);

// 2. tools advertised
const tools = (res.get(2)?.result?.tools || []).map((t) => t.name);
const expected = ["rattle_api_search", "rattle_request", "rattle_knowledge_list", "rattle_knowledge_get"];
check(`advertises all ${expected.length} tools`, expected.every((t) => tools.includes(t)), `got ${tools.join(", ")}`);

// 3. endpoint discovery, and paths are request-ready (no /api/v1 doubling)
const search = payload(3);
check("api_search finds operations in the bundled spec", search.matched > 0 && search.total_operations > 100);
check(
  "api_search returns request-ready paths (no leading /api/v1)",
  search.operations.every((o) => !o.path.startsWith("/") && !o.path.startsWith("api/v1")),
  JSON.stringify(search.operations.map((o) => o.path)),
);

// 4. knowledge surface
check("knowledge_get serves the entry-point skill", payload(4).content.includes("#1 rule") || payload(4).content.length > 500);

// 5. THE safety property: read-only by default
const write = res.get(5);
check("refuses a write when RATTLE_MCP_ALLOW_WRITES is unset", !!write?.error && /read-only/i.test(write.error.message), JSON.stringify(write));

// 6. no path traversal
const traversal = res.get(6);
check("refuses to read outside the bundle", !!traversal?.error, JSON.stringify(traversal));

console.log();
if (failures.length) {
  console.error(`FAILED — ${failures.length} check(s): ${failures.join("; ")}`);
  process.exit(1);
}
console.log(`OK — ${search.total_operations} API operations reachable, read-only enforced.`);
