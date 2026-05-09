---
name: rattle-safety-notices
description: Use this skill whenever the user is producing, auditing, or reviewing safety notices (Sicherheitshinweise, Warnhinweise) inside a Rattle technical documentation. Activates for any "safety notice", "Warnhinweis", "Sicherheitshinweis", "DANGER/WARNING/CAUTION/NOTICE", "GEFAHR/WARNUNG/VORSICHT/HINWEIS", "ISO 7010", "ISO 3864", "ANSI Z535" task. Encodes the four-level signal word ladder (DANGER/WARNING/CAUTION/NOTICE) per ISO 3864-2 and ANSI Z535.6-2011 (R2017), the SAFE warning structure (Signalwort, Art und Quelle, Folgen, Entkommen), the **five** ISO 7010 categories (warning W*, prohibition P*, mandatory M*, safe condition E*, fire protection F*) plus the **separate CLP/GHS pictogram set** (Annex V of (EC) 1272/2008), the EditorJS `safety_notice` block contract from `app/static/js/editor_safety_note.js`, and the locale-aware signal words for 32 languages from `app/utils/safety_notice_words.py`. Pair with rattle-techdoc (the host skill) and rattle-ghs-statements (for chemical-hazard statements).
license: MIT
---

# Rattle safety notices

Every safety-relevant message inside a Rattle technical documentation MUST be expressed as an EditorJS `safety_notice` block, never as plain prose with bold "Achtung!" prefixes. The block carries the signal-word level, the ISO 7010 / GHS pictogram, the locale-aware signal word, and the SAFE-principle hazard breakdown.

This skill encodes the rules and the catalogue: when to use which level, which symbol, which locale word, and which structure.

## Live API for symbol selection (use this first)

**Before picking a symbol, query the API.** The platform exposes the complete safety-logo catalogue (ISO 7010 + GHS, with EN + DE descriptions) at:

```
GET /api/v1/safety-logos[?category=warning|prohibition|mandatory|safe_condition|fire_protection|gefahrstoffe]
```

Response shape (excerpt):

```json
{
  "data": {
    "categories": [{
      "id": "warning",
      "label": "Warning (W...)",
      "files": [{
        "file": "W024_crushing_of_hands.svg",
        "code": "W024",
        "label": "W024 crushing of hands",
        "description": "Crushing of hands",
        "description_de": "Quetschgefahr für die Hände",
        "url": "/safety_logos/warning/W024_crushing_of_hands.svg"
      }]
    }]
  }
}
```

Use `description` / `description_de` to match the hazard semantically; use the returned `file` value verbatim as `safety_notice.isoSymbol.file`. **Never invent filenames or fall back to `W001_general_warning_sign.svg` without first checking whether a more specific code matches.** The audit `unmatched-iso-symbol` and `addressless-pictogram` are direct consequences of skipping this step.

For signal words, the same module exposes:

```
GET /api/v1/safety-notices/signal-words[?locale=de]
```

This is the same data as the static catalogue in `references/signal-words.md` but live. Use it to pre-fill `safety_notice.signalWord` in batch authoring (or to confirm the locale is supported before publishing the document in that locale).

The static catalogue in `references/iso-7010-symbols.md` is still useful for **offline reasoning** (which W-code applies to "crushing"?), but the live API is the source of truth for the exact filename and the human description, and it lists the manifest descriptions the `description` / `description_de` matching depends on.

## When to use this skill

Activate when the user:

- Is creating, editing, or auditing a safety notice / Warnhinweis / Sicherheitshinweis.
- Asks about signal words: DANGER / WARNING / CAUTION / NOTICE (and their German / French / etc equivalents).
- Asks about ISO 7010 symbols (W001…W097, P001…P064, M001…M057, E001…E024, F001…F010).
- Asks about ISO 3864 colour and shape rules.
- Asks about ANSI Z535.6 product-manual safety information.
- Wants to convert an existing "Achtung!" / "Wichtig!" call-out into a normative `safety_notice` block.
- Wants the locale-resolved signal word for a language Rattle supports.

