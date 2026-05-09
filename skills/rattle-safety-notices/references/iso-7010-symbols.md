# ISO 7010 + GHS symbol catalogue

Complete catalogue of the safety symbols Rattle ships with. Pick a symbol by its **code** (W024, P010, M002, …), never by visual interpretation. Filenames in this catalogue match the SVG files in `app/static/img/safety_logos/<category>/<file>.svg` in rattleapp.

> **Live data source.** This file is an offline reference for reasoning about codes. **For runtime symbol selection, query `GET /api/v1/safety-logos[?category=...]`** — the API response carries the complete file list **plus EN and DE manifest descriptions** that let an AI agent match a hazard description (e.g. "crushing of hands") to the right SVG file (`W024_crushing_of_hands.svg`). See `rattle-api/references/api-reference.md` § Safety Reference for the full endpoint contract. Use this file when you need to reason about codes without a live API connection.

The `isoSymbol.category` field on a `safety_notice` EditorJS block must be one of: `warning`, `prohibition`, `mandatory`, `safe_condition`, `fire_protection` (the **five** ISO 7010 categories), plus `gefahrstoffe` for CLP/GHS pictograms — **note that `gefahrstoffe` is NOT an ISO 7010 category**, it carries the separate CLP-pictogram set (see "Hazardous materials" section below). The `isoSymbol.file` field must be one of the filenames listed below for that category — or, equivalently, one of the `file` values returned by `GET /api/v1/safety-logos`.

> **Coverage note.** The catalogue below is the *currently shipped* set in rattleapp. ISO 7010 itself defines a slightly larger set (~230 signs). When a hazard has no exact match, fall back to the most specific available; for "moving parts" without a finer match, `W001_general_warning_sign.svg` is acceptable but always note the imprecision in the audit `notes` field.

---

## Warning · `warning` (yellow triangle)

ISO 7010 W-codes. Purpose: alert to a hazard. Use whenever the safety notice has `level=danger` or `level=warning`.

```text
W001_general_warning_sign.svg
W002_explosive_material.svg
W003_radioactive_material_or_ionizing_radiation.svg
W004_laser_beam.svg
W005_non_ionizing_radiation.svg
W006_magnetic_field.svg
W007_floor_level_obstacle.svg
W008_drop_fall.svg
W009_biological_hazard.svg
W010_low_temperature_freezing_conditions.svg
W011_slippery_surface.svg
W012_electricity.svg
W013_guard_dog.svg
W014_forklift_trucks_and_other_industrial_vehicles.svg
W015_overhead_load.svg
W016_toxic_material.svg
W017_hot_surface.svg
W018_automatic_start_up.svg
W019_crushing.svg
W020_overhead_obstacle.svg
W021_flammable_material.svg
W022_sharp_element.svg
W023_corrosive_substance.svg
W024_crushing_of_hands.svg
W025_counterrotating_rollers.svg
W026_battery_charging.svg
W027_optical_radiation.svg
W028_oxidizing_substance.svg
W029_pressurized_cylinder.svg
W030_hand_crushing_between_press_brake_tool.svg
W031_hand_crushing_between_press_brake_and_material.svg
W035_falling_objects.svg
W039_falling_ice.svg
W068_falling_into_water_when_stepping_on_or_off_a_floating_surface.svg
W069_jellyfish.svg
W070_step_down.svg
W071_substance_or_mixture_presenting_a_health_hazard.svg
W072_substance_or_mixture_that_can_cause_an_environmental_hazard.svg
W073_large_scale_fire_zone.svg
W074_tornado_zone.svg
W075_active_volcano_zone.svg
W076_debris_flow_zone.svg
W077_flood_zone.svg
W078_landslide_zone.svg
W079_hot_content.svg
W080_hot_steam.svg
W087_high_sound_volume_levels.svg
W088_moving_blades.svg
W089_moving_gears.svg
```

**Common picks for industrial-machine documentation:**

| Hazard | Code |
|---|---|
| Generic / unspecified | W001 |
| Crushing (whole-body) | W019 |
| Crushing (hands) | W024 |
| Hot surface | W017 |
| Electricity / live conductors | W012 |
| Automatic start-up | W018 |
| Counter-rotating rollers | W025 |
| Sharp element | W022 |
| Pressurised cylinder | W029 |
| Moving blades | W088 |
| Moving gears | W089 |
| High noise level | W087 |
| Hot steam | W080 |
| Falling objects | W035 |
| Slippery surface | W011 |
| Forklift / industrial vehicles | W014 |
| Laser radiation | W004 |
| Magnetic field | W006 |
| Optical radiation | W027 |
| Battery charging | W026 |

