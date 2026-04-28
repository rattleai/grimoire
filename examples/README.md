# Examples — golden I/O for Rattle workflows

Synthetic, end-to-end input → output pairs for every workflow in the bundle. Used by:

- AI agents to anchor on the expected shape of each contract.
- Humans to sanity-check a setup (`make example` or by-hand walk-throughs).
- Validators (`scripts/`) to confirm schema compliance.

All data here is **fully synthetic** (Widget Pro, acme tenant, 17/19-inch wheels). No real tenants, no real prices, no real part numbers.

## Files

| File | Workflow | Schema |
|---|---|---|
| `pricelist-input.json` | input to `rattle-pricelist-analysis` | — |
| `pricelist-anti-patterns.json` | output of `scripts/detect_anti_patterns.py pricelist-input.json` | — |
| `recommendation.json` | output of `rattle-suggest-config` | `schemas/recommendation.schema.json` |
| `audit-findings.json` | output of `rattle-audit/scripts/audit_runner.py` | `schemas/audit-findings.schema.json` |
| `offer-template.json` | output of `rattle-document-templates` | `schemas/offer-template.schema.json` |
| `apply-operations.json` | output of `system_prompt_apply_config` | `schemas/apply-operations.schema.json` |
| `tenant-profile.md` | example `memory/<tenant>/profile.md` | — |

## End-to-end walk-through

```bash
# 1. Detect deterministic anti-patterns in the pricelist:
python skills/rattle-pricelist-analysis/scripts/detect_anti_patterns.py examples/pricelist-input.json
# expect: matches against examples/pricelist-anti-patterns.json

# 2. Validate the recommendation against the schema:
python -c "import json,sys,jsonschema; \
  schema=json.load(open('schemas/recommendation.schema.json')); \
  doc=json.load(open('examples/recommendation.json')); \
  jsonschema.validate(doc, schema); print('valid')"

# 3. Validate the recommendation against the rules:
python skills/rattle-apply-config/scripts/validate_recommendation.py examples/recommendation.json
# expect: {"valid": true, "violations": []}

# 4. Validate the apply-operations:
python -c "import json,sys,jsonschema; \
  schema=json.load(open('schemas/apply-operations.schema.json')); \
  doc=json.load(open('examples/apply-operations.json')); \
  jsonschema.validate(doc, schema); print('valid')"
```

## How to use these in prompts

When constructing a prompt for any of the workflow skills, append the matching example as a "here is what the output should look like" anchor. The Skills already document the contracts; the example makes the shape concrete.
