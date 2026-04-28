import argparse
import json
import os
import sys

from .client import RattleClient
from .source import list_sources

# ---------------------------------------------------------------------------
# Original commands
# ---------------------------------------------------------------------------


def cmd_test_connection(tenant, args):
    client = RattleClient(tenant)
    try:
        data = client.get("products", per_page=1)
        print(f"Connection OK for tenant '{tenant}'")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
    except Exception as e:
        print(f"Connection FAILED: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_sources(tenant, args):
    files = list_sources(tenant)
    if not files:
        print(f"No source files found for tenant '{tenant}'")
        return
    print(f"Source files for '{tenant}':")
    for f in files:
        print(f"  {f}")


# ---------------------------------------------------------------------------
# AI-powered commands
# ---------------------------------------------------------------------------


def cmd_ai_describe(tenant, args):
    """Generate AI product descriptions and push to Rattle."""
    from .tasks import describe_products

    results = describe_products(
        tenant,
        limit=args.limit,
        language=args.language,
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


def cmd_ai_classify(tenant, args):
    """Classify products using AI."""
    from .tasks import classify_products

    results = classify_products(tenant, limit=args.limit)
    print(json.dumps(results, indent=2, ensure_ascii=False))


def cmd_ai_transform(tenant, args):
    """Transform interchange data between formats using AI."""
    from .tasks import transform_interchange

    results = transform_interchange(
        tenant,
        args.source_format,
        args.target_format,
        args.data_file,
        push=args.push,
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


def cmd_ai_analyse(tenant, args):
    """Ask AI to analyse product data."""
    from .tasks import analyse_data

    analyse_data(tenant, question=args.question)


def cmd_ai_analyse_pricelist(tenant, args):
    """Analyse a pricelist using AI + consulting knowledge."""
    from .tasks import analyse_pricelist

    result = analyse_pricelist(
        tenant,
        args.source_file,
        language=args.language,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_ai_suggest_config(tenant, args):
    """Generate BOM-aware configuration recommendations."""
    from .tasks import suggest_configuration

    result = suggest_configuration(
        tenant,
        args.source_file,
        language=args.language,
        product_filter=args.product,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_ai_providers(tenant, args):
    """List available AI providers."""
    from .provider import list_providers

    print("Available AI providers:")
    for name in list_providers():
        print(f"  - {name}")
    current = os.environ.get("AI_PROVIDER", "openai")
    print(f"\nActive provider (AI_PROVIDER): {current}")


# ---------------------------------------------------------------------------
# Tenant memory commands
# ---------------------------------------------------------------------------


def cmd_memory(tenant, args):
    """Dispatch `memory <action>` subcommands."""
    from .memory import TenantMemory

    mem = TenantMemory(tenant)
    action = args.memory_action

    if action == "show":
        profile = mem.profile
        if profile:
            print(profile.rstrip())
        else:
            print(f"(no profile.md for tenant '{tenant}' at {mem.profile_path})")

        decisions = mem.load_decisions(limit=5)
        if decisions:
            print("\n## Recent decisions")
            for entry in decisions:
                ts = entry.get("timestamp", "")
                date = ts.split("T", 1)[0] if ts else ""
                text = (
                    entry.get("text")
                    or entry.get("message")
                    or json.dumps(
                        {k: v for k, v in entry.items() if k != "timestamp"},
                        ensure_ascii=False,
                    )
                )
                prefix = f"- {date} " if date else "- "
                print(f"{prefix}{text}")

        audit = mem.load_audit_history(limit=3)
        if audit:
            print("\n## Recent audit runs")
            for entry in audit:
                ts = entry.get("timestamp", "")
                n = len(entry.get("findings", []))
                print(f"- {ts}: {n} finding(s)")
        return

    if action == "edit":
        path = mem.profile_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"# {tenant} — tenant preferences\n\n", encoding="utf-8")
        editor = os.environ.get("EDITOR")
        if not editor:
            print(str(path))
            return
        import subprocess

        subprocess.call([editor, str(path)])
        return

    if action == "set-preference":
        mem.set_preference(args.key, args.value)
        print(f"preference set: {args.key}={args.value}")
        print(f"  -> {mem.profile_path}")
        return

    if action == "record-decision":
        record = mem.append_decision({"text": args.text})
        print(json.dumps(record, ensure_ascii=False))
        return

    raise SystemExit(f"unknown memory action: {action}")


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Rattle AI Workspace — AI-powered console CLI for the Rattle API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "AI provider is selected via the AI_PROVIDER env var:\n"
            "  openai (default), anthropic, ollama, custom\n\n"
            "Examples:\n"
            "  rattle acme test-connection\n"
            "  AI_PROVIDER=anthropic rattle acme ai-describe --limit 3\n"
            "  rattle acme ai-transform datanorm rattle data.json --push\n"
        ),
    )
    parser.add_argument("tenant", help="Tenant name (e.g. acme)")
    sub = parser.add_subparsers(dest="command", required=True, help="Command")

    # -- existing commands ---------------------------------------------------
    sub.add_parser("test-connection", help="Verify API connectivity")
    sub.add_parser("list-sources", help="List source files for a tenant")

    # -- AI commands ---------------------------------------------------------
    p_desc = sub.add_parser(
        "ai-describe",
        help="Generate product descriptions with AI",
    )
    p_desc.add_argument("--limit", type=int, default=5, help="Max products to process (default 5)")
    p_desc.add_argument("--language", default="de", help="Target language (default de)")

    p_cls = sub.add_parser(
        "ai-classify",
        help="Classify products with AI",
    )
    p_cls.add_argument("--limit", type=int, default=10, help="Max products to process (default 10)")

    p_xform = sub.add_parser(
        "ai-transform",
        help="Transform interchange data between formats",
    )
    p_xform.add_argument("source_format", help="Source format (datanorm, eclass, bmecat, …)")
    p_xform.add_argument("target_format", help="Target format (rattle, datanorm, …)")
    p_xform.add_argument("data_file", help="Path to JSON input file")
    p_xform.add_argument(
        "--push", action="store_true", help="POST transformed records to Rattle API"
    )

    p_analyse = sub.add_parser(
        "ai-analyse",
        help="Ask AI to analyse product data",
    )
    p_analyse.add_argument(
        "--question", default=None, help="Custom question (default: data quality audit)"
    )

    p_pricelist = sub.add_parser(
        "ai-analyse-pricelist",
        help="Analyse a pricelist for configurator anti-patterns",
    )
    p_pricelist.add_argument(
        "source_file",
        help="Source file (relative to source/<tenant>/ or absolute)",
    )
    p_pricelist.add_argument("--language", default="de", help="Output language (default de)")

    p_suggest = sub.add_parser(
        "ai-suggest-config",
        help="Generate BOM-aware configuration recommendations",
    )
    p_suggest.add_argument(
        "source_file",
        help="Source file (relative to source/<tenant>/ or absolute)",
    )
    p_suggest.add_argument("--language", default="de", help="Output language (default de)")
    p_suggest.add_argument("--product", default=None, help="Focus on a specific product name")

    sub.add_parser("ai-providers", help="List available AI providers")

    # -- tenant memory commands ---------------------------------------------
    p_mem = sub.add_parser(
        "memory",
        help="Read or update per-tenant consulting memory (profile + decisions)",
    )
    mem_sub = p_mem.add_subparsers(
        dest="memory_action",
        required=True,
        help="Memory action",
    )
    mem_sub.add_parser("show", help="Print profile.md and recent decisions / audits")
    mem_sub.add_parser("edit", help="Open profile.md in $EDITOR (or print its path)")

    p_set = mem_sub.add_parser(
        "set-preference",
        help="Upsert a preference under ## Preferences in profile.md",
    )
    p_set.add_argument("key", help="Preference key (e.g. custom-keys)")
    p_set.add_argument("value", help="Preference value (e.g. never)")

    p_dec = mem_sub.add_parser(
        "record-decision",
        help="Append a decision entry to decisions.jsonl (with UTC timestamp)",
    )
    p_dec.add_argument("text", help="Free-text decision description")

    # -- dispatch ------------------------------------------------------------
    args = parser.parse_args()

    commands = {
        "test-connection": cmd_test_connection,
        "list-sources": cmd_list_sources,
        "ai-describe": cmd_ai_describe,
        "ai-classify": cmd_ai_classify,
        "ai-transform": cmd_ai_transform,
        "ai-analyse": cmd_ai_analyse,
        "ai-analyse-pricelist": cmd_ai_analyse_pricelist,
        "ai-suggest-config": cmd_ai_suggest_config,
        "ai-providers": cmd_ai_providers,
        "memory": cmd_memory,
    }
    commands[args.command](args.tenant, args)


if __name__ == "__main__":
    main()
