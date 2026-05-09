# H/P statement locales — supported languages

The Rattle distribution ships official CLP (EC 1272/2008) H/P/EUH statement texts for **24 EU locales** plus locale aliases. Source files: `app/static/data/hp_statements/hpstatements-<lang>-latest.json`.

> **Live API.** For runtime locale resolution, call `GET /api/v1/hp-statements?locale=<locale>` — the endpoint applies the same alias / fallback chain documented below and returns the resolved dictionary. A 200 with a `count > 0` confirms the locale is supported. See `rattle-api/references/api-reference.md` § Safety Reference.

## Primary locales

| Locale | Language | File present |
|---|---|---|
| `bg` | Bulgarian | hpstatements-bg-latest.json |
| `cs` | Czech | hpstatements-cs-latest.json |
| `da` | Danish | hpstatements-da-latest.json |
| `de` | German | hpstatements-de-latest.json |
| `el` | Greek | hpstatements-el-latest.json |
| `en` | English (default) | hpstatements-en-latest.json |
| `es` | Spanish | hpstatements-es-latest.json |
| `et` | Estonian | hpstatements-et-latest.json |
| `fi` | Finnish | hpstatements-fi-latest.json |
| `fr` | French | hpstatements-fr-latest.json |
| `ga` | Irish | hpstatements-ga-latest.json |
| `hr` | Croatian | hpstatements-hr-latest.json |
| `hu` | Hungarian | hpstatements-hu-latest.json |
| `it` | Italian | hpstatements-it-latest.json |
| `lt` | Lithuanian | hpstatements-lt-latest.json |
| `lv` | Latvian | hpstatements-lv-latest.json |
| `mt` | Maltese | hpstatements-mt-latest.json |
| `nl` | Dutch | hpstatements-nl-latest.json |
| `pl` | Polish | hpstatements-pl-latest.json |
| `pt` | Portuguese | hpstatements-pt-latest.json |
| `ro` | Romanian | hpstatements-ro-latest.json |
| `sk` | Slovak | hpstatements-sk-latest.json |
| `sl` | Slovenian | hpstatements-sl-latest.json |
| `sv` | Swedish | hpstatements-sv-latest.json |

## Locale aliases

Source: `app/utils/hp_statements.py` `_LOCALE_ALIASES`.

| Alias | Resolves to | Note |
|---|---|---|
| `nb` (Norwegian Bokmål) | `da` (Danish) | Closest available locale |
| `nn` (Norwegian Nynorsk) | `da` | |
| `no` (Generic Norwegian) | `da` | |
| `pt-br` | `pt` | Brazilian Portuguese → Portuguese |
| `pt-pt` | `pt` | Iberian Portuguese → Portuguese |
| `en-us` | `en` | US English → English |
| `en-gb` | `en` | British English → English |
| `es-es` | `es` | Spain Spanish → Spanish |
| `es-mx` | `es` | Mexican Spanish → Spanish |
| `fr-fr` | `fr` | France French → French |
| `fr-be` | `fr` | Belgian French → French |
| `de-de` | `de` | Germany German → German |
| `de-at` | `de` | Austrian German → German |
| `de-ch` | `de` | Swiss German → German |
| `nl-be` | `nl` | Belgian Dutch → Dutch |
| `nl-nl` | `nl` | Netherlands Dutch → Dutch |

## Resolution algorithm

The Python helper `get_hp_statement_text(code, locale, slots)` walks:

1. Normalise `locale` (replace `_` with `-`, lower-case).
2. If exact alias found → use mapped locale.
3. Else if primary subtag (e.g. `de` from `de-CH`) is itself an alias → use that.
4. Try the resolved code in the language file.
5. If `slots` provided, try the *enhanced* variant first (e.g. `H340-1`).
6. Fall back to `en` if all else fails.
7. Return `None` if the code is unknown even in `en`.

For combined statements, `get_combined_hp_statement(combined_key, locale)` does the same walk with the combined key.

## Enhanced variants

Codes with `{1}` / `{2}` placeholders have **enhanced** entries in `app/static/data/hp_statements/enhanced/hpstatements-<lang>-latest.json`. These spell out specific routes of exposure / affected organs:

- `H340-1` — May cause genetic defects if it is conclusively proven that no other route of exposure causes the hazard.
- `H340-2` — May cause genetic defects when ingested.
- `H372-1` — Causes damage to organs through prolonged or repeated exposure.

When `enhancedSlots` is provided in the EditorJS `hp_statement` block, the renderer chooses the enhanced variant whose text contains the `{1}` placeholder, then substitutes.

## How to choose the original locale

Per MRL / MVO §1.7.4.1, the technical documentation has an *original-language version* and zero or more translations. For the H/P statements specifically:

- **Always set the document's primary locale on creation.** The renderer uses that locale by default.
- **Do not pre-cache `resolvedText`.** Leave it empty in the input. The server resolves at render time.
- **For EU placement:** make sure the locale of the country of placement is among the document's locales. The same machine sold into DE + FR + NL needs three locale renderings of the same `hp_statement` blocks; the codes themselves are locale-independent.
