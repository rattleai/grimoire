# Top 50 most-used H/P/EUH codes

Quick-reference catalogue of the H/P/EUH codes most often appearing in industrial-machine technical documentations (lubricants, coolants, cleaning agents, paints, batteries, refrigerants).

**The text below is for redactor reference only.** When emitting an `hp_statement` block, set `codes` and let the renderer resolve the official locale text from `app/utils/hp_statements.py`. Do not hand-type the localised text into `resolvedText`.

For the complete catalogue (~280 codes per locale), consult the source JSON files at `app/static/data/hp_statements/hpstatements-<lang>-latest.json`.

---

## H-statements — Physical hazards (H200–H290)

| Code | EN | DE | GHS |
|---|---|---|---|
| H220 | Extremely flammable gas. | Extrem entzündbares Gas. | GHS02 |
| H222 | Extremely flammable aerosol. | Extrem entzündbares Aerosol. | GHS02 |
| H223 | Flammable aerosol. | Entzündbares Aerosol. | GHS02 |
| H224 | Extremely flammable liquid and vapour. | Flüssigkeit und Dampf extrem entzündbar. | GHS02 |
| H225 | Highly flammable liquid and vapour. | Flüssigkeit und Dampf leicht entzündbar. | GHS02 |
| H226 | Flammable liquid and vapour. | Flüssigkeit und Dampf entzündbar. | GHS02 |
| H228 | Flammable solid. | Entzündbarer Feststoff. | GHS02 |
| H260 | In contact with water releases flammable gases which may ignite spontaneously. | In Berührung mit Wasser entstehen entzündbare Gase, die sich spontan entzünden können. | GHS02 |
| H261 | In contact with water releases flammable gases. | In Berührung mit Wasser entstehen entzündbare Gase. | GHS02 |
| H271 | May cause fire or explosion; strong oxidiser. | Kann Brand oder Explosion verursachen; starkes Oxidationsmittel. | GHS03 |
| H272 | May intensify fire; oxidiser. | Kann Brand verstärken; Oxidationsmittel. | GHS03 |
| H280 | Contains gas under pressure; may explode if heated. | Enthält Gas unter Druck; kann bei Erwärmung explodieren. | GHS04 |
| H281 | Contains refrigerated gas; may cause cryogenic burns or injury. | Enthält tiefkaltes Gas; kann Kälteverbrennungen oder -verletzungen verursachen. | GHS04 |
| H290 | May be corrosive to metals. | Kann gegenüber Metallen korrosiv sein. | GHS05 |

## H-statements — Health hazards (H300–H373)

| Code | EN | DE | GHS |
|---|---|---|---|
| H300 | Fatal if swallowed. | Lebensgefahr bei Verschlucken. | GHS06 |
| H301 | Toxic if swallowed. | Giftig bei Verschlucken. | GHS06 |
| H302 | Harmful if swallowed. | Gesundheitsschädlich bei Verschlucken. | GHS07 |
| H304 | May be fatal if swallowed and enters airways. | Kann bei Verschlucken und Eindringen in die Atemwege tödlich sein. | GHS08 |
| H310 | Fatal in contact with skin. | Lebensgefahr bei Hautkontakt. | GHS06 |
| H311 | Toxic in contact with skin. | Giftig bei Hautkontakt. | GHS06 |
| H312 | Harmful in contact with skin. | Gesundheitsschädlich bei Hautkontakt. | GHS07 |
| H314 | Causes severe skin burns and eye damage. | Verursacht schwere Verätzungen der Haut und schwere Augenschäden. | GHS05 |
| H315 | Causes skin irritation. | Verursacht Hautreizungen. | GHS07 |
| H317 | May cause an allergic skin reaction. | Kann allergische Hautreaktionen verursachen. | GHS07 |
| H318 | Causes serious eye damage. | Verursacht schwere Augenschäden. | GHS05 |
| H319 | Causes serious eye irritation. | Verursacht schwere Augenreizung. | GHS07 |
| H330 | Fatal if inhaled. | Lebensgefahr bei Einatmen. | GHS06 |
| H331 | Toxic if inhaled. | Giftig bei Einatmen. | GHS06 |
| H332 | Harmful if inhaled. | Gesundheitsschädlich bei Einatmen. | GHS07 |
| H334 | May cause allergy or asthma symptoms or breathing difficulties if inhaled. | Kann bei Einatmen Allergie, asthmaartige Symptome oder Atembeschwerden verursachen. | GHS08 |
| H335 | May cause respiratory irritation. | Kann die Atemwege reizen. | GHS07 |
| H336 | May cause drowsiness or dizziness. | Kann Schläfrigkeit und Benommenheit verursachen. | GHS07 |
| H340 | May cause genetic defects {1}. | Kann genetische Defekte verursachen {1}. | GHS08 |
| H341 | Suspected of causing genetic defects {1}. | Kann vermutlich genetische Defekte verursachen {1}. | GHS08 |
| H350 | May cause cancer {1}. | Kann Krebs erzeugen {1}. | GHS08 |
| H351 | Suspected of causing cancer {1}. | Kann vermutlich Krebs erzeugen {1}. | GHS08 |
| H360 | May damage fertility or the unborn child {1}. | Kann die Fruchtbarkeit beeinträchtigen oder das Kind im Mutterleib schädigen {1}. | GHS08 |
| H370 | Causes damage to organs {1}. | Schädigt die Organe {1}. | GHS08 |
| H371 | May cause damage to organs {1}. | Kann die Organe schädigen {1}. | GHS08 |
| H372 | Causes damage to organs {2} through prolonged or repeated exposure {1}. | Schädigt die Organe {2} bei längerer oder wiederholter Exposition {1}. | GHS08 |