---

## Prohibition · `prohibition` (red ring + slash)

ISO 7010 P-codes. Purpose: forbid an action.

```text
P001_general_prohibition_sign.svg
P002_no_smoking.svg
P003_no_open_flame_fire_open_ignition_source_and_smoking_prohibited.svg
P004_no_thoroughfare.svg
P005_not_drinking_water.svg
P006_no_access_for_forklift_trucks_and_industrial_vehicles.svg
P007_no_access_for_people_with_active_implanted_cardiac_devices.svg
P008_no_metallic_articles_or_watches.svg
P009_no_climbing.svg
P010_do_not_touch.svg
P011_do_not_extinguish_with_water.svg
P012_no_heavy_load.svg
P013_no_activated_mobile_phone.svg
P014_no_access_for_people_with_metallic_implants.svg
P015_no_reaching_in.svg
P016_do_not_spray_with_water.svg
P017_no_pushing.svg
P018_no_sitting.svg
P019_no_stepping_on_surface.svg
P020_do_not_use_lift_in_the_event_of_fire.svg
P021_no_dogs.svg
P022_no_eating_or_drinking.svg
P023_do_not_obstruct.svg
P024_do_not_walk_or_stand_here.svg
P025_do_not_use_this_incomplete_scaffold.svg
P028_do_not_wear_gloves.svg
P031_do_not_alter_the_state_of_the_switch.svg
P069_not_to_be_serviced_by_users.svg
P080_no_access_for_unauthorized_persons.svg
P081_do_not_cover_appliance.svg
```

(Catalogue includes additional codes P026, P027, P029, P030, P032–P075 — see the SVG directory for the complete list.)

**Common picks:**

| Prohibition | Code |
|---|---|
| Generic | P001 |
| No smoking | P002 |
| No open flame | P003 |
| Do not touch | P010 |
| No reaching in | P015 |
| Do not extinguish with water | P011 |
| No mobile phones | P013 |
| Not for unauthorised access | P080 |
| Do not service (user-serviceable: false) | P069 |

---

## Mandatory action · `mandatory` (blue circle)

ISO 7010 M-codes. Purpose: prescribe a required action / PPE.

```text
M001_general_mandatory_action_sign.svg
M002_refer_to_instruction_manual_booklet.svg
M003_wear_ear_protection.svg
M004_wear_eye_protection.svg
M005_connect_an_earth_terminal_to_the_ground.svg
M006_disconnect_mains_plug_from_electrical_outlet.svg
M007_opaque_eye_protection_must_be_worn.svg
M008_wear_safety_footwear.svg
M009_wear_protective_gloves.svg
M010_wear_protective_clothing.svg
M011_wash_your_hands.svg
M013_wear_a_face_shield.svg
M014_wear_head_protection.svg
M015_wear_high_visibility_clothing.svg
M016_wear_a_mask.svg
M017_wear_respiratory_protection.svg
M018_wear_a_safety_harness.svg
M019_wear_a_welding_mask.svg
M020_wear_safety_belts.svg
M021_disconnect_before_carrying_out_maintenance_or_repair.svg
M026_use_protective_apron.svg
M057_ensure_continuous_ventilation.svg
M059_wear_laboratory_coat.svg
M068_lock_moving_mechanical_parts.svg
M069_tools_must_be_tethered.svg
```

**Common picks for PPE / lockout sections:**

| Mandatory action | Code |
|---|---|
| Generic | M001 |
| Read the manual | M002 |
| Ear protection | M003 |
| Eye protection | M004 |
| Earth / PE | M005 |
| Disconnect mains plug | M006 |
| Safety footwear | M008 |
| Protective gloves | M009 |
| Protective clothing | M010 |
| Face shield | M013 |
| Head protection | M014 |
| High-vis clothing | M015 |
| Respiratory protection | M017 |
| Safety harness | M018 |
| Disconnect before maintenance | M021 |
| Lock moving mechanical parts | M068 |

---

## Safe condition · `safe_condition` (green rectangle)

ISO 7010 E-codes. Purpose: locate emergency / first-aid equipment.

```text
E001_emergency_exit_left_hand.svg
E002_emergency_exit_right_hand.svg
E003_first_aid.svg
E004_emergency_telephone.svg
E007_evacuation_assembly_point.svg
E009_doctor.svg
E010_automated_external_heart_defibrillator.svg
E011_eyewash_station.svg
E012_safety_shower.svg
E013_stretcher.svg
E020_emergency_stop_button.svg
E024_evacuation_temporary_refuge.svg
```