For chemical hazard statements (H/P/EUH codes, GHS pictograms in chemical context), use `rattle-ghs-statements`. For the wider technical-documentation chapter structure, use `rattle-techdoc`.

## The four-level signal-word ladder

Normative reference: ISO 3864-2:2016 Annex B + ANSI Z535.6-2011 (R2017).

| Level | Meaning | Colour | When to use |
|---|---|---|---|
| **DANGER** | Imminent hazard → death or serious injury | Red (`#DC143C` / `#7F0000` — rendering approximation; the normative red of ISO 3864-2 Annex B is RAL 3001 / Pantone 485) | The hazard is immediate AND severe AND involves serious injury or death. Reserved for truly imminent hazards. |
| **WARNING** | Potential hazardous situation → death or serious injury | Orange (`#FF8C00` — rendering approximation; the normative orange of ISO 3864-2 is RAL 2010 / Pantone 152) | Possible (not imminent) and could result in death or serious injury. Most safety notices in industrial machine documentation are WARNING. |
| **CAUTION** | Potential hazardous situation → minor / moderate injury | Yellow (`#FFD700` — rendering approximation; the normative yellow of ISO 3864-2 is RAL 1003 / Pantone 109) | Could cause minor / moderate injury (cuts, bruises, abrasions, minor burns). |
| **NOTICE** | Property damage or functional impairment possible | Blue (`#1E90FF`) — Rattle / ANSI Z535.6 convention; ISO 3864-2 does **not** standardise a NOTICE colour | No personal injury, but property damage, data loss, performance degradation. |

> **The hex codes above are display approximations for the digital renderer.** Normative colour conformity for printed safety labels requires the exact RAL / Pantone references in ISO 3864-2 Annex B (red RAL 3001, yellow RAL 1003, blue RAL 5005, green RAL 6032, etc.). Do not cite the hex values as normative.

> **Rule of thumb.** If unsure between DANGER and WARNING, use WARNING. DANGER is rare and reserved for truly imminent hazards (energised live conductors that the user is about to touch, etc.). Over-using DANGER dilutes its signal value.

## The SAFE principle (Signalwort, Art und Quelle, Folgen, Entkommen)

Every safety notice has a four-part body. The German mnemonic SAFE expands to: **S**ignalwort · **A**rt und Quelle der Gefahr · **F**olgen bei Nichtbeachtung · **E**ntkommen / Vermeidung. The English equivalent is the ANSI Z535.6 four-part body.

```
S — Signal word            (level + signalWord)
        ↓
A — Hazard type AND source (title — name BOTH the type and the physical source)
        ↓
F — Consequences if not avoided
        ↓
E — Avoidance / Escape — imperative instructions
```

In the EditorJS block, this maps to:

- `data.level` → signal word level
- `data.title` → short hazard label (3–8 words) naming **type and source** ("Quetschgefahr **durch bewegliche Maschinenteile**")
- `data.hazard` → one-sentence hazard description
- `data.consequences[]` → bullet list of "what happens if ignored"
- `data.avoidance[]` → bullet list of imperative-mood instructions ("E" — Entkommen / Vermeidung)

Example (DE):

```json
{
  "type": "safety_notice",
  "data": {
    "level": "warning",
    "title": "Quetschgefahr durch bewegliche Maschinenteile",
    "hazard": "Bewegliche Teile können Hände und Finger einklemmen.",
    "consequences": [
      "Schwere Quetschverletzungen",
      "Knochenbrüche"
    ],
    "avoidance": [
      "Vor dem Eingriff Maschine stillsetzen.",
      "Gegen Wiedereinschalten sichern.",
      "Schutzhandschuhe tragen."
    ],
    "ref": "Kap. 9.4",
    "isoSymbol": {
      "category": "warning",
      "file": "W024_crushing_of_hands.svg"
    },
    "showAlertSymbol": true,
    "signalWord": "WARNUNG"
  }
}
```

