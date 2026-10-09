# Licence conflicts resolved: CropStack open catalog data sources (checked 9 Oct 2026)

Context: CropStack code is MIT and its bundled data would be CC BY-SA 4.0. Every quote below comes from the primary page or file named, fetched on 2026-10-09.

## 1. FAO ECOCROP: CC BY 4.0 (Data Catalog) or CC BY-NC-SA 3.0 IGO / open-access policy?

### Takeaway
The FAO Data Catalog record for ECOCROP is the most specific statement FAO publishes, and it says CC BY 4.0. Treat the database values as CC BY 4.0, which can go into a CC BY-SA 4.0 repo with attribution. The CC BY-NC-SA 3.0 IGO licence and the open-access policy's pre-2018 / pre-23-Dec-2024 rules apply to FAO **publications** (the Knowledge Repository), not to datasets. ECOCROP is **not** named in Annex 1 of the Statistical Database Terms of Use, but Annex 1 is only a list of "examples", so leaving it out does not take ECOCROP out of CC BY 4.0. One practical catch: the catalog record links only to the interactive tool and offers no bulk download.

### Cited Findings
- The FAO Data Catalog API record `ecocrop` (title "ECOCROP") has `license_id: "CC-BY-4.0"`, `license_title: "Creative Commons Attribution 4.0 International"`, `isopen: true`. The record was created 2025-03-18 and modified 2025-04-03. Maintainer: "FAO Land and Water Division". Its organisation description refers to the FAO/IIASA GAEZ cooperation. — [FAO Data Catalog API, package_search?q=ecocrop](https://data.apps.fao.org/catalog/api/3/action/package_search?q=ecocrop); [package_show?id=ecocrop](https://data.apps.fao.org/catalog/api/3/action/package_show?id=ecocrop)
- The record's description reads "information on plants characteristics and crop environmental requirements for more than 2000 plant species". Its only data resource is a link named "ECOCROP tool" to https://ecocrop.apps.fao.org/ecocrop/srv/en/home. It has no CSV or dump. — [same API record](https://data.apps.fao.org/catalog/api/3/action/package_show?id=ecocrop)
- The HTML catalog page (data.apps.fao.org/catalog/dataset?q=ecocrop) returned HTTP 403 to this fetch, so only the API JSON was read. — [FAO Data Catalog](https://data.apps.fao.org/catalog/dataset?q=ecocrop)
- The FAO Statistical Database Terms of Use say datasets are CC BY 4.0 "Unless specified otherwise in their metadata or webpage". The Annex is titled "ANNEX 1: EXAMPLES OF FAO CORPORATE STATISTICAL DATABASES". It lists AMIS, AIDmonitor, DIEM, DAD-IS, FAODATA Explorer, FAOSTAT, FAO/INFOODS, FishStat, FPMA, EMPRES-i+, FRA, FAO/WHO GIFT, AQUASTAT, Hand-in-Hand, WaPOR and WIEWS. **ECOCROP does not appear anywhere on that page.** — [FAO Statistical Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use/en/)
- The same terms add extra conditions beyond CC BY 4.0. Datasets "shall not be used for or in conjunction with the promotion of a commercial enterprise". They also forbid implying FAO endorsement and include a third-party-data exception. — [FAO Statistical Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use/en/)
- FAO's general web terms say publications fall under the Open Access policy and "Specific statistical databases are covered by the Open Data Licensing Policy". Other web content is limited to non-commercial use. — [FAO Terms and Conditions](https://www.fao.org/contact-us/terms/en/)
- The open-access policy for publications, effective 23 December 2024, says "Creative Commons licences do not apply to works published before June 2018." Works from June 2018 to December 2024 that carry the "Creative Commons IGO 3.0 licence icon" keep that licence. Commercial requests for publications from before 23 Dec 2024 go to the licence-request form. This policy covers publications and points to the separate "FAO Policy on Open Data Licensing for Statistical Databases". — [Policy on Open Access for FAO publications (PDF via openknowledge.fao.org)](https://openknowledge.fao.org/bitstreams/6e7af061-3928-4c55-99c5-6b5e4cb8e3f0/download)
- The ecocrop.apps.fao.org home page served only a ~3 KB shell with the welcome text. The fetched HTML had no licence or terms footer, probably because the page is rendered in JavaScript. — [ECOCROP tool](https://ecocrop.apps.fao.org/ecocrop/srv/en/home)
- Recocrop 0.4-2 (CRAN, dated 2025-07-21): the DESCRIPTION gives `License: GPL (>= 3)`, which covers the package. It says nothing separate about a data licence. The help file `man/parameters.Rd` says "Default ecocrop parameters for 1710 taxa" and that they are "derived from values that used to be available on the website of the" FAO. Several values are transformed: monthly precipitation is derived from annual, KTMP±1, and duration is GMIN+1 month. `man/Recocrop-package.Rd` says "Default *parameters* used to be available from the UN FAO." The data ships as `inst/parameters/ecocrop.rds`. — [CRAN DESCRIPTION](https://cran.r-project.org/web/packages/Recocrop/DESCRIPTION); [source tarball Recocrop_0.4-2.tar.gz](https://cran.r-project.org/src/contrib/Recocrop_0.4-2.tar.gz)

### Inferences
- The conflict comes from mixing up two FAO regimes. "CC BY-NC-SA 3.0 IGO" and the June 2018 / Dec 2024 rules belong to the publications policy. The ECOCROP catalog record belongs to the data regime and says CC BY 4.0 explicitly. Under the terms' "unless specified otherwise in their metadata" rule, the dataset's own metadata decides, and here it says CC BY 4.0. The CC BY 4.0 finding governs.
- Data under CC BY 4.0 can be included in a CC BY-SA 4.0 data collection, provided the FAO attribution and a note of changes are kept. FAO's extra "no commercial promotion / no endorsement" terms are not part of the CC licence and cannot be passed on through BY-SA. List them in a NOTICE/ATTRIBUTION file for this subset and do not claim they are removed.
- Recocrop's GPL licence does not relicense FAO's data. Recocrop is useful as a provenance trail and as a possible source of the values, but its values are transformed. If CropStack wants the original FAO fields, it should not take them from the derived Recocrop columns without saying so.

### Gaps
- The ecocrop.apps.fao.org footer and terms are unverified, because the page is rendered in JavaScript and no licence text was in the fetched HTML.
- I found no official bulk download of the ECOCROP values on the catalog record, so the record covers "the tool/database" and nothing is downloadable from it. Whether FAO would see scraping the tool as covered is unverified. Both the catalog record and the terms are silent on it.
- I found no FAO-specified citation string for ECOCROP. Use the generic database citation format quoted in §3.

## 2. OpenFarm data: CC0?

### Takeaway
Confirmed. The archived OpenFarm README has a "Data License" section stating CC0. The repo's LICENSE file is MIT and covers the code only. The rescue repo `thefullnacho/openfarm-crops-rescue` is CC0 1.0 and holds 340 records rebuilt from Wayback Machine captures. Both are fine to redistribute under CC BY-SA 4.0. The rescue README warns that the data quality is poor.

### Cited Findings
- The archived OpenFarm README, under the heading "### Data License", says: "All data within the OpenFarm.cc database is in the Public Domain (CC0)". It links to creativecommons.org/publicdomain/zero/1.0/. — [OpenFarm README (raw, branch mainline)](https://raw.githubusercontent.com/openfarmcc/OpenFarm/mainline/README.md)
- The same README has a separate "### Software License" section with MIT terms. The repo's LICENSE file is MIT, "Copyright (c) 2016 OpenFarm". — [OpenFarm LICENSE](https://raw.githubusercontent.com/openfarmcc/OpenFarm/mainline/LICENSE)
- The README's shutdown notice says servers were shut down "in April of 2025" and the repo was publicly archived. — [OpenFarm README](https://raw.githubusercontent.com/openfarmcc/OpenFarm/mainline/README.md)
- The rescue repo's LICENSE is the full "CC0 1.0 Universal" legal code. The latest commit is 754cfd7, dated 2026-07-10, by TheFullNacho. Files: LICENSE, README.md, crops.json (375,121 bytes). — [thefullnacho/openfarm-crops-rescue (git clone)](https://github.com/thefullnacho/openfarm-crops-rescue)
- The rescue README describes the provenance. The author scraped "the Wayback Machine's latest captures" of every archived `openfarm.cc/en/crops/*` page, 358 pages in all. 13 junk or duplicate entries were pruned, wrong identifications were removed, and 4 binomial typos were fixed against GrowStuff names. The result is "340 crops". The README also says "no public data dump was ever released" and cites OpenFarm issue #940. — [rescue README](https://github.com/thefullnacho/openfarm-crops-rescue)
- I checked crops.json directly: it is a JSON list of **340** records. Each one has `source.license: "CC0-1.0"` and a `waybackUrl`. Field coverage per the README: description 330, binomialName 305, companions 134. — [crops.json](https://github.com/thefullnacho/openfarm-crops-rescue)
- The README's quality warning: "Treat this as a useful scaffold, not an authority". It also says GrowStuff data (CC BY-SA) was deliberately not mixed in. — [rescue README](https://github.com/thefullnacho/openfarm-crops-rescue)

### Inferences
- CC0 data can go into a CC BY-SA 4.0 collection with no conditions. Crediting OpenFarm and the rescue repo is still good practice.
- The GrowStuff name cross-check corrected only names, so it should not bring GrowStuff's CC BY-SA content into the set. That rests on the README's description and was not independently audited.

### Gaps
- The GitHub API and web UI returned 403 for the rescue repo in this session. The repo was read through an anonymous git clone, so the star count, issues and other metadata were not checked.
- No official OpenFarm data dump was found, which matches the rescue README's statement.

## 3. FAO DAD-IS: listed in Annex 1 under CC BY 4.0? Required citation?

### Takeaway
Confirmed. Annex 1 of the FAO Statistical Database Terms of Use lists "Domestic Animal Diversity Information System (DAD-IS)", so DAD-IS data defaults to CC BY 4.0 plus FAO's additional terms. The required citation follows the generic format below.

### Cited Findings
- Annex 1 lists "Domestic Animal Diversity Information System (DAD-IS)". — [FAO Statistical Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use/en/)
- Required citation format: "FAO. [YYYY (year of last update)]. [Name of database: Name of dataset OR Name of database]. [Accessed on [DD Month YYYY]]. [URL] Licence: CC-BY-4.0." — [FAO Statistical Database Terms of Use, §3 Attribution](https://www.fao.org/contact-us/terms/db-terms-of-use/en/)
- The CC BY 4.0 default applies "Unless specified otherwise in their metadata or webpage". — [same](https://www.fao.org/contact-us/terms/db-terms-of-use/en/)

### Inferences
- A filled-in example: "FAO. 2026. Domestic Animal Diversity Information System (DAD-IS). Accessed on 9 October 2026. https://www.fao.org/dad-is/ Licence: CC-BY-4.0." The year and URL are placeholders. Check them against DAD-IS before use.

### Gaps
- I did not check the DAD-IS site's own metadata or footer for any dataset-level override ("unless specified otherwise"). That is unverified.

## 4. FAO-56 Kc tables via pyfao56: what does pyfao56 say?

### Takeaway
pyfao56 as a whole is a CC0 / US-government public-domain work. tables.py says only that its data comes from FAO-56 Tables 11, 12, 17 and 22. It has no copyright or licence statement about the FAO table content and does not claim FAO's permission. Whether FAO's copyright extends to the numbers is a legal question that pyfao56 does not address.

### Cited Findings
- pyfao56 `LICENSE.md` says "As a work of the United States Government, this package is in the public domain within the United States." It also waives rights worldwide via CC0 1.0. — [pyfao56 LICENSE.md](https://raw.githubusercontent.com/kthorp/pyfao56/main/LICENSE.md)
- PyPI lists pyfao56 version 1.4.3 with licence "Public Domain". — [PyPI JSON](https://pypi.org/pypi/pyfao56/json)
- The README says tables.py "Provides the data from Table 11 (growth stage lengths), Table 12 (Kcm and hmax), Table 17 (Kcb), and Table 22 (Zrmax and pbase) in FAO-56". It cites Allen et al. 1998, FAO Irrigation and Drainage Paper No. 56. — [pyfao56 README](https://raw.githubusercontent.com/kthorp/pyfao56/main/README.md)
- The tables.py docstring says it "contains suggested values ... as defined in FAO-56, specifically in Tables 11, 12, 17, and 22". It is credited "12/12/2024 FAOTables class created by Reagan Ames and Tyler Pokoski" and "01/08/2025 Modification for release by Kelly Thorp". A grep found **zero** occurrences of "copyright" or "licen" in tables.py. — [tables.py](https://raw.githubusercontent.com/kthorp/pyfao56/main/src/pyfao56/tools/tables.py)
- For context, FAO-56 was published in 1998. FAO's open-access policy says CC licences "do not apply to works published before June 2018". — [FAO Open Access policy PDF](https://openknowledge.fao.org/bitstreams/6e7af061-3928-4c55-99c5-6b5e4cb8e3f0/download)

### Inferences
- pyfao56's CC0 can only waive the rights USDA-ARS holds, which cover the code and the typing-in. It cannot waive FAO's rights in the 1998 publication. Bare numeric facts such as Kc values are generally not copyrightable in the US, but the selection and arrangement of a table, and EU sui generis database rights, may be. FAO-56 is pre-2018, so no CC licence covers it. This is a legal judgement and not something a primary source confirms.
- Low-risk approach: store only the numeric values, with CropStack's own crop keys and structure. Cite FAO-56 (Allen et al. 1998) as the source of the facts. Do not copy the table layout, footnotes or prose verbatim.

### Gaps
- No primary source from FAO or pyfao56 states whether the FAO-56 table values may be redistributed. That is unverified.

## 5. Wikipedia "List of companion plants": CC BY-SA 4.0? Row count?

### Takeaway
Confirmed CC BY-SA 4.0, which matches CropStack's data licence exactly. The page has about 99 plant rows in 5 tables.

### Cited Findings
- The page footer links the "Creative Commons Attribution-ShareAlike 4.0 License" at creativecommons.org/licenses/by-sa/4.0. — [Wikipedia: List of companion plants](https://en.wikipedia.org/wiki/List_of_companion_plants)
- The raw wikitext (82,444 bytes, fetched 2026-10-09) has 5 tables under the headings "For vegetables", "For fruit", "For herbs", "For flowers" and "Other". Row blocks counted per table, each including one header block: 39, 10, 31, 20 and 4, so 104 in total. That leaves **about 99 plant rows**: roughly 38 vegetables, 9 fruit, 30 herbs, 19 flowers and 3 other. — [raw wikitext](https://en.wikipedia.org/w/index.php?title=List_of_companion_plants&action=raw)

### Inferences
- Reuse needs attribution, a link to the page and its history, a note of changes, and the same BY-SA 4.0 licence. CropStack's data licence already meets the last condition.

### Gaps
- I could not record the revision ID or timestamp because the MediaWiki API rate-limited the request. Pin a revision ID when the data is imported.
- The row count is a wikitext heuristic and may be off by a few where rows are merged or blank.
