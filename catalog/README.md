# CropStack catalog

What CropStack knows about crops, varieties, animal species and breeds, organisms (pests, diseases, beneficials,
weeds, deficiencies) and task templates. Licensed **CC BY-SA 4.0** ([LICENSE](LICENSE), [NOTICE](NOTICE));
the app code is MIT, which does not cover this folder.

## Layout

| Path | Contents |
|---|---|
| `sources.yaml` | Registry of every source: licence, how it may be used (`bundle`, `facts-only`, `link-only`), terms review date |
| `crops/`, `varieties/` | One YAML file per crop or variety (`kind: crop` / `kind: variety` with `parent`) |
| `species/`, `breeds/` | Animal species and breeds |
| `organisms/` | Pests, diseases, beneficials, pollinators, weeds, deficiencies |
| `task-templates/` | Reusable task templates |
| `schema/` | JSON Schema files generated from `backend/app/catalog.py` (`python scripts/catalog_schema.py`) for editors and tooling |

## A value

Every number or fact is a cited statement (SPEC §16.1):

```yaml
requirements:
  temperature:
    lethal_min:
      value: -1
      unit: Cel
      evidence: extension-service   # peer-reviewed | government | extension-service | model | grower-reported | traditional
      confidence: medium            # high | medium | low
      rank: preferred               # preferred | normal | deprecated
      sources:
        - {ref: some-source-id, retrieved: 2026-10-09, locator: "Table 2"}
```

Ranges use `value: {min: …, opt: …, max: …}`. When sources disagree by region or cultivar, give a list of
values with `qualifiers` instead of averaging. A value with no source must say `estimate: true`.

## Rules (checked in CI)

- Files validate against the schema; slugs are unique per kind; varieties and breeds point to an existing parent.
- Every cited source exists in `sources.yaml`; `bundle` sources must have an open licence; nothing may cite a
  `link-only` source.
- Write descriptions fresh. Never copy prose, tables, lists or images from a source.

## Imported values

Most numbers are imported by `scripts/ingest` from the sources in `sources.yaml` and carry the snapshot hash of
the raw copy they came from. Values written by hand are never overwritten by an import. Parameters in use:

| Path | Unit | Meaning |
|---|---|---|
| `requirements.soil_temperature.germination` | Cel | soil temperature range for germination (min, opt, max) |
| `params.days_to_emergence` | d | days to emergence, one value per `qualifiers.soil_temp_c` |
| `requirements.water.kc_initial` / `kc_mid` / `kc_late` | 1 | FAO-56 single crop coefficient per stage |
| `requirements.water.root_depth` | m | maximum effective rooting depth (range) |
| `requirements.water.depletion_fraction` | 1 | share of available soil water used before stress (FAO-56 p) |
| `params.stage_days_initial` / `_development` / `_mid` / `_late` | d | stage lengths in field trials, per `qualifiers.region` and `planting` |
| `params.height_max` | m | mean maximum plant height |
| `params.row_spacing`, `params.plant_spread`, `params.height` | cm | grower-reported sizes |
| `params.sun` | | `full_sun`, `partial_sun`, `partial_shade` or `shade` |

## Private pack

A server can add its own entries in `<data>/catalog-private/` (same format, same folders). They are loaded after
this catalog and win field by field, are never committed or shipped, and skip the licence check, so they can
hold values looked up for personal use. Errors in a private pack are shown to the household owner instead of
stopping the app. After editing, use the reload endpoint (`POST /api/v1/catalog/reload`) or restart.