## H-statements — Environmental hazards (H400–H413)

| Code | EN | DE | GHS |
|---|---|---|---|
| H400 | Very toxic to aquatic life. | Sehr giftig für Wasserorganismen. | GHS09 |
| H410 | Very toxic to aquatic life with long lasting effects. | Sehr giftig für Wasserorganismen mit langfristiger Wirkung. | GHS09 |
| H411 | Toxic to aquatic life with long lasting effects. | Giftig für Wasserorganismen, mit langfristiger Wirkung. | GHS09 |

## EUH supplemental

| Code | EN | DE |
|---|---|---|
| EUH014 | Reacts violently with water. | Reagiert heftig mit Wasser. |
| EUH019 | May form explosive peroxides. | Kann explosionsfähige Peroxide bilden. |
| EUH066 | Repeated exposure may cause skin dryness or cracking. | Wiederholter Kontakt kann zu spröder oder rissiger Haut führen. |
| EUH208 | Contains \<sensitiser\>. May produce an allergic reaction. | Enthält \<Sensibilisator\>. Kann allergische Reaktionen hervorrufen. |
| EUH210 | Safety data sheet available on request. | Sicherheitsdatenblatt auf Anfrage erhältlich. |

---

## P-statements — General + Prevention (P1xx, P2xx)

| Code | EN | DE |
|---|---|---|
| P101 | If medical advice is needed, have product container or label at hand. | Ist ärztlicher Rat erforderlich, Verpackung oder Kennzeichnungsetikett bereithalten. |
| P102 | Keep out of reach of children. | Darf nicht in die Hände von Kindern gelangen. |
| P201 | Obtain special instructions before use. | Vor Gebrauch besondere Anweisungen einholen. |
| P210 | Keep away from heat, hot surfaces, sparks, open flames and other ignition sources. No smoking. | Von Hitze, heißen Oberflächen, Funken, offenen Flammen sowie anderen Zündquellenarten fernhalten. Nicht rauchen. |
| P233 | Keep container tightly closed. | Behälter dicht verschlossen halten. |
| P240 | Ground and bond container and receiving equipment. | Behälter und zu befüllende Anlage erden. |
| P241 | Use explosion-proof equipment. | Explosionsgeschützte Geräte verwenden. |
| P260 | Do not breathe dust/fume/gas/mist/vapours/spray. | Staub/Rauch/Gas/Nebel/Dampf/Aerosol nicht einatmen. |
| P261 | Avoid breathing dust/fume/gas/mist/vapours/spray. | Einatmen von Staub/Rauch/Gas/Nebel/Dampf/Aerosol vermeiden. |
| P264 | Wash hands thoroughly after handling. | Nach Gebrauch Hände gründlich waschen. |
| P270 | Do not eat, drink or smoke when using this product. | Bei Gebrauch nicht essen, trinken oder rauchen. |
| P271 | Use only outdoors or in a well-ventilated area. | Nur im Freien oder in gut belüfteten Räumen verwenden. |
| P272 | Contaminated work clothing should not be allowed out of the workplace. | Kontaminierte Arbeitskleidung nicht außerhalb des Arbeitsplatzes tragen. |
| P273 | Avoid release to the environment. | Freisetzung in die Umwelt vermeiden. |
| P280 | Wear protective gloves/protective clothing/eye protection/face protection. | Schutzhandschuhe/Schutzkleidung/Augenschutz/Gesichtsschutz tragen. |
| P282 | Wear cold insulating gloves and either face shield or eye protection. | Kälteisolierende Handschuhe und Gesichtsschild oder Augenschutz tragen. |
| P284 | Wear respiratory protection. | Atemschutz tragen. |

## P-statements — Response (P3xx)

