# CropStack organism catalog: open data sources for pests, diseases, beneficials, weeds and deficiencies

Scope: licence, access method and coverage of sources for an MIT-licensed, self-hosted app with worldwide users and a maintainer in South Africa. Checked October 2026. "Unverified" means the primary terms page could not be fetched or does not state terms.

Overall picture: the authoritative plant-health references (EPPO Global Database content, CABI Compendium, UC IPM, PPDB, PlantwisePlus) are **not** openly licensed for redistribution. The usable open layers are:
- EPPO Codes (open licence)
- GBIF and iNaturalist records and photos, filtered per item to CC0 or CC BY
- Wikimedia Commons
- GloBI interaction data
- Published model parameters, used as facts
- A few CC BY image datasets (PlantDoc, DeepWeeds)

## EPPO Global Database (pests, hosts, distribution): API and licence

### Takeaway
Only the **EPPO Codes** have an open licence. It allows commercial use and derivatives, with attribution and the download date. EPPO Data Services needs an account and the licence must be accepted. The REST API returns hosts, categorisation and taxonomy, and needs a token. Global Database photos are "educational purposes only". No open licence was found for host or distribution content, so ship codes only and link out for the rest.

### Cited findings
- EPPO Codes Open Data Licence grant: "a worldwide, perpetual, free of charge, non-exclusive, personal right to use the EPPO Codes". Re-use must not mislead third parties or misrepresent the codes. Required notice: "Contains EPPO Codes (www.eppo.int)". — [EPPO Codes Open Data Licence](https://data.eppo.int/documentation/opendata)
- Freedoms granted: "reproduce, copy, publish and transmit the EPPO Codes", "build upon them in order to create Derivative information" and "exploit the EPPO Codes freely or commercially".
  - Attribution must name at least EPPO and give the date of last download.
  - The EPPO logo may not be used. No endorsement may be implied.
  - Scope is the EPPO Codes only. — [Open Licence PDF](https://data.eppo.int/media/Open_Licence.pdf)
- EPPO Data Services requires an account and acceptance of the Open Data Licence.
  - It offers a REST API and bulk code exports (TXT, XML, ZIP). SQLite is listed as "in preparation".
  - The page does not state pricing or redistribution terms for Global Database content. — [EPPO Data Services](https://data.eppo.int/)
- The pestr R client (MIT) documents access:
  - Hosts, categorisation, taxonomy and pests-of-host come through the REST API and need an EDS token.
  - Distribution is fetched from the Global Database without a token.
  - The SQLite names database must now be downloaded manually.
  - The client asks users to cite EPPO. — [pestr README](https://ftp.fau.de/cran/web/packages/pestr/readme/README.html)
- Global Database photo pages state: "All photos included on this page can only be used for educational purposes. For publication in journals, books or magazines, permission should be obtained from the original photographers." — [EPPO GD photos (example)](https://gd.eppo.int/taxon/STIVU/photos)

### Inferences
- EPPO codes are a good stable cross-reference key between pests and crops. They can be bundled in the repo with the required notice and download date.
- Host and distribution data from the API is not openly licensed. Treat it as fetch-on-demand by each user with their own token, or as a link-out only. Do not ship it in a bundled seed database until EPPO confirms in writing.
- EPPO photos cannot be used.

### Gaps
- The gd.eppo.int "about" and terms page did not load, so the reuse terms for host and distribution tables are **unverified**. EPDS pricing and quotas are also unverified.

## CABI Compendium and PlantwisePlus Knowledge Bank

### Takeaway
I found no primary-source evidence that CABI Compendium datasheets carry an open (CC) licence. Library guides still describe it as a licensed product. CABI's own Hugging Face release of selected Compendium datasheets is **CC BY-NC 4.0**, which signals that CABI content is non-commercial at best. PlantwisePlus factsheets have no stated open licence. Use both as link-out references only.

### Cited findings
- CABI's "Plant Health Knowledge for AI" dataset includes seven selected Compendium datasheets.
  - It is licensed **CC BY-NC 4.0**.
  - Commercial use requires contacting enquiries@cabi.org. — [Hugging Face: CABInternational](https://huggingface.co/datasets/CABInternational/Palm-Weevil-Content)
- The UC Davis library guide describes CABI Compendium access as "Limited to single user", with data available to researchers on request. — [UC Davis guide](https://guides.library.ucdavis.edu/plant-sciences/reference-sources)
- The Invasive Species Compendium was announced as "Open Access", but the announcement gives no licence. — [MU Libraries](https://library.missouri.edu/news/resources-and-services/cabi-announcements)
- The PlantwisePlus call for Knowledge Bank content seeks "open access factsheets, that we can link to". The site footer reads "© Copyright 2026 CABI". No CC licence is stated. — [PlantwisePlus blog](https://blog.plantwise.org/2020/05/18/call-for-content-knowledge-bank-factsheets/)
- CABI updated Wikipedia pages for 19 species from Plantwise content. "Individual copyright statements" were applied to Knowledge Bank content, but the post names no licence. — [PlantwisePlus blog](https://blog.plantwise.org/2020/12/16/cabi-helps-update-wikipedia-species-pages-to-help-spread-advice-on-fighting-crop-pests-and-diseases/)

### Inferences
- "Open access" (free to read) is not the same as an open licence. Datasheet text and images must not be copied into an MIT repo.
- The CABI-derived text already on Wikipedia is CC BY-SA under Wikipedia's licence. ShareAlike would apply to text that CropStack copies from it.

### Gaps
- The cabidigitallibrary.org Compendium page could not be fetched, so the current (2026) Compendium licence is **unverified**. The per-factsheet copyright on PlantwisePlus is also unverified.

## GBIF, iNaturalist and Wikimedia Commons (taxonomy, observations, CC photos)

### Takeaway
All three are usable if CropStack filters licences **per photo** and stores attribution.
- **iNaturalist:** default content licence is CC BY-NC. Filter with `photo_license=cc0,cc-by`, or use the AWS Open Data bucket with `photos.csv`.
- **GBIF:** records are CC0, CC BY or CC BY-NC. Filter with `license=CC0_1_0|CC_BY_4_0`.
- **Wikimedia Commons:** the imageinfo API with `extmetadata` returns the licence and author for each file.

### Cited findings
- GBIF accepts only CC0, CC BY and CC BY-NC for occurrence data. It promotes CC BY citation practice, and users of CC BY-NC data must act in good faith. Use of portal and web-service data is "at the user's own risk". — [GBIF terms](https://www.gbif.org/terms)
- GBIF occurrence search has a `license` filter (values `CC0_1_0`, `CC_BY_4_0`, `CC_BY_NC_4_0`) that applies to the "dataset or record", and a `mediaType=StillImage` filter. — [rgbif occ_search docs](https://docs.ropensci.org/rgbif/reference/occ_search.html)
- iNaturalist's default content licence is **CC BY-NC** unless the user chooses otherwise. The terms also say "Users may not use any iNaturalist data for training artificial intelligence, machine learning models" for commercial purposes. — [iNaturalist Terms](https://www.inaturalist.org/pages/terms)
- iNaturalist API recommended practice:
  - About 1 request per second and about 10k requests per day; HTTP 429 when over the limit.
  - More than 5 GB of media per hour or 24 GB per day may get a permanent block.
  - Set a custom User-Agent.
  - Use the GBIF research-grade export (DOI 10.15468/ab3s5x) or the exports for bulk data.
  - Results cap at 10k per query; up to 200 per page. — [iNat API practices](https://www.inaturalist.org/pages/api+recommended+practices)
- The `photo_license` filter accepts CC0, CC-BY, CC-BY-NC, CC-BY-SA, CC-BY-ND, CC-BY-NC-SA, CC-BY-NC-ND, "any" and "none". "An observation and its photos don't necessarily have the same licence." — [rinat get_inat_obs](https://docs.ropensci.org/rinat/reference/get_inat_obs.html)
- iNaturalist Open Data on AWS (bucket `inaturalist-open-data`):
  - More than 400M photos with metadata (`photos.csv.gz`, `observers.csv.gz`, `taxa.csv.gz`) and monthly snapshots.
  - Attribution pattern for CC0: "[observer], no rights reserved (CC0)".
  - Attribution pattern for other CC licences: "© [observer], some rights reserved ([licence])".
  - URL pattern: `https://inaturalist-open-data.s3.amazonaws.com/photos/[id]/medium.[ext]`. — [inaturalist-open-data GitHub](https://github.com/inaturalist/inaturalist-open-data)
- Wikimedia CommonsMetadata exposes LicenseShortName, LicenseUrl, UsageTerms and Artist/Credit through the imageinfo API with `iiprop=extmetadata`. — [Extension:CommonsMetadata](https://www.mediawiki.org/wiki/Extension:CommonsMetadata)

### Inferences
- Photo pipeline: query iNat or GBIF for taxon plus licence in {CC0, CC BY}. Store `photo_id`, licence, attribution string and source URL in the catalog. Hotlink, or cache only small sizes.
- Exclude NC (incompatible with commercial forks of an MIT app), ND and SA (SA would force the same licence on derivatives such as crops and overlays).
- Ship the photos' licences separately from the MIT code licence, for example in a `CREDITS` or `data/LICENSES` file.
- GBIF's `license` filter applies to the record, not each image, so check the image's own licence field too.

### Gaps
- The per-image `license` field in GBIF multimedia extension records was not verified on GBIF's API docs: **unverified**.
- The exact column list of iNat `photos.csv` was not shown on the page.

## UC IPM and USPest.org degree-day models

### Takeaway
UC IPM text and photos are © Regents. Commercial distribution is prohibited, and photos may not go into software without written consent. Model thresholds are facts that can be re-implemented with citation. USPest.org lists 160+ degree-day models and 22+ hourly disease models with published thresholds and biofix. It has no stated licence.

### Cited findings
- UC IPM site content is "copyright ©1995-2019 by the Regents of the University of California".
  - Text may be used for personal or educational reproduction with credits intact. Commercial distribution is prohibited.
  - Photos may not be used "in software, photo sets, or other electronic media" without written consent.
  - Linking is allowed. — [UC IPM copyright (archived 2019)](https://ipm.ucanr.edu/GENERAL/copyright.html)
- The UC IPM degree-day database was compiled "from published literature" into a standard format. It defines lower and upper developmental thresholds. — [UC IPM ddphenology](https://ipm.ucanr.edu/weather/ddphenology.html)
- USPest.org has "160 or more" degree-day species models.
  - These include "thresholds, biofix, calculation method, and key life stage/management events", with documentation and validation status.
  - It also has more than 22 hourly disease models (2020 figure).
  - No terms of use are stated. Funding comes from USDA-NIFA, APHIS and RMA. — [USPest FAQ](https://hopper.science.oregonstate.edu/wea/weafaq.html)

### Inferences
- Implement the degree-day engine (single-sine or triangle, with thresholds) in CropStack's own code.
- Encode per-pest parameters (lower and upper threshold °C, biofix, DD to life-stage events) as cited facts with a reference to the original paper, not copied UC IPM pages.
- Thresholds and constants are generally not copyrightable, but this is a legal judgement. The maintainer should keep citations.
- Many UC IPM and USPest models are calibrated for US climates. Flag them as unvalidated for Southern Hemisphere or South African use, and invert seasons for the biofix.

### Gaps
- The current ipm.ucanr.edu legal page did not load, so whether the 2019 terms have changed is **unverified**. I did not fetch the per-pest model tables, so no individual threshold values are given here.

## Weather-driven disease models published with parameters

### Takeaway
Several models are fully specified in public sources and can be coded directly:
- Hutton Criteria and Smith Period (late blight)
- TOM-CAST and Alternaria thresholds
- Gubler-Thomas grape powdery mildew index

Open-source reference implementations exist in NIBIO VIPS. The platform is AGPL-derived; the models are separate, with licence not verified.

### Cited findings
- **Hutton Criteria** (AHDB national system since 2017): "two consecutive days with a minimum temperature of 10°C and at least 6 hours each day with a relative humidity ≥90%." — [AHDB](https://potatoes.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria)
- **Smith Period:**
  - Full period: on each of 2 consecutive days, minimum temperature at least 10°C and at least 11 hours with RH ≥90%.
  - Near miss: the temperature criterion is met but only 10 humid hours on one or both days. — [Skelsey et al., EuroBlight 2013](https://web14.agro.au.dk/project2/euroblight/Workshop/2013Limassol/Proceedings/Page035-40_Skelsey.pdf)
- **TOM-CAST / Alternaria (NIBIO VIPS):**
  - Daily DSV comes from temperature and leaf-wetness hours.
  - Default lower temperature threshold is 13.0, described as the original TOMCAST value.
  - Risk bands: green below 15 DSV, yellow from 15, red at the threshold of 20.
  - Spraying resets the accumulation to 0.
  - The DSV lookup table itself is not in the README. — [NIBIO Model_ALTERNARIA](https://gitlab.nibio.no/VIPS/models/java/Model_ALTERNARIA/-/commit/4bb438ba6e743c74458d27ee9eb54c86f2410437.diff)
- **Gubler-Thomas powdery mildew index (grape, conidial):**
  - Starts after 3 consecutive days, each with 6 continuous hours at 70–85°F (21–30°C).
  - +20 per qualifying day; −10 for a day without 6 continuous hours (a break means more than 45 minutes outside the band).
  - −10 for 15 or more minutes at 95°F (35°C) or above.
  - The index is clamped to 0–100.
  - Spray intervals: 0–30 → label maximum; 40–50 → intermediate; 60–100 → label minimum. Reset after treatment.
  - The ascospore stage uses the Mills table at about two-thirds of the wetness hours. — [UC IPM model DB](https://ipm.ucanr.edu/DISEASE/DATABASE/grapepowderymildew.html); [APS feature](https://www.apsnet.org/edcenter/apsnetfeatures/Pages/UCDavisRisk.aspx) (APS page "All rights reserved"; it states the heat penalty inconsistently)
- **NIBIO licence:** the VIPS platform licence "is based on the GNU Affero General Public License, version 3". It covers the platform, but "not the specific forecasting models, their algorithms, or their implementations". — [NIBIO licence diff](https://gitlab.nibio.no/VIPS/VIPSLogic/-/commit/d8478af270408fb9173f17a76a4871a70dcb3492.diff)
- **BLITECAST / Wallin:** sources exist, including the MSU severity-value page and the Plant Disease 1980 paper.
  - The MSU fetch was blocked, so I could not extract the parameters. — [MSU svalue](https://www.canr.msu.edu/psbp/resources/svalue); [Plant Disease 64:1103 (1980)](https://apsnet.org/publications/plantdisease/backissues/Documents/1980Articles/PlantDisease64n12_1103.PDF)

### Inferences
- Hutton, Smith and Gubler-Thomas can be implemented from the rules above with hourly temperature and RH only. Leaf wetness can be approximated as RH ≥90%; flag this as an approximation.
- Do not copy NIBIO code into the MIT repo, because of the AGPL-derived licence. Re-implement from the published rules.
- Most home gardeners will lack leaf-wetness sensors, so the RH-only models (Hutton, Smith) are the best defaults.

### Gaps
- The Wallin/BLITECAST DSV table and the TOM-CAST DSV table values were not extracted in this session.
- Downy mildew models (for example the grape 10-10-24 rule) were not researched.
- The licence of individual NIBIO model repos is **unverified**.

## Open image datasets for AI diagnosis

### Takeaway
The PlantVillage licence is **inconsistent across sources** (CC BY-SA 3.0 per an AI summary; the arXiv page links CC BY-NC-SA 4.0; the GitHub mirror has no LICENSE). Treat it as **unverified or NC** and do not bundle it. PlantDoc (CC BY 4.0) and DeepWeeds (CC BY 4.0) are clean. Most nutrient-deficiency datasets found are NC.

### Cited findings
- PlantVillage on arXiv 1511.08060: "over 50,000 expertly curated images". The arXiv page links a **CC BY-NC-SA 4.0** licence, which may be the paper's licence rather than the images'. — [arXiv](https://arxiv.org/abs/1511.08060)
- An alphaXiv overview claims "Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)". This is AI-generated and not verified. — [alphaXiv](https://alphaxiv.org/abs/1511.08060)
- The spMohanty/PlantVillage-Dataset GitHub repo has no LICENSE file. — [GitHub](https://github.com/spMohanty/PlantVillage-Dataset)
- TFDS lists 54,303 images in 38 classes and gives no dataset-specific licence. — [TFDS](https://www.tensorflow.org/datasets/catalog/plant_village)
- PlantDoc: LICENSE.txt is **CC BY 4.0**. It has 2,598 data points, 13 species and up to 17 disease classes. — [PlantDoc GitHub](https://github.com/pratikkayal/PlantDoc-Dataset)
- DeepWeeds: images and annotations are **CC BY 4.0**, and the code is Apache 2.0. It has 17,509 images of 8 Australian weed species plus a negative class. — [Zenodo](https://zenodo.org/record/7939059)
- DND-SB (sugar beet nutrient deficiency): 5,648 images, 7 fertiliser treatments, **CC BY-NC-SA 4.0**. — [Zenodo](https://zenodo.org/records/4106221)
- iNaturalist bans using its data for commercial AI training. — [iNat Terms](https://www.inaturalist.org/pages/terms)

### Inferences
- For a local vision model shipped with CropStack, train only on CC0 or CC BY data (PlantDoc, DeepWeeds, CC0 or CC BY iNat photos) and document the training-data licences.
- Otherwise, let users download weights themselves and keep NC datasets out of the repo.

### Gaps
- Several Mendeley nutrient-deficiency datasets (banana, maize, pepper, rose) were found but their licences were not verified: **unverified**. I found no CC BY-licensed text reference for nutrient-deficiency symptoms.

## Natural enemies, beneficials, pollinators and host-pathogen links

### Takeaway
GloBI is the best open source for host-pathogen, parasitoid-host, predator-prey and pollinator-plant links. It offers an API, plus versioned Zenodo dumps and DuckDB/SQLite-ready TSV, CSV and Parquet. It has no single licence: attribution follows each source dataset.

### Cited findings
- GloBI aggregates open interaction data (predator-prey, pollinator-plant, pathogen-host, parasite-host). Users should credit the original contributors and cite datasets. Each record carries a citation. — [GloBI about](https://www.globalbioticinteractions.org/about)
- Access:
  - Web API, rglobi, and versioned Zenodo releases (doi:10.5281/zenodo.3950589).
  - TSV, CSV and Parquet interaction tables, a Darwin Core Archive, and Neo4j.
  - Loadable in SQLite or DuckDB.
  - No overall licence is named. — [GloBI data](https://globalbioticinteractions.org/data)

### Inferences
- Filter GloBI rows by source dataset licence. Use them to seed `pathogenOf`, `parasitoidOf` and `visitsFlowersOf` edges between crop and organism taxa, and keep the citation per edge.

### Gaps
- I did not verify a dedicated pollinator-plant dataset with an open licence, or a natural-enemy database such as BioControl/BIOCAT, in this session.

## Pesticide data: South Africa, PPDB, EPA, organic lists

### Takeaway
- **PPDB** forbids redistribution and derived databases, and integration needs a paid licence. Do not use it as a data source; link only.
- **South Africa:** Act 36 of 1947 governs registration through DALRRD (now the Department of Agriculture). I found no open, machine-readable register.
- **US EPA PPLS:** label PDFs are public under the EPA data licence, but are US-only.
- **Recommendation:** model treatments generically by active ingredient or type, and tell users to check the local label.

### Cited findings
- PPDB / AERU conditions:
  - Free for "academic and non-commercial use" with citation.
  - "Data may not be copied, reproduced, republished, posted, broadcast or transmitted".
  - "Users are not entitled to distribute, modify, supplement or split the contents".
  - Integration into tools "will be subject to a licence fee".
  - Only "unsubstantial parts" may be extracted, for non-commercial use. — [AERU conditions of use](https://aeru.herts.ac.uk/aeru/iupac/docs/Conditions_of_use.pdf)
- DALRRD publishes registration guidelines for agricultural remedies under Act 36 of 1947. — [DALRRD guideline](https://old.dalrrd.gov.za/doaDev/sideMenu/ActNo36_1947/AIC/Guideline%20for%20Registration%20Process%20for%20Agricultural%20Remedies%202015.pdf)
- Agribook points to AgriIntel ("A database of agrochemicals... for South Africa") and to the Department's *Guide for the Control of Plant Pests/Diseases*. No data terms are stated. — [Agribook](https://www.agribook.co.za/?p=28)
- EPA PPLS contains FIFRA Section 3 label PDFs, at access level "public" under the EPA Data License. — [data.gov PPLS](https://catalog.data.gov/dataset/pesticide-product-label-system)

### Inferences
- The treatment ladder should be generic (cultural → mechanical → biological → organic-approved chemistry → conventional), keyed to active ingredient and mode-of-action group, with a user-local "check registration and label" step.
- Do not ship product names or withholding periods unless they come from an open regulator source per country.
- OMRI is proprietary, as stated in the brief; this was not re-verified.

### Gaps
- No public, machine-readable South African registered-products database was found. CropLife SA's terms are **unverified**.
- Bee-toxicity open data (for example EPA ECOTOX) and the terms of open organic input lists (for example EU Regulation 2021/1165 Annex I, which is likely reusable as EU law) were not verified.

## South African sources (ARC-PPRI, SANBI)

### Takeaway
I found no open licence for ARC-PPRI content. South African biodiversity records are best reached through GBIF, where each dataset carries a CC0, CC BY or CC BY-NC licence.

### Cited findings
- ARC-PPRI runs the National Collection of Insects (page found; no data licence seen). — [ARC-PPRI NCI](https://arc.agric.za/arc-ppri/Pages/Biosystematics/National-Collection-of-Insects.aspx)
- GBIF dataset licences are limited to CC0, CC BY and CC BY-NC. — [GBIF terms](https://www.gbif.org/terms)

### Gaps
- SANBI and SABIF data terms and ARC-PPRI terms of use: **unverified** (no primary terms pages were retrieved).
