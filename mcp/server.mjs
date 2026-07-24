#!/usr/bin/env node
/**
 * grimoire-mcp — the Rattle MCP server.
 *
 * Design goal: ZERO DRIFT and ZERO DEPENDENCIES.
 *
 * Drift. The Rattle API has 472 operations across 260 paths. A server that
 * hand-declares one MCP tool per endpoint would rot the day rattleapp.de ships
 * a new endpoint. This server therefore declares NO per-endpoint code at all.
 * It exposes a generic authenticated passthrough (`rattle_request`) plus a
 * search tool over the bundled OpenAPI spec (`rattle_api_search`). A new Rattle
 * endpoint works the day it ships; the only maintenance step is refreshing
 * docs/openapi.json via `python3 scripts/build_api_reference.py`.
 *
 * Dependencies. Claude Code loads a plugin by cloning it — there is no
 * `npm install` step. So this speaks MCP's stdio transport (newline-delimited
 * JSON-RPC 2.0) directly against Node's stdlib rather than pulling in the MCP
 * SDK. Node >= 18 (global fetch) is the only requirement.
 *
 * Knowledge delivery. Claude Code has a native Skills mechanism; Cursor,
 * Windsurf, Claude Desktop and ChatGPT do not. `rattle_knowledge_list` /
 * `rattle_knowledge_get` and the MCP resource surface hand those clients the
 * same SKILL.md / references / schemas that Claude Code loads natively. This is
 * how one bundle serves every client.
 *
 * Env:
 *   RATTLE_API_KEY            single-tenant key (or RATTLE_API_KEY_<TENANT>)
 *   RATTLE_BASE_URL           default https://www.rattleapp.de/api/v1
 *   RATTLE_TENANT             default tenant for RATTLE_API_KEY_<TENANT> lookup
 *   RATTLE_MCP_ALLOW_WRITES   "1" to permit non-GET requests. Default: read-only.
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PROTOCOL_VERSION = "2025-06-18";
const SUPPORTED_PROTOCOLS = new Set(["2024-11-05", "2025-03-26", "2025-06-18"]);

const BASE_URL = (process.env.RATTLE_BASE_URL || "https://www.rattleapp.de/api/v1").replace(/\/$/, "");
// The plugin's userConfig substitutes a JSON boolean as the string "true"/"false",
// while a shell / .mcp.json user is far likelier to write "1". Accept both, and
// treat everything else — including the empty string an unset userConfig yields —
// as false. Read-only is the safe default and must survive a malformed value.
const ALLOW_WRITES = ["1", "true", "yes"].includes(String(process.env.RATTLE_MCP_ALLOW_WRITES || "").toLowerCase());
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

/** Resolve an API key: explicit tenant -> RATTLE_API_KEY_<TENANT> -> RATTLE_API_KEY. */
function resolveApiKey(tenant) {
  const name = tenant || process.env.RATTLE_TENANT;
  if (name) {
    const scoped = process.env[`RATTLE_API_KEY_${name.toUpperCase()}`];
    if (scoped) return scoped;
  }
  const flat = process.env.RATTLE_API_KEY;
  if (flat) return flat;

  const known = Object.keys(process.env)
    .filter((k) => k.startsWith("RATTLE_API_KEY_"))
    .map((k) => k.slice("RATTLE_API_KEY_".length).toLowerCase());
  throw new Error(
    name
      ? `No API key for tenant '${name}'. Set RATTLE_API_KEY_${name.toUpperCase()}. Known tenants: ${known.join(", ") || "(none)"}`
      : `No Rattle API key. Set RATTLE_API_KEY, or RATTLE_API_KEY_<TENANT> plus a tenant argument. Known tenants: ${known.join(", ") || "(none)"}`,
  );
}

// ---------------------------------------------------------------------------
// Bundled OpenAPI spec — lazily loaded, searched, never hand-mirrored
// ---------------------------------------------------------------------------

let specCache = null;

function loadSpec() {
  if (specCache) return specCache;
  for (const candidate of ["skills/rattle-api/references/openapi.json", "docs/openapi.json"]) {
    try {
      specCache = JSON.parse(readFileSync(path.join(ROOT, candidate), "utf8"));
      return specCache;
    } catch {
      /* try next */
    }
  }
  throw new Error("Bundled OpenAPI spec not found (looked in skills/rattle-api/references/ and docs/).");
}