**Common picks:**

| Safe condition | Code |
|---|---|
| Emergency exit (left) | E001 |
| Emergency exit (right) | E002 |
| First aid | E003 |
| Emergency telephone | E004 |
| Evacuation assembly point | E007 |
| Eyewash station | E011 |
| Safety shower | E012 |
| Emergency stop button | E020 |

---

## Fire protection · `fire_protection` (red square)

ISO 7010 F-codes. Purpose: locate fire-fighting equipment.

```text
F001_fire_extinguisher.svg
F002_fire_hose_reel.svg
F003_fire_ladder.svg
F004_collection_of_firefighting_equipment.svg
F005_fire_alarm_call_point.svg
F006_fire_emergency_telephone.svg
F007_fire_protection_door.svg
F008_fixed_fire_extinguishing_battery.svg
F009_wheeled_fire_extinguisher.svg
F010_portable_foam_applicator_unit.svg
F016_fire_blanket.svg
```

**Common picks:**

| Fire protection | Code |
|---|---|
| Fire extinguisher | F001 |
| Fire hose reel | F002 |
| Fire alarm call point | F005 |
| Fire blanket | F016 |

---

## Hazardous materials · `gefahrstoffe` *(CLP pictograms — separate normative basis, NOT ISO 7010)*

GHS pictograms come from the **CLP Regulation (EC) 1272/2008 Annex V** (and the UN GHS), **not** from ISO 7010. They have a different shape (red-bordered diamond on white), a different colour rule, and a different scope (chemical labelling). Treating them as a 6th ISO 7010 category in a CE-conformity dossier is a normative error.

For chemical hazards, **always prefer the dedicated `hp_statement` block** under `rattle-ghs-statements`. It carries the H/P/EUH codes and resolves the right pictogram + locale text from `ghs_pictogram_map.json` and the per-locale CLP statement tables. The `safety_notice.isoSymbol.category="gefahrstoffe"` path exists for the rare case where a single safety notice mixes a non-chemical hazard with a CLP pictogram, but it should be the exception, not the default.

The two SVG locations on disk:

- `app/static/img/safety_logos/gefahrstoffe/<file>.svg` — **mnemonic filenames** used by the `safety_notice` block. These are the only filenames `GET /api/v1/safety-logos?category=gefahrstoffe` will return; agents must use these verbatim.
- `app/static/img/ghs/GHS0X.svg` — numeric filenames (`GHS01.svg` … `GHS09.svg`) used by the `hp_statement` renderer for the GHS pictogram badge. **Not interchangeable with the safety-logos path** — `safety_notice.isoSymbol.file = "GHS06.svg"` will 404 in the renderer because that filename does not exist under the `gefahrstoffe` folder.

Mnemonic catalogue under `gefahrstoffe`:

```text
GHS-pictogram-acid.svg            (GHS05 — corrosive)
GHS-pictogram-bottle.svg          (GHS04 — gas under pressure)
GHS-pictogram-exclam.svg          (GHS07 — exclamation mark / health hazard)
GHS-pictogram-explos.svg          (GHS01 — explosive)
GHS-pictogram-flamme.svg          (GHS02 — flammable)
GHS-pictogram-pollu.svg           (GHS09 — environmental hazard)
GHS-pictogram-question.svg        (placeholder)
GHS-pictogram-rondflam.svg        (GHS03 — oxidising)
GHS-pictogram-silhouette.svg      (GHS08 — health hazard / serious)
GHS-pictogram-skull.svg           (GHS06 — toxic)
```

The `hp_statement` block resolves the right pictogram automatically from the H-code via `ghs_pictogram_map.json`.

---

## Symbol-picking heuristic

Given a hazard description, walk:

1. **Is the hazard about a chemical?** → use `hp_statement` block (resolves GHS pictogram).
2. **Is the message a prohibition?** ("do not …") → category `prohibition`, P-code.
3. **Is the message a required action / required PPE?** → category `mandatory`, M-code.
4. **Is the message about emergency / first-aid equipment?** → category `safe_condition`, E-code.
5. **Is the message about fire-fighting equipment?** → category `fire_protection`, F-code.
6. **Otherwise (a hazard alert)** → category `warning`, W-code. Pick the most specific W-code from the table above; fall back to W001 with a note.

When in doubt, M002 (`Refer to instruction manual booklet`) often pairs well with any safety notice that points the reader back to the IFU.
