# Open / openly licensed crop species and cultivar databases for CropStack (status as of 2026-10-09)

Context: CropStack is MIT-licensed and wants to store derived YAML in the repo. Licence compatibility key used below:
- GREEN = CC0 / public domain / US-government work: can ship derived YAML in an MIT repo with no conditions (attribution courteous).
- YELLOW = CC BY 4.0: can ship, but the data files carry their own CC BY notice + attribution (data licence separate from MIT code licence). FAO adds extra terms.
- RED = share-alike (CC BY-SA) or non-commercial (NC) or "all rights reserved": derived YAML would have to be licensed BY-SA / NC, not MIT-compatible as a bundled catalog; use only as reference or user-side optional import.

## FAO ECOCROP: status, location, fields, species count, reuse terms

### Takeaway
ECOCROP was discontinued around 2015 but still runs at ecocrop.apps.fao.org (HTTP 200 on 2026-10-09) and is listed in the FAO data catalog under CC BY 4.0; there is no official bulk download, so the practical bulk source is the ECOCROP table extracted into Robert Hijmans' R package Recocrop (1,710 taxa; package code GPL>=3). FAO's database terms add non-CC conditions (no use to promote a commercial enterprise, no implied endorsement), so the data is YELLOW: shippable with CC BY attribution, but the extra FAO terms should be noted.

