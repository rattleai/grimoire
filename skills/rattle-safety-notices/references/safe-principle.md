# SAFE-principle authoring guide

The four-part SAFE structure every `safety_notice` follows:

```
S — SIGNAL WORD          (level: danger/warning/caution/notice)
A — Art der Gefahr       (title: short hazard label)
F — Folgen               (consequences[]: what happens if ignored)
E — Erforderliche       (avoidance[]: imperative-mood instructions)
    Maßnahme
```

This is the German acronym; the English equivalent is sometimes called the "ANSI structure" or "Z535 four-part body". They describe the same thing.

## Authoring rules

### 1 · Signal-word level

| If the hazard is… | Pick |
|---|---|
| Imminent + serious injury / death | DANGER |
| Possible + serious injury / death | WARNING |
| Possible + minor / moderate injury | CAUTION |
| Property damage only | NOTICE |

Default to WARNING when in doubt. Over-using DANGER dilutes its signal value.

### 2 · `title` — short hazard label

3–8 words. Capitalise normally for the locale (German: noun-only capitalisation; English: title case for short noun phrases).

| Bad | Good |
|---|---|
| "Be careful around moving parts!" | "Quetschgefahr durch bewegliche Maschinenteile" / "Crushing hazard from moving machine parts" |
| "Hot" | "Hot surface burn hazard" |
| "Achtung" | "Stromschlaggefahr beim Öffnen des Schaltschranks" |

Avoid: imperatives, vague adjectives, exclamation marks (the signal word already carries the emphasis).

### 3 · `hazard` — one-sentence hazard description

Describe the **physical mechanism** of the hazard. This is what makes the warning actionable.

| Bad | Good |
|---|---|
| "Be careful." | "Bewegliche Teile können Hände und Finger einklemmen." |
| "Risk of injury." | "Heiße Oberflächen verursachen schwere Verbrennungen bei Berührung." |
| "Electrical danger." | "Spannungsführende Teile können tödlichen Stromschlag verursachen." |

### 4 · `consequences[]` — what happens if ignored

3–6 short bullet phrases. Be specific about the **harm**, not the *probability*.

| Bad | Good |
|---|---|
| "Could be bad." | ["Schwere Quetschverletzungen", "Knochenbrüche", "Fingerverlust"] |
| "Risk of injury." | ["Verbrennungen 2. und 3. Grades", "Bleibende Hautschäden"] |
| Empty list | At least one concrete consequence |

### 5 · `avoidance[]` — imperative-mood instructions

3–7 imperative-mood instructions. Each starts with a verb. Order from most-important to least-important.

| Bad | Good |
|---|---|
| "Should be careful." | ["Vor dem Eingriff Maschine stillsetzen.", "Gegen Wiedereinschalten sichern.", "Schutzhandschuhe tragen."] |
| "Don't get hurt." | ["Sicherheitsabstand von 1 m einhalten.", "Vor Annäherung E-Stop drücken."] |
| "Read the manual." | (only if accompanied by a section reference: `ref: "Kap. 9.4"`) |

The avoidance list is the **most important** part of the safety notice. If the user only reads one part, this is what they read. Make it concrete, ordered, and actionable.

### 6 · `ref` — cross-reference

Optional. When set, points to the chapter / section that gives more detail. Use the locale-appropriate abbreviation:

- DE: `Kap. 9.4`, `Abschn. 2.4`
- EN: `Sec. 9.4`, `Chap. 9`, `§9.4`

### 7 · `isoSymbol` — the pictogram

Pick a category + file from the `references/iso-7010-symbols.md` catalogue. The category drives the colour/shape, the file drives the icon.

For `safety_notice` blocks at `level=warning` or `level=danger`, the `category` is **almost always** `warning` (yellow triangle). Other categories appear when the safety notice's primary purpose is:

- Forbidding an action → `prohibition`
- Mandating an action / PPE → `mandatory`
- Pointing to emergency equipment → `safe_condition`
- Pointing to fire-fighting equipment → `fire_protection`

For chemical hazards, switch to `hp_statement` block (sister skill).

## Bad-vs-good rewrite examples

### Example 1 — generic Achtung

**Source:**

> ⚠ ACHTUNG! Bewegliche Teile.

**SAFE-correct:**

```json
{
  "type": "safety_notice",
  "data": {
    "level": "warning",
    "title": "Quetschgefahr durch bewegliche Teile",
    "hazard": "Bewegliche Maschinenteile können Hände und Finger einklemmen.",
    "consequences": ["Schwere Quetschverletzungen", "Fingerverlust"],
    "avoidance": [
      "Vor dem Eingriff Maschine stillsetzen.",
      "Gegen Wiedereinschalten sichern.",
      "Stillstand der Maschine abwarten."
    ],
    "ref": "Kap. 9.4",
    "isoSymbol": {"category": "warning", "file": "W024_crushing_of_hands.svg"},
    "showAlertSymbol": true
  }
}
```

### Example 2 — electrical hazard

**Source:**

> Vorsicht! Stromschlag möglich. Vor Wartung Schaltschrank ausschalten.

**SAFE-correct:**

```json
{
  "type": "safety_notice",
  "data": {
    "level": "danger",
    "title": "Stromschlaggefahr beim Öffnen des Schaltschranks",
    "hazard": "Spannungsführende Teile auch nach Hauptschalter-AUS noch unter Spannung.",
    "consequences": ["Tödlicher Stromschlag", "Schwere Verbrennungen"],
    "avoidance": [
      "Hauptschalter AUS und gegen Wiedereinschalten sichern (LOTO).",
      "Spannungsfreiheit vor Beginn der Arbeiten messen.",
      "Nur durch Elektrofachkraft nach DIN VDE 1000-10 ausführen."
    ],
    "ref": "Kap. 9.1 (LOTO)",
    "isoSymbol": {"category": "warning", "file": "W012_electricity.svg"},
    "showAlertSymbol": true
  }
}
```

Note: this is `level=danger` (imminent + serious) because the hazard is "about to happen if the user opens the cabinet without LOTO".

### Example 3 — property damage only

**Source:**

> Note: Use only the recommended cleaning agent. Other agents may damage the seal.

**SAFE-correct:**

```json
{
  "type": "safety_notice",
  "data": {
    "level": "notice",
    "title": "Sealring damage from incorrect cleaning agent",
    "hazard": "Solvents and acidic cleaners attack the EPDM seal ring.",
    "consequences": ["Premature seal failure", "Leakage", "Loss of warranty cover"],
    "avoidance": [
      "Use only neutral pH cleaning agent (pH 6–8).",
      "Refer to approved cleaning-agent list in Sec. 9.3."
    ],
    "ref": "Sec. 9.3",
    "isoSymbol": {"category": "warning", "file": "W001_general_warning_sign.svg"},
    "showAlertSymbol": false
  }
}
```

`showAlertSymbol: false` is allowed for `level=notice` since there is no personal-injury risk.
