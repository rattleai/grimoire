---
name: rattle-safety-notices
description: Use this skill whenever the user is producing, auditing, or reviewing safety notices (Sicherheitshinweise, Warnhinweise) inside a Rattle technical documentation. Activates for any "safety notice", "Warnhinweis", "Sicherheitshinweis", "DANGER/WARNING/CAUTION/NOTICE", "GEFAHR/WARNUNG/VORSICHT/HINWEIS", "ISO 7010", "ISO 3864", "ANSI Z535" task. Encodes the four-level signal word ladder (DANGER/WARNING/CAUTION/NOTICE) per ISO 3864-2 and ANSI Z535.6, the SAFE warning structure, the six ISO 7010 categories (warning W*, prohibition P*, mandatory M*, safe condition E*, fire protection F*, hazardous materials), the EditorJS `safety_notice` block contract from `app/static/js/editor_safety_note.js`, and the locale-aware signal words for 30+ languages from `app/utils/safety_notice_words.py`. Pair with rattle-techdoc (the host skill) and rattle-ghs-statements (for chemical-hazard statements).
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

Normative reference: ISO 3864-2:2016 Annex B + ANSI Z535.6:2023.

| Level | Meaning | Colour | When to use |
|---|---|---|---|
| **DANGER** | Imminent hazard → death or serious injury | Red (#DC143C / 7F0000) | The hazard is immediate AND severe AND involves serious injury or death. Reserved for truly imminent hazards. |
| **WARNING** | Potential hazardous situation → death or serious injury | Orange (#FF8C00) | Possible (not imminent) and could result in death or serious injury. Most safety notices in industrial machine documentation are WARNING. |
| **CAUTION** | Potential hazardous situation → minor / moderate injury | Yellow (#FFD700) | Could cause minor / moderate injury (cuts, bruises, abrasions, minor burns). |
| **NOTICE** | Property damage or functional impairment possible | Blue (#1E90FF) | No personal injury, but property damage, data loss, performance degradation. |

> **Rule of thumb.** If unsure between DANGER and WARNING, use WARNING. DANGER is rare and reserved for truly imminent hazards (energised live conductors that the user is about to touch, etc.). Over-using DANGER dilutes its signal value.

## The SAFE principle

Every safety notice has a four-part body:

```
SIGNAL WORD — short hazard label
        ↓
Signal Word + Hazard Type
        ↓
Consequences if not avoided
        ↓
Avoidance / Required action
```

In the EditorJS block, this maps to:

- `data.level` → signal word level
- `data.title` → short hazard label (3–8 words)
- `data.hazard` → one-sentence hazard description
- `data.consequences[]` → bullet list of "what happens if ignored"
- `data.avoidance[]` → bullet list of imperative-mood instructions

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

## The six ISO 7010 categories

Symbol catalogue location in Rattle: `app/static/img/safety_logos/<category>/<file>.svg`. Use the dedicated category folder names exactly as listed below; both German aliases (`warnzeichen`, `verbotszeichen`, `gebotszeichen`, `rettungszeichen`, `brandschutz`) and English (`warning`, `prohibition`, `mandatory`, `safe_condition`, `fire_protection`) exist. **For the EditorJS block, always use the English name.**

| Category | EditorJS `isoSymbol.category` | Code prefix | Shape | Colour | Examples |
|---|---|---|---|---|---|
| **Warning** (Gefahrenzeichen) | `warning` | W001…W097 | yellow triangle, black border + symbol | yellow + black | crushing, hot surface, electricity, laser, magnetic field, automatic start-up |
| **Prohibition** (Verbotszeichen) | `prohibition` | P001…P064 | round, white background, red border + diagonal slash | red + black on white | no smoking, no entry, do not touch, no climbing |
| **Mandatory action** (Gebotszeichen) | `mandatory` | M001…M057 | round, blue background, white symbol | blue + white | wear gloves, wear ear protection, refer to manual, wear safety footwear |
| **Safe condition** (Rettungszeichen) | `safe_condition` | E001…E024 | square / rectangle, green background, white symbol | green + white | emergency exit, first aid, safety shower, eyewash station |
| **Fire protection** (Brandschutzzeichen) | `fire_protection` | F001…F010 | square, red background, white symbol | red + white | fire extinguisher, fire alarm, fire hose reel |
| **Hazardous materials** (Gefahrstoffe) | `gefahrstoffe` | GHS01…GHS09 | diamond on point, white background, red border + black symbol | red border, black symbol | explosive, flammable, oxidising, toxic, corrosive, environmental |

Full filename catalogue per category lives in `references/iso-7010-symbols.md`. Always pick by the W/P/M/E/F/GHS code, not by visual interpretation.

## Locale-aware signal words

Source: `app/utils/safety_notice_words.py`. Rattle ships normative signal words for **31 locales**. Every `safety_notice` block can omit `signalWord` and the renderer resolves it from the document locale. Specifying `signalWord` is only needed when overriding for a regional variant.

The 31 locales (and the four signal words per locale) are listed in `references/signal-words.md`. Selected examples:

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
- `references/signal-words.md` — 31 locale signal-word table (offline reference).
- `references/safe-principle.md` — extended SAFE-principle authoring guide with bad-vs-good rewrite examples.
- `rattle-techdoc/SKILL.md` — host skill that uses this one.
- `rattle-ghs-statements/SKILL.md` — chemical hazards (sister skill).
- `rattle-api/references/api-reference.md` — full Safety Reference endpoint reference.