| Code | EN | DE |
|---|---|---|
| P301 | IF SWALLOWED: | BEI VERSCHLUCKEN: |
| P302 | IF ON SKIN: | BEI BERÜHRUNG MIT DER HAUT: |
| P304 | IF INHALED: | BEI EINATMEN: |
| P305 | IF IN EYES: | BEI KONTAKT MIT DEN AUGEN: |
| P310 | Immediately call a POISON CENTER/doctor. | Sofort GIFTINFORMATIONSZENTRUM/Arzt anrufen. |
| P311 | Call a POISON CENTER/doctor. | GIFTINFORMATIONSZENTRUM/Arzt anrufen. |
| P312 | Call a POISON CENTER/doctor if you feel unwell. | Bei Unwohlsein GIFTINFORMATIONSZENTRUM/Arzt anrufen. |
| P313 | Get medical advice/attention. | Ärztlichen Rat einholen / ärztliche Hilfe hinzuziehen. |
| P314 | Get medical advice/attention if you feel unwell. | Bei Unwohlsein ärztlichen Rat einholen / ärztliche Hilfe hinzuziehen. |
| P321 | Specific treatment (see … on this label). | Besondere Behandlung (siehe … auf diesem Kennzeichnungsetikett). |
| P330 | Rinse mouth. | Mund ausspülen. |
| P331 | Do NOT induce vomiting. | KEIN Erbrechen herbeiführen. |
| P332 | If skin irritation occurs: | Bei Hautreizung: |
| P333 | If skin irritation or rash occurs: | Bei Hautreizung oder -ausschlag: |
| P336 | Thaw frosted parts with lukewarm water. Do not rub the affected area. | Vereiste Bereiche mit lauwarmem Wasser auftauen. Betroffene Bereiche nicht reiben. |
| P337 | If eye irritation persists: | Bei anhaltender Augenreizung: |
| P338 | Remove contact lenses, if present and easy to do. Continue rinsing. | Eventuell vorhandene Kontaktlinsen nach Möglichkeit entfernen. Weiter ausspülen. |
| P352 | Wash with plenty of water/… | Mit viel Wasser/… waschen. |
| P353 | Rinse skin with water [or shower]. | Haut mit Wasser abwaschen [oder duschen]. |

## P-statements — Storage + Disposal (P4xx, P5xx)

| Code | EN | DE |
|---|---|---|
| P403 | Store in a well-ventilated place. | An einem gut belüfteten Ort aufbewahren. |
| P404 | Store in a closed container. | In einem geschlossenen Behälter aufbewahren. |
| P405 | Store locked up. | Unter Verschluss aufbewahren. |
| P410 | Protect from sunlight. | Vor Sonnenbestrahlung schützen. |
| P411 | Store at temperatures not exceeding … °C/… °F. | Bei Temperaturen von nicht mehr als … °C/… °F aufbewahren. |
| P412 | Do not expose to temperatures exceeding 50 °C/122 °F. | Nicht Temperaturen von mehr als 50 °C/122 °F aussetzen. |
| P420 | Store separately. | Getrennt aufbewahren. |
| P501 | Dispose of contents/container to … | Inhalt/Behälter … zuführen. |
| P502 | Refer to manufacturer or supplier for information on recovery or recycling. | Informationen zur Wiederverwendung oder Wiederverwertung beim Hersteller oder Lieferanten erfragen. |

---

## Common combined statements

| Combined key | EN | DE |
|---|---|---|
| H300+H310 | Fatal if swallowed or in contact with skin. | Lebensgefahr bei Verschlucken oder Hautkontakt. |
| H300+H310+H330 | Fatal if swallowed, in contact with skin or if inhaled. | Lebensgefahr bei Verschlucken, Hautkontakt oder Einatmen. |
| H315+H319 | Causes skin and eye irritation. | Verursacht Haut- und Augenreizungen. |
| H332+H335 | Harmful if inhaled. May cause respiratory irritation. | Gesundheitsschädlich beim Einatmen. Kann die Atemwege reizen. |
| P301+P310 | IF SWALLOWED: Immediately call a POISON CENTER/doctor. | BEI VERSCHLUCKEN: Sofort GIFTINFORMATIONSZENTRUM/Arzt anrufen. |
| P302+P352 | IF ON SKIN: Wash with plenty of water/… | BEI BERÜHRUNG MIT DER HAUT: Mit viel Wasser/… waschen. |
| P303+P361+P353 | IF ON SKIN (or hair): Take off immediately all contaminated clothing. Rinse skin with water [or shower]. | BEI BERÜHRUNG MIT DER HAUT (oder dem Haar): Alle kontaminierten Kleidungsstücke sofort ausziehen. Haut mit Wasser abwaschen [oder duschen]. |
| P305+P351+P338 | IF IN EYES: Rinse cautiously with water for several minutes. Remove contact lenses, if present and easy to do. Continue rinsing. | BEI KONTAKT MIT DEN AUGEN: Einige Minuten lang behutsam mit Wasser ausspülen. Eventuell vorhandene Kontaktlinsen nach Möglichkeit entfernen. Weiter ausspülen. |
| P332+P313 | If skin irritation occurs: Get medical advice/attention. | Bei Hautreizung: Ärztlichen Rat einholen / ärztliche Hilfe hinzuziehen. |
| P337+P313 | If eye irritation persists: Get medical advice/attention. | Bei anhaltender Augenreizung: Ärztlichen Rat einholen / ärztliche Hilfe hinzuziehen. |
