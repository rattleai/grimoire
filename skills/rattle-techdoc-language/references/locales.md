# Locale matrix for technical documentation

A consolidated view of locale support across all three normative content sources Rattle uses in technical documentations: signal words (`safety_notice`), H/P statements (`hp_statement`), and free-form document content.

| Locale | Signal words | H/P statements | Free-form content (DeepL / AI) |
|---|---|---|---|
| `bg` Bulgarian | ✓ | ✓ | ✓ |
| `cs` Czech | ✓ | ✓ | ✓ |
| `da` Danish | ✓ | ✓ | ✓ |
| `de` German | ✓ | ✓ | ✓ |
| `el` Greek | ✓ | ✓ | ✓ |
| `en` English | ✓ | ✓ | ✓ |
| `en-us` US English | ✓ | (alias `en`) | ✓ |
| `es` Spanish | ✓ | ✓ | ✓ |
| `et` Estonian | ✓ | ✓ | ✓ |
| `fi` Finnish | ✓ | ✓ | ✓ |
| `fr` French | ✓ | ✓ | ✓ |
| `ga` Irish | — | ✓ | ✓ |
| `hr` Croatian | — | ✓ | ✓ |
| `hu` Hungarian | ✓ | ✓ | ✓ |
| `id` Indonesian | ✓ | — | DeepL: no, AI: yes |
| `it` Italian | ✓ | ✓ | ✓ |
| `ja` Japanese | ✓ | — | ✓ |
| `ko` Korean | ✓ | — | ✓ |
| `lt` Lithuanian | ✓ | ✓ | ✓ |
| `lv` Latvian | ✓ | ✓ | ✓ |
| `mt` Maltese | — | ✓ | ✓ |
| `nb` Norwegian Bokmål | ✓ | (alias `da`) | ✓ |
| `nl` Dutch | ✓ | ✓ | ✓ |
| `pl` Polish | ✓ | ✓ | ✓ |
| `pt` Portuguese | ✓ | ✓ | ✓ |
| `pt-br` Brazilian | (alias `pt`) | (alias `pt`) | ✓ |
| `ro` Romanian | ✓ | ✓ | ✓ |
| `ru` Russian | ✓ | — | ✓ |
| `sk` Slovak | ✓ | ✓ | ✓ |
| `sl` Slovenian | ✓ | ✓ | ✓ |
| `sv` Swedish | ✓ | ✓ | ✓ |
| `tr` Turkish | ✓ | — | ✓ |
| `uk` Ukrainian | ✓ | — | ✓ |
| `zh` Chinese | ✓ | — | ✓ |

> Legend: ✓ = native data shipped. (alias) = falls back to another locale by alias rule. — = not available; renderer falls back to `en`.

## Document locale → recommended publish locales

| Original locale | Auto-translate targets (machine market) | Notes |
|---|---|---|
| `de` | `en`, `fr`, `it`, `es`, `nl`, `pl`, `cs` | Typical DACH-EU export portfolio. |
| `en` | `de`, `fr`, `it`, `es`, `nl`, `pt` | Default-of-default; English is acceptable as original. |
| `fr` | `de`, `en`, `it`, `es`, `nl` | Typical France/Benelux. |
| `it` | `de`, `en`, `fr`, `es` | Typical Italian-export portfolio. |

## Picking the original locale

The "original-language version" must be the one **verified by the manufacturer**. In practice:

1. **DACH manufacturer:** original `de`, translations to all EU markets.
2. **EU multilingual market entry:** original `en`, translations as needed.
3. **For MDR products:** the original-language must be one of the official EU languages of the country of placement, OR a translation must be provided in that language. The MDR is stricter than MRL.

## Picking translation locales

Per MRL §1.7.4.1 / MVO Annex III §1.7.4: the technical documentation must be **provided in an official language of the EU country where the product is placed on the market**. So if the product is sold in Germany + France + Italy + Poland, you need DE + FR + IT + PL versions. Each version must:

- Have its own `cover` chapter with the original-language marker (or translation marker).
- Have its `sec-12-3-doc-status` say which locale is the original.
- Be linked to the same product but as separate locales (or as a separate template — see `rattle-techdoc/SKILL.md` for the trade-off).

## Locale fallback in EditorJS rendering

| Block type | Fallback locale chain |
|---|---|
| `safety_notice.signalWord` | `xx-YY` → `xx` → `en`. |
| `hp_statement.resolvedText` | `xx-YY` → alias → `xx` → `en`. |
| Free-form `paragraph` text | None — translation must be provided explicitly per locale. |

If a `safety_notice` block is rendered in a locale the renderer doesn't know, it gets the English signal word. If a `hp_statement` block is rendered without locale data, the H/P text falls back to English. Free-form content does not fall back — missing locales render as empty paragraphs.

## Translation pipeline

Recommended pipeline for translating a published technical documentation:

```
1. Snapshot source locale (DE).
2. POST /documents/templates/{id}/translate target_language=en
3. Audit the EN result (run language-review checks).
4. Repeat for FR, IT, … until all required locales are present.
5. POST /documents/templates/{id}/publish (re-publishes all locales).
```

> **Always** review safety-critical chapters (Chapter 2 Safety, Section 9.1 LOTO, Chapter 11 Disposal) by a native speaker familiar with the directive vocabulary. AI translation is a draft, not a final text, for these chapters.
