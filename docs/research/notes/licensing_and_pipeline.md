# Legal and engineering rules for building CropStack's open crop/pest/livestock catalog

Not legal advice. These notes summarise primary and secondary sources as of 2026-10-09 and flag uncertainty. The maintainer is in South Africa (ZA); users and contributors are worldwide.

## 1. Copyright in facts and data (US, EU, UK, ZA): facts vs expression

### Takeaway
Single facts (for example "sow 6 mm deep", "germinates at 20-30 C", "days to maturity 70") are not protected anywhere. The risk lies in copying expression (prose), copying a whole compilation's selection or arrangement, and, in the EU and UK only, extracting a substantial part of a database that someone invested in. South Africa is the most protective of the four for compilations ("sweat of the brow") but has no sui generis database right. Practical rule: take individual values from many sources, write all prose yourself, and never bulk-mirror one site's structure.

### Cited Findings
- **US, Feist v. Rural (1991):** "No author may copyright his ideas or the facts he narrates." A compilation is protected only for its original selection or arrangement, "In no event may copyright extend to the facts themselves", "the copyright in a factual compilation is thin", and "copyright rewards originality, not effort" (sweat of the brow rejected). — [Justia, 499 U.S. 340](https://supreme.justia.com/cases/federal/us/499/340/)
- **US Copyright Office, Circular 33:** "A mere list of ingredients" or simple directions is not copyrightable. A recipe that creatively explains how or why to do something may be protected as to its written explanation and photos, but not the process. Procedures, processes and methods of operation are not protected. Layout or format of a web page or form is not copyrightable. — [USCO Circular 33](https://www.copyright.gov/circs/circ33.pdf)
- **US federal works, 17 USC 105(a):** "Copyright protection under this title is not available for any work of the United States Government." — [Cornell LII](https://www.law.cornell.edu/uscode/text/17/105)
- **EU sui generis right, BHB v William Hill (CJEU, 9 Nov 2004, C-203/02):**
  - Only investment in *obtaining*, verifying or presenting existing data counts. Investment in *creating* the data does not.
  - "Substantial part" is judged both quantitatively (volume against the whole) and qualitatively (scale of the investment behind the extracted part).
  - Repeated, systematic extraction of insubstantial parts is prohibited only if, taken together, it reconstitutes a substantial part and seriously prejudices the investment.
  - [CJEU press release 89/04](https://curia.europa.eu/en/actu/communiques/cp04/aff/cp040089en.pdf)
- **EU, Ryanair v PR Aviation (CJEU, 15 Jan 2015, C-30/14):** If a database is protected by neither copyright nor the sui generis right, the Database Directive does not apply. Its owner may then restrict screen scraping by contract (website terms), subject to national law. — [SCL](https://www.scl.org/3280-the-cjeu-takes-flight-databases-and-air-fares/); [Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/ryanair-ltd-v-pr-aviation-bv-contracts-rights-and-users-in-a-low-cost-database-law/)
- **UK after Brexit:** The UK keeps its own sui generis database right. A database qualifies when there was "substantial investment in obtaining, verifying or presenting the data". For databases created on or after 1 Jan 2021, only UK citizens, residents and businesses qualify for UK database right, and UK makers cannot get EEA database rights. Database copyright (original selection or arrangement) is unaffected. — [GOV.UK guidance](https://www.gov.uk/guidance/sui-generis-database-rights)
- **South Africa, Copyright Act 98 of 1978:**
  - s1(1) "literary work" includes "tables and compilations of data stored or embodied in a computer".
  - Originality means "not copied", plus a substantial (not trivial) degree of skill, judgment or labour (*Haupt t/a Softcopy v Brewers Marketing Intelligence*, SCA 2006). In effect this is a sweat-of-the-brow approach, so even plain compilations can be protected.
  - *Board of Healthcare Funders v Discovery Health* (2012) protected a coding-system compilation.
  - The source does not identify any sui generis database right in ZA.
  - [CIPIT/Strathmore](https://cipit.strathmore.edu/database-protection-and-the-limits-of-copyright-lessons-from-south-africa/)
- **ZA Copyright Amendment Bill:** On 26 June 2026 the Constitutional Court (CCT 306/24) upheld the move to "fair use" and the personal, education and library exceptions, read narrowly. It struck down s12D(1)-(5), so the Bill cannot yet be signed. Neither the Act nor the Bill has a text-and-data-mining exception. — [GoLegal (Adams & Adams commentary)](https://www.golegal.co.za/constitutional-court-copyright/); [ENSafrica](https://www.ensafrica.com/news/detail/12103/a-decade-in-the-making-constitutional-court-r)

### Inferences
- **Facts vs expression rule set for CropStack:**
  - **Safe:** Numeric and enumerated values (spacing, depth, pH range, temperature, days to maturity, host/pest relationships, companion yes/no) stored as structured fields with a citation.
  - **Risky:** Copying or lightly paraphrasing sentences or paragraphs of care guidance, symptom descriptions or images. Treat prose as expression. Write original text from several sources. Do not do "close paraphrase", which keeps sentence structure and sequence.
  - **Risky:** Taking one site's entire species list, its field set and its categories wholesale. This touches selection/arrangement copyright (thin in the US, stronger in ZA under the low *Haupt* threshold) and the EU/UK sui generis right if the site is EU/UK-based and the extraction is substantial.
- **Jurisdiction is driven by where acts happen.** Redistribution from GitHub reaches the EU and UK, so EU/UK database right matters even though the maintainer is in ZA. The most conservative common rule is: never reconstitute a substantial part of any single protected database without a licence.
- **ZA's lower originality bar** makes "copying a South African compilation in bulk" (for example a local planting-calendar table) riskier than under US law. Prefer licensed or government sources for ZA-specific data.
- **US federal sources are public domain.** These include USDA PLANTS, USDA-ARS GRIN, NRCS and many extension pages from federal agencies (but not state land-grant universities, which are usually copyrighted). Images and third-party content embedded in them may still be copyrighted.

### Gaps
- No primary-source verification of whether ZA courts would apply *Haupt* to a scraped plant-care dataset. This needs a ZA IP lawyer's view.
- The EUR-Lex fetch of DSM Directive 2019/790 Art. 3/4 (TDM exceptions and machine-readable opt-out) failed. From general knowledge: Art. 4 lets anyone mine lawfully accessed content unless the rightholder reserves rights in a machine-readable way. This is unverified here.
- The UK database right term (15 years from completion/substantial change) is not stated on the fetched GOV.UK page. It comes from general knowledge.

## 2. Licence compatibility for data inside an MIT code repo

### Takeaway
Keep the code under MIT and put `catalog/` under a separate data licence. Accept inputs only under CC0, public domain, CC BY 4.0, ODC-By or (with care) CC BY-SA 4.0 / ODbL. Choose the catalog licence to match the strictest share-alike input you accept. Reject NC and ND sources (FAO CC BY-NC-SA 3.0 IGO, PFAF CC BY-NC-SA, iNaturalist CC BY-NC media) for redistribution in the repo; only cite them as "further reading" links.

### Cited Findings
- **CC licences apply only where copyright exists:** "CC licenses are operative only when applied to material in which a copyright exists." Unlike ODbL/ODC-BY, they impose no contractual conditions on unprotected facts. — [CC FAQ](https://creativecommons.org/faq/)
- CC recommends against CC licences for software. CC0 is GPL-compatible. CC BY works may be included in CC BY-SA works with attribution. — [CC FAQ](https://creativecommons.org/faq/)
- **CC 4.0 and sui generis database rights:**
  - Extracting all or a substantial portion of a database into your own SGDR-protected database creates "Adapted Material".
  - For BY-SA, you must share alike your rights in the new database, but not the licensed database's contents.
  - Attribution is required "when you are publicly sharing all or a substantial portion of the database contents".
  - NC limits extraction to non-commercial use, and ND bars Adapted Material.
  - [CC wiki: 4.0/Sui generis database rights](https://wiki.creativecommons.org/4.0/Sui_generis_database_rights)
- **ODbL 1.0:** Attribute the database. If you publicly use an adapted database, or works produced from an adapted database, you must offer that adapted database under ODbL. DRM is allowed only if an unrestricted version is also distributed. — [ODC ODbL summary](https://opendatacommons.org/licenses/odbl/summary/)
- **Open Food Facts layered licensing:** database under ODbL, individual contents under DbCL, product images under CC BY-SA 3.0. — [OFF docs](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/license-be-on-the-legal-side/)
- **FAO publications:** example page under CC BY-NC-SA 3.0 IGO.
  - Copy and adapt only "for non-commercial purposes".
  - Adaptations must use "the same or equivalent Creative Commons licence".
  - No implied endorsement, and no FAO logo.
  - Commercial use needs a licence request.
  - [FAO copyright page](https://openknowledge.fao.org/server/api/core/bitstreams/02e3c6af-7df7-4a38-a7de-85a037e32e64/content/copyright.html)
  - Note: some newer FAO publications have moved to CC BY 4.0. Check each item ([FAO Open Knowledge item example](https://openknowledge.fao.org/handle/20.500.14283/cd7464en)). This is unverified for specific titles.
- **PFAF:**
  - The licence page is internally inconsistent: it says "CC Attribution 4.0" but links to CC BY-NC-SA 4.0 for text.
  - Database images are CC BY-NC-ND 3.0, other images "cannot be used", and code is all-rights-reserved.
  - [PFAF licence page](https://pfaf.org/User/cmspage.aspx?pageid=136)
- **Growstuff:** Structured data is CC BY-SA 3.0 Unported. Its Australian Food Composition data is CC BY 4.0. — [Growstuff API policy](https://www.growstuff.org/policy/api)
- **OpenFarm:** Data was originally CC BY 4.0. A 2014 Loomio proposal to move to CC0 (argument: attribution chains get unmanageable when guides are forked and remixed) passed with no objections, and a 2017 note says "we'll change the OpenFarm data license to CC0". Whether this was implemented is unconfirmed. — [Loomio](https://www.loomio.com/d/BRoQnYHX/should-openfarm-s-data-be-cc0-instead-of-cc-by). OpenFarm itself shut down, and its crop data was later restored elsewhere by the community ([growingfruit.org](https://growingfruit.org/t/openfarms-crop-data-restored-in-website/81182)).
- **iNaturalist:**
  - Users choose a licence, and the default for photos is reported as CC BY-NC.
  - Only CC0, CC BY and CC BY-NC observations flow to GBIF; CC BY-SA and BY-ND observations are excluded.
  - [iNaturalist blog](https://www.inaturalist.org/posts/30692-tech-tip-tuesday-understanding-licensing)

### Inferences
- **Recommended repo layout:**
  - `LICENSE` (MIT) covers code.
  - `catalog/LICENSE` covers data, plus a `NOTICE`/`ATTRIBUTION` file. The README and wiki state that the MIT grant does not cover `catalog/`.
  - OpenStreetMap (ODbL data, separate code licences), Open Food Facts (ODbL/DbCL/CC BY-SA) and Wikidata (CC0 data) all use this split. Wikidata's CC0 status is from general knowledge; the fetch failed.
- **Catalog licence options:**
  1. **CC BY-SA 4.0:** Lets you ingest CC BY-SA and CC BY sources. Downstream users must share alike. It is compatible with Wikipedia/Growstuff-style data. CC 4.0 handles sui generis rights explicitly.
  2. **ODbL + DbCL:** The OSM/OFF model. It is better tailored to databases, but ODbL is not CC BY-SA compatible in either direction. That would block CC BY-SA 3.0 Growstuff data.
  3. **CC0:** Maximum reuse, but you could then only ingest CC0, public domain and pure facts, and no CC BY data unless attribution is still delivered per value.
  - **Pragmatic pick:** CC BY-SA 4.0 for the catalog. Keep per-value licence fields so a CC0 subset can be exported later.
- **NC licences (CC BY-NC, BY-NC-SA, FAO 3.0 IGO) are incompatible with an open-source/open-data catalog.** CropStack is MIT, which allows commercial use, and self-hosters may be farms or businesses. NC content in the repo would make the repo non-redistributable under a single open licence and cannot be relicensed. Reading NC sources to verify facts is fine, because facts are not covered. Copying NC prose, images or substantial database portions is not.
- **CC BY-SA 3.0 into a 4.0 catalog:** The 3.0 SA clause allows later versions ("a later version of this License with the same License Elements"). From general knowledge, this is unverified here.
- **Public domain (US federal) values** need no licence, but cite them anyway for provenance. Mark them as `license: public-domain-us-gov` and do not assume the same status outside the US. Other countries may treat foreign government works differently. This is uncertain.

### Gaps
- CC FAQ answers on mixing licences, NC definitions and TASL were truncated in the fetch.
- No primary confirmation of the Wikidata licence page (fetch failed). Wikidata's CC0 status is from general knowledge.
- The exact CC BY-SA 3.0 to 4.0 forward-compatibility text is not fetched.

## 3. Website terms of service, robots.txt and ethical scraping

### Takeaway
In the US, scraping public, logged-off pages is unlikely to be a CFAA crime. However, terms of service you have *accepted* (through an account, or possibly clickwrap) are enforceable contracts, and the EU allows contractual bans on scraping unprotected databases. robots.txt is a standard, not access control, but honour it, rate-limit and identify yourself. Prefer official APIs and bulk dumps over HTML scraping.

### Cited Findings
- **hiQ v LinkedIn:**
  - The 9th Circuit twice held that scraping public pages likely did not violate the CFAA "without authorization" clause.
  - In Nov 2022 LinkedIn nevertheless won summary judgment on breach of contract: hiQ had accepted the user agreement when it created an account, and had used fake profiles.
  - The case settled in Dec 2022 with a consent judgment: a permanent ban, deletion of data and code, and $500k damages. Being stipulated, it is non-precedential.
  - [ZwillGen](https://www.zwillgen.com/alternative-data/hiq-v-linkedin-wrapped-up-web-scraping-lessons-learned/)
- **Meta v. Bright Data (N.D. Cal., Judge Chen, Jan 2024):**
  - The court granted summary judgment to Bright Data on breach of contract. The terms governed "your use" of the products, and logged-off scraping of public data was not "use", so selling that data was not a breach.
  - [Farella Braun + Martel](https://www.fbm.com/data-analytics/publications/major-decision-affects-law-of-scraping-and-online-data-collection-meta-platforms-v-bright-data/)
  - Meta dropped the suit and its right to appeal around late Feb or March 2024 ([MediaPost](https://www.mediapost.com/publications/article/393996/None)). The FBM date says Jan 23 and MediaPost says "February 2024 ruling", so there is a minor date discrepancy.
- **Ryanair v PR Aviation:** EU website owners of unprotected databases can contractually prohibit scraping, subject to national contract law. — [SCL](https://www.scl.org/3280-the-cjeu-takes-flight-databases-and-air-fares/)
- **RFC 9309 (Sept 2022, IETF Standards Track):**
  - Robots rules "are not a form of access authorization".
  - Crawlers identify with a product token that appears in the User-Agent.
  - Do not rely on a cached robots.txt for more than 24 h.
  - A 4xx means everything is allowed. A 5xx means assume complete disallow; if that persists (for example 30 days), the crawler may treat the file as unavailable.
  - [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html)
- **EU AI/TDM opt-outs** are increasingly expressed in robots.txt and related machine-readable signals. — [Communia](https://communia-association.org/?p=4602) (secondary, not fully read)

### Inferences
- **Practical rules for CropStack scrapers:**
  - Never log in, create accounts or click "I agree" on a source you scrape.
  - Read the ToS of every source anyway, and record a `tos_reviewed` date and any scraping prohibition in the source registry. If the ToS explicitly forbids scraping or reuse, skip the source or ask for permission. Because of Ryanair, this matters most for EU sites.
  - Honour robots.txt (use Protego/Scrapy's `ROBOTSTXT_OBEY=True`) and any `Crawl-delay`.
  - Use about 1 request per 1-5 s per host with AutoThrottle, and send conditional requests (ETag / If-Modified-Since).
  - Send a descriptive User-Agent such as `CropStackCatalogBot/1.0 (+https://github.com/<org>/cropstack; maintainer-email)`.
  - Scrape only on a schedule, not on user request. Self-hosted instances should *never* scrape; they consume the curated YAML. This avoids thousands of instances hammering sources and keeps the legal footprint with the maintainer-run pipeline.
- The CFAA, the ZA Cybercrimes Act 19 of 2020 and the UK CMA cover unauthorised access. Staying on public, unauthenticated pages and respecting blocks (no IP rotation to evade bans) keeps the pipeline clear of them. The ZA Cybercrimes Act point is from general knowledge, not researched here.

### Gaps
- No ZA case law on web scraping or ToS enforceability was found in this session.
- The EU DSM Art. 4 machine-readable opt-out text was not fetched (see section 1 gaps).

## 4. Attribution: TASL in the app UI and in YAML

### Takeaway
Store TASL (Title, Author, Source URL, Licence) plus retrieval date for every source once in a source registry. Reference it from each value by ID. Render a per-plant "Sources" panel and a global Credits/Attributions page in the app. This matches CC's own recommended practice for many-source works.

### Cited Findings
- **CC recommended practice:**
  - Give Title, Author, Source and Licence for each work. Title is optional in 4.0.
  - Link to the original URL and to the licence deed.
  - Note modifications for adaptations, and follow the licensor's requested credit.
  - When space is limited, use a separate credits page listing each item, with clickable Author/Source/Licence.
  - Credit the creator, not just the host site.
  - "There is no single correct format."
  - [CC wiki: Recommended practices for attribution](https://wiki.creativecommons.org/wiki/Recommended_practices_for_attribution)
- CC 4.0 attribution for databases is triggered by publicly sharing all or a substantial portion. — [CC wiki SGDR](https://wiki.creativecommons.org/4.0/Sui_generis_database_rights)
- FAO additionally requires no implied endorsement and no logo use. — [FAO](https://openknowledge.fao.org/server/api/core/bitstreams/02e3c6af-7df7-4a38-a7de-85a037e32e64/content/copyright.html)

### Inferences
- Suggested YAML (illustrative):
  ```yaml
  # catalog/sources.yaml
  - id: usda-plants
    title: USDA PLANTS Database
    author: USDA NRCS
    url: https://plants.usda.gov/
    license: public-domain-us-gov
    tos_reviewed: 2026-10-01
    access: bulk-download   # api | bulk-download | html-scrape | manual
  # catalog/crops/tomato.yaml
  days_to_maturity:
    value: {min: 60, max: 85}
    unit: day
    sources:
      - {ref: usda-plants, retrieved: 2026-09-30, locator: "symbol=SOLY2", snapshot: "sha256:..."}
      - {ref: some-extension-guide, retrieved: 2026-09-28, page: 4}
    modified: "range merged from 2 sources"
  ```
- **App UI:** Add an info icon per field showing source titles linked to URLs. Add a "Data sources & licences" page generated from `sources.yaml`. Show a licence notice in exports and API responses. For CC BY-SA, state that adaptations of the catalog must be shared alike.

### Gaps
- No primary guidance found on the minimum attribution granularity (per value vs per dataset) a court would require. CC says flexibility is "reasonable to the medium".

## 5. Provenance and data-quality architecture

### Takeaway
Use a lightweight, Wikidata-inspired model: value, qualifiers and a references list, validated by JSON Schema/Pydantic in CI. Wrap the catalog as a Frictionless Data Package (v2) whose resources carry their own `licenses`, `sources` and `hash`. Keep raw snapshots content-hashed outside git (DVC or WARC files in object storage). All scraper output lands as PR diffs for human review.

### Cited Findings
- **Data Package v2:**
  - Package-level `licenses` (each with `name` as an Open Definition ID and/or `path`, plus `title`), `sources` (`title`, `path`, `email`, `version`) and `contributors` (with roles such as `rightsHolder`, `dataCurator`). The spec notes `licenses` "is not legally binding".
  - [datapackage.org Data Package](https://datapackage.org/standard/data-package/)
- **Data Resource:** Each resource may declare its own `sources` and `licenses`, inheriting from the package if omitted. The `hash` defaults to MD5 and can be algorithm-prefixed, for example `"sha1:..."` (so `sha256:` is possible). — [datapackage.org Data Resource](https://datapackage.org/standard/data-resource/)
- **Tool versions and status (from the PyPI JSON API, 2026-10-09):**
  - frictionless 5.20.0 (2026-10-08, MIT) — [PyPI](https://pypi.org/project/frictionless/)
  - jsonschema 4.26.0 (2026-01) — [PyPI](https://pypi.org/project/jsonschema/)
  - pydantic 2.14.0 (2026-10-08) — [PyPI](https://pypi.org/project/pydantic/)
  - linkml 1.12.0 (2026-10-08, Apache-2.0; a schema language that generates JSON Schema/Pydantic) — [PyPI](https://pypi.org/project/linkml/)
  - dvc 3.67.1 (2026-03-31) — [PyPI](https://pypi.org/project/dvc/)
  - warcio 1.8.1 (2026-03-31; WARC snapshot read/write) — [PyPI](https://pypi.org/project/warcio/)

### Inferences
- **Per-value schema** (modelled on Wikidata statement/qualifier/reference and W3C PROV's entity–activity–agent):
  - `value` (scalar, or a `{min, max}` range) with `unit` (UCUM or SI)
  - optional `qualifiers` (region/climate zone, cultivar, growing condition)
  - `sources[]`, each with ref, retrieved date, locator and snapshot hash
  - `evidence` (`peer-reviewed | extension-service | government | grower-reported | inferred`)
  - `confidence` (`high | medium | low`)
  - optional `rank` (`preferred | normal | deprecated`, Wikidata-style)
  - Keep it far simpler than full PROV-O. PROV-JSON export can be generated later if needed.
- **Conflicting values:**
  - Store as a range when the sources agree on a domain but differ in magnitude.
  - Keep separate statements with qualifiers when the difference is contextual (zone or cultivar).
  - Mark one `preferred` by evidence level (government/peer-reviewed beats blogs).
  - Never silently average. A CI check flags a conflict when the sources' ranges do not overlap.
- **Reproducible pipeline:**
  1. `sources.yaml` registry (licence, ToS review, access method).
  2. Fetchers, one per source, that prefer API or bulk dump. Output goes to `raw/<source>/<date>/…` as WARC or the original file, named by SHA-256. Raw snapshots are kept out of git (DVC remote, or a GitHub release asset), because they may be copyrighted. Store them for internal verification, not redistribution.
  3. Pure, deterministic extractors (raw to normalised JSON) with unit tests on fixture snapshots.
  4. A merger that combines the result with hand-curated YAML. Curated values win, and scraped values only propose.
  5. Validation: Pydantic/JSON Schema, plus `frictionless validate datapackage.yaml`, plus licence-gate rules (CI fails if any value's source licence is NC, ND or unknown, or if any `prose` field is identical to its source text, for example with a fuzzy-match threshold).
  6. A scheduled GitHub Actions cron (monthly) runs the fetchers and opens a PR with the YAML diff and a change summary. A human reviews it, because the PR is the audit trail.
  7. Tag catalog releases separately (for example `catalog-v2026.10`) and include the datapackage `hash` per resource.
- **Lazy alternative:** DVC is optional. A simple `snapshots.lock` (url, retrieved, sha256, size) in git, with the bytes stored in an object bucket or Internet Archive (Save Page Now), gives most of the reproducibility with no extra tooling.

### Gaps
- W3C PROV and Wikidata Help:Sources pages were not fetched (Wikidata fetch failed). Their descriptions here come from general knowledge: P248 "stated in", P854 "reference URL", P813 "retrieved", and preferred/normal/deprecated ranks.
- No measured data on the size or performance limits of YAML catalogs at "hundreds of varieties" scale. This is likely a non-issue.

## 6. Current Python tooling (October 2026)

### Takeaway
All the main tools are actively maintained. The exceptions are httpx (stable but no release since Dec 2024) and SPARQLWrapper (last release 2022, still works). A minimal stack: httpx + hishel (HTTP caching) + Protego (robots) + selectolax/parsel (parsing) + trafilatura (main-text extraction for human review only) + pygbif / Wikidata SPARQL. Use Scrapy only if crawling many pages, and Playwright only for JS-only sites.

### Cited Findings (latest version, upload date, licence, from the PyPI JSON API on 2026-10-09)
- Scrapy 2.19.0, 2026-09-10, BSD-3 — [PyPI](https://pypi.org/project/Scrapy/)
- scrapy-playwright 0.0.48, 2026-07-10, BSD-3 (still 0.0.x) — [PyPI](https://pypi.org/project/scrapy-playwright/)
- httpx 0.28.1, 2024-12-06, BSD-3 (no release in ~22 months; still pre-1.0) — [PyPI](https://pypi.org/project/httpx/)
- hishel 1.4.0, 2026-09-16 (HTTP caching for httpx) — [PyPI](https://pypi.org/project/hishel/)
- selectolax 1.0.0, 2026-10-03, MIT (just reached 1.0) — [PyPI](https://pypi.org/project/selectolax/)
- parsel 1.12.1, 2026-09-28, BSD-3 — [PyPI](https://pypi.org/project/parsel/)
- trafilatura 2.3.1, 2026-10-06, Apache-2.0 — [PyPI](https://pypi.org/project/trafilatura/)
- playwright 1.63.0, 2026-09-15, Apache-2.0 — [PyPI](https://pypi.org/project/playwright/)
- Protego 0.7.0, 2026-09-21, BSD-3 (robots.txt parser used by Scrapy) — [PyPI](https://pypi.org/project/Protego/)
- SPARQLWrapper 2.0.0, 2022-03-13, W3C licence (stale but functional) — [PyPI](https://pypi.org/project/SPARQLWrapper/)
- pygbif 0.7.0, 2026-10-07, MIT — [PyPI](https://pypi.org/project/pygbif/)
- frictionless 5.20.0, 2026-10-08, MIT — [PyPI](https://pypi.org/project/frictionless/)
- warcio 1.8.1, dvc 3.67.1, jsonschema 4.26.0, pydantic 2.14.0, linkml 1.12.0 — see section 5.

### Inferences
- **Wikidata:** SPARQLWrapper is not required. A plain `httpx.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"})` with a descriptive User-Agent is enough and avoids a stale dependency. The User-Agent requirement comes from the Wikimedia User-Agent policy, which could not be fetched; it is from general knowledge.
- **trafilatura** output is prose. Use it only to show reviewers the source text, never to populate catalog prose (copyright risk, see section 1).
- **CropStack's architecture** argues for a stack small enough to run in CI. Scrapy's crawler machinery is overkill for a few dozen API or bulk sources.

### Gaps
- Maintenance health beyond release dates (open issues, bus factor) was not assessed.
- The MIT licence of the pygbif 0.7.0 release was read from PyPI metadata only.

## 7. How comparable open projects handle this

### Takeaway
Successful open food and plant datasets choose one explicit open data licence, separate from the code licence, and are strict about the input licences they accept. OSM and Open Food Facts use ODbL, Growstuff uses CC BY-SA, and OpenFarm moved toward CC0. PFAF is the counter-example: NC and confusingly stated terms that make it unusable as a redistributable source.

### Cited Findings
- **Open Food Facts:** ODbL for the database, DbCL for contents, CC BY-SA 3.0 for images. It keeps a public "non-compliance shamelist" of reusers who don't comply, and a reuse@ contact. — [OFF docs](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/license-be-on-the-legal-side/)
- **Growstuff:** CC BY-SA 3.0 structured data. It imports CC BY 4.0 government food-composition data. Users keep copyright in their posts and images, and privacy settings are honoured. — [Growstuff API policy](https://www.growstuff.org/policy/api)
- **OpenFarm:** CC BY 4.0, with a move to CC0 decided in principle, to avoid attribution chains for remixed guides. — [Loomio](https://www.loomio.com/d/BRoQnYHX/should-openfarm-s-data-be-cc0-instead-of-cc-by)
- **iNaturalist:** Per-user licence choice, with a CC BY-NC default for photos. Only CC0, BY and BY-NC observations go to GBIF. — [iNaturalist](https://www.inaturalist.org/posts/30692-tech-tip-tuesday-understanding-licensing)
- **PFAF:** CC BY-NC-SA text, CC BY-NC-ND images, and inconsistent statements on the licence page. — [PFAF](https://pfaf.org/User/cmspage.aspx?pageid=136)

### Inferences
- **For GBIF/iNaturalist ingestion:** Filter records by licence at fetch time. Keep CC0 and CC BY, and drop BY-NC if the catalog is CC BY-SA. Pest presence and distribution facts are facts, but the GBIF download terms still ask for citation via a DOI. Record the GBIF download DOI as the source. This is from general knowledge of GBIF practice, not verified this session.
- **PFAF** may be used only as a human reference for fact-checking, never as an ingestion source.
- The OFF "shamelist" pattern shows that a share-alike licence needs community enforcement effort. CC BY-SA has lower overhead for a single-maintainer project.

### Gaps
- The OpenStreetMap and Wikidata licence pages were not fetched this session. Their licences (OSM: ODbL; Wikidata: CC0) are well known but cited from general knowledge.
- Whether OpenFarm actually relicensed to CC0 before shutting down is unconfirmed.
