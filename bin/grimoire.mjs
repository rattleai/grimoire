#!/usr/bin/env node
/**
 * grimoire
 *
 * Drops the Grimoire AI workspace artifacts (skills/, agents/, commands/,
 * schemas/, examples/, AGENTS.md, .claude-plugin/) into a target project so
 * any AI agent (Claude Code, Cursor, Codex, Aider, Continue, …) can pick
 * them up.
 *
 * Usage:
 *   npx @rattleai/grimoire install                    # install into ./
 *   npx @rattleai/grimoire install --target ./my-app  # install into a path
 *   npx @rattleai/grimoire install --layout claude    # only Claude Code paths (.claude/skills, .claude/agents, .claude/commands)
 *   npx @rattleai/grimoire install --layout flat      # default — root-level skills/, agents/, commands/, AGENTS.md
 *   npx @rattleai/grimoire install --layout user      # ~/.claude/skills, ~/.claude/agents, ~/.claude/commands (machine-wide)
 *   npx @rattleai/grimoire install --dry-run          # show what would be copied without copying
 *
 * Layouts:
 *   - flat   (default): writes skills/, agents/, commands/, AGENTS.md, .claude-plugin/ at the target root.
 *   - claude:           writes .claude/skills/, .claude/agents/, .claude/commands/, plus AGENTS.md.
 *   - user:             writes into ~/.claude/skills, ~/.claude/agents, ~/.claude/commands (no AGENTS.md).
 *
 * Idempotent: re-running re-copies (overwrites) files. Existing files outside
 * the workspace footprint are never touched.
 *
 * Suppressed when invoked as `node bin/grimoire.mjs --postinstall`
 * (used as the npm `postinstall` hook so installing the package itself doesn't
 * spam the user's project).
 */

import { promises as fs } from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PACKAGE_ROOT = path.resolve(__dirname, "..");

const ARTIFACTS = [
  { src: "skills", required: true },
  { src: "agents", required: true },
  { src: "commands", required: true },
  { src: "schemas", required: false },
  { src: "examples", required: false },
  // The MCP server is what gives Cursor / Windsurf / Claude Desktop the skills
  // and live API access that Claude Code gets natively. Without it, an npx
  // install leaves those clients with Markdown and no way to reach the tenant.
  { src: "mcp", required: false },
  { src: ".mcp.json", required: false },
  { src: ".claude-plugin", required: true },
  { src: "AGENTS.md", required: true },
  { src: "CLAUDE.md", required: false },
];

function parseArgs(argv) {
  const args = {
    command: null,
    target: process.cwd(),
    layout: "flat",
    dryRun: false,
    postinstall: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--target") args.target = argv[++i];
    else if (a === "--layout") args.layout = argv[++i];
    else if (a === "--dry-run") args.dryRun = true;
    else if (a === "--postinstall") args.postinstall = true;
    else if (a === "--help" || a === "-h") args.command = "help";
    else if (!args.command) args.command = a;
  }
  return args;
}

async function pathExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function copyRecursive(src, dst, dryRun) {
  const stat = await fs.lstat(src);
  if (stat.isDirectory()) {
    if (!dryRun) await fs.mkdir(dst, { recursive: true });
    const entries = await fs.readdir(src);
    for (const entry of entries) {
      await copyRecursive(path.join(src, entry), path.join(dst, entry), dryRun);
    }
  } else {
    if (!dryRun) {
      await fs.mkdir(path.dirname(dst), { recursive: true });
      await fs.copyFile(src, dst);
    }
    process.stdout.write(`  ${dryRun ? "[dry] " : ""}${dst}\n`);
  }
}

function resolveTargetForArtifact(target, layout, srcName) {
  // Project-root artifacts: never moved under .claude/, never installed user-wide.
  const ROOT_ARTIFACTS = new Set([
    "AGENTS.md",
    "CLAUDE.md",
    ".claude-plugin",
    "schemas",
    "examples",
  ]);
  if (layout === "user") {
    if (ROOT_ARTIFACTS.has(srcName)) return null;
    const home = os.homedir();
    return path.join(home, ".claude", srcName);
  }
  if (layout === "claude") {
    if (ROOT_ARTIFACTS.has(srcName)) {
      return path.join(target, srcName);
    }
    return path.join(target, ".claude", srcName);
  }
  // flat
  return path.join(target, srcName);
}

async function install(args) {
  const target = path.resolve(args.target);
  if (args.layout !== "flat" && args.layout !== "claude" && args.layout !== "user") {
    console.error(`Unknown layout: ${args.layout}. Use flat, claude, or user.`);
    process.exit(2);
  }
  if (!(await pathExists(target))) {
    console.error(`Target directory does not exist: ${target}`);
    process.exit(1);
  }

  console.log(
    `${args.dryRun ? "[DRY RUN] " : ""}Installing grimoire artifacts`
  );
  console.log(`  layout : ${args.layout}`);
  console.log(`  target : ${args.layout === "user" ? path.join(os.homedir(), ".claude") : target}`);
  console.log("");

  for (const { src, required } of ARTIFACTS) {
    const srcPath = path.join(PACKAGE_ROOT, src);
    if (!(await pathExists(srcPath))) {
      if (required) {
        console.error(`Missing required artifact in package: ${src}`);
        process.exit(1);
      }
      continue;
    }
    const dstPath = resolveTargetForArtifact(target, args.layout, src);
    if (dstPath === null) continue;
    console.log(`* ${src} → ${dstPath}`);
    await copyRecursive(srcPath, dstPath, args.dryRun);
    console.log("");
  }

  console.log("Done.");
  console.log("");
  if (args.layout === "flat" || args.layout === "claude") {
    console.log("Next steps:");
    console.log("  - Restart your AI agent (Claude Code, Cursor, Codex, Aider, …)");
    console.log("  - Open AGENTS.md to see the knowledge layout.");
    console.log("  - In Claude Code, type /rattle-analyse, /rattle-suggest-config, /rattle-audit, or /rattle-build-offer.");
  } else {
    console.log("Next steps:");
    console.log("  - Restart Claude Code so it picks up the user-level skills.");
    console.log("  - Try /rattle-analyse <pricelist.xlsx> or /rattle-audit <tenant>.");
  }
}

function help() {
  console.log(
    `Usage: npx @rattleai/grimoire install [--target <path>] [--layout flat|claude|user] [--dry-run]

Drops the Rattle AI Workspace artifacts (skills/, agents/, commands/, AGENTS.md,
.claude-plugin/) into a target project or your machine-wide ~/.claude/.

Layouts:
  flat   (default): root-level skills/, agents/, commands/, AGENTS.md
  claude:           .claude/skills, .claude/agents, .claude/commands + AGENTS.md
  user:             ~/.claude/skills, ~/.claude/agents, ~/.claude/commands

Examples:
  npx @rattleai/grimoire install
  npx @rattleai/grimoire install --layout claude --target ./my-project
  npx @rattleai/grimoire install --layout user
  npx @rattleai/grimoire install --dry-run
`
  );
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.postinstall) {
    // Suppress: only used as npm postinstall on the package itself.
    return;
  }
  if (args.command === "help" || !args.command) {
    help();
    return;
  }
  if (args.command === "install") {
    await install(args);
    return;
  }
  console.error(`Unknown command: ${args.command}`);
  help();
  process.exit(2);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