The same hazard in EN auto-translates the signal word but **everything else is content-translated separately** (the translator service handles only the user content, not the normative signal word):

```json
{
  "type": "safety_notice",
  "data": {
    "level": "warning",
    "title": "Crushing hazard from moving machine parts",
    "hazard": "Moving parts can crush hands and fingers.",
    "consequences": ["Serious crushing injuries", "Bone fractures"],
    "avoidance": [
      "Stop machine before reaching into the work area.",
      "Secure against unintended restart.",
      "Wear protective gloves."
    ],
    "ref": "Sec. 9.4",
    "isoSymbol": {
      "category": "warning",
      "file": "W024_crushing_of_hands.svg"
    },
    "showAlertSymbol": true,
    "signalWord": "WARNING"
  }
}
```

## The five ISO 7010 categories (plus the separate CLP/GHS pictogram set)

Symbol catalogue location in Rattle: `app/static/img/safety_logos/<category>/<file>.svg`. Use the dedicated category folder names exactly as listed below; both German aliases (`warnzeichen`, `verbotszeichen`, `gebotszeichen`, `rettungszeichen`, `brandschutz`) and English (`warning`, `prohibition`, `mandatory`, `safe_condition`, `fire_protection`) exist. **For the EditorJS block, always use the English name.**

| Category | EditorJS `isoSymbol.category` | Code prefix | Shape | Colour | Examples |
|---|---|---|---|---|---|
| **Warning** (Gefahrenzeichen) | `warning` | W001…W097 | yellow triangle, black border + symbol | yellow + black | crushing, hot surface, electricity, laser, magnetic field, automatic start-up |
| **Prohibition** (Verbotszeichen) | `prohibition` | P001…P064 | round, white background, red border + diagonal slash | red + black on white | no smoking, no entry, do not touch, no climbing |
| **Mandatory action** (Gebotszeichen) | `mandatory` | M001…M057 | round, blue background, white symbol | blue + white | wear gloves, wear ear protection, refer to manual, wear safety footwear |
| **Safe condition** (Rettungszeichen) | `safe_condition` | E001…E024 | square / rectangle, green background, white symbol | green + white | emergency exit, first aid, safety shower, eyewash station |
| **Fire protection** (Brandschutzzeichen) | `fire_protection` | F001…F010 | square, red background, white symbol | red + white | fire extinguisher, fire alarm, fire hose reel |

ISO 7010:2019 defines exactly these **five** categories. The catalogue per category lives in `references/iso-7010-symbols.md`. Always pick by the W/P/M/E/F code, not by visual interpretation.

### CLP / GHS pictograms — **separate normative basis, NOT ISO 7010**

| Container | EditorJS `isoSymbol.category` (presentational only) | Code prefix | Shape | Colour | Normative basis |
|---|---|---|---|---|---|
| **GHS pictograms** (Gefahrstoffe) | `gefahrstoffe` | GHS01…GHS09 | diamond on point, white background, red border + black symbol | red border, black symbol | **CLP Regulation (EC) 1272/2008 Annex V** + UN GHS — *not* ISO 7010 |

> **Important.** GHS pictograms come from the CLP Regulation, not ISO 7010. They have a different shape (diamond on point), a different normative basis, and a different scope (chemical labelling). The Rattle frontend exposes them under `safety_notice.isoSymbol.category="gefahrstoffe"` for **presentational convenience** when a single safety notice mixes a CLP pictogram with an ISO 7010 hazard, but the **canonical container for chemical hazards is the dedicated `hp_statement` block** under `rattle-ghs-statements`. Document any document/template that asserts ISO 7010 conformity for a GHS pictogram as a finding (`mixed-normative-basis`); the audit will reject it.

