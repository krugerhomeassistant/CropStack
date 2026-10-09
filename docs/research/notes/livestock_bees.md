# Open data sources for small-holder livestock and bees (CropStack)

Scope: chicken, duck, goose, turkey, quail, goat, sheep, cattle, pig, rabbit, honeybee. Pages checked 2026-10-09. Licence statements were read on the primary pages unless marked otherwise. CropStack is MIT-licensed, so "redistributable" below means the data can ship inside an MIT repo (a CC BY data file with attribution is fine; NC/ND/all-rights-reserved is not).

## FAO DAD-IS and EFABIS: breed records, fields, export/API, licence

### Takeaway
DAD-IS is the most complete open breed source (over 8,800 breeds, about 40 species, 182 countries). FAO's Statistical Database Terms of Use list DAD-IS in Annex 1, so it falls under CC BY 4.0 by default. That makes it redistributable with attribution. Access is through web export tools only; I found no documented public API.

### Cited Findings
- DAD-IS covers more than 15,000 national breed populations, over 8,800 breeds, about 40 species and 182 countries. It holds breed profiles, characteristics, uses, population numbers and trends, adaptedness classes, risk status (SDG indicator 2.5.2) and national coordinator contacts. Regional data comes from EFABIS. — [FAO DAD-IS home](https://www.fao.org/dad-is/en/)
- The data-export page offers "Download datasets and generate custom tables, charts, and reports" and "Extract breed and bee data or build customized cross-tabulations". It has separate export tools for breeds and for bees. The page names no formats or API. — [DAD-IS data export](https://www.fao.org/dad-is/data/data-export/en)
- FAO statistical datasets are licensed under "the Creative Commons Attribution-4.0 International licence" unless their metadata or webpage says otherwise. DAD-IS is listed in Annex 1 with no restriction. The required citation is FAO, year of last update, dataset name, access date, URL and "CC-BY-4.0". Third-party data with its own terms takes precedence. — [FAO Statistical Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use)
- FAO's general website content (as opposed to databases) is limited to private study, research, teaching and non-commercial use. Commercial use, adaptation and translation need permission. — [FAO Terms and Conditions](https://www.fao.org/contact-us/terms/en/)
- DAD-IS also links an "About DAD-IS data" PDF and a "Metadata file (2026)". — [FAO DAD-IS home](https://www.fao.org/dad-is/en/)

### Inferences
- Import breed name, species, country, risk status and adaptedness from a DAD-IS export as a CC BY 4.0 data file, and put the FAO citation string in the repo's NOTICE or DATA-LICENSES file.
- Breed photos and descriptive text that national coordinators upload may count as third-party content with other terms. To be safe, import only structured fields.
- EFABIS feeds into DAD-IS, so a separate EFABIS integration is probably unnecessary.

### Gaps
- I did not see DAD-IS export formats or the full field list; the export page does not state them. Check the "About DAD-IS data" PDF and the metadata file.
- I found no public REST API documentation. Do not assume one exists.
- I did not separately verify an EAAP/EFABIS licence.

## Other breed databases: Oklahoma State, The Livestock Conservancy, Wikidata

### Takeaway
Wikidata (CC0) is the only freely redistributable breed list besides DAD-IS. Oklahoma State and The Livestock Conservancy are "all rights reserved", so CropStack can only link to them.

### Cited Findings
- OSU Breeds of Livestock covers cattle, goats, horses, poultry, sheep, swine and donkeys. Its footer reads "Oklahoma State University. All rights reserved." — [breeds.okstate.edu](https://breeds.okstate.edu/)
- The Livestock Conservancy's Conservation Priority List covers cattle, chickens, donkeys, ducks, geese, goats, horses, pigs, rabbits, sheep and turkeys. Its categories are Critical, Threatened, Watch, Recovering and Study. The footer reads "© Copyright 2026 | ALL RIGHTS RESERVED." — [Livestock Conservancy CPL](https://livestockconservancy.org/heritage-breeds/conservation-priority-list/)
- "All structured data in the main, property and lexeme namespaces is made available under the Creative Commons CC0 License". — [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
- My own SPARQL run on query.wikidata.org (2026-10-09) counted items that are an instance of a subclass of "breed" (Q38829). By class: sheep breed 627, cattle breed 592, chicken breed 389, goat breed 224, pig breed 172, rabbit breed 154, goose breed 66, duck breed 44, turkey breed 26, plus generic "breed" 117 and "rare breed" 19. The total across all breed classes, including dogs and horses, is 5,187. There is no Wikidata property for DAD-IS IDs; label search for "DAD-IS" found none. Related properties found: P4743 "animal breed", P13612 "breed belongs to taxon", P2024 "German cattle breed ID". — [Wikidata Query Service](https://query.wikidata.org/)

### Inferences
- A sensible design is DAD-IS (CC BY) for authoritative breed and risk data, Wikidata (CC0) for multilingual labels and image links, and hyperlinks only to OSU and the Livestock Conservancy.
- Without a DAD-IS ID property on Wikidata, matching the two sources has to use name, species and country.
- Wikidata has few quail breed items (I did not see a quail class), and Wikidata has almost no numeric production traits.

### Gaps
- The Wikidata counts are a snapshot and depend on how classes are modelled. Quail breeds were not counted separately.

## Nutrient requirements and feed data: NRC/NASEM vs open alternatives

### Takeaway
NASEM/NRC books are copyrighted, but individual facts and numbers can be cited. Feedipedia is not CC BY: reuse is limited to non-commercial extracts with attribution, and commercial or adaptation rights go through AFZ. For a redistributable dataset, use the FAO statistical databases (CC BY 4.0) and extension rules of thumb that cite NRC.

### Cited Findings
- Feedipedia is run by INRAE, CIRAD, AFZ and FAO and covers "nearly 1400 worldwide livestock feeds", mostly tropical, subtropical and Mediterranean. — [About Feedipedia](https://www.feedipedia.org/content/about-feedipedia)
- Its terms say "Extracts may be copied, printed and downloaded for private study, research and teaching purposes" with acknowledgement. "Requests for translation and adaptation rights, resale and other commercial use rights should be addressed to AFZ." — [Feedipedia Copyright](https://www.feedipedia.org/content/copyright)
- Water intake (beef cows), using NRC 2000 as the basis: a 1,100 lb dry cow drinks 8.2 gal/day at 40°F and 10.8 gal/day at 65°F; a 1,500 lb cow giving 35 lb milk drinks 15.3 and 18.8 gal/day. Rules of thumb: "an additional one gallon of water should be supplied per animal" for every 10°F above 40°F, and 1 extra gallon of water per extra gallon of milk. Dry-matter intake is assumed at 2.2% of body weight when non-lactating and 2.7% when lactating. — [OSU Extension: Estimating water requirements for mature beef cows](https://extension.okstate.edu/fact-sheets/estimating-water-requirements-for-mature-beef-cows.html)
- Sheep and goats: provide "one to three pounds of water per-pound dry matter". — [SDSU Extension: Heat stress in small ruminants](https://extension.sdstate.edu/heat-stress-small-ruminants)

### Inferences
- Encode water intake as a base rate plus a temperature slope (for example, beef cows +1 gal per 10°F above 40°F). Cite the extension page and NRC (2000) as facts, without copying NRC tables wholesale.
- Do not bundle Feedipedia tables, because MIT redistribution permits commercial reuse, which Feedipedia does not allow without AFZ permission. Link to it instead.

### Gaps
- I did not verify open water and feed intake values for poultry, pigs or rabbits in this session.
- I did not check NASEM's own reuse terms page.

## Temperature-humidity index (THI) formulas and heat-stress thresholds

### Takeaway
Use NRC (1971) THI = (1.8T+32) − (0.55−0.0055·RH)(1.8T−26). For dairy cattle, the classic comfort threshold is 72, with newer evidence for lower onsets (60 to 69) depending on climate. For pigs and sows, use 74/78/82. I did not verify small ruminant and poultry thresholds from open-access peer-reviewed papers in this session.

### Cited Findings
- Dairy cattle: formula THI = (1.8T + 32) − (0.55 − 0.0055RH)(1.8T − 26) (NRC 1971). "a THI threshold of 72 has been extensively used". Armstrong (1994) classes: <72 comfort, 72–79 mild, 80–89 moderate, >90 severe. Regional thresholds: 69 Mediterranean and tropical, 74 semi-arid USA, 78 subtropical USA, 62 Luxembourg, and 60 Germany (where milk yield starts to decline). The article does not mention 68. Paper: Mbuthia, Eggert & Reinsch 2022, *Frontiers in Animal Science*, DOI 10.3389/fanim.2022.946592, CC BY. — [Frontiers PDF](https://www.frontiersin.org/journals/animal-science/articles/10.3389/fanim.2022.946592/pdf)
- Dairy industry commentary argues the onset is about 65 rather than 72. This is trade press, not peer-reviewed. — [Hoard's Dairyman: "65 is the new 72"](https://hoards.com/blog-2641-heat-stress-65-is-the-new-72.html)
- Pigs and sows: THI2 = 0.8·T + RH·(T − 14.4)/100 + 46.4, with <74 suitable, 74–78 mild, 78–82 moderate, ≥82 severe (Mellado et al., as cited). THI6, the °F form, uses ≤74/74–78/78–84/>84. The paper also gives sow ETIS bands: <33.1, 33.1–34.5, 34.5–35.9, ≥35.9. Paper: Cao et al. 2021, "Modeling of Heat Stress in Sows Part 2", DOI 10.3390/ani11061498 (MDPI *Animals*, PMC8224342). The PMC text extract did not show the licence; MDPI *Animals* is normally CC BY 4.0. — [PMC8224342](https://pmc.ncbi.nlm.nih.gov/articles/PMC8224342)
- Sheep and goats: SDSU Extension gives a THI table with categories moderate 82–<84, severe 84–<86, extreme ≥86, on a °F THI-scale table, with no formula shown. A fleeced sheep's comfort zone is "about 10–90 degrees Fahrenheit". It cites Marai et al. 2007 (*Small Ruminant Research* 71:1–12), Silanikove 2000 (*Livestock Production Science* 67:1–18) and Sarangi 2018. — [SDSU Extension](https://extension.sdstate.edu/heat-stress-small-ruminants)

### Inferences
- Store THI thresholds per species as configurable bands, with a citation on each band. Default dairy cattle to 68 or 72 (the value of 68 needs a source; see Gaps), with 72/80/90 for mild/moderate/severe.
- Pig bands (74/78/82) also work as a general mammalian default.

### Gaps
- I did not find an open-access source with DOI for the commonly quoted dairy cattle value of 68 (Zimbelman et al. 2009 is a conference proceeding); do not cite it as verified.
- I did not verify poultry, rabbit, goat or sheep THI formulas and thresholds with DOIs. The Marai 2007 sheep THI scale (THI = db°C − [(0.31 − 0.31RH)(db°C − 14.4)], with <22.2 / 22.2–23.3 / 23.3–25.6 / ≥25.6) is widely quoted, but I did not verify it from the paper or get its DOI.
- I did not find cold-stress (lower critical temperature) values per species.

## Space allowances: EU law, welfare-scheme standards, South African SANS

### Takeaway
EU Directive 1999/74/EC gives citable, public-law numbers for laying hens. South African chicken welfare is in draft SANS 1758, which is a paid SABS standard and so cannot be redistributed. Certified Humane and RSPCA standards are proprietary, so CropStack should link to them only.

### Cited Findings
- Directive 1999/74/EC, alternative systems: at most 9 hens per m² of usable area; 1 nest per 7 hens (or 1 m² of group nest per 120 hens); perch ≥15 cm per hen; linear feeder 10 cm or circular 4 cm per bird; drinkers 2.5 cm (continuous) or 1 cm (circular) per hen, or 1 nipple per 10 hens; litter ≥250 cm² per hen covering ≥1/3 of the floor. — [EUR-Lex 31999L0074](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:31999L0074)
- The same directive requires enriched cages to give 750 cm² per hen (600 cm² usable) and lighting to "follow a 24-hour rhythm and include an adequate uninterrupted period of darkness" (about one-third of the day). — [EUR-Lex 31999L0074](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:31999L0074)
- South Africa: draft SANS 1758 (DSS 1758), from SABS TC 1094, is a 53-page chicken welfare standard covering environment, management, daily care and euthanasia. It was at public enquiry with comments closing 22 March 2021, and it is described as "guidelines". — [Mining Weekly, 2021-03-18](https://www.miningweekly.com/article/south-african-national-standard-that-focuses-on-the-welfare-of-chickens-2021-03-18)
- Certified Humane (HFAC) publishes its chicken standard as a PDF. — [Certified Humane Standard_Chickens.pdf](https://certifiedhumane.org/wp-content/uploads/Standard_Chickens.pdf)

### Inferences
- EU legislation can be reused under the EU's reuse policy (generally free reuse with acknowledgement), so it is a safe default for hen numbers.
- For other species, the EU pig (2008/120/EC) and calf (2008/119/EC) directives are the next public-law candidates.

### Gaps
- I did not verify whether SANS 1758 has been finalised or what it costs.
- I did not verify RSPCA or HFAC terms of use, or the EU pig and calf directive values.
- I found no open space-allowance sources for small holdings of rabbits, quail, ducks, geese, goats or sheep.

## Poultry lighting, laying and incubation; mammal reproduction

### Takeaway
The MSD Veterinary Manual (reviewed November 2024) gives artificial lighting of 13–16 hours and incubation periods for chickens, quail, guinea fowl, ducks and geese. Separate MSD tables give oestrous and gestation values for mammals. MSD content is copyrighted (Merck), so cite the facts and do not copy the tables.

### Cited Findings
- Laying: artificial lighting is typically 13–16 hours per 24 hours, or continuous. Incubation: chicken 21 d, bobwhite quail 23–24 d, guinea fowl 27–28 d, duck 28 d, goose 28–33 d. Chicken incubation temperature is 36.7–38.3°C. Turkey and Muscovy are not listed. Author Yuko Sato, DVM, reviewed November 2024. — [MSD Vet Manual: Laying and reproduction in backyard poultry](https://www.msdvetmanual.com/en-au/exotic-and-laboratory-animals/backyard-poultry/laying-and-reproduction-in-backyard-poultry)
- Oestrous cycle: cow 21 d (18–24), oestrus 18 h, polyoestrous all year. Ewe 17 d (14–20), seasonal from early autumn to winter. Doe (goat) 21 d, oestrus 24–48 h, seasonal from early autumn to late winter. Sow 21 d (19–23), oestrus 40–60 h, all year. Rabbit not listed. — [MSD: Features of the reproductive cycle](https://www.msdvetmanual.com/multimedia/table/features-of-the-reproductive-cycle)
- Gestation: cattle about 9 months, sheep 150 d, goat 150 d, pig 114 d, rabbit 31 d. — [MSD: Approximate gestation periods](https://www.msdvetmanual.com/multimedia/table/approximate-gestation-periods)

### Inferences
- Model sheep and goat breeding seasonality as short-day breeders ("early autumn" means March–May in the Southern Hemisphere). CropStack should derive the season from latitude and photoperiod, not fixed calendar months.
- Rabbits are induced ovulators, which is why the table has no cycle length for them. This is general knowledge and was not verified in this session.

### Gaps
- I did not verify a source for turkey (28 d), Muscovy (35 d) or Japanese/coturnix quail (17–18 d) incubation in this session.
- I did not verify eggs-per-year by breed, milk yields or growth curves. DAD-IS breed records may carry some production traits; check the metadata.

## Parasite weather risk: Haemonchus and FAMACHA

### Takeaway
Haemonchus larvae develop best at about 21–27°C (70–80°F) with about 50 mm (2 in) of rain a month. The FAMACHA eyelid score runs from 1 to 5, and animals scoring 4 or 5 (sometimes 3) are treated. Rose et al. 2015 (GLOWORM-FL) is the citable model, although only the author manuscript is open.

### Cited Findings
- *H. contortus* females lay up to 5,000 eggs per day, and the life cycle takes about 21 days. Larvae develop best at 70–80°F and need about 2 inches of rain a month. L3 larvae survive up to 90 days on summer pasture and 180 days in fall and winter. FAMACHA runs from 1 (red) to 5 (white), with treatment generally at 4–5 and sometimes 3; goats need lower thresholds. Source: Purdue Extension AS-573-W (2006). — [Purdue AS-573-W](https://www.extension.purdue.edu/extmedia/AS/AS-573-W.PDF)
- FAMACHA: "Producers must receive training in order to receive a card." The page cites Van Wyk & Bath (2002, *Veterinary Research*) and Malan, Bath & van Wyk (2015, W4 congress, Pretoria). Copyright © 2025 ACSRPC, with no open licence stated. — [wormx.info/famacha](https://www.wormx.info/famacha)
- GLOWORM-FL is a climate-driven simulation of free-living GIN stages. Higher temperature speeds up *H. contortus* development, with a summer trade-off from higher mortality. Rose, Wang, van Dijk & Morgan, *Ecological Modelling* 297:232–245 (2015), DOI 10.1016/j.ecolmodel.2014.11.033. The repository holds the author accepted manuscript. — [Liverpool repository](https://livrepository.liverpool.ac.uk/id/eprint/3050743)

### Inferences
- A simple CropStack risk flag: raise the barber pole worm alert for small ruminants when the 30-day mean temperature is about 18–30°C and rainfall is ≥50 mm, and prompt FAMACHA checks every 2–3 weeks. The interval is common guidance but was not verified here.
- CropStack can mention FAMACHA by name and record scores 1–5, but it should not reproduce the card's colours, and it should point users to certified training.

### Gaps
- I did not verify FAMACHA's Onderstepoort (South Africa) origin on a primary page, or the Van Wyk & Bath 2002 DOI; the wormx page names the authors only.
- I did not get exact development temperature and moisture thresholds from GLOWORM-FL's full text.

## Honeybees: inspection temperatures, swarm season, varroa, South Africa

### Takeaway
The Honey Bee Health Coalition's Varroa guide (9th edition, June 2026) is CC BY-NC-ND 4.0. CropStack can cite and link it but not bundle or adapt it. Its thresholds are 1% (dormant and increase phases) and 2% (peak and decrease phases) mites per 100 bees. For inspections, open hives only above about 13°C (55°F). In South Africa the key issue is the capensis–scutellata boundary.

### Cited Findings
- HBHC "Tools for Varroa Management", 9th edition dated 11 June 2026, © Keystone Policy Center, licensed CC BY-NC-ND 4.0. Thresholds: dormant and population increase <1% no action, ≥1% control; peak and decrease <2% and ≥2%. Alcohol or soap wash of about 300 bees (½ cup) is recommended; the powdered sugar shake is less reliable. Product temperature windows include Apiguard 15–40°C, Thymovar 15–30°C, ApiLife Var 18–35°C, Formic Pro 10–29.5°C, HopGuard3 13–38°C and Apistan >10°C. For oxalic acid there is no set limit, but opening a hive below 4°C carries risk. — [HBHC guide 9th ed. PDF](https://honeybeehealthcoalition.org/wp-content/uploads/2026/08/Tools-for-Varroa-Management-Guide-9th-Edition.pdf)
- Utah State Extension calendar: full inspection "On a warm day with temperatures above 55° F". Clustering begins at 57°F. Cleansing flights happen above 50°F. Swarm season (Utah) starts in May and tapers by July. Mite checks are monthly, with a threshold of ">5 mites per 300 bees". — [USU Beekeeping calendar](https://extension.usu.edu/beekeeping/learn/calendar.php)
- South Africa: *A. m. capensis* laying workers reproduce by thelytoky and take over *A. m. scutellata* colonies. The problem has been serious in the summer rainfall region since 1991. ARC advises minimising movement of bees and frames and testing trapped swarms. The page is dated 2014. — [ARC-PPRI: Honeybee biology / The Capensis problem](https://arc.agric.za/arc-ppri/Pages/Insect%20Ecology/Honeybee-Biology.aspx)
- The department (DALRRD, now DoA) publishes "Consolidated Control Measures relating to honey bees" and a honey bee brochure. I could not fetch them because robots.txt blocked access. — [Consolidated Control Measures PDF](https://old.dalrrd.gov.za/doaDev/sideMenu/plantHealth/docs/Consolidated%20Control%20Measures%20relating%20to%20honey-bees.pdf); [Honey Bee brochure](https://old.dalrrd.gov.za/doaDev/sideMenu/plantHealth/docs/Honey%20Bee%20brochure.pdf)
- DAD-IS has a separate bee data export tool. — [DAD-IS data export](https://www.fao.org/dad-is/data/data-export/en)

### Inferences
- Inspection rule: allow full inspections when the forecast is ≥13°C (55°F), calm and dry; warn below 10°C. Show varroa treatment options filtered by the forecast temperature window.
- Swarm season should come from the local flowering and colony build-up period, not a fixed month. In the South African winter rainfall region (Western Cape), this is roughly spring, August–November. That is an inference and was not verified.
- For SA users, show a warning about moving capensis or scutellata colonies across the regulated boundary.

### Gaps
- I could not read the SA control-measures text (the legal basis is likely the Agricultural Pests Act 36 of 1983, but this is not verified) or the boundary definition.
- I found no open source for SA-specific swarm timing or varroa thresholds for African subspecies, which are generally considered more varroa-tolerant (not verified).

## Medication withdrawal periods: FARAD (US) and South African registrations

### Takeaway
FARAD's VetGRAM gives withdrawal times for US FDA-approved drugs, but the site states no reuse licence, so link to it and do not bundle it. In South Africa, stock remedies are registered under Act 36 of 1947, and I found no open, searchable withdrawal database.

### Cited Findings
- FARAD provides VetGRAM, a searchable database of "uses, restrictions and required withdrawal times (WDT)" for FDA-approved food-animal drugs, and a free request form for licensed veterinarians. No content licence is stated on the home page. — [farad.org](https://farad.org/)
- In South Africa, stock remedy registration runs under the Fertilizers, Farm Feeds, Agricultural Remedies and Stock Remedies Act 36 of 1947. — [gov.za: Register a stock remedy](https://www.gov.za/services/fertilizers-farm-feeds-agricultural-remedies/register-stock-remedy)

### Inferences
- CropStack should not ship withdrawal-period data. Instead it should record the product, date and the withdrawal days the user enters from the label, and then calculate the safe-to-slaughter or safe-to-use-milk or eggs date. This avoids licensing and liability problems across countries.

### Gaps
- I did not verify the Medicines and Related Substances Act 101 of 1965 (SAHPRA) registration database or its terms.
- I did not read FARAD's Data Sharing policy.
