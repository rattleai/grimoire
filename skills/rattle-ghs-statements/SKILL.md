---
name: rattle-ghs-statements
description: Use this skill whenever the user is producing, auditing, or reviewing chemical hazard statements (H/P/EUH codes) and GHS pictograms inside a Rattle technical documentation. Activates for any "GHS", "H-statement", "P-statement", "EUH", "CLP", "Gefahrstoff", "Sicherheitsdatenblatt", "Hazard statement", "Precautionary statement", "Pictogram" task. Encodes the EU CLP Regulation (EC) 1272/2008 vocabulary, the 9 GHS pictograms (GHS01–GHS09), the H-code → pictogram mapping, the EditorJS `hp_statement` block contract from `app/static/js/editor_hp_statement.js`, the locale-resolved statement text for 24 EU locales, combined H-statements (e.g. H300+H310), and enhanced statements with placeholders. Pair with rattle-techdoc (host skill) and rattle-safety-notices (sister skill for non-chemical safety notices).
license: MIT
---

# Rattle GHS / H&P statements

Every chemical hazard reference in a Rattle technical documentation MUST be expressed as an EditorJS `hp_statement` block. The block carries a list of normative codes (H300, P301, EUH014…), and the renderer resolves the **official locale text** + the GHS pictogram automatically. Statement text is **not user-editable and MUST NOT be AI-translated**: it is regulated, locale-resolved from the CLP Regulation tables.

This skill encodes the rules and the catalogue: what an H-code / P-code / EUH-code means, which GHS pictogram it carries, how combined statements work, and how the EditorJS block consumes them.

## When to use this skill

Activate when the user:

- Mentions GHS, CLP, H-statement, P-statement, EUH-statement, hazard pictogram.
- Asks about chemical hazard text in a technical documentation (cleaning agents, lubricants, coolants, refrigerants, batteries, paints, adhesives, …).
- Asks about Sections 11.5 (`sec-11-5-hazardous-substances`) or any section that lists chemicals.
- Asks for the German / French / Italian / etc translation of an H-code text → tell them it is not translated, it is **resolved** from the official tables.
- Wants to add a hazard pictogram to a chapter — clarify whether it is a workplace ISO 7010 sign (use `safety_notice`) or a chemical CLP pictogram (use `hp_statement`).

For non-chemical safety messages (machine hazards), use `rattle-safety-notices`. For the wider chapter structure, use `rattle-techdoc`.

## Legal basis

EU CLP Regulation **(EC) No 1272/2008** on classification, labelling and packaging of substances and mixtures. Annex I defines the hazard classes; Annex III defines the H-statement codes; Annex IV defines the P-statement codes; Annex V defines the GHS pictograms.

Statement data in Rattle comes from the open-source **mhchem/hpstatements** project (CC BY 4.0), stored as JSON files in `app/static/data/hp_statements/hpstatements-<lang>-latest.json`.

## The H/P/EUH code families

| Code prefix | Family | Meaning |
|---|---|---|
| **H200–H290** | Physical hazards | Explosive (H200–H208), flammable (H220–H229, H242), oxidising (H270–H272), pressurised (H280–H281), reactive with water (H260–H261), corrosive to metals (H290), …. |
| **H300–H373** | Health hazards | Acute toxicity (H300–H332), corrosion / irritation (H314–H319), sensitisation (H317, H334), CMR (H340, H350, H360), aspiration (H304), specific organ toxicity (H370–H372), …. |
| **H400–H413** | Environmental hazards | Aquatic toxicity, ozone layer hazard. |
| **EUH001–EUH401** | EU-specific supplemental | Explosive when dry (EUH001), flammable mixed with water (EUH014), can become highly flammable (EUH019), …. |
| **P101–P102** | Precautionary general | "Read label", "Keep out of reach of children". |
| **P201–P284** | Precautionary prevention | Prevention measures (handling, PPE). |
| **P301–P391** | Precautionary response | First-aid, fire-response, accidental-release. |
| **P401–P420** | Precautionary storage | Storage temperature, segregation. |
| **P501–P503** | Precautionary disposal | Waste-stream identification. |

Full code-text catalogue per locale lives in `references/hp-statement-codes.md` (top 50 most-used) and `references/hp-statement-locales.md` (locale overview).

## The 9 GHS pictograms

Source: `app/static/data/ghs_pictogram_map.json` (open data, public domain regulatory mapping).