### Cited Findings
- FAO page: ECOCROP "was discontinued around 2015" but remains available due to demand; now accessed via FAO GAEZ platform (https://data.apps.fao.org/gaez/) and directly at https://ecocrop.apps.fao.org/ecocrop/srv/en/cropSearchForm and .../cropFindForm; covers "over 2,568 plant species" — [FAO Geospatial: ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/en)
- Fields per FAO: plant descriptors (category, life form, growth habit, life span); environmental descriptors with min/max (and optimal) for temperature, annual precipitation, soil pH, light intensity, Koppen climate zone, photoperiod sensitivity, latitude, altitude, other soil characteristics; use descriptors (main use, used part) — [FAO Geospatial: ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/en)
- FAO Agro-informatics Data Catalog entry "ecocrop": licence "Creative Commons Attribution 4.0 International"; resources are the web tool and a WMTS basemap only (no CSV/bulk file); metadata last updated 2025-04-03; "more than 2000 plant species" — [FAO data catalog: ecocrop](https://data.apps.fao.org/catalog/dataset/ecocrop)
- FAO Database terms of use: datasets are CC BY 4.0 "as complemented by the Terms of Use"; you may "access, download, create copies, adapt and re-disseminate"; prohibited: use "to promote a commercial enterprise, its products or services", implying FAO endorsement, misrepresenting content; third-party data may need provider consent; required citation "FAO. [year]. [Database name]. Accessed [date]. URL. Licence: CC-BY-4.0."; disputes go to UNCITRAL arbitration; FAO may discontinue at any time — [FAO Statistical Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use)
- Live check 2026-10-09: https://ecocrop.apps.fao.org/ecocrop/srv/en/cropSearchForm returned HTTP 200 (own curl test).
- Recocrop (CRAN) v0.4-2, published 2025-07-21, licence GPL (>= 3), maintainer Robert J. Hijmans — [CRAN Recocrop](https://cran.r-project.org/web/packages/Recocrop/index.html)
- Recocrop `parameters` data: "default ecocrop parameters for 1,710 taxa", mostly crops; parameters `duration` (GMIN + 1 month unless GMIN = GMAX; GMIN/GMAX retained), `prec` (monthly precip thresholds min/lower-opt/upper-opt/max, derived from annual precip / season months+1), `tavg` (4-point temperature), `ktmp` (killing temperature), `ph`; values "derived from figures that FAO once published on its website", documented as expert opinion "not necessarily optimal"; full raw database including non-extracted fields shipped as `parameters/ecocrop.rds` — [Recocrop reference manual](https://cran.r-project.org/web/packages/Recocrop/refman/Recocrop.html)
- The older dismo package also has an `ecocrop` function/data — [dismo ecocrop doc](https://search.r-project.org/CRAN/refmans/dismo/html/ecocrop.html)

### Inferences
- The underlying FAO facts are CC BY 4.0 (+FAO terms); the GPL on Recocrop covers the package as distributed. Extracting FAO-derived values into YAML and attributing FAO is arguably governed by FAO's licence, not GPL (facts/data vs. code), but this is a judgement call — safest is to cite FAO ECOCROP as source and note that values were cross-checked against the live FAO site rather than copying the .rds verbatim.
- MIT + CC BY 4.0 data in a `data/` folder with a separate `DATA_LICENSE` / NOTICE file is standard practice and compatible. The FAO "no promotion of a commercial enterprise" clause is irrelevant for a non-commercial OSS project but is an extra term downstream forks inherit.
- Species count discrepancy: FAO page "2,568", catalog ">2000", Recocrop "1,710 taxa" (Recocrop only kept taxa with extractable parameters).

### Gaps
- No official FAO bulk export found; the GAEZ portal integration was not inspected in detail.
- Did not locate a Zenodo/GitHub mirror of a full ECOCROP CSV with an explicit licence (did not search exhaustively; GitHub repo rspatial/Recocrop fetch failed).

## USDA PLANTS Database (characteristics)

### Takeaway
PLANTS is live (redirects to plants.sc.egov.usda.gov), listed on data.gov as CC0 / public, and exposes an undocumented-but-working JSON API (plantsservices.sc.egov.usda.gov) that returns characteristics such as Frost Free Days Minimum, Temperature Minimum (F), pH min/max, Precipitation min/max (inches), Root Depth Minimum, Active Growth Period. GREEN. Characteristics coverage is sparse and US-centric (strong for cover crops/forages, weak for garden vegetables — tomato returned zero characteristics).

### Cited Findings
- data.gov "PLANTS" dataset: public access, licence "Creative Commons CCZero"; data last modified 2022-12-07, metadata updated 2025-05-08; downloads/data dictionary at https://plants.sc.egov.usda.gov/home/downloads — [data.gov: PLANTS](https://catalog.data.gov/dataset/plants)
- plants.usda.gov 302-redirects to https://plants.sc.egov.usda.gov/ (Angular SPA; WebFetch could not render page text) — own fetch, 2026-10-09.
- Own API test 2026-10-09: `GET https://plantsservices.sc.egov.usda.gov/api/PlantProfile?symbol=SOLY2` returned 200 (Id 55438); `GET .../api/PlantCharacteristics/{Id}` returned 0 characteristic rows for tomato; for crimson clover (TRIN3) it returned 390 rows including 'Frost Free Days, Minimum'=180/210, 'pH, Minimum'=5.5, 'pH, Maximum'=7.5, 'Precipitation, Minimum'=32/35, 'Precipitation, Maximum'=65/70, 'Root Depth, Minimum (inches)'=12, 'Temperature, Minimum (°F)'=-7..14, 'Active Growth Period', 'Growth Rate' (multiple rows = per-cultivar values); hairy vetch (VISA) returned 78 rows. (Primary observation, no URL page beyond the API endpoints.)
- EOL publishes a USDA PLANTS trait extract (usda_plant_traits.tar.gz, 30.9 MB) on Zenodo, v7 2025-12-11, licence "Not Specified" — [Zenodo: USDA PLANTS structured data DwCA](https://zenodo.org/records/17903503)

### Inferences
- US federal works are public domain; CC0 on data.gov confirms it is fine to vendor into MIT repo.
- Use for cover crops, grains, forages, perennials; do not expect vegetable cultivar characteristics. Units are imperial (inches, °F).
- API is undocumented and could change; snapshotting to YAML is preferable to runtime dependency.

### Gaps
- Could not read the downloads page or help PDF (JS-rendered/redirect); the exact list of bulk files and the total number of taxa with characteristics are unverified.
- Maintenance cadence: data.gov says data last modified 2022-12-07; no 2025-2026 update notes found.

## USDA GRIN-Global / GRIN Taxonomy (germplasm, cultivar names, descriptors)

### Takeaway
GRIN-Global is listed on data.gov with the US Public Domain label (GREEN), but the catalog lists only the web site as a resource — no documented bulk or API. Useful for authoritative crop taxonomy and accession/cultivar names and descriptor (evaluation) data via the web UI; NPGS germplasm itself is not distributed to home gardeners.

### Cited Findings
- data.gov "The GRIN-Global Project": licence "Public domain label 1.0", public, publisher ARS; only resource is https://www.grin-global.org/ ; last modified 2025-11-21 — [data.gov: GRIN-Global](https://catalog.data.gov/dataset/the-grin-global-project)
- NPGS search page: "NPGS germplasm is not available for individual, home, or community gardening"; international distribution under ITPGRFA/SMTA; from 2026-06-01 recipients pay shipping; links to Descriptors and a Software Disclaimer — [GRIN-Global search](https://npgsweb.ars-grin.gov/gringlobal/search)

### Inferences
- Descriptor/observation data can be exported per-query from the web UI (common knowledge, not verified here); scraping is legally fine (public domain) but should be rate-limited.

### Gaps
- No official API or bulk download verified. The GRIN Taxonomy "World Economic Plants" crop list (useful common names in many languages) was not checked.

## Wikidata (taxa, multilingual common names, cultivars)

### Takeaway
All structured data is CC0 (GREEN) and the SPARQL endpoint works. As of 2026-10-09 there are 9,879 items typed `instance of (P31) cultivar (Q4886)` and 2,636 Afrikaans `taxon common name (P1843)` values — good for multilingual names (incl. Afrikaans) and IDs linking to GBIF/USDA/GRIN/WFO, thin for vegetable cultivars and growing requirements.

### Cited Findings
- "All structured data in the main, property and lexeme namespaces is made available under the Creative Commons CC0 License." — [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
- Own SPARQL queries against https://query.wikidata.org/sparql on 2026-10-09: `SELECT (COUNT(*) AS ?n) WHERE { ?i wdt:P31 wd:Q4886 }` -> 9879; `SELECT (COUNT(*) AS ?n) WHERE { ?t wdt:P1843 ?l . FILTER(LANG(?l)="af") }` -> 2636.

### Inferences
- Recommended use: canonical name/ID crosswalk (P225 taxon name, P1843 common name per language, plus external-ID properties for GBIF/USDA PLANTS/GRIN/WFO) and labels in af/zu/xh etc. Cultivar coverage skewed to ornamentals/fruit (assumption; not measured).
- Must send a descriptive User-Agent and cache results; do not call at runtime from each self-hosted instance.

### Gaps
- Breakdown of the 9,879 cultivars by crop/edibility not measured. Afrikaans coverage of specific vegetables not measured.

## Canonical scientific names: GBIF Backbone, Catalogue of Life, World Flora Online

### Takeaway
GBIF Backbone = CC BY 4.0 (YELLOW); last backbone build 2023-08-28 per GBIF release notes. Catalogue of Life monthly releases (Base 2026-06-12; Extended 2026-05-15 XR) are CC BY 4.0 per a secondary source (primary licence page not readable). World Flora Online backbone snapshots on Zenodo are CC0 (GREEN) — the best fit for vendoring plant names into an MIT repo.

### Cited Findings
- GBIF API dataset record for Backbone (d7dddbf4-...): license `http://creativecommons.org/licenses/by/4.0/legalcode`; modified 2023-11-17, DwC-A modified 2025-07-09 — [GBIF API dataset](https://api.gbif.org/v1/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c)
- Backbone draws on 54 sources, COL the largest (3,175,925 names) — [GBIF Backbone dataset page](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c)
- Latest backbone note: 2023-08-28 "New GBIF backbone taxonomy, with three new sources"; release notes' latest entry 2024-02-29 — [GBIF release notes](https://www.gbif.org/release-notes)
- COL releases: Base 2026-06-12 (5,397,623 names, 2,250,638 species); XR 2026-05-15 (7,851,869 names, 2,484,225 species); formats via ChecklistBank (ColDP, DwC-A, etc.); licence not stated on page — [COL download](https://www.catalogueoflife.org/data/download)
- taxadb 2026 snapshot README lists COL (2026-08-20) as CC BY 4.0, GBIF Backbone (2023-08-28) CC BY 4.0, ITIS public domain/CC0, NCBI public domain/CC0, Open Tree Taxonomy CC0 — [taxadb 2026 README (secondary)](https://data.source.coop/cboettig/taxadb/2026/README.md)
- WFO Taxonomic Backbone on Zenodo: licence CC0 1.0 (rights "Other (Public Domain)"); v1.2.201904 (zip 144 MB), newer version available; seeded from The Plant List v1.1, curated by Taxonomic Expert Networks — [Zenodo 7461831](https://zenodo.org/record/7461831); also [Zenodo 7460932](https://zenodo.org/records/7460932)

### Inferences
- For CropStack, store only accepted name + authorship + a WFO ID / GBIF taxonKey per crop (a few hundred rows). Even from CC BY sources, such facts are minimal, but attribution in a NOTICE file is cheap.
- ITIS (public domain) is another GREEN option for US-centric names.

### Gaps
- COL licence on its own site (checklistbank) could not be fetched (robots); CC BY 4.0 is from a secondary source.
- WFO current release version/licence on worldfloraonline.org could not be fetched (robots); only the Zenodo 2019 snapshots verified. Whether the 2025/2026 WFO "plant list" releases remain CC0 is unverified.
- Whether GBIF replaced the 2023 backbone with a COL-XR-based one in 2025-2026 is unverified.

## Community plant databases: PFAF, Permapeople, Trefle, OpenFarm, Growstuff, Practical Plants

### Takeaway
Only OpenFarm data is CC0 (GREEN) — OpenFarm servers shut down 2025-04-21, repo archived 2025-04-22, and a community rescue (340 crop records, CC0, JSON) exists on GitHub. Trefle is alive and its own data is CC BY 4.0 but carries upstream licences per record (mixed). PFAF (BY-NC-SA, inconsistent wording), Permapeople (CC BY-SA 2.0, no free commercial API), Growstuff (CC BY-SA 3.0) are RED for bundling.

### Cited Findings
- OpenFarm: "on April 21st, 2025, we shut down the OpenFarm servers after being online for a little more than 10 years"; no data dump mentioned — [FarmBot blog: Sunsetting OpenFarm](https://farm.bot/blogs/news/sunsetting-openfarm)
- OpenFarm repo archived 2025-04-22; code MIT; README: "All data within the OpenFarm.cc database is in the Public Domain (CC0)." — [GitHub openfarmcc/OpenFarm](https://github.com/openfarmcc/OpenFarm). openfarm.cc now 301-redirects to that repo (own curl, 2026-10-09).
- OpenFarm rescue: `crops.json`, 340 records rebuilt from Wayback captures; CC0 1.0 LICENSE; fields slug, name, binomialName, taxon, description, sun, sowingMethod, spreadCm, rowSpacingCm, heightCm, companions (134 records), tags, growingDegreeDays (35 records), source{origin, license, waybackUrl, captured}; README warns data quality = original wiki edits, not for edibility/safety; explicitly excludes Growstuff data because it is CC-BY-SA — [GitHub thefullnacho/openfarm-crops-rescue](https://github.com/thefullnacho/openfarm-crops-rescue); announced 2026-07-10 — [Growing Fruit forum](https://growingfruit.org/t/openfarms-crop-data-restored-in-website/81182)
- Trefle: site live, v2.7.0, beta; claims ~1M plants (399,174 species, 27,690 varieties, 8 cultivars, ~840,631 synonyms); REST JSON, free token, 60 req/min — [trefle.io](https://trefle.io/). Terms: Trefle's own data "licensed under ... CC BY 4.0"; upstream data keeps source licence (see `sources` array); display "Data: Trefle.io (CC BY 4.0)"; to acquire major portions from one provider "contact that content provider directly" — [Trefle terms](https://trefle.io/terms). API code AGPL-3.0, not archived — [GitHub treflehq/trefle-api](https://github.com/treflehq/trefle-api)
- PFAF: copyright Ken Fern/Plants for a Future 1995-2019; page text says "Creative Commons Attribution 4.0 License" but links BY-NC-SA 4.0 and describes share-alike; images CC BY-NC-ND/NC-SA 3.0 (inconsistent links), no commercial use; search-page images are commercial and cannot be used; software copyright PFAF 2019 — [PFAF copyright page](https://pfaf.org/User/cmspage.aspx?pageid=136)
- Permapeople API: "all data available through this API is licensed under CC BY-SA 2.0"; "We do not currently allow commercial projects free access to the API"; key/secret headers; fields include Edible, Water/Light requirement, USDA Hardiness zone, Layer, Soil type, Family, Edible parts; Plant vs Variety types — [Permapeople API docs](https://permapeople.org/knowledgebase/api-docs.html)
- Growstuff API structured data: "Creative Commons Attribution-ShareAlike (CC-BY-SA) 3.0 Unported License"; exceptions: Australian Food Composition data CC BY 4.0; members' content remains members' copyright — [Growstuff API policy](https://www.growstuff.org/policy/api). Code AGPL-3.0 — [GitHub Growstuff/growstuff](https://github.com/Growstuff/growstuff)
- Practical Plants: described as "Over 7400 plant articles"; page footer shows CC BY-SA 4.0 badge (of the p2pfoundation wiki, not necessarily Practical Plants) — [P2P Foundation wiki](https://wiki.p2pfoundation.net/Practical_Plants). practicalplants.org responds HTTP 200 at /wiki/practical_plants/ (own curl 2026-10-09).

### Inferences
- OpenFarm rescue is the only directly vendorable community crop-guide dataset; small (340) and uneven quality — usable as a seed list with spacing/sun/sowing method, needs curation.
- Trefle: mixed licensing per record; use only Trefle-originated fields with CC BY attribution, or as an optional runtime lookup — not bulk vendoring.
- PFAF/Permapeople/Growstuff/Practical Plants: do not copy into MIT repo. Could offer an optional user-run importer (data stays on the user's instance under its own licence), though NC terms (PFAF, Permapeople commercial restriction) still bind users.

### Gaps
- Practical Plants' own licence page and any dump not verified ("unverified").
- Trefle's claimed counts do not reconcile (1M vs component sums); no bulk dump found.
- Growstuff activity level in 2026 not determined.

## Crop calendar / crop parameter datasets (SAGE/Sacks, GGCMI, MIRCA2000)

### Takeaway
These are global field-crop calendars (18-26 staple crops, gridded), mostly not relevant to garden vegetables, and none had a licence verified on a primary page — mark all "unverified" for redistribution.

### Cited Findings
- Sacks et al. crop calendar (SAGE, UW-Madison): 19 crops; planting/harvest dates, days to harvest, climate at planting; netCDF/ASCII grids (5' and 0.5°) and All_data_with_climate.csv; page states no licence, only asks users to email Bill Sacks — [SAGE crop calendar](https://sage.nelson.wisc.edu/data-and-models/datasets/crop-calendar-dataset/)
- GGCMI Phase 3 crop calendar: 18 crops, 0.5° grid, planting & maturity day, rainfed/irrigated separated (Jägermeyr et al. 2021); licence not shown in fetched content — [Zenodo 5062513](https://zenodo.org/record/5062513) (ISIMIP mirror blocked by bot protection)
- MIRCA2000: 26 irrigated and rainfed crops, crop calendars for 402 spatial units, 5 arc-min; licence not stated on page — [Uni Frankfurt MIRCA](https://www.uni-frankfurt.de/45218023/MIRCA)

### Inferences
- At most useful as a sanity check for grain/staple sowing windows by region (e.g. maize/wheat in South Africa); not a garden catalog source.

### Gaps
- Licences for all three are unverified; the Zenodo record's licence field may exist but was not returned by the fetch.

## South African sources (ARC, DALRRD/DoA, SANBI)

### Takeaway
SANBI's National Plant Checklist 2025 is CC BY 4.0 (YELLOW) — useful for SA names/natives, not crop requirements. ARC-VOPI production guideline PDFs are copyright ARC (terms page not read) — reference only, do not copy text/tables.

### Cited Findings
- SANBI "South African National Plant Checklist: 2025 official yearly release", Zenodo, CC BY 4.0, single .xlsb file (9.8 MB); newer version exists — [Zenodo 15050848](https://zenodo.org/records/15050848)
- ARC-VOPI Production Guidelines page: free PDF booklets for summer vegetables (tomato, Swiss chard, sweet potato, cucurbits, green beans, African leafy vegetables) and winter vegetables (cabbage, carrot, beetroot, onion, potato); sweet potato guide sold (R180); footer "Copyright © 2014 ARC" linking to T&Cs — [ARC-VOPI Production Guidelines](https://arc.agric.za/arc-vopi/Pages/Production-Guidelines.aspx)

### Inferences
- Facts (e.g. sowing months for Highveld) can be independently restated with citation, but verbatim tables/text should not be copied without ARC permission. Asking ARC for written permission is a realistic option for an SA maintainer.

### Gaps
- ARC Terms and Conditions text, and DALRRD (now Dept of Agriculture) production guideline terms, were not read: "unverified". SA government copyright default is restrictive (assumption, not verified).
- No SA open machine-readable crop-requirement dataset found.
