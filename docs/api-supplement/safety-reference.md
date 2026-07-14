> **Use these instead of guessing.** Before emitting a `safety_notice` block, call `GET /api/v1/safety-logos[?category=…]` to pick the right ISO 7010 / GHS file. Before emitting an `hp_statement` block, call `GET /api/v1/hp-statements[/{code}]` to validate the code and obtain the locale-resolved text. These endpoints are the single source of truth. Falling back to a default symbol, or hand-typing a CLP text, is the audit finding `default-fallback-symbol` / `mismatched-ghs-pictogram` — and in a CE-marked technical documentation that is a legal defect, not a cosmetic one.

**Categories** returned by `GET /safety-logos`: the five ISO 7010 sets — `warning` (W*), `prohibition` (P*), `mandatory` (M*), `safe_condition` (E*), `fire_protection` (F*) — plus `gefahrstoffe`, the **separate** CLP/GHS pictogram set from Annex V of (EC) 1272/2008. GHS pictograms are not ISO 7010 symbols; never substitute one for the other.

**Statement text is regulated and locale-resolved — never AI-translated.** `GET /hp-statements/{code}` resolves combined codes (`H300+H310`) and enhanced statements carrying slot placeholders. Translations are ECHA-traceable to CLP Annex III / IV / VI on EUR-Lex.

Full block contracts, the 32-locale signal-word catalogue, and the 24-locale H/P/EUH catalogue live in `skills/rattle-safety-notices/` and `skills/rattle-ghs-statements/`.