| ID | Symbol | Meaning | Typical H-codes |
|---|---|---|---|
| **GHS01** | exploding bomb | Explosive | H200–H208, H240–H241 |
| **GHS02** | flame | Flammable | H220–H229, H242, H250–H252, H260–H261 |
| **GHS03** | flame over circle | Oxidising | H270–H272 |
| **GHS04** | gas cylinder | Gas under pressure | H280–H281 |
| **GHS05** | corrosion | Corrosive to metals / skin / eyes | H290, H314, H318 |
| **GHS06** | skull and crossbones | Acute toxicity (severe) | H300–H301, H310–H311, H330–H331 |
| **GHS07** | exclamation mark | Health hazard (less severe) | H302, H312, H315, H317, H319, H332, H335, H336, H420 |
| **GHS08** | health hazard / silhouette | Serious health hazard (CMR, organ toxicity, aspiration) | H304, H334, H340, H341, H350, H351, H360, H361, H362, H370–H373 |
| **GHS09** | environment | Environmental hazard | H400, H410, H411 |

**The mapping is automatic.** When you set `data.codes: ["H315"]` on an `hp_statement` block, the renderer looks up `H315 → GHS07` from `ghs_pictogram_map.json` and displays the pictogram. You do not specify pictograms manually.

For SVG sources see `app/static/img/ghs/GHS01.svg` … `GHS09.svg` in rattleapp.

## The `hp_statement` EditorJS block

```json
{
  "type": "hp_statement",
  "data": {
    "codes": ["H315"],
    "combinedKey": "",
    "isCombined": false,
    "enhancedSlots": {},
    "resolvedLocale": "de",
    "resolvedText": "Verursacht Hautreizungen."
  }
}
```

Field reference:

| Field | Type | Required | Notes |
|---|---|---|---|
| `codes` | string[] | yes | Array of H/P/EUH codes. Validated against the loaded code set per locale. |
| `combinedKey` | string | optional | When the hazards are combined into a single statement (e.g. `"H300+H310"`), this is the combined-statement lookup key. |
| `isCombined` | bool | optional | `true` when the statement is a combined entry (`combinedKey` set). |
| `enhancedSlots` | object | optional | Map of slot index → value for enhanced statements. Example: `{"1": "beim Einatmen"}` for `H340`. |
| `resolvedLocale` | string | rendered | The locale used for resolution (set by the renderer or pre-cached). |
| `resolvedText` | string | rendered | The official text in `resolvedLocale`. Set by the renderer; safe to leave empty in input — but if you pre-cache, the value MUST match the official text byte-for-byte. |

> **Cardinal rule.** Never hand-edit `resolvedText`. If the renderer does not yet know the locale, leave it empty. The server-side helper `get_hp_statement_text(code, locale, slots)` from `app/utils/hp_statements.py` is the single source of truth.

## Combined statements

CLP Annex III lists **combined statements** that merge two or more H-codes into a single normative sentence. Example:

| Combined key | Locale (de) | Locale (en) |
|---|---|---|
| `H300+H310` | Lebensgefahr bei Verschlucken oder Hautkontakt. | Fatal if swallowed or in contact with skin. |
| `H301+H311` | Giftig bei Verschlucken oder Hautkontakt. | Toxic if swallowed or in contact with skin. |
| `H300+H310+H330` | Lebensgefahr bei Verschlucken, Hautkontakt oder Einatmen. | Fatal if swallowed, in contact with skin or if inhaled. |
| `H315+H319` | Verursacht Haut- und Augenreizungen. | Causes skin and eye irritation. |
| `H332+H335` | Gesundheitsschädlich beim Einatmen. Kann die Atemwege reizen. | Harmful if inhaled. May cause respiratory irritation. |

To use, set:

```json
{
  "type": "hp_statement",
  "data": {
    "codes": ["H300", "H310"],
    "combinedKey": "H300+H310",
    "isCombined": true,
    "resolvedLocale": "de",
    "resolvedText": ""
  }
}
```

## Enhanced statements with slots

Some H-statements carry `{1}` / `{2}` placeholders for the route of exposure or the affected organ. Example:

| Code | Statement text (en) |
|---|---|
| `H340` | May cause genetic defects {1}. |
| `H340-1` | May cause genetic defects if it is conclusively proven that no other route of exposure causes the hazard. |

Enhanced statements use the `enhancedSlots` field:

```json
{
  "type": "hp_statement",
  "data": {
    "codes": ["H340"],
    "isCombined": false,
    "enhancedSlots": {"1": "beim Einatmen"},
    "resolvedLocale": "de",
    "resolvedText": ""
  }
}
```

The renderer applies `resolve_hp_statement_slots(text, {"1": "beim Einatmen"})` and produces:

