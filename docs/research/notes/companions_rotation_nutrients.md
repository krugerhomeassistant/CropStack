# Companion planting, crop rotation and crop nutrient demand: evidence and open data for CropStack

Research date: 2026-10-09. I checked DOIs against the Crossref API: each DOI resolves to the title given. For papers marked "(title/TLDR only)", I could not read the abstract or full text, so do not claim specific numbers from them.

## 1. Peer-reviewed evidence on companion planting and intercropping in vegetables

### Takeaway
Strong evidence supports some claims and not others:
- **Supported:** Mixing plants (intercropping, trap crops, push-pull, flowering plants) reduces herbivore pests and crop damage on average across meta-analyses. Marigold's effect on whitefly on tomato has direct experimental support.
- **Weak or mixed:** Yield effects are mixed, and the effect of marigolds on nematodes varies.
- **Little or no support:** Most specific "X helps Y" pairs in popular lists have little or no direct testing. CropStack should label pairs "traditional" unless a pair-specific study exists.

### Cited Findings
**Meta-analyses (broad diversification)**
- **Seimandi-Corda et al. 2026**, *Agronomy for Sustainable Development* 46:19, DOI 10.1007/s13593-025-01082-7, CC BY 4.0. The study covers 449 publications and 19,421 observations.
  - Intercropping cut herbivore abundance by 39% (95% CI −47 to −29%) and crop damage by 30% (95% CI −46 to −8%).
  - Intercropping raised predators by 48% and parasitoids by 56%.
  - Flower strips had no significant effect on herbivores.
  - Results depend on sowing time, spatial layout and companion-crop use.
  - Between-study variability was high, and yield was not analysed.
  - [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12946007/)
