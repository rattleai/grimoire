# Style guide — DE / EN technical documentation

Concrete bad-vs-good rewrites for the most common style violations in technical documentations. Use this as the day-to-day reference; the parent skill (`SKILL.md`) covers the rules.

## German (de)

### Imperativ vs. Konjunktiv

| Bad | Good |
|---|---|
| "Der Bediener sollte vor Wartungsarbeiten den Hauptschalter ausschalten." | "Schalten Sie vor Wartungsarbeiten den Hauptschalter aus." |
| "Es wäre ratsam, die Dichtung zu prüfen." | "Prüfen Sie die Dichtung." |
| "Man muss die Schraube anziehen." | "Ziehen Sie die Schraube an." |
| "Die Filter können regelmäßig gereinigt werden." | "Reinigen Sie die Filter monatlich." |

### Nominalisierungen → Verben

| Bad (Nominalisierung) | Good (Verb) |
|---|---|
| "Durchführung einer Inspektion" | "Inspizieren" |
| "Vornahme der Reinigung" | "Reinigen" |
| "Erfolgt die Bestätigung durch …" | "Bestätigt … " |
| "Es findet eine Prüfung der Sensoren statt" | "Prüfen Sie die Sensoren" |

### Passiv → Aktiv

| Bad (Passiv) | Good (Aktiv) |
|---|---|
| "Die Schraube wird angezogen." | "Ziehen Sie die Schraube an." |
| "Vor dem Wiedereinbau ist zu prüfen, ob die Dichtung intakt ist." | "Prüfen Sie vor dem Wiedereinbau die Dichtung auf Beschädigungen." |

### Füllwörter

| Bad | Good |
|---|---|
| "in der Regel" | (entfernen) |
| "grundsätzlich" | (entfernen oder durch "immer" / "nie") |
| "mehr oder weniger" | (entfernen — Tolerance angeben) |
| "im Allgemeinen" | (entfernen) |
| "selbstverständlich" | (entfernen) |

### Abkürzungen

- Erstmals voll ausschreiben + Abkürzung in Klammern: "Lockout/Tagout (LOTO)".
- Danach nur noch Abkürzung.
- Im Glossar (13.6) jede Abkürzung mit voller Definition.

### Präzision

| Bad | Good |
|---|---|
| "ca. 10 Nm" | "10 Nm ± 1 Nm" oder "8–12 Nm" |
| "ein paar Sekunden" | "5–10 s" |
| "die meisten Modelle" | "Modelle XY-500A und XY-500B" |
| "sollte zugänglich sein" | "Höhe Bedienelement: 800–1200 mm AGL" |

## English (en)

### Active imperative

| Bad | Good |
|---|---|
| "The operator should engage the lockout-tagout." | "Engage the lockout-tagout." |
| "It is necessary that the seal be checked." | "Check the seal." |
| "The technician may want to verify alignment." | "Verify alignment." |

### Nominalisations → verbs

| Bad | Good |
|---|---|
| "Perform inspection of the bearings." | "Inspect the bearings." |
| "Carry out a check on the sensor." | "Check the sensor." |
| "Make a determination as to whether the seal is intact." | "Determine whether the seal is intact." OR "Check the seal." |

### Passive → active

| Bad | Good |
|---|---|
| "The bolt should be tightened to 10 Nm." | "Tighten the bolt to 10 Nm." |
| "The cover must be reinstalled before testing." | "Reinstall the cover before testing." |

### Filler

| Bad | Good |
|---|---|
| "in order to" | "to" |
| "due to the fact that" | "because" |
| "at this point in time" | "now" |
| "for the purpose of" | "to" |
| "it should be noted that" | (delete) |
| "it is recommended that" | (use imperative) |

### Numbers and tolerances

| Bad | Good |
|---|---|
| "approximately 10 Nm" | "10 Nm ± 1 Nm" or "8–12 Nm" |
| "a few seconds" | "5–10 s" |
| "most models" | "Models XY-500A and XY-500B" |

### Hyphenation and units

- Use SI units with non-breaking space: `230 V`, `50 Hz`, `Nm`.
- Use en-dash for ranges: `5–10 Nm`, never `5-10 Nm`.
- Decimal point: `0.5 mm` (en); decimal comma: `0,5 mm` (de).

## Common procedure pattern

Every procedure (Chapter 5–11) has the same shape:

```
Heading: <task name>
Tools required: <list>
Time required: <approx>
Personnel: <qualification>
Pre-conditions:
  - LOTO engaged.
  - Cooling time elapsed (> 30 min after shutdown).
Procedure:
  1. <imperative step> [expected result]
  2. <imperative step> [expected result]
  ...
Post-conditions:
  - <verification>
Tests:
  - <safety function test>
```

Every step is a single imperative sentence. Multi-action steps split into multiple steps. Expected results in brackets at the end of the step (or as a sub-bullet).

## Checklists vs. procedures

- **Procedure** (ordered list, EditorJS `list` style=`ordered`) — used when sequence matters.
- **Checklist** (unordered list, EditorJS `list` style=`checklist`) — used when items can be done in any order; user ticks each.
- **Schedule** (table, EditorJS `table` withHeadings=true) — used for periodic maintenance.

Mixing the three (procedure with checkboxes inside) confuses the reader. Pick one and use the right EditorJS block style.
