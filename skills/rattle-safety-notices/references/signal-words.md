# Signal-word locale catalogue

The 32 locales Rattle ships normative signal words for. Source: `app/utils/safety_notice_words.py` in rattleapp (the `_SIGNAL_WORDS` dict has 32 keys).

> **Live data source.** For runtime resolution, call `GET /api/v1/safety-notices/signal-words[?locale=de]` — same data, served from the same backing module. With no `locale` query parameter the endpoint returns the full mapping for all 32 locales plus a `default` alias. See `rattle-api/references/api-reference.md` § Safety Reference for the full contract.

> **National-standard divergence note.** The locale words below follow Rattle's internal convention. For jurisdictions with their own national-standard signal words (e.g. PN-EN ISO 3864-2 in Poland, NEN-EN ISO 3864-2 in the Netherlands, ANSI Z535.6 in the US), confirm with a national-standard reviewer before publication. Known divergences from common industry usage:
>
> - **Polish:** `OSTROŻNOŚĆ` is the noun form for CAUTION; the more common adverbial signal word is **OSTROŻNIE** or **UWAGA**. `OGŁOSZENIE` for NOTICE means "announcement" in everyday Polish; the safety-notice convention more commonly uses **UWAGA** or **WSKAZÓWKA**.
> - **Dutch:** `VOORZICHTIGHEID` is the abstract noun for CAUTION; industry signage commonly uses the adjective **VOORZICHTIG** or the bracketed **LET OP**. `KENNISGEVING` for NOTICE is legal-register; technical safety notices often use **OPMERKING**.
> - **German:** `HINWEIS` for NOTICE is the Rattle / DIN ISO 3864-2 convention; some ANSI Z535.6 native-German localisations prefer **ACHTUNG** to disambiguate from non-safety editorial notes.

The renderer resolves `signalWord` automatically from the document locale; you only need to set it explicitly when overriding for a regional variant. Locale fallback chain: `xx-YY` → `xx` → `en`.

| Locale | DANGER | WARNING | CAUTION | NOTICE |
|---|---|---|---|---|
| `bg` (Bulgarian) | ОПАСНОСТ | ПРЕДУПРЕЖДЕНИЕ | ВНИМАНИЕ | ЗАБЕЛЕЖКА |
| `cs` (Czech) | NEBEZPEČÍ | VAROVÁNÍ | POZOR | OZNÁMENÍ |
| `da` (Danish) | FARE | ADVARSEL | FORSIGTIGHED | MEDDELELSE |
| `de` (German) | GEFAHR | WARNUNG | VORSICHT | HINWEIS |
| `el` (Greek) | ΚΙΝΔΥΝΟΣ | ΠΡΟΕΙΔΟΠΟΙΗΣΗ | ΠΡΟΣΟΧΗ | ΑΝΑΚΟΙΝΩΣΗ |
| `en` (English, default) | DANGER | WARNING | CAUTION | NOTICE |
| `en-us` | DANGER | WARNING | CAUTION | NOTICE |
| `es` (Spanish) | PELIGRO | ADVERTENCIA | PRECAUCIÓN | AVISO |
| `et` (Estonian) | OHT | HOIATUS | ETTEVAATUST | MÄRKUS |
| `fi` (Finnish) | VAARA | VAROITUS | HUOMIO | ILMOITUS |
| `fr` (French) | DANGER | AVERTISSEMENT | ATTENTION | AVIS |
| `hu` (Hungarian) | VESZÉLY | FIGYELMEZTETÉS | VIGYÁZAT | ÉRTESÍTÉS |
| `id` (Indonesian) | BAHAYA | PERINGATAN | PERHATIAN | PENGUMUMAN |
| `it` (Italian) | PERICOLO | AVVERTENZA | ATTENZIONE | AVVISO |
| `ja` (Japanese) | 危険 | 警告 | 注意 | 通知 |
| `ko` (Korean) | 위험 | 경고 | 주의 | 공지 |
| `lt` (Lithuanian) | PAVOJUS | ĮSPĖJIMAS | ATSARGIAI | PRANEŠIMAS |
| `lv` (Latvian) | BĪSTAMI | BRĪDINĀJUMS | UZMANĪBU | PAZIŅOJUMS |
| `nb` (Norwegian Bokmål) | FARE | ADVARSEL | FORSIKTIGHET | MERKNAD |
| `nl` (Dutch) | GEVAAR | WAARSCHUWING | VOORZICHTIGHEID | KENNISGEVING |
| `pl` (Polish) | NIEBEZPIECZEŃSTWO | OSTRZEŻENIE | OSTROŻNOŚĆ | OGŁOSZENIE |
| `pt` (Portuguese) | PERIGO | ATENÇÃO | CUIDADO | AVISO |
| `pt-br` | PERIGO | ATENÇÃO | CUIDADO | AVISO |
| `pt-pt` | PERIGO | ATENÇÃO | CUIDADO | AVISO |
| `ro` (Romanian) | PERICOL | AVERTISMENT | ATENȚIE | NOTIFICARE |
| `ru` (Russian) | ОПАСНОСТЬ | ПРЕДУПРЕЖДЕНИЕ | ВНИМАНИЕ | УВЕДОМЛЕНИЕ |
| `sk` (Slovak) | NEBEZPEČENSTVO | VAROVANIE | POZOR | UPOZORNENIE |
| `sl` (Slovenian) | NEVARNOST | OPOZORILO | POZOR | OBVESTILO |
| `sv` (Swedish) | FARA | VARNING | FÖRSIKTIGHET | MEDDELANDE |
| `tr` (Turkish) | TEHLİKE | UYARI | DİKKAT | BİLDİRİM |
| `uk` (Ukrainian) | НЕБЕЗПЕКА | ПОПЕРЕДЖЕННЯ | ОБЕРЕЖНО | ПОВІДОМЛЕННЯ |
| `zh` (Chinese, simplified) | 危险 | 警告 | 注意 | 须知 |

## Casing convention

Signal words are conventionally rendered in **UPPERCASE** to maximise visibility, regardless of the language's natural casing. The locale tables above already preserve UPPERCASE for languages where it's customary.

For CJK locales (`ja`, `ko`, `zh`), there is no upper/lower case — they render in the standard form.

## Fallback rules

`safety_notice_words.py` resolves locales using this chain:

1. Exact match (`pt-br` → entry for `pt-br`).
2. Primary subtag (`pt-br` → `pt`).
3. English (`en`).

If a locale is missing entirely, the renderer always succeeds with the English signal word.
