# H-code → GHS pictogram mapping

The complete mapping from `app/static/data/ghs_pictogram_map.json` (CLP Regulation EC 1272/2008 Annex I, public-domain regulatory data).

The mapping is **automatic**: the `hp_statement` EditorJS block resolves the pictogram from the H-code at render time. You do not specify pictograms manually. This file is a redactor reference for understanding which icon will appear.

> **Live API.** Two endpoints expose this mapping:
>
> - `GET /api/v1/hp-statements?include_ghs_map=true` returns `data.ghs_pictogram_map` — the entire H-code → `GHS0X` dictionary.
> - `GET /api/v1/hp-statements/<code>` returns `data.ghs_pictogram` for the single code (when one exists; combined codes and P/EUH codes have no pictogram).
>
> Use the API when you want a sanity check on which icon will display for a given block. See `rattle-api/references/api-reference.md` § Safety Reference.

## The 9 GHS pictograms

| ID | SVG file | Symbol | Hazard category |
|---|---|---|---|
| **GHS01** | `GHS01.svg` | exploding bomb | Explosive |
| **GHS02** | `GHS02.svg` | flame | Flammable |
| **GHS03** | `GHS03.svg` | flame over circle | Oxidising |
| **GHS04** | `GHS04.svg` | gas cylinder | Gas under pressure |
| **GHS05** | `GHS05.svg` | corrosion | Corrosive |
| **GHS06** | `GHS06.svg` | skull and crossbones | Acute toxicity (severe) |
| **GHS07** | `GHS07.svg` | exclamation mark | Health hazard (less severe) |
| **GHS08** | `GHS08.svg` | health-hazard silhouette | Serious health hazard |
| **GHS09** | `GHS09.svg` | environment | Environmental hazard |

SVG sources in rattleapp: `app/static/img/ghs/GHS0X.svg`.

## Full H-code → GHS map

| H-code | GHS | Notes |
|---|---|---|
| H200 | GHS01 | Unstable explosive |
| H201 | GHS01 | Explosive; mass-explosion hazard |
| H202 | GHS01 | Explosive; severe projection hazard |
| H203 | GHS01 | Explosive; fire / blast / projection hazard |
| H204 | GHS01 | Fire or projection hazard |
| H205 | GHS01 | May mass-explode in fire |
| H206 | GHS01 | Fire / blast / projection hazard; increased risk if desensitiser reduced |
| H207 | GHS01 | Fire / projection hazard; increased risk if desensitiser reduced |
| H208 | GHS01 | Fire hazard; increased risk if desensitiser reduced |
| H220 | GHS02 | Extremely flammable gas |
| H221 | GHS02 | Flammable gas |
| H222 | GHS02 | Extremely flammable aerosol |
| H223 | GHS02 | Flammable aerosol |
| H224 | GHS02 | Extremely flammable liquid and vapour |
| H225 | GHS02 | Highly flammable liquid and vapour |
| H226 | GHS02 | Flammable liquid and vapour |
| H228 | GHS02 | Flammable solid |
| H229 | GHS02 | Pressurised container; may burst if heated |
| H230 | GHS02 | May react explosively even in absence of air |
| H231 | GHS02 | May react explosively even in absence of air at elevated pressure / temperature |
| H232 | GHS02 | May ignite spontaneously if exposed to air |
| H240 | GHS01 | Heating may cause explosion |
| H241 | GHS01 | Heating may cause fire or explosion |
| H242 | GHS02 | Heating may cause fire |
| H250 | GHS02 | Catches fire spontaneously if exposed to air |
| H251 | GHS02 | Self-heating; may catch fire |
| H252 | GHS02 | Self-heating in large quantities; may catch fire |
| H260 | GHS02 | In contact with water releases flammable gases that may ignite spontaneously |
| H261 | GHS02 | In contact with water releases flammable gases |
| H270 | GHS03 | May cause or intensify fire; oxidiser |
| H271 | GHS03 | May cause fire or explosion; strong oxidiser |
| H272 | GHS03 | May intensify fire; oxidiser |
| H280 | GHS04 | Contains gas under pressure; may explode if heated |
| H281 | GHS04 | Contains refrigerated gas; may cause cryogenic burns |
| H290 | GHS05 | May be corrosive to metals |
| H300 | GHS06 | Fatal if swallowed |
| H301 | GHS06 | Toxic if swallowed |
| H302 | GHS07 | Harmful if swallowed |
| H304 | GHS08 | May be fatal if swallowed and enters airways |
| H310 | GHS06 | Fatal in contact with skin |
| H311 | GHS06 | Toxic in contact with skin |
| H312 | GHS07 | Harmful in contact with skin |
| H314 | GHS05 | Causes severe skin burns and eye damage |
| H315 | GHS07 | Causes skin irritation |
| H317 | GHS07 | May cause an allergic skin reaction |
| H318 | GHS05 | Causes serious eye damage |
| H319 | GHS07 | Causes serious eye irritation |
| H330 | GHS06 | Fatal if inhaled |
| H331 | GHS06 | Toxic if inhaled |
| H332 | GHS07 | Harmful if inhaled |
| H334 | GHS08 | May cause allergy or asthma symptoms or breathing difficulties if inhaled |
| H335 | GHS07 | May cause respiratory irritation |
| H336 | GHS07 | May cause drowsiness or dizziness |
| H340 | GHS08 | May cause genetic defects |
| H341 | GHS08 | Suspected of causing genetic defects |
| H350 | GHS08 | May cause cancer |
| H351 | GHS08 | Suspected of causing cancer |
| H360 | GHS08 | May damage fertility or the unborn child |
| H361 | GHS08 | Suspected of damaging fertility or the unborn child |
| H362 | GHS08 | May cause harm to breast-fed children |
| H370 | GHS08 | Causes damage to organs |
| H371 | GHS08 | May cause damage to organs |
| H372 | GHS08 | Causes damage to organs through prolonged or repeated exposure |
| H373 | GHS08 | May cause damage to organs through prolonged or repeated exposure |
| H400 | GHS09 | Very toxic to aquatic life |
| H410 | GHS09 | Very toxic to aquatic life with long-lasting effects |
| H411 | GHS09 | Toxic to aquatic life with long-lasting effects |

## When multiple H-codes give multiple pictograms

A single substance often carries several H-codes that map to different pictograms. Example: a solvent with `H225` (flammable, GHS02) and `H319` (eye irritation, GHS07) and `H336` (drowsiness, GHS07) gets **two distinct pictograms**: GHS02 + GHS07.

The `hp_statement` renderer collects unique pictograms across all `codes` in the block:

```javascript
_getAllUniqueGhs() {
  const seen = new Set();
  const result = [];
  for (const code of this.data.codes) {
    const ghs = this._getGhsPictogram(code);
    if (ghs && !seen.has(ghs)) {
      seen.add(ghs);
      result.push(ghs);
    }
  }
  return result;
}
```

## Codes with no pictogram

Some H-codes (and all P-codes / EUH-codes) do not carry a GHS pictogram. The map returns `null` for them. In the EditorJS renderer, this means the block displays only the resolved text without a pictogram. Examples:

- `P-codes` — no pictogram (precautionary statements)
- `EUH066` — no pictogram (`Repeated exposure may cause skin dryness or cracking`)
- `EUH210` — no pictogram (`Safety data sheet available on request`)

For these codes, the block still applies but renders text-only — that is normal and expected.