/**
 * The spec embeds the version prefix in every path ("/api/v1/products") while
 * its `servers` entry is just "/". RATTLE_BASE_URL, meanwhile, already ends in
 * that same prefix. Copying a path straight out of the spec would therefore
 * produce /api/v1/api/v1/products. Derive the prefix from BASE_URL — the thing
 * we actually concatenate against — and strip it on both the search and the
 * request side, so 'products' and '/api/v1/products' both work.
 */
function specPrefix() {
  try {
    return new URL(BASE_URL).pathname.replace(/\/$/, "");
  } catch {
    return "";
  }
}

/** Strip a duplicated base prefix so both 'products' and '/api/v1/products' resolve. */
function normalizePath(p) {
  const prefix = specPrefix();
  let out = String(p).replace(/^\//, "");
  if (prefix && ("/" + out).startsWith(prefix + "/")) {
    out = ("/" + out).slice(prefix.length).replace(/^\//, "");
  }
  return out;
}

/** Flatten the spec into one searchable record per operation. */
function operations() {
  const spec = loadSpec();
  const out = [];
  for (const [p, item] of Object.entries(spec.paths || {})) {
    const requestPath = normalizePath(p);
    for (const [method, op] of Object.entries(item)) {
      if (!["get", "post", "put", "patch", "delete"].includes(method)) continue;
      out.push({
        method: method.toUpperCase(),
        path: requestPath,
        operationId: op.operationId || "",
        summary: op.summary || "",
        tags: op.tags || [],
        parameters: (op.parameters || []).map((prm) => ({
          name: prm.name,
          in: prm.in,
          required: !!prm.required,
        })),
        requestBody: op.requestBody ? Object.keys(op.requestBody.content || {}) : null,
      });
    }
  }
  return out;
}

function searchApi(query, limit = 15) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const scored = operations()
    .map((op) => {
      const hay = `${op.method} ${op.path} ${op.operationId} ${op.summary} ${op.tags.join(" ")}`.toLowerCase();
      // Every term must appear; rank by path-hit (most specific) then summary-hit.
      if (!terms.every((t) => hay.includes(t))) return null;
      let score = 0;
      for (const t of terms) {
        if (op.path.toLowerCase().includes(t)) score += 3;
        if (op.operationId.toLowerCase().includes(t)) score += 2;
        if (op.summary.toLowerCase().includes(t)) score += 1;
      }
      return { op, score };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((s) => s.op);

  return {
    query,
    matched: scored.length,
    total_operations: operations().length,
    operations: scored,
    hint: "Call the chosen operation with rattle_request. Paths are relative to the API base; do not prefix /api/v1.",
  };
}

// ---------------------------------------------------------------------------
// Knowledge surface — how non-Claude-Code clients get the Skills
// ---------------------------------------------------------------------------

const KNOWLEDGE_DIRS = ["skills", "schemas", "examples", "agents", "commands"];
const KNOWLEDGE_EXT = new Set([".md", ".json", ".py"]);

function knowledgeFiles() {
  const out = [];
  const walk = (dir) => {
    let entries;
    try {
      entries = readdirSync(path.join(ROOT, dir));
    } catch {
      return;
    }
    for (const entry of entries) {
      const rel = path.join(dir, entry);
      const abs = path.join(ROOT, rel);
      if (statSync(abs).isDirectory()) {
        if (entry === "__pycache__") continue;
        walk(rel);
      } else if (KNOWLEDGE_EXT.has(path.extname(entry))) {
        out.push(rel);
      }
    }
  };
  KNOWLEDGE_DIRS.forEach(walk);
  return out.sort();
}

/** First non-empty prose line, or the frontmatter description — used as the listing blurb. */
function blurb(rel) {
  try {
    const text = readFileSync(path.join(ROOT, rel), "utf8");
    const fm = text.match(/^---\n([\s\S]*?)\n---/);
    if (fm) {
      const d = fm[1].match(/^description:\s*(.+)$/m);
      if (d) return d[1].trim().slice(0, 240);
    }
    if (rel.endsWith(".json")) {
      const j = JSON.parse(text);
      if (j.description) return String(j.description).slice(0, 240);
      if (j.title) return String(j.title).slice(0, 240);
    }
    const line = text.split("\n").find((l) => l.trim() && !l.startsWith("#"));
    return (line || "").trim().slice(0, 240);
  } catch {
    return "";
  }
}

function knowledgeGet(ref) {
  // Contain reads to the bundle — never let a path escape ROOT.
  const rel = path.normalize(ref).replace(/^(\.\.(\/|\\|$))+/, "");
  const abs = path.resolve(ROOT, rel);
  if (!abs.startsWith(ROOT + path.sep)) throw new Error(`Refusing to read outside the bundle: ${ref}`);
  if (!KNOWLEDGE_DIRS.some((d) => rel === d || rel.startsWith(d + path.sep))) {
    throw new Error(`Not a knowledge path: ${ref}. Must live under ${KNOWLEDGE_DIRS.join(", ")}.`);
  }
  return readFileSync(abs, "utf8");
}

// ---------------------------------------------------------------------------
// The generic, drift-proof API passthrough
// ---------------------------------------------------------------------------

async function rattleRequest({ method = "GET", path: apiPath, body, query, tenant }) {
  const verb = String(method).toUpperCase();
  if (!apiPath) throw new Error("`path` is required, e.g. 'products' or 'groups/42/options'.");

  if (!SAFE_METHODS.has(verb) && !ALLOW_WRITES) {
    throw new Error(
      `Refusing ${verb} ${apiPath}: this server is read-only. ` +
        `Writes to a live Rattle tenant are irreversible. Set RATTLE_MCP_ALLOW_WRITES=1 to enable them, ` +
        `and prefer routing writes through the rattle-apply-config idempotent ensure_* flow.`,
    );
  }

  const url = new URL(`${BASE_URL}/${normalizePath(apiPath)}`);
  for (const [k, v] of Object.entries(query || {})) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }

  const res = await fetch(url, {
    method: verb,
    headers: {
      Authorization: `Bearer ${resolveApiKey(tenant)}`,
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let parsed;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = text;
  }

  if (!res.ok) {
    // Rattle returns RFC 9457 problem+json — surface it verbatim rather than flattening.
    throw new Error(`Rattle API ${res.status} on ${verb} ${url.pathname}: ${typeof parsed === "string" ? parsed : JSON.stringify(parsed)}`);
  }
  return { status: res.status, body: parsed };
}

// ---------------------------------------------------------------------------
// Tool registry
// ---------------------------------------------------------------------------

const TOOLS = [
  {
    name: "rattle_api_search",
    description:
      "Search the bundled Rattle OpenAPI spec (472 operations / 260 paths) for the endpoints matching a query. " +
      "Use this to DISCOVER the right endpoint before calling rattle_request, instead of loading the 7,000-line API reference into context. " +
      "Example queries: 'create option', 'list groups product', 'constraints replace', 'bom item usage subclause'.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Space-separated terms. All terms must match." },
        limit: { type: "integer", description: "Max operations to return (default 15).", default: 15 },
      },
      required: ["query"],
    },
  },
  {
    name: "rattle_request",
    description:
      "Execute any Rattle REST API call. This is a generic authenticated passthrough — every one of the 472 operations is reachable through it, " +
      "and new endpoints work with no change to this server. Discover the right path with rattle_api_search first. " +
      "Paths are relative to the API base: use 'products', not '/api/v1/products'. " +
      "Read-only by default; non-GET requires RATTLE_MCP_ALLOW_WRITES=1.",
    inputSchema: {
      type: "object",
      properties: {
        method: { type: "string", enum: ["GET", "POST", "PUT", "PATCH", "DELETE"], default: "GET" },
        path: { type: "string", description: "Path relative to the API base, e.g. 'groups/42/options'." },
        query: { type: "object", description: "Query-string parameters, e.g. {\"limit\": 50, \"cursor\": \"...\"}." },
        body: { type: "object", description: "JSON request body for POST/PUT/PATCH." },
        tenant: { type: "string", description: "Tenant name; resolves RATTLE_API_KEY_<TENANT>. Omit to use RATTLE_API_KEY." },
      },
      required: ["path"],
    },
  },
  {
    name: "rattle_knowledge_list",
    description:
      "List every Grimoire knowledge file — the Rattle configurator skills, references, JSON Schemas, golden examples, agents and commands. " +
      "Use this in clients that have no native Skills mechanism (Cursor, Windsurf, Claude Desktop, ChatGPT) to find the right doc, then fetch it with rattle_knowledge_get. " +
      "ALWAYS read skills/rattle-configurator/SKILL.md before answering any Rattle question — it carries the #1 rule.",
    inputSchema: {
      type: "object",
      properties: {
        filter: { type: "string", description: "Optional substring filter on the path, e.g. 'bom' or 'techdoc'." },
      },
    },
  },
  {
    name: "rattle_knowledge_get",
    description:
      "Fetch the full text of one Grimoire knowledge file by its bundle-relative path, e.g. 'skills/rattle-configurator/SKILL.md' " +
      "or 'schemas/recommendation.schema.json'. Paths come from rattle_knowledge_list.",
    inputSchema: {
      type: "object",
      properties: {
        ref: { type: "string", description: "Bundle-relative path under skills/, schemas/, examples/, agents/ or commands/." },
      },
      required: ["ref"],
    },
  },
];

async function callTool(name, args) {
  switch (name) {
    case "rattle_api_search":
      return searchApi(args.query, args.limit ?? 15);

    case "rattle_request":
      return await rattleRequest(args);

    case "rattle_knowledge_list": {
      const files = knowledgeFiles().filter((f) => !args.filter || f.includes(args.filter));
      return {
        count: files.length,
        start_here: "skills/rattle-configurator/SKILL.md",
        files: files.map((f) => ({ ref: f, description: blurb(f) })),
      };
    }

    case "rattle_knowledge_get":
      return { ref: args.ref, content: knowledgeGet(args.ref) };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// ---------------------------------------------------------------------------
// MCP stdio transport — newline-delimited JSON-RPC 2.0
// ---------------------------------------------------------------------------

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

function reply(id, result) {
  send({ jsonrpc: "2.0", id, result });
}

function replyError(id, code, message) {
  send({ jsonrpc: "2.0", id, error: { code, message } });
}

async function handle(msg) {
  const { id, method, params } = msg;

  // Notifications carry no id and take no response.
  if (id === undefined || id === null) return;

  try {
    switch (method) {
      case "initialize": {
        const asked = params?.protocolVersion;
        return reply(id, {
          protocolVersion: SUPPORTED_PROTOCOLS.has(asked) ? asked : PROTOCOL_VERSION,
          capabilities: { tools: {}, resources: {} },
          serverInfo: { name: "grimoire-rattle", version: "0.7.0" },
        });
      }

      case "ping":
        return reply(id, {});

      case "tools/list":
        return reply(id, { tools: TOOLS });

      case "tools/call": {
        const result = await callTool(params.name, params.arguments || {});
        return reply(id, {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        });
      }

      case "resources/list":
        return reply(id, {
          resources: knowledgeFiles().map((f) => ({
            uri: `grimoire://${f}`,
            name: f,
            description: blurb(f),
            mimeType: f.endsWith(".json") ? "application/json" : "text/markdown",
          })),
        });

      case "resources/read": {
        const ref = String(params.uri).replace(/^grimoire:\/\//, "");
        return reply(id, {
          contents: [
            {
              uri: params.uri,
              mimeType: ref.endsWith(".json") ? "application/json" : "text/markdown",
              text: knowledgeGet(ref),
            },
          ],
        });
      }

      default:
        return replyError(id, -32601, `Method not found: ${method}`);
    }
  } catch (err) {
    // Tool failures come back as a JSON-RPC error so the model sees the reason
    // (missing key, read-only refusal, 4xx from Rattle) and can correct itself.
    return replyError(id, -32603, err.message);
  }
}

let buffer = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", async (chunk) => {
  buffer += chunk;
  let nl;
  while ((nl = buffer.indexOf("\n")) !== -1) {
    const line = buffer.slice(0, nl).trim();
    buffer = buffer.slice(nl + 1);
    if (!line) continue;
    try {
      await handle(JSON.parse(line));
    } catch {
      replyError(null, -32700, "Parse error");
    }
  }
});
process.stdin.on("end", () => process.exit(0));
