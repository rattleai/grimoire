# Anti-patterns — full reference

Mirror of `rattle_api.knowledge.ANTI_PATTERNS`. Use these as a checklist when scanning any pricelist, product spec, or existing tenant catalogue. Detection on text inputs uses the indicator keywords below; detection on live tenant data uses the structural checks in `structural-checks.md`.

---

## 1. `implicit-base-config` — Implicit Base Configuration

**Description.** The pricelist describes standard features as included in the base product without creating explicit options for them. Only upgrades / add-ons appear as selectable options.

**Indicators (case-insensitive substring match):**

- `standard`
- `Grundausstattung`
- `Serienausstattung`
- `im Lieferumfang`
- `included`
- `inkl.`
- `serienmäßig`
- `Basisausstattung`

**Correction.** Create an explicit group with explicit options for ALL variants — including the standard one. Mark the standard option as `recommended=true`.

**Example — wrong**

> Product comes with 17" wheels as standard. Option: "19 inch wheels" (price: 500). Problem: no BOM item can carry a `usage_subclause` for the 17" wheels because no option represents them.

**Example — correct**

```
Group "Wheels" (is_multi: false)
  Option "17 inch" (recommended: true,  price: 0)
  Option "19 inch" (recommended: false, price: 500)
BOM:
  child_part "17-inch wheel assy", usage_subclauses: [{option_id: <17_inch>, factor: 1.0}]
  child_part "19-inch wheel assy", usage_subclauses: [{option_id: <19_inch>, factor: 1.0}]
```

**Related rule**: `explicit-options-for-all-variants` (the #1 rule).

---

## 2. `addon-only-options` — Add-on Only Options

**Description.** Options are listed only as surcharges or add-ons to a base product, without explicitly stating what the base/default is.

**Indicators:**

- `Aufpreis`
- `Zuschlag`
- `surcharge`
- `zusätzlich`
- `extra`
- `Mehrpreis`
- `Aufschlag`
- `optional`

**Correction.** For every add-on, identify the base variant it replaces or supplements. Create a group with both the base and the add-on as explicit options.

**Example — wrong**

> Aufpreis Frässpindel HSK-63F mit Encoder: +2.500€. Problem: what is the default spindle? No option exists for it.

**Example — correct**

```
Group "Frässpindel" (is_multi: false)
  Option "ISO 30 Standard"        (recommended: true,  price: 0)
  Option "HSK-63F ohne Encoder"   (price: 1800)
  Option "HSK-63F mit Encoder"    (price: 2500)
```

**Related rule**: `explicit-options-for-all-variants`.

---

## 3. `description-area-smell` — Narrative Area Smell

**Description.** The input mentions narrative sections like "Description", "Overview", "Beschreibung", "Produktbeschreibung", or chapter titles like "Mechanics" / "Sensors" / "Electronics" / "Software" as if they were on par with configurable options. Signals the author is about to create a narrative-only area that will have no groups.

**Indicators:**

- `Beschreibung`
- `Produktbeschreibung`
- `Description`
- `Overview`
- `Übersicht`
- `Mechanics`
- `Mechanik`
- `Sensorik`
- `Elektronik`
- `Bedienung`

**Correction.** Narrative content does not belong in a configuration area. Create a document template (`doc_type='offer'`) with a "Product Overview" chapter and attach a static EditorJS content block carrying the narrative. Attach the system `dynamic:document_configuration` block in a separate chapter so the live configuration still renders.

**Example — wrong**

> Area "Widget Pro — Description" (0 groups, just rich text about the product). The area has nothing to configure.

**Example — correct**

> Document template "Widget Pro — Offer" (`doc_type=offer`): chapter "Product Overview" with attached content block containing EditorJS narrative; chapter "Configuration" with attached `dynamic:document_configuration`. Areas carry only configurable groups.

**Related rules**: `no-empty-areas`, `narrative-in-documents-system`, `offer-requires-configuration-block`, `use-system-dynamic-blocks`.

---

## 4. `addon-only-software-modules` — Add-on Only Software Modules

**Description.** Software / licence modules appear only as surcharges without a matching base-module option. Common in pricelists because software has no physical BOM and is easy to miss when applying the explicit-options-for-all-variants rule.

**Indicators:**

- `Software-Modul`
- `Software Modul`
- `Modul-Aufpreis`
- `Lizenzmodul`
- `zusätzliches Modul`
- `Software surcharge`

**Correction.** Create a group for the software capability (e.g. "Cyclic testing software") with both the baseline option (price 0, recommended) and the upgrade module option. Set `is_multi` based on whether modules stack.

**Example — wrong**

> Aufpreis Software-Modul "Multistep cyclic": 500€. Problem: no option exists for the default (no-module) state.

**Example — correct**

```
Group "Software — Cyclic testing" (is_multi: false)
  Option "Manual cyclic testing (included)" (recommended: true, price: 0)
  Option "Multistep cyclic testing module"  (price: 500)
```

**Related rule**: `explicit-options-for-all-variants`.

---

## How to use this list

1. **Scan first, write second.** Before proposing groups for a new product, run the indicator strings against the input. Surface every match before generating recommendations.
2. **Combine with `detect_anti_patterns()`.** The Python helper in `rattle_api.knowledge.detect_anti_patterns(data)` performs the substring match deterministically over a list of dict rows (e.g. parsed Excel). Use it for repeatable, no-LLM detection. The script bundled with the `rattle-pricelist-analysis` skill mirrors this logic.
3. **Don't auto-fix without confirming.** When you find a likely `implicit-base-config`, ask the user what the actual standard variant is — the pricelist often elides it. The fix shape is fixed (explicit group with all variants), but the *content* needs human input.
4. **Cite the id.** When reporting findings, always include the anti-pattern id (`implicit-base-config`, etc.) and the related rule id from `configuration-rules.md`. This is what audit history and tenant memory will index against over time.