> **Filename convention warning.** The `gefahrstoffe` folder ships **mnemonic** filenames (`GHS-pictogram-flamme.svg`, `GHS-pictogram-skull.svg`, …) — *not* `GHS01.svg` … `GHS09.svg`. The numeric form (`GHS06.svg`) lives in a different path (`/static/img/ghs/`) and is unrelated to the `safety_notice` block. Always discover the correct filename by `GET /api/v1/safety-logos?category=gefahrstoffe` and use the returned `file` value verbatim — guessing the numeric form will 404 in the renderer.

## Locale-aware signal words

Source: `app/utils/safety_notice_words.py`. Rattle ships normative signal words for **32 locales** (plus a `default` alias). Every `safety_notice` block can omit `signalWord` and the renderer resolves it from the document locale. Specifying `signalWord` is only needed when overriding for a regional variant.

The 32 locales (and the four signal words per locale) are listed in `references/signal-words.md`. Selected examples:

| Locale | DANGER | WARNING | CAUTION | NOTICE |
|---|---|---|---|---|
| `de` | GEFAHR | WARNUNG | VORSICHT | HINWEIS |
| `en` | DANGER | WARNING | CAUTION | NOTICE |
| `fr` | DANGER | AVERTISSEMENT | ATTENTION | AVIS |
| `es` | PELIGRO | ADVERTENCIA | PRECAUCIÓN | AVISO |
| `it` | PERICOLO | AVVERTENZA | ATTENZIONE | AVVISO |
| `pt` | PERIGO | ATENÇÃO | CUIDADO | AVISO |
| `nl` | GEVAAR | WAARSCHUWING | VOORZICHTIGHEID | KENNISGEVING |
| `pl` | NIEBEZPIECZEŃSTWO | OSTRZEŻENIE | OSTROŻNOŚĆ | OGŁOSZENIE |
| `ja` | 危険 | 警告 | 注意 | 通知 |
| `zh` | 危险 | 警告 | 注意 | 须知 |

Locales with no exact mapping fall through to the closest available (e.g. `nb` → `da`, `pt-br` → `pt`).

## Workflow — converting "Achtung!" to a `safety_notice`

When an input manual contains a non-normative warning like:

> ⚠ **ACHTUNG! Bewegliche Teile.** Vor Wartungsarbeiten Strom abschalten und gegen Wiedereinschalten sichern. Sonst Quetschgefahr für Hände!

Walk these steps:

1. **Pick the level.** "Quetschgefahr für Hände" + serious injury possible = `warning` (not `danger`, since it is not imminent — only when the user is currently working on the machine).
2. **Query the symbol catalogue.** `GET /api/v1/safety-logos?category=warning` → scan the `files[]` array for a `description` / `description_de` matching "crushing of hands" / "Quetschgefahr Hände". The match is `W024 / W024_crushing_of_hands.svg`. **Always pick by API match, never by guess.** If the API returns no good match, only then fall back to W001 (`W001_general_warning_sign.svg`) — and flag the imprecision in the `notes` field.
3. **Decompose into SAFE.** title = "Quetschgefahr durch bewegliche Maschinenteile". hazard = "Bewegliche Teile können Hände und Finger einklemmen.". consequences = ["Schwere Quetschverletzungen", "Knochenbrüche"]. avoidance = ["Vor Wartungsarbeiten Strom abschalten.", "Gegen Wiedereinschalten sichern.", "Schutzhandschuhe tragen."].
4. **Set `ref`.** Cross-reference the chapter the hazard belongs to. For maintenance-context warnings, `ref: "Kap. 9.4"`.
5. **(Optional) Resolve the locale signal word.** `GET /api/v1/safety-notices/signal-words?locale=de` → `signal_words.warning = "WARNUNG"`. Set `safety_notice.signalWord` to this value when you author multiple locales in one batch.
6. **Emit the block.** As shown in the example above (with `isoSymbol.category="warning"`, `isoSymbol.file="W024_crushing_of_hands.svg"` from the API result).
7. **Replace the original prose.** Remove the entire "ACHTUNG! …" paragraph; the `safety_notice` block carries the message normatively.