> *"Kann genetische Defekte verursachen beim Einatmen."*

## Locale resolution

H/P/EUH text is shipped per-locale as `app/static/data/hp_statements/hpstatements-<lang>-latest.json`. Locales available:

`bg`, `cs`, `da`, `de`, `el`, `en`, `es`, `et`, `fi`, `fr`, `ga`, `hr`, `hu`, `it`, `lt`, `lv`, `mt`, `nl`, `pl`, `pt`, `ro`, `sk`, `sl`, `sv`.

Norwegian Bokmål (`nb`), Norwegian Nynorsk (`nn`), generic Norwegian (`no`) all alias to `da` (Danish).
`pt-br` and `pt-pt` alias to `pt`. `en-us`, `en-gb` alias to `en`. `es-es`, `es-mx` alias to `es`. Etc — see `app/utils/hp_statements.py` `_LOCALE_ALIASES`.

Fallback chain: `xx-YY` → alias → primary subtag → `en`.

## Workflow — adding hazardous-substance statements to Section 11.5

1. **Identify the substance.** Get its trade name + CAS no + the SDS H/P statements from Section 2 of the safety data sheet.
2. **Pick the H-codes.** From SDS Section 2.2 ("Label elements"). These are normative — copy verbatim.
3. **Pick the P-codes.** From SDS Section 2.2 ("Precautionary statements"). Group into prevention (P2xx), response (P3xx), storage (P4xx), disposal (P5xx).
4. **Check for combined statements.** If two H-codes have a CLP-defined combined key, prefer the combined block over two single-code blocks.
5. **Emit the blocks.** One `hp_statement` block per code (or combined-key group). Group H-codes first, then P-codes, in code order.
6. **Insert in Section 11.5** under the substance heading. Pre-amble paragraph: substance name, CAS no, where used in the machine.

Example output for a cleaning agent (H315, H319, P264, P302+P352, P305+P351+P338):

```json
[
  {"type": "header", "data": {"text": "Reinigungsmittel ABC-100", "level": 4}},
  {"type": "paragraph", "data": {"text": "<strong>CAS-Nr.:</strong> 1234-56-7. <strong>Verwendung:</strong> Reinigung der Spindelaufnahme nach jedem Werkzeugwechsel."}},
  {"type": "hp_statement", "data": {"codes": ["H315"], "isCombined": false, "resolvedLocale": "de", "resolvedText": ""}},
  {"type": "hp_statement", "data": {"codes": ["H319"], "isCombined": false, "resolvedLocale": "de", "resolvedText": ""}},
  {"type": "hp_statement", "data": {"codes": ["P264"], "isCombined": false, "resolvedLocale": "de", "resolvedText": ""}},
  {"type": "hp_statement", "data": {"codes": ["P302", "P352"], "combinedKey": "P302+P352", "isCombined": true, "resolvedLocale": "de", "resolvedText": ""}},
  {"type": "hp_statement", "data": {"codes": ["P305", "P351", "P338"], "combinedKey": "P305+P351+P338", "isCombined": true, "resolvedLocale": "de", "resolvedText": ""}}
]
```

## Audit-related rules this skill enforces

- `addressless-pictogram` — GHS pictogram in an `image` block without an `hp_statement` peer.
- `inline-hp-text` — Paragraph hand-typed with H/P-code text (e.g. "H315: Verursacht Hautreizungen.") instead of an `hp_statement` block.
- `unknown-hp-code` — `codes` contains a code not in the active locale's table.
- `untranslated-hp-resolved-text` — `resolvedText` set in one locale but document is being rendered in another locale.

## Output contract — `hp-statements.json`

```json
{
  "domain": "hp_statement",
  "substance": {
    "name": "Reinigungsmittel ABC-100",
    "cas": "1234-56-7",
    "usage": "Reinigung der Spindelaufnahme"
  },
  "h_codes": ["H315", "H319"],
  "p_codes": ["P264", "P302+P352", "P305+P351+P338"],
  "ghs_pictograms": ["GHS07"],
  "blocks_de": [...],
  "blocks_en": [...]
}
```

## Related references

- `references/hp-statement-codes.md` — top 50 most-used H/P/EUH codes with EN + DE text and GHS mapping.
- `references/hp-statement-locales.md` — full list of available locales and aliases.
- `references/ghs-mapping.md` — H-code → GHS pictogram mapping reference.
- `rattle-techdoc/SKILL.md` — host skill.
- `rattle-safety-notices/SKILL.md` — non-chemical safety notices.
