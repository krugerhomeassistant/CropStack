# Adding plants, animals and values

CropStack's knowledge lives in [`catalog/`](../catalog/README.md), one YAML file per crop, variety, species, breed or
organism. Anyone can add to it with a pull request, and it is meant to keep growing. You do not need to run the app.

## Where to start

1. Open [`COVERAGE.md`](COVERAGE.md): every missing or estimated value, per crop. Any row is a good first change.
2. Or **request a species** with the issue form if you would rather not write YAML. A maintainer or another
   contributor picks it up, and issues labelled `needs data` are the standing to-do list.
3. Or **report a value** that is wrong for your region; give your source and we will add it as a regional value.

## Making a change

1. Fork, then edit or add a file in `catalog/` (copy a similar one; `catalog/crops/tomato.yaml` is complete).
2. Every number needs a source registered in `catalog/sources.yaml`, or `estimate: true` with a short basis.
   Prefer extension services, government and peer-reviewed sources; `evidence` says which kind you used.
3. When sources disagree by region or cultivar, add several values with `qualifiers`; do not average them.
4. Write descriptions and how-to text **in your own words**. Facts and numbers may come from a source; its wording may not.
   Only use sources whose licence allows it (`bundle`) or take facts only (`facts-only`); check the `use` field in `sources.yaml`.
5. Check it:

   ```bash
   cd backend && python -m pytest tests/test_catalog.py   # schema, sources, slugs
   python ../scripts/coverage.py                         # refreshes docs/COVERAGE.md
   ```

6. Open the pull request using the **catalog** template. By contributing you agree your change is licensed
   [CC BY-SA 4.0](../catalog/LICENSE).

CI rejects a pull request when a file does not validate, a value has no source or estimate flag, a slug repeats, a
source is not registered, or `COVERAGE.md` is stale.

## What the app does with each value

| Field | Used for |
|---|---|
| `requirements.temperature.stress_min` / `base` | Growth threshold for heat-sum (GDD) timing |
| `requirements.temperature.lethal_min` | Frost kill: which sowing days are safe |
| `requirements.temperature.stress_max` | Heat stress: days that stop growth |
| `requirements.temperature.optimal` | Season quality score |
| `requirements.soil_temperature.germination` | Earliest sowing day |
| `params.cycle_days` | Days from sowing to harvest |
| `params.transplant_age_days` | Seedling age at set-out; enables the indoor-start windows |
| `requirements.water.*` | Watering (coming) |

## How-to steps

The steps under each job on Today are task templates in `catalog/task-templates/` (copy `how-to-water.yaml`). One file per job kind: `task_kind` is one of `sow`, `set_out`, `harvest`, `water`, `frost`, `heat`, and `steps` is a list of short sentences in your own words.

## How collection keeps going

- A scheduled GitHub Action (monthly) re-runs the importers in `scripts/ingest/` and opens a pull request with the
  YAML diff for review. Nothing is merged without a person reading it.
- `scripts/coverage.py` turns the remaining gaps into [`COVERAGE.md`](COVERAGE.md), so the to-do list is always current.
- Each crop page has a **Suggest a correction** link that opens the "report a value" form with the crop filled in.