### One-shot Python helper

```python
import requests

def pick_iso_symbol(api_base, token, category, hazard_keywords, locale="en"):
    """Return the best (file, code, description) for a hazard description."""
    r = requests.get(
        f"{api_base}/api/v1/safety-logos",
        params={"category": category},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    r.raise_for_status()
    files = r.json()["data"]["categories"][0]["files"]
    desc_field = "description_de" if locale.startswith("de") else "description"
    needle = " ".join(hazard_keywords).lower()
    scored = sorted(
        files,
        key=lambda f: -sum(1 for w in needle.split() if w in (f.get(desc_field) or "").lower()),
    )
    return scored[0] if scored else None
```

## Audit-related rules this skill enforces

When this skill is loaded, these violations should be flagged:

- `unstructured-warnings` — `{type: "warning"}` with safety-relevant content.
- `non-normative-warning-words` — "Achtung!", "Wichtig!", "Important:" prefixes inline.
- `addressless-pictogram` — image whose URL hits `/safety_logos/` or `/ghs/` without an adjacent W-/P-/M-/E-/F-/GHS code.
- `wrong-level-for-severity` — DANGER used for non-imminent hazards (heuristic: DANGER appears > 5× per chapter).
- `incomplete-safe-structure` — `safety_notice` block without all of `title` / `hazard` / `consequences[]` / `avoidance[]`.
- `unmatched-iso-symbol` — `isoSymbol.file` not present in the symbol catalogue for the declared `isoSymbol.category`. Verify by `GET /api/v1/safety-logos?category=<cat>` and confirming the `file` value appears in `categories[].files[].file`.
- `default-fallback-symbol` — `isoSymbol.file` is `W001_general_warning_sign.svg` (or another generic) when a more specific code is available in the API response. Re-run the symbol picker against `description` / `description_de`.

## Output contract — `safety-notices.json`

When asked to enumerate or produce safety notices in batch, output:

```json
{
  "domain": "safety_notice",
  "count": 1,
  "notices": [
    {
      "id": "sn-pfm3200-9.4-crushing",
      "structure_block_slug": "sec-9-4-maintenance-tasks",
      "level": "warning",
      "title_de": "Quetschgefahr durch bewegliche Maschinenteile",
      "title_en": "Crushing hazard from moving machine parts",
      "hazard_de": "...",
      "hazard_en": "...",
      "consequences_de": ["..."],
      "consequences_en": ["..."],
      "avoidance_de": ["..."],
      "avoidance_en": ["..."],
      "iso_symbol": {"category": "warning", "code": "W024",
                     "file": "W024_crushing_of_hands.svg"},
      "ref": "Kap. 9.4",
      "block_de": {"type": "safety_notice", "data": {...}},
      "block_en": {"type": "safety_notice", "data": {...}}
    }
  ],
  "notes": []
}
```

## Related references

- **API** `GET /api/v1/safety-logos[?category=...]` — live catalogue with EN+DE descriptions for hazard matching. **Source of truth.**
- **API** `GET /api/v1/safety-notices/signal-words[?locale=...]` — live signal-word lookup.
- `references/iso-7010-symbols.md` — full SVG-filename catalogue per category (offline reference).
- `references/signal-words.md` — 32 locale signal-word table (offline reference).
- `references/safe-principle.md` — extended SAFE-principle authoring guide with bad-vs-good rewrite examples.
- `rattle-techdoc/SKILL.md` — host skill that uses this one.
- `rattle-ghs-statements/SKILL.md` — chemical hazards (sister skill).
- `rattle-api/references/api-reference.md` — full Safety Reference endpoint reference.