- **Letourneau et al. 2011**, "Does plant diversity benefit agroecosystems? A synthetic review", *Ecological Applications*, DOI 10.1890/09-2026.1. The study covers 552 experiments in 45 articles.
  - Diversified crops had significantly stronger herbivore suppression, natural-enemy enhancement and crop-damage suppression.
  - Mean crop yield effect was "relatively small, but significantly negative", partly because the main crop was planted at lower density.
  - [OpenAlex abstract](https://api.openalex.org/works/doi:10.1890/09-2026.1); [PDF](https://people.ucsc.edu/~dletour/migrated/lab/documents/LetArmSalLeretal.EA2011.pdf)
- **Iverson et al. 2014**, "Do polycultures promote win-wins or trade-offs…? A meta-analysis", *Journal of Applied Ecology*, DOI 10.1111/1365-2664.12334. The study covers 26 studies and 301 observations.
  - Win-wins between per-plant yield and biocontrol occurred when planting was substitutive.
  - Additive planting with a legume as the secondary crop gave a biocontrol benefit with no loss of main-crop yield per area.
  - [OpenAlex](https://api.openalex.org/works/doi:10.1111/1365-2664.12334)
- **Martin-Guay et al. 2018**, "The new Green Revolution: sustainable intensification of agriculture by intercropping", *Science of the Total Environment*, DOI 10.1016/j.scitotenv.2017.10.024 (title/TLDR only). It is described as the first global meta-analysis of intercrop benefits and found intercropping beneficial under both stressful and non-stressful moisture conditions. [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/j.scitotenv.2017.10.024)
- **Li et al. 2020**, "Syndromes of production in intercropping impact yield gains", *Nature Plants*, DOI 10.1038/s41477-020-0680-9 (title only; this is a yield/LER meta-analysis, so check the abstract before citing figures). [Crossref](https://api.crossref.org/works/10.1038/s41477-020-0680-9)
- **Ratnadass et al. 2012**, "Plant species diversity for sustainable management of crop pests and diseases in agroecosystems: a review", *Agronomy for Sustainable Development*, DOI 10.1007/s13593-011-0022-4, CC BY-NC.
  - It lists the mechanisms: resource dilution and stimulo-deterrent diversion, disruption of spatial and temporal cycles, allelopathy, soil suppressiveness, crop physiological resistance, and natural-enemy conservation.
  - [OpenAlex](https://api.openalex.org/works/doi:10.1007/s13593-011-0022-4)
- **Tooker & Frank 2012**, cultivar mixtures for insect pest management, *Journal of Applied Ecology*, DOI 10.1111/j.1365-2664.2012.02173.x (TLDR only). It concerns intraspecific diversity, not companion pairs. [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1111/j.1365-2664.2012.02173.x)

**Trap crops and push-pull**
- **Shelton & Badenes-Perez 2006**, "Concepts and applications of trap cropping in pest management", *Annual Review of Entomology*, DOI 10.1146/annurev.ento.51.110104.150959. It finds trap cropping "more knowledge-intensive than many other forms of pest management": success depends on spatial and temporal deployment and on pest behaviour. [OpenAlex](https://api.openalex.org/works/doi:10.1146/annurev.ento.51.110104.150959)
- **Cook, Khan & Pickett 2007**, "The use of push-pull strategies in integrated pest management", *Annual Review of Entomology*, DOI 10.1146/annurev.ento.52.110405.091407. Push-pull combines stimuli that make the crop unattractive (push) with lures (pull) and is usually integrated with biocontrol. [OpenAlex](https://api.openalex.org/works/doi:10.1146/annurev.ento.52.110405.091407)
- **Sarkar et al. 2018**, "Application of trap cropping as companion plants…: a review", *Insects* 9:128, DOI 10.3390/insects9040128, CC BY 3.0. [MDPI](https://www.mdpi.com/2075-4450/9/4/128) Reported pairs with field reports:
  - Indian mustard to protect cabbage and crucifers from diamondback moth
  - White cabbage to protect Chinese cabbage from flea beetles
  - Black mustard to protect sweet corn from *Nezara viridula* (kernel injury cut by 22%)
  - Silking corn border to protect tomato from *Helicoverpa zea*
  - Buckwheat to protect onion from thrips
  - Napier grass with Desmodium to protect maize from stem borer (push-pull, Kenya)

  Stated limits:
  - There is little consensus on optimal systems.
  - Pests can disperse back from trap plants.
  - Trap crops should cover about 2–10% of the area.
  - Supplemental control is often needed.

**Aphids and aromatic companions**
- **Ben-Issa, Gomez & Gautier 2017**, "Companion plants for aphid pest management", *Insects* 8:112, DOI 10.3390/insects8040112, CC BY 3.0. This is a narrative review, not a meta-analysis. [MDPI](https://www.mdpi.com/2075-4450/8/4/112)
  - Mechanisms: trap, masking, repellence by volatiles, altered host acceptability, and natural-enemy support.
  - Examples: basil and savory reduced *Aphis fabae* on faba bean; garlic delayed and reduced green peach aphid on tobacco; onion and garlic reduced mustard aphid; coriander reduced aphids on cabbage only early in the season.
  - Field results are less consistent than lab results, and companion planting is unlikely to replace other controls.

**Marigold**
- **Conboy et al. 2019**, "Companion planting with French marigolds protects tomato plants from glasshouse whiteflies through the emission of airborne limonene", *PLOS ONE*, DOI 10.1371/journal.pone.0213071, CC BY. [OpenAlex](https://api.openalex.org/works/doi:10.1371/journal.pone.0213071)
  - Large glasshouse trials found marigolds significantly slowed whitefly population growth on tomato.
  - Other non-hosts (basil, nasturtium, Chinese cabbage) also reduced whitefly.
  - Perimeter "pull" plants had little effect.
- **Hooks, Wang, Ploeg et al. 2010**, "Using marigold (*Tagetes* spp.) as a cover crop to protect crops from plant-parasitic nematodes", *Applied Soil Ecology*, DOI 10.1016/j.apsoil.2010.09.005 (TLDR only).
  - The review found "variable findings from marigold use" and called for research on the causes of the variability.
  - Implication: marigold against root-knot nematodes is peer-reviewed but conditional. It applies to marigold grown as a dense cover or rotation crop, not interplanted, though the interplanting point is my inference.
  - [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/j.apsoil.2010.09.005)

**Basil and tomato**
- **Yoshida, Taguchi et al. 2024**, "Companion basil plants prime the tomato wound response through volatile signaling in a mixed planting system", *Plant Cell Reports*, DOI 10.1007/s00299-024-03285-w, CC BY.
  - In growth chambers, basil volatiles (and basil essential oil) primed tomato wound-response genes (jasmonic acid, MAPK and ROS signalling).
  - This is mechanistic, not field yield or pest data.
  - [OpenAlex](https://api.openalex.org/works/doi:10.1007/s00299-024-03285-w)

**Three Sisters (maize, bean, squash)**
- **Zhang, Postma et al. 2014**, *Annals of Botany*, DOI 10.1093/aob/mcu191. Maize/bean/squash and maize/bean polycultures had greater yield and biomass on a land-equivalent basis than monocultures. The gain came mainly from complementarity, with species foraging at different root depths. [OpenAlex](https://api.openalex.org/works/doi:10.1093/aob/mcu191)
- **Postma & Lynch 2012**, "Complementarity in root architecture for nutrient uptake in ancient maize/bean and maize/bean/squash polycultures", *Annals of Botany*, DOI 10.1093/aob/mcs082 (title only; simulation study). [Crossref](https://api.crossref.org/works/10.1093/aob/mcs082)
- **Liao, Zhou et al. 2024**, *European Journal of Agronomy*, DOI 10.1016/j.eja.2024.127118, "'The Three Sisters' polyculture promotes the direct and indirect defences of maize against herbivores" (title only). [Crossref](https://api.crossref.org/works/10.1016/j.eja.2024.127118)

**Allelopathy and antagonists**
- **Jose & Gillespie 1998**, black walnut (juglone) allelopathy in alley cropping, *Plant and Soil*, DOI 10.1023/A:1004301309997 (title only). Walnut as an "avoid" neighbour is one of the few antagonisms with peer-reviewed study. [Crossref](https://api.crossref.org/works/10.1023/a:1004301309997)

**Popular lists**
- Wikipedia's "List of companion plants" itself states that "only a few of these have been subjected to scientific testing". Its references mix journals, extension pages and popular gardening sites, and most table cells have no inline citation. [Wikipedia](https://en.wikipedia.org/wiki/List_of_companion_plants)

### Inferences
- Suggested evidence-level rules for CropStack:
  - **Peer-reviewed:** a pair-specific trial exists (e.g. marigold–tomato against whitefly; basil–tomato for priming only, not yield; trap crops listed by Sarkar et al. 2018; Three Sisters land-equivalent yield).
  - **Observational:** extension or mechanism-only support.
  - **Traditional:** everything else from folk lists.
- Use mechanism tags (trap, repel or mask, natural-enemy habitat, nitrogen or complementarity, allelopathy). The literature consistently explains outcomes by mechanism, not by pair.
- Add a "yield trade-off" caveat to companion links: Letourneau 2011 found a small negative mean yield effect when the companion displaces main-crop plants.

### Gaps
- I found no meta-analysis restricted to home-garden vegetable companion pairs.
- I did not find peer-reviewed tests of most classic claims, such as "carrots love tomatoes" or "beans dislike onions". I found no source contradicting them either, so they stay unverified, not "disproven".
- I did not retrieve abstracts for Li et al. 2020 (Nature Plants) or Postma & Lynch 2012.
- I did not read Chalker-Scott's *The Informed Gardener* (DOI 10.1515/9780295800325), a commonly cited myth-busting source.

## 2. Open companion-planting datasets and licences

### Takeaway
- **Wikipedia's list:** the only verified-open, ready-made pair table. It is CC BY-SA 4.0 (share-alike) and has poor per-cell sourcing.
- **OpenFarm:** shut down in April 2025. Its code is MIT, but I could not confirm the data licence or a public data dump.

### Cited Findings
- **Wikipedia "List of companion plants".** [Wikipedia](https://en.wikipedia.org/wiki/List_of_companion_plants)
  - Licence: the page footer cites the "Creative Commons Attribution-ShareAlike 4.0 License" (checked in the page HTML).
  - Contents: about 100 plant rows in 5 tables, with columns Helps, Helped by, Attracts, Repels/distracts, Avoid and Comments.
  - Sourcing: uneven, with heavy use of popular sites.
- **OpenFarm.** FarmBot "shut down the OpenFarm servers" on 21 April 2025. Information was copied into the FarmBot web app only for crops with icons. The GitHub repo (openfarmcc/OpenFarm) was to be publicly archived. [FarmBot blog](https://farm.bot/blogs/news/sunsetting-openfarm)
- **OpenFarm repo licence.** The repo README states "Software License: The MIT License (MIT)". [README](https://raw.githubusercontent.com/openfarmcc/OpenFarm/main/README.md)
- **OpenFarm data licence.** A community discussion "Should OpenFarm's Data be CC0 instead of CC-BY?" exists, but I did not read the outcome. [Loomio](https://www.loomio.org/d/BRoQnYHX/should-openfarm-s-data-be-cc0-instead-of-cc-by)
- **Other mirrors.** A forum thread reports OpenFarm crop data was "restored" on another website (not verified). [growingfruit.org](https://growingfruit.org/t/openfarms-crop-data-restored-in-website/81182)

### Inferences
- **Wikipedia data:** importing it into an MIT repo imposes share-alike on that data file. Keep it as a separately licensed data file with attribution, and default every imported link to "traditional".
- **OpenFarm data:** do not ingest it until a data licence (CC-BY or CC0) is confirmed on a primary page.

### Gaps
- I did not identify a verified GitHub or Zenodo companion-pair dataset with a clear licence. One search hit (npm "@cropgraph/core") was not examined.
- I could not access GitHub via the API in this session to check whether the archived OpenFarm repo contains a database seed or dump.

## 3. Crop rotation intervals by family and soil-borne disease; pathogen survival

### Takeaway
- **General rule:** extension guidance gives a 3-year rotation between families.
- **Disease-specific minimums are longer:**
  - Clubroot: 5–7 years
  - Sclerotinia: 3–5 years
  - Verticillium: 3–5 years or more
  - Fusarium wilt: 4–7 years or more
- **Where rotation fails:** for pathogens whose survival structures outlast practical rotations, rotation alone does not work and the app should say so. Examples are white rot (more than 20 years) and clubroot (up to 20 years by some sources).

### Cited Findings
**Cornell / Penn State table, "Minimum years to avoid crops susceptible to specific diseases"** (MacNab & Zitter, updated August 2020). [Cornell](https://www.vegetables.cornell.edu/pest-management/disease-factsheets/do-rotations-matter-within-disease-management-programs)

| Crop group | Disease | Minimum years |
|---|---|---|
| Cabbage-related crops | Clubroot | 7 |
| Cabbage-related crops | Fusarium yellows | "many years" |
| Cabbage-related crops | Blackleg | 3–4 |
| Cabbage-related crops | Black rot | 2–3 |
| Cabbage-related crops | White mold | 3 |
| Radish, turnip | Clubroot | 7 |
| Beans | Root rots | 3 |
| Beans | White mold | 3 |
| Lettuce | Drop (Sclerotinia) | 3 |
| Lettuce | Bottom rot | 3 |
| Eggplant | Verticillium | 4–5 |
| Potato | Verticillium | 3–4 |
| Potato | Sclerotinia | 4 |
| Potato | Early blight | 2 |
| Potato | Common scab | 2–3 |
| Tomato | Fusarium wilt | 3 |
| Tomato | Verticillium | "several years" |
| Tomato | Bacterial canker | 3+ |
| Tomato | Early blight | 2 |
| Tomato | Septoria | 1–2 |
| Peas | Fusarium wilt | 4–5 |
| Peas | Root rots | 3–4 |
| Melons | Fusarium wilt | 4+ |
| Onion | Leaf blights | 1–2 |
| Beets | Cercospora | 3 |
| Carrots | Leaf blights | 2–3 |
| Asparagus | Fusarium | "indefinite" |

**SARE, *Crop Rotation on Organic Farms*** (Mohler & Johnson eds., 2009; chapter by M.T. McGrath). [SARE](https://www.sare.org/publications/crop-rotation-on-organic-farms/physical-and-biological-processes-in-crop-production/managing-plant-diseases-with-crop-rotation/)
- **Clubroot:** "can survive in soil for seven years". It declined faster after tomato, cucumber, snap bean or buckwheat.
- **Verticillium dahliae:** microsclerotia "survive up to 13 years".
- **Fusarium oxysporum:** "rotations of at least five or seven years often prevent" population buildup, but "even seven years may not be enough" after severe disease. The book recommends resistant varieties.
- **Sclerotinia sclerotiorum:** sclerotia "can survive up to ten years". Rotation away from susceptible crops for "at least five years" is needed; maize and cereals are non-hosts; the pathogen has more than 360 hosts.
- **Root-knot nematodes (*Meloidogyne hapla*, *M. incognita*):** sorghum, small grains, grasses or clean fallow reduce populations, but the effect is short-lived. Hairy vetch is a good host.
- **General principle:** rotation works best when a pathogen survives no more than a few years. Pythium, Rhizoctonia and Fusarium live as saprophytes and are "hard to manage with rotation".

**Other extension sources**
- **Clubroot (UMN Extension):** spores "can survive for 20 years". Avoid brassicas for "5 to 7 years", which reduces but does not eliminate the pathogen. Infection is more likely below pH 6.5. [UMN Extension](https://extension.umn.edu/plant-diseases/clubroot)
- **Onion white rot (UC IPM):** "Sclerotia can survive for over 20 years, even in the absence of a host plant". Do not replant onion or garlic in that area. [UC IPM](https://ipm.ucanr.edu/home-and-landscape/white-rot/)

**Primary survival papers** (titles verified via Crossref; contents not read)
- Leggett & Rahe 1983, survival of *Sclerotium cepivorum* sclerotia in muck soil, DOI 10.1016/0038-0717(83)90078-0
- Green 1980, soil factors affecting survival of *V. dahliae* microsclerotia, DOI 10.1094/phyto-70-353
- Merriman 1976, survival of Sclerotinia sclerotiorum sclerotia in soil, DOI 10.1016/0038-0717(76)90038-9
- Smolinska 2000, *S. cepivorum* sclerotia and *F. oxysporum* chlamydospores in amended soil, DOI 10.1046/j.1439-0434.2000.00519.x

[Crossref](https://api.crossref.org/works)

### Inferences
- Model rotation in two layers:
  1. A default family gap of 3 years (2 intervening years).
  2. Disease-specific overrides that apply only when the user records the disease. Example override values:
     - Clubroot: 7 years
     - Sclerotinia: 5 years, including lettuce and beans, since hosts cross families
     - Verticillium: 4–5 years, shared by Solanaceae and other hosts
     - Fusarium wilt: 4–7 years, with "use resistant varieties"
     - White rot: "do not replant Allium; rotation ineffective (>20 y)"
- Sclerotinia and Verticillium cross family lines, so conflicts should come from disease-host links, not family alone.

### Gaps
- I found no single open, machine-readable table of pathogen survival times. Values must be curated by hand from the sources above.
- I found no extension number for a root-knot nematode rotation interval in years.
- The Cornell page is © Cornell, with no open licence stated. Cite facts rather than copying the table.

## 4. Botanical family groupings for rotation

### Takeaway
Cornell Cooperative Extension publishes a garden-oriented family grouping that maps cleanly onto the requested families. Modern taxonomy differs on two points:
- Alliums sit in Amaryllidaceae (Allioideae).
- Beet and spinach sit in Amaranthaceae, which now includes the former Chenopodiaceae.

### Cited Findings
CCE "Rotating vegetables by family" advises "usually a 3-year rotation" with 2 years of unrelated crops between. [CCE Allegany](https://allegany.cce.cornell.edu/gardening/food-gardening/rotating-vegetables-by-family)

| Group (CCE name) | Members |
|---|---|
| Allium | chive, garlic, leek, onion, shallot |
| Amaranth | amaranth |
| Brassica | bok choi, broccoli, Brussels sprouts, cabbage, cauliflower, collard, horseradish, kale, kohlrabi, mustard, rutabaga, radish, turnip |
| Composite | artichoke, chicory, endive, Jerusalem artichoke, lettuce, sunflower |
| Cucurbit | cucumber, gourd, melon, pumpkin, squash, watermelon, zucchini |
| Goosefoot | beet, chard, quinoa, spinach |
| Grain | barley, corn, oats, rice, rye, wheat |
| Legume | bean, clover, pea, vetch |
| Lily | asparagus |
| Mallow | okra |
| Mint | basil, mint, oregano, sage |
| Morning glory | sweet potato |
| Nightshade | eggplant, ground cherry, pepper, potato, tomatillo, tomato |
| Rose | strawberry |
| Smartweed | buckwheat, rhubarb, sorrel |
| Umbel | carrot, celeriac, celery, dill, fennel, lovage, parsley, parsnip |

### Inferences
- Store the accepted family name (APG IV: Amaryllidaceae, Amaranthaceae, Asteraceae, Apiaceae, Fabaceae, Poaceae, Solanaceae, Brassicaceae, Cucurbitaceae, Asparagaceae for asparagus) plus a "rotation group" alias. Note that "Goosefoot" is treated as its own group in garden practice, although taxonomically it falls under Amaranthaceae.
- Family membership is public taxonomic fact, so no licensing issue arises. GBIF or POWO can supply it (not checked here).

### Gaps
- I did not verify the APG IV placements against POWO or GBIF in this session; they are stated from general knowledge.

## 5. Crop nutrient uptake and removal, stage-wise demand, and fertiliser recommendations

### Takeaway
- **Nutrient offtake per tonne:** available from FAO, UK AHDB RB209 (via PDA), UCCE/CDFA (N only) and NZ sources, but almost none are under an open licence.
  - FAO allows non-commercial reproduction with acknowledgement.
  - UF/IFAS EDIS is CC BY-NC-ND 4.0.
  - HortNZ is all rights reserved.
- **Recommended approach:** store numeric facts with citations rather than copying documents.
- **FERTASA (South Africa):** a paid, hard-copy handbook with no stated open terms.

### Cited Findings
- **FAO, *Plant Nutrition for Food Security*** (Roy, Finck, Blair & Tandon 2006, Fertilizer and Plant Nutrition Bulletin 16). [FAO PDF](https://www.fao.org/4/a0443e/a0443e.pdf)
  - Table 28 gives nutrient content (kg/t) of major crop products and residues, mostly field crops. Tables 29–30 give Indian per-tonne uptake data.
  - Average uptake shares are 35% N, 17% P2O5 and 48% K2O, a ratio of 1.0 : 0.5 : 1.4.
  - Licence: "Reproduction and dissemination … for educational or other non-commercial purposes are authorized without any prior written permission … provided the source is fully acknowledged. Reproduction … for resale or other commercial purposes is prohibited without written permission."
- **AHDB RB209 offtake values** (via the UK Potato/PDA "Nutrients in crop material", March 2020), in kg/t fresh weight. No N values are given, and there is no copyright statement on the page; check AHDB terms. [PDA](https://www.pda.org.uk/?p=509)

  | Crop | P2O5 (kg/t) | K2O (kg/t) |
  |---|---|---|
  | Potato | 1.0 | 5.8 |
  | Carrot | 0.7 | 3.0 |
  | Onion | 0.7 | 1.8 |
  | Beetroot | 1.0 | 4.5 |
  | Cabbage | 0.9 | 3.6 |
  | Cauliflower | 1.4 | 4.8 |
  | Kale | 1.2 | 5.0 |
  | Brussels sprouts (buttons) | 2.6 | 6.3 |
  | Broad beans | 1.6 | 3.6 |
  | French beans | 1.0 | 2.4 |
  | Vining peas | 1.5 | 3.0 |

- **UCCE / CDFA-FREP N-removal coefficients for about 75 Central Coast crops** (Smith, Cahn, Gazula, Biscaro; table updated March 2024). The page is © State of California; check ca.gov Conditions of Use. [CDFA FREP](https://blogs.cdfa.ca.gov/FREP/index.php/research-update-estimating-nitrogen-removal-from-the-harvested-portion-of-central-coast-crops)
  - Coefficients are in kg N per kg harvested.
  - Romaine (cartons): 0.00184.
  - Arugula, broccoli, cilantro, kale, spinach: 0.004–0.007.
  - Cabbage, fennel, leek, mature lettuce, onion: 0.001–0.0025.
  - Pea tips: 0.00727.
- **Montana State "Nutrient Uptake & Removal"**: uptake curves through the season and removal tables, mostly field crops. Potato tubers remove N 0.2, P2O5 0.13 and K2O 0.38 lb per 55-lb bushel. No licence stated. [MSU](https://landresources.montana.edu/soilfertility/nutuptake.html)
- **Arkansas FSA-2176**: removal per bushel for row crops only, sourced from IPNI. [UADA](https://www.uaex.uada.edu/publications/pdf/FSA-2176.pdf)
- **HortNZ, *Nutrient Management for Vegetable Crops in NZ*** (Reid & Morton, 2019). This is the best stage-wise and vegetable-specific source found, but it is all rights reserved and needs written permission. [HortNZ PDF](https://www.hortnz.co.nz/assets/Compliance/Nutrient-Management-for-Vegetable-Crops-in-NZ-Manual-Feb-2020.pdf)
  - Buttercup squash removes N 3.7, P 0.56 and K 3.62 kg/t.
  - Process beans remove N 3.7, P 0.60 and K 2.8 kg/t.
  - Broccoli and cabbage take up very little N in the first month after transplant.
  - About 71% of broccoli N stays in residues.
- **UF/IFAS EDIS CV236, tomato** (Hochmuth & Hanlon, revised 2020/2023). [EDIS](https://ask.ifas.ufl.edu/publication/CV236)
  - Target 200-150-225 lb/acre N-P2O5-K2O. For the North Florida fall crop: 40 lb N preplant, then 15 lb N per week in weeks 5–8.
  - EDIS licence: "Creative Commons Attribution-NonCommercial-NoDerivatives International 4.0", not applying to images. [EDIS copyright](https://ask.ifas.ufl.edu/copyright)
- **FERTASA Fertilizer Handbook** (South Africa): "7th Revised Edition 2016", hard cover, R1200 including postage. Ordered by email or fax. The publications page states no copyright or licence terms. [FERTASA](https://fertasa.co.za/publications)

### Inferences
- Under all of these terms, CropStack can store per-crop numbers (facts) with a citation. It cannot redistribute the documents, and it should avoid copying entire tables from NC-ND or all-rights-reserved sources (HortNZ, EDIS, FERTASA).
- Feeding tasks should state N-P-K demand as "removal per tonne × expected yield" and label the source and region.
- For stage-wise splits, the evidence found is qualitative: low early N uptake in brassicas, and weekly N split from week 5 for tomato.

### Gaps
- The legacy IPNI/APNI vegetable removal tables were not located or verified; APNI's current terms were not checked.
- I found no open-licence (CC BY or CC0) table of vegetable N-P-K uptake by growth stage.
- I did not extract N values per tonne for UK crops; RB209 itself was not read.

## 6. Organic amendment nutrient analyses

### Takeaway
Extension tables exist (UMaine, UMass, UMD, NCDA, MOFGA), but the one fetched states no licence and has unlabelled columns. Typical label values should be stored as ranges, with the caveat to "check the label/analysis".

### Cited Findings
- **UMaine Cooperative Extension, "Characteristics of Common Natural Fertilizers"** (from the GardenPro Answer Book, revised by Lois Berg Stack). Typical percentages as listed, with the nutrient taken from context:
  - Blood meal: 13 (N)
  - Feather meal: 12 (N)
  - Bone meal/char: 15 (P)
  - Rock phosphate: 30 (P total, about 3% quickly available)
  - Wood ash (dry): 5 (K; liming)
  - Alfalfa meal: 2.5, 2
  - Fresh cow manure: ≤1, ≤1
  - Fresh poultry manure: ≤3, ≤3
  - Potassium sulfate: 50 (K)

  The page advises "Always check the label". No licence stated. [UMaine](https://extension.umaine.edu/gardening/?p=8825)
- Other candidate tables, found in search but not read: [UMass fertilizer materials](https://www.umass.edu/agriculture-food-environment/sites/ag.umass.edu/files/fact-sheets/pdf/fertilizer_materials_nutrient_amendment.pdf), [UMD B-11](https://extension.umd.edu/sites/extension.umd.edu/files/2021-03/B-11.pdf), [NCDA Soil Fertility Note 12](https://ncagr.gov/soil-fertility-note-12-fertilizing-organic-nutrients/download), [MOFGA FS-11](https://www.mofga.org/wp-content/uploads/2021/01/FS-11-Sources-of-Plant-Nutrients-web.pdf), [U Idaho CIS 922](https://www.uidaho.edu/-/media/UIdaho-Responsive/Files/Extension/publications/cis/cis0922.pdf?la=en).

### Inferences
- These values are generic facts that can be recorded with citation. Compost and manure vary greatly, so CropStack should show ranges and prompt users to enter their own lab analysis.

### Gaps
- I did not verify compost and composted-manure analyses or reuse terms for the extension tables above.

## 7. Cover crop databases and licences

### Takeaway
- **Code:** the Northeast/Midwest/Southern cover crop selector code (Precision Sustainable Agriculture, "dst-selector") is MIT-licensed according to ecosyste.ms.
- **Underlying data:** the licence was not verified.
- **SARE books:** non-commercial reuse with attribution only, not an open licence.

### Cited Findings
- **dst-selector repository**: the ecosyste.ms record for the Cover Crop Species Selector lists repo precision-sustainable-ag/dst-selector with licence "mit", last pushed 2026-09-28. [ecosyste.ms](https://ost.ecosyste.ms/api/v1/projects/190698)
- **Northeast Cover Crops Council** decision tools were developed with SARE funding (project ENE16-144). [SARE project](https://projects.sare.org/sare_project/ene16-144/); [PSU Extension](https://extension.psu.edu/a-cover-crop-selection-tool-for-northeast-us-farmers)
- **Midwest Cover Crops Council decision tool**: SARE project ENC17-159. [SARE project](https://projects.sare.org/sare_project/ENC17-159/)
- **SARE reuse policy**: "Copyright is retained by SARE and the University of Maryland." [SARE permissions](https://sare.org/about/sare-outreach/publishing-with-sare-outreach/recommended-attribution-format/)
  - "SARE content may be copied and distributed with attribution for educational, non-commercial purposes."
  - Limited commercial use requires prior permission, unadapted and attributed.
- ***Managing Cover Crops Profitably*** (3rd ed., 2007, ed. Andy Clark, ISBN 978-1-888626-12-4) is offered as a free PDF and as print ($19). The PDF front matter has no open licence. [SARE](https://www.sare.org/resources/managing-cover-crops-profitably-3rd-edition/)

### Inferences
- An MIT project can link to SARE and cite facts from it. Bundling SARE text or tables risks the non-commercial and no-adaptation terms, since forks may be commercial.
- If CropStack needs a cover-crop catalogue, check whether the dst-selector data comes from an open API or is bundled in the repo.

### Gaps
- I could not access GitHub in this session to check whether dst-selector bundles its species data or what licence that data carries.
- I did not check the Midwest Cover Crops Council's own data terms.

## 8. Yield per m² for home gardens

### Takeaway
- **Best lead:** the Measure Your Harvest citizen-science dataset (University of Sheffield, UK allotments, 5 years) is the best open lead. Its page says the data "can be shared openly", but no formal licence or per-crop yields were visible.
- **No CC0 or CC BY table found:** this search did not locate an open table of home-garden yield per m² by crop.

### Cited Findings
- **Sheffield ORDA dataset** "Measure Your Harvest: long-term citizen-science reveals the contribution of own-growing to UK food security – dataset". [ORDA](https://orda.shef.ac.uk/articles/dataset/Measure_Your_Harvest_long-term_citizen-science_reveals_the_contribution_of_own-growing_to_UK_food_security_-_dataset/30675815)
  - Own-grown fruit and vegetable yields over a 5-year project at myharvest.org.uk.
  - Funded by EPSRC EP/N030095/1.
  - Includes a readme with units.
  - Licence not named on the fetched page.
- **Commercial yield proxies:** the yields used in the removal sources above (e.g. HortNZ squash 28 t/ha, which equals 2.8 kg/m²; beans 27 t/ha) are commercial field yields, not garden yields. [HortNZ](https://www.hortnz.co.nz/assets/Compliance/Nutrient-Management-for-Vegetable-Crops-in-NZ-Manual-Feb-2020.pdf)

### Inferences
- Default garden yields could be curated from commercial t/ha figures (1 t/ha = 0.1 kg/m²) with a "commercial benchmark" label until garden data (e.g. MYHarvest per-crop figures) is confirmed.

### Gaps
- The MYHarvest licence (ORDA/Figshare usually shows CC BY 4.0, but this was not confirmed), its DOI and its per-crop content were not verified.
- I did not examine the ASHS HortScience garden-yield article seen in search results.
