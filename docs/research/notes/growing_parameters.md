# Open, citable sources of practical growing parameters for CropStack

Scope: sources for germination temperatures and emergence times, sowing depth, spacing, maturity, GDD and phenology, frost and stress temperatures, photoperiod and vernalization, chill requirements, FAO-56 Kc, yield, seed longevity, and produce storage life, with the reuse terms checked on each primary page where possible (as of 2026-10-09). Legal analysis (Feist, database rights) is out of scope. I only record the stated licences and terms. "Unverified" means I could not load the primary licence page during this session.

## 1. FAO Irrigation & Drainage Paper 56 (Kc, stage lengths, root depth, p): licence and machine-readable versions

### Takeaway
FAO-56 (1998) is "All rights reserved" and is not under a Creative Commons licence. FAO's open-access policy says CC licences do not apply to works published before June 2018, and commercial use of pre-2024 publications needs a licence request. However, USDA-ARS's **pyfao56** ships FAO-56 Tables 11, 12, 17 and 22 as Python data under **CC0 / US public domain**. That makes it the cleanest machine-readable route, with FAO-56 cited as the original source of the values. AquaCrop-OSPy is Apache-2.0.

### Cited Findings
- FAO-56 ("Crop evapotranspiration", Allen et al.) is "© FAO 1998", ISBN 92-5-104219-5. Its notice reads: "No part of this publication may be reproduced, stored in a retrieval system, or transmitted in any form or by any means" without prior permission, and requests go to the Director, Information Division, FAO, Rome — [FAO-56 online, x0490e00](https://www.fao.org/4/x0490e/x0490e00.htm)
- FAO's open-access policy:
  - Default licence is CC BY 4.0 from 1 July 2024, and the revised policy took effect on 23 December 2024.
  - Works from June 2018 to December 2024 that show a CC IGO 3.0 icon stay under that licence.
  - "Creative Commons licences do not apply to works published before June 2018."
  - Commercial use of publications released before 23 Dec 2024 requires a request via fao.org/contact-us/licence-request.
  - [FAO Policy on Open Access (PDF)](https://openknowledge.fao.org/bitstreams/6e7af061-3928-4c55-99c5-6b5e4cb8e3f0/download)
- FAO's general website terms allow copying "for private study, research and teaching purposes" with acknowledgement. Requests for "translation and adaptation rights, and for resale and other commercial use rights" go to FAO's licence request form — [FAO Terms](https://www.fao.org/contact-us/terms/en/)
- pyfao56 LICENSE.md: "As a work of the United States Government, this package is in the public domain within the United States. Additionally, we waive copyright and related rights in the work worldwide through the CC0 1.0 Universal public domain dedication." — [pyfao56 LICENSE.md (raw)](https://raw.githubusercontent.com/kthorp/pyfao56/main/LICENSE.md); [repo](https://github.com/kthorp/pyfao56)
- pyfao56 `tools/tables.py` holds the following, searchable by crop name and synonym through a `FAO56Tables` class (created 12/12/2024 by Reagan Ames and Tyler Pokoski) — [pyfao56 tables.py (raw)](https://raw.githubusercontent.com/kthorp/pyfao56/main/src/pyfao56/tools/tables.py)
  - FAO-56 Table 11: lengths of crop development stages
  - Table 12: single Kc (Kc ini/mid/end, plus hmax)
  - Table 17: basal Kcb
  - Table 22: maximum root depth Zr and depletion fraction p
- AquaCrop-OSPy (Python port of FAO AquaCrop) is Apache-2.0 — [aquacrop LICENSE (raw)](https://raw.githubusercontent.com/aquacropos/aquacrop/master/LICENSE); [repo](https://github.com/aquacropos/aquacrop)
- AquaCrop-OSPy's crop class exposes these parameters, with a 'Maize' default visible in code — [aquacrop crop.py (raw)](https://raw.githubusercontent.com/aquacropos/aquacrop/master/aquacrop/entities/crop.py)
  - Thermal parameters: Tbase, Tupp
  - Stage timings in GDD or calendar days: Emergence, MaxRooting, Senescence, Maturity, HIstart, Flowering
  - Cold and heat stress: PolColdStress, PolHeatStress, TrColdStress
  - Root depth: Zmin, Zmax
  - Kcb, plus other fields

### Inferences
- For Kc/Kcb, stage lengths, Zr and p, CropStack can import pyfao56's tables (CC0) and attribute each value to "Allen et al. 1998, FAO-56 Table X". That gives per-value provenance without copying FAO's prose. Whether facts transcribed from a copyrighted table are free to reuse is a question for the legal researcher.
- FAO-56 covers many vegetables, including tomato, pepper, lettuce, onion, carrot, brassicas, cucurbits, beans and potato. Its stage lengths are given per climate and region and planting month, which suits a location-aware planner.

### Gaps
- I did not open the AquaCrop-OSPy built-in crop parameter list, so I don't know which vegetables beyond maize, wheat and others are included. The FAO AquaCrop (Windows) standalone .CRO crop file licence was not checked.
- I did not count the exact number of crops in pyfao56's tables.

## 2. US government public-domain sources and US extension publication terms

### Takeaway
USDA-ARS Agriculture Handbook 66 (2016) is the strongest public-domain source for produce storage life: 138 commodities, published by a US federal agency, although the PDF carries no explicit PD notice. University extension publications (OSU, UNL, UF/IFAS EDIS, USU) generally carry ordinary university copyright. None of the extension pages I checked showed a CC licence on the relevant content.

### Cited Findings
- USDA ARS Agriculture Handbook 66, *The Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks*, was revised in February 2016 (a complete revision of the 1986 edition). It has 138 commodity summaries in 17 chapters. The PDF has no explicit copyright or PD statement and says it "in its entirety is freely accessible on the Internet." — [USDA ARS AH-66 PDF](https://www.ars.usda.gov/arsuserfiles/oc/np/commercialstorage/commercialstorage.pdf)
- OSU Extension "Soil temperature conditions for vegetable seed germination" (J. F. Harrington, UC Davis; published April 2013, reviewed 2024) — [OSU Extension](https://extension.oregonstate.edu/es/catalog/soil-temperature-conditions-vegetable-seed-germination)
  - It reproduces the Harrington tables: min/optimum range/optimum/max soil temperature for 24 crops, and days to emergence for 25 crops at soil temperatures from 32°F to 104°F.
  - The footer reads "Copyright © 1995–2023 Oregon State University", and there is no CC licence on the article. A CC BY label appears only on an unrelated image.
- UNL Extension G2090, "Vegetable Garden Seed Storage and Germination Requirements" (June 2011) — [UNL G2090](https://extensionpubs.unl.edu/publication/g2090/na/html/view)
  - Table I gives "Relative Longevity under Cool, Dry Condition (Years)".
  - The table cites Knott's *Handbook for Vegetable Growers* (1988, Wiley) and Splittstoesser's *Vegetable Growing Handbook* (1979, AVI).
  - The page has no licence statement.
- UF/IFAS EDIS Vegetable Production Handbook chapter (2018): the article page states no licence — [EDIS on FLVC](https://journals.flvc.org/edis/article/view/107111)
- Utah Vegetable Production Guide (5th ed., USU Digital Commons): the page shows no CC licence. It is NIFA grant-funded (2021-70006-35687), but no licence follows from that — [USU Digital Commons](https://digitalcommons.usu.edu/extension_curall/2460)
- The Mid-Atlantic Commercial Vegetable Production Recommendations (Penn State, Rutgers and others) is a multi-state annual guide with crop-by-crop sections — [Penn State Extension](https://extension.psu.edu/mid-atlantic-commercial-vegetable-production-recommendations-sections). The licence was not checked.

### Inferences
- Extension tables are mostly re-publications of Harrington (UC Davis, 1950s), Knott's, or USDA handbooks. For per-value sourcing, cite the original (Harrington, Knott's) plus the extension page that is accessible.
- Treat extension text as copyrighted. Record only numeric facts with a citation, and leave the copyright question to the legal researcher.

### Gaps
- UC ANR and Penn State reuse terms: the UC ANR germination page failed to load and the OSU copyright page errored, so both are **unverified**.
- I found no confirmed CC-licensed US extension vegetable-parameter publication.
- USDA-ARS GRIN-Global (germination test protocols, seed data) and USDA NRCS PLANTS were not checked in this session.
- Knott's Handbook (5th ed., Maynard & Hochmuth, Wiley 2007) is commercially copyrighted. I did not verify the current edition or its terms.

## 3. Soil-temperature germination tables and seed-company data

### Takeaway
The widely reproduced Harrington (UC Davis) tables give min/opt/max soil temperature for about 24 crops and days to emergence at 32–104°F for about 25 crops. They circulate via OSU, UC Master Gardener and others under ordinary copyright. Seed-company catalogs (Johnny's, Kitazawa) could not be checked for terms.

### Cited Findings
- Harrington tables as reproduced by OSU: 24 crops (asparagus, beans, beets, cabbage, carrots, cauliflower, chard, corn, cucumber, eggplant, lettuce, muskmelon, onion, parsley, parsnip, peas, peppers, pumpkin, radish, spinach, squash, tomato, turnip, watermelon), with days to emergence by soil temperature — [OSU Extension](https://extension.oregonstate.edu/es/catalog/soil-temperature-conditions-vegetable-seed-germination)
- The UC Master Gardener Program hosts the same "Soil Temperature Conditions for Vegetable Seed Germination" content — [UC ANR MG page](https://ucanr.edu/program/uc-master-gardener-program/seed-germination-temperature-and-timing). Its terms are **unverified** because the fetch failed.

### Inferences
- Germination cardinal temperatures and days to emergence for the about 24 core vegetables can be sourced as "Harrington, J.F. (UC Davis), via OSU Extension (2013, reviewed 2024)".
- Herbs and minor crops need other sources.

### Gaps
- The original Harrington 1954 / Harrington & Minges 1954 citation details were not confirmed.
- Johnny's Selected Seeds terms page failed to load. Kitazawa was not checked. Both are **unverified**.

## 4. Phenology/GDD: open crop model parameter sets and the BBCH scale

### Takeaway
- **BBCH monograph (Meier, JKI 2018): CC BY 4.0, verified.** It has stage codes for most common vegetables, which is ideal for a phenology vocabulary.
- **DSSAT CSM: BSD-3-Clause, verified.** Its genotype files include tomato, pepper, cabbage, green bean, potato, beet and others.
- **APSIM: a bespoke "General Use" licence** (fee-free, revocable, IP vesting clauses), so it is not OSI-open.
- **PCSE (WOFOST engine): EUPL 1.1+.**
- The WOFOST crop parameter repo licence is **unverified**. It holds about 23 crops, mostly field crops.

### Cited Findings
- BBCH monograph "Growth stages of mono- and dicotyledonous plants", ed. U. Meier, Julius Kühn-Institut, Quedlinburg, 2018 — [BBCH English PDF, OpenAgrar](https://www.openagrar.de/servlets/MCRFileNodeServlet/openagrar_derivate_00016780/BBCH%20ENGLISCH_%20.pdf)
  - Licence: "This work is licensed under a Creative Commons Attribution 4.0 International License."
  - It is a digitised version of the 1997 Blackwell edition, and the document says "The scientific content is identical."
  - Vegetable scales cover onion, garlic, shallot, carrot, celeriac, kohlrabi, swede, chicory, radish, cabbage, Chinese cabbage, lettuce, spinach, kale, Brussels sprout, cauliflower, broccoli, cucumber, melon, pumpkin, watermelon, tomato, aubergine, paprika, pea and bean.
- DSSAT CSM licence: "Copyright (c) 2021, DSSAT Foundation", BSD-3-Clause — [DSSAT license.txt (raw)](https://raw.githubusercontent.com/DSSAT/dssat-csm-os/develop/license.txt); [repo](https://github.com/DSSAT/dssat-csm-os)
- DSSAT cultivar files that exist in `Data/Genotype` (HTTP 200) — [DSSAT repo, Data/Genotype](https://github.com/DSSAT/dssat-csm-os/tree/develop/Data/Genotype)
  - TMGRO048.CUL (tomato), PRGRO048.CUL (bell pepper), CBGRO048.CUL (cabbage), GBGRO048.CUL (green bean), PTSUB048.CUL (potato), BSCER048.CUL (sugar beet), PNGRO048.CUL (peanut), TRARO048.CUL (taro/aroids), CNGRO048.CUL (canola), SWCER048.CUL
  - Not found at the guessed names: cucumber, onion, strawberry
- APSIM licence: "a limited non-exclusive, fee-free, revocable, worldwide, non-sublicensable and non-transferable, General Use licence", with clauses that vest IP in "Improvements" in the Licensor — [ApsimX LICENSE.md (raw)](https://raw.githubusercontent.com/APSIMInitiative/ApsimX/master/LICENSE.md)
- PCSE: "Copyright 2024 Wageningen Environmental Research ... Licensed under the EUPL, Version 1.1 or ... subsequent versions" — [PCSE LICENSE (raw)](https://raw.githubusercontent.com/ajwdewit/pcse/master/LICENSE)
- WOFOST crop parameters repo — [repo](https://github.com/ajwdewit/WOFOST_crop_parameters)
  - It states parameter sets for 23 crops, and the README names barley, chickpea, millet, mungbean, potato, soybean and sorghum.
  - Parameters include TSUMEM (emergence temperature sum, e.g. 90), TSUM1 (emergence→anthesis, e.g. soybean 500) and TSUM2 (anthesis→maturity, e.g. 1300).
  - Licence **unverified**: the LICENSE fetch returned 404 or an error.

### Inferences
- DSSAT `.CUL`/`.ECO`/`.SPE` files (BSD-3) are the best open source for cardinal temperatures (base/optimum/upper) and stage thermal-time targets for tomato, pepper, cabbage, snap bean and potato. They are model-calibration values, not gardener rules of thumb, so label them as such.
- Use BBCH codes (CC BY 4.0, attribute JKI/Meier) as CropStack's stage vocabulary.
- Avoid embedding APSIM parameter files in an MIT repo because of the revocable bespoke licence. Citing values is a separate legal question.

### Gaps
- I did not parse the DSSAT species files for actual base/upper temperatures, so I can't list them.
- WOFOST repo licence and full crop list: **unverified**.
- I found no open-access review table of vegetable base temperatures. The IRTA repository record was access-denied.

## 5. Chill requirements for fruit trees by cultivar

### Takeaway
chillR (GPL-3) provides chill models (Chilling Hours, Utah, Dynamic/chill portions) but, from its manual index, apparently no cultivar-requirement dataset. The best open compilation found is Fadón et al. 2020 (*Agronomy* 10(3):409, MDPI) with about 530 Prunus cultivars across eight species in CH, CU and CP. Its CC licence was not confirmed on the primary page.

### Cited Findings
- chillR v0.77 (CRAN, published 2025-12-11), License: GPL-3 — [CRAN DESCRIPTION](https://cran.r-project.org/web/packages/chillR/DESCRIPTION)
  - Functions include Chilling_Hours, Dynamic_Model, GDH and daylength — [rdrr.io chillR index](https://rdrr.io/cran/chillR/)
  - No cultivar chill-requirement dataset was visible in the index I saw (see Gaps).
- Fadón, Herrera, Guerrero, Guerra & Rodrigo (2020), "Chilling and heat requirements of temperate stone fruit trees (Prunus sp.)", *Agronomy* 10(3):409, doi:10.3390/agronomy10030409 — [MDPI article](https://www.mdpi.com/2073-4395/10/3/409); [Zaguán record](https://zaguan.unizar.es/record/88572?ln=en)
  - Tables 1–7 list chill requirements per cultivar for almond, apricot (European and Japanese), peach, plum (European and Japanese) and cherry, in chill hours, chill units and chill portions, plus GDH heat requirements.
  - It reports 530 cultivars, though the peach count is internally inconsistent: 204 vs 216.
  - The Zaguán repository record shows a Creative Commons notice without naming the version.
  - The MDPI page text I received showed no licence, so the licence is **unverified**. MDPI journals are normally CC BY 4.0, but I did not confirm this here.
- CITA Aragón repository lists "Agroclimatic requirements of temperate fruit trees" — [citaREA](https://citarea.cita-aragon.es/items/4a8d8e71-807c-462c-9ef1-fd12e7930af0/full). Its metadata did not load.

### Inferences
- Fadón et al. 2020 can seed stone-fruit cultivar chill data with per-value citation.
- Apple, pear, blueberry and other pome fruit and small fruit still need other sources.
- For South African users, chill portions (Dynamic Model) are preferable to chill hours in warm-winter climates. This is common practice and not verified here.

### Gaps
- UC Davis Fruit & Nut chill pages failed to load: **unverified**.
- I found no open apple/pear cultivar chill dataset.
- chillR may include example phenology datasets (e.g. KA_bloom), but none are cultivar-requirement tables. Not confirmed.

## 6. Seed longevity

### Takeaway
Extension seed-longevity tables (e.g. UNL G2090) derive from Knott's and Splittstoesser, both copyrighted books. The Kew Seed Information Database (SID) has moved to SER/INSR and has no stated data licence. I found no open-licensed vegetable seed-longevity table.

### Cited Findings
- UNL G2090 gives a longevity-in-years column sourced from Knott's (1988) and Splittstoesser (1979). The page has no licence — [UNL G2090](https://extensionpubs.unl.edu/publication/g2090/na/html/view)
- SID now has a new host — [SER-INSR SID page](https://ser-insr.org/seed-information-database); [ser-sid.org](https://ser-sid.org/)
  - "INSR is the new host of the Seed Information Database (SID)", where INSR is SER's International Network for Seed-based Restoration.
  - It holds 54,803 taxa and 182,232 records.
  - Fields include seed weight, storage behaviour and germination requirements.
  - The page states no licence or terms.
- data.gov.uk lists SID (publisher: Royal Botanic Gardens, Kew) with Licence: "Not set" — [data.gov.uk SID](https://www.data.gov.uk/dataset/seed-information-database--sid)
- Kew's planned discontinuation of SID prompted a 2022 SER-INSR appeal — [SER-INSR news](https://ser-insr.org/news/2022/2/15/please-kew-dont-drop-the-sid-seed-information-database)

### Inferences
- Seed longevity years must be cited to Knott's or extension pages as facts. SID storage behaviour (orthodox/recalcitrant) is of limited use for vegetables.

### Gaps
- SID terms of use: **unverified**.
- Seed Savers Exchange tables were not checked.
- USDA-ARS NLGRP longevity data were not checked.

## 7. South African sources (ARC, Department of Agriculture, seed companies)

### Takeaway
ARC-VOPI publishes vegetable production guidelines. The ARC website terms allow you to "retrieve, store, cite or refer to or print" material, but forbid reproducing, publishing or adapting it without written permission. ARC guidelines can therefore be cited but not copied. Terms for the DALRRD/DoA guideline series, Starke Ayres and Hygrotech were not verified.

### Cited Findings
- ARC-VOPI production guidelines cover summer crops (tomato, Swiss chard, sweet potato, cucurbits, green beans, African leafy vegetables) and winter crops (cabbage, carrot, beetroot, onion, potato). A printed sweet potato guide costs R180 — [ARC-VOPI Production Guidelines](https://arc.agric.za/arc-vopi/Pages/Production-Guidelines.aspx)
- ARC Terms (last updated September 2014) — [ARC Terms and Conditions](https://www.arc.agric.za/Pages/Terms-and-Conditions.aspx)
  - ARC owns copyright in all materials, including "data".
  - Permission is given to "retrieve, store, cite or refer to or print material".
  - Without prior written permission you may not "reproduce, retransmit, distribute, publish, broadcast, adapt...".

### Inferences
- Cite ARC values per crop (e.g. SA sowing months by region) as references only, and don't embed text.
- South African planting calendars by climatic region are valuable for the maintainer's local users.

### Gaps
- DALRRD (now Dept. of Agriculture) "Production guidelines" series: terms **unverified**.
- Starke Ayres and Hygrotech guides: terms not checked.

## 8. Open-access (CC BY) peer-reviewed compilations of vegetable parameters

### Takeaway
I confirmed only one open compilation, Fadón et al. 2020 (MDPI) for stone-fruit chill, and its licence is only partially verified. Broad CC BY compilations of vegetable cardinal temperatures, photoperiod, vernalization or frost-kill temperatures were not found in this session.

### Cited Findings
- Fadón et al. 2020, *Agronomy* 10:409 — [MDPI](https://www.mdpi.com/2073-4395/10/3/409)

### Inferences
- For frost and lethal temperatures, photoperiod and bulbing, vernalization and bolting, and yield per m², CropStack will likely depend on these, all cited per value:
  - DSSAT species files (BSD-3), for cardinal and stress temperatures
  - BBCH (CC BY 4.0), for stage definitions
  - Extension and Knott's facts

### Gaps
- No sources were found or checked for:
  - Square-foot gardening counts. Mel Bartholomew's *Square Foot Gardening* is copyrighted, and no open table was found.
  - Yield per m².
  - Photoperiod and vernalization tables.
  - Frost-kill temperatures for vegetables.
- I did not run searches of Zenodo, Dryad or GBIF/TRY.
- The TRY plant trait database has restricted terms, from memory, so it is unverified.
