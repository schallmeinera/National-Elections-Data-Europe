# Codebook

All tables share one schema. `national_all` adds a leading `table` column.

## Unit of observation

One row = one party (or residual rollup) × one NUTS region × one election
event. An election event is identified by `country_code + year + month`
(`month = 0` where the source does not record it — all EU-NED-era rows).
Within one election, the rows of a country form a **complete, non-overlapping
national partition** at the levels indicated by `nuts_level`.

## Columns

| column | type | description |
|---|---|---|
| `table` | str | `national_all` only: `finest` / `nuts2` / `nuts1`. **Always filter `table` and `nuts_vintage` together** — each slice repeats the same votes at a different aggregation. |
| `country` | str | Country name. |
| `country_code` | str | ISO-3166-alpha-2, except `GB` (United Kingdom) and `GR` (Greece) following EU-NED. NUTS codes use `UK`/`EL` prefixes for the same countries. |
| `year` | int | Election year. |
| `month` | int | Election month; **0 = month not recorded** (EU-NED-era rows). Part of the key: BG 2021 has three elections (months 4, 7, 11), GR 2023 two (5, 6). |
| `election_type` | str | Always `parliament` (lower chamber). |
| `nuts_code` | str | NUTS code in the vintage given by `nuts_vintage`. Pseudo-codes ending in `Z` (e.g. `FRZZZ`, `ATZZZ`, `PLZZ`) are **extra-regio** rows: postal/abroad/diaspora votes that cannot be regionalised. They keep national totals consistent; drop them for purely territorial analyses. |
| `nuts_level` | int | 1, 2 or 3 (= `len(nuts_code) − 2`). Mixed within a country-election only in `finest`. |
| `nuts_vintage` | int | 2016, 2021 or 2024 — the NUTS classification the codes refer to. |
| `regionname` | str | Region name. |
| `party_abbreviation` | str | Party identifier, populated on every row. On EU-NED-backbone rows and the AT/SI/GB/LU/NO/DK/IS parsers it is the abbreviation the source supplied. On the remaining extension rows it is the source's own party string copied verbatim from `party_native`, which in the CLEA-sourced countries is a full name (`Rassemblement National`, `NEA DIMOKRATIA`). It is an identifier, not a guaranteed abbreviation. |
| `party_label_source` | str | `source` = the ingester supplied `party_abbreviation`; `native` = it was copied from `party_native` by `code/39_fill_party_labels.py`. 64 / 36 % in `finest_2016`. |
| `party_english` | str | English party name as the sources gave it (47.6 % populated, all EU-NED). Incomplete, and therefore not usable as a key. |
| `party_native` | str | Native-language name as reported by the source (extension rows always have this; Greek CLEA names are transliterated, e.g. SYRIZA = "SYNASPISMOS RIZOSPASTIKIS ARISTERAS…"). Verbatim source text, never modified. For matching, search all three name columns. |
| `partyfacts_id` | float | Partyfacts id as delivered by EU-NED (missing on CLEA rows). |
| `partyfacts_id_matched` | float | Partyfacts id after the classification build's name-matching (81 % of rows). Prefer this over `partyfacts_id`. |
| `pf_name_short`, `pf_name_english` | str | Partyfacts labels joined on `partyfacts_id_matched` with a country guard (81 % of rows). Convenient for cross-country display, but they inherit the id match's errors, so they are exposed separately rather than merged into the name columns. Triage in `crosswalks/party_label_audit.csv`. |
| `partyvote` | float | Votes for the party in the region. |
| `electorate` | float | Registered voters in the region (repeated on each party row; NaN where the source lacks it). |
| `totalvote` | float | Ballots cast in the region (same repetition/NaN convention). |
| `validvote` | float | Valid votes in the region (same convention). Where the source has no separate turnout figures, `validvote` = sum of party votes. |
| `conversion` | str | `native` (reported in this vintage's codes), `exact` (1:1 recode), `weighted` (population/area-weighted split — treat with care for small-area work). |
| `source` | str | Provenance of the row (EU-NED v1.1, CLEA 2025-10, or the specific official national source). |
| `party_family` | str | CHES 11-family taxonomy: Radical right, Conservative, Liberal, Christian democratic, Social democratic, Radical left, Green, Regionalist, Agrarian/center, Confessional/agrarian/other, No family. Missing = unclassified (small local lists; 0.9 % of votes, none reaching 1 % in any single election). |
| `family_source` | str | Where the family came from, in priority order: `ep_panel` > `ess_build` > `ches_link` > `populist_implied` > `manual` / `manual_override` > `generic` / `variant_harmonized`. |
| `populist`, `farright`, `farleft`, `eurosceptic` | float | **Time-aware PopuList dummies evaluated at the election year**, using PopuList's borderline-**inclusive** window (e.g. Fidesz counts as far right from 2010). 1 = flagged, 0 = identified party not flagged, NaN = party not identified. PopuList does not cover Turkey; Turkish flags are family-implied via manual coding. |
| `populist_strict`, `farright_strict`, `farleft_strict`, `eurosceptic_strict` | float | The same flags on PopuList's **strict** window, which excludes parties it marks as borderline. Same NaN pattern as the inclusive flags. 22 party identities differ on `farright`, 37 on `populist`, 16 on `farleft`, 9 on `eurosceptic`. See README § Borderline flags. |

### Pseudo-party rows

Rows whose name is `Others` or `Blanks` are residual rollups inherited from
the sources (EU-NED and CLEA both carry them; e.g. CH 2023 "Others" = 2.7 %).
They keep regional totals consistent — exclude them when computing party
counts, keep them when computing shares of the valid vote.

### Party classification lookup

`crosswalks/party_classification.csv` (2,244 distinct party identities) is the
election-invariant lookup used to stamp the tables. It carries the raw PopuList
windows behind the flags: `{flag}_start` / `{flag}_end` for the inclusive
series and `{flag}_startnobl` / `{flag}_endnobl` for the strict one, with 1900
meaning "from the beginning" and 2100 meaning "ongoing" or, when both ends are
2100, "never".

Manual conventions worth knowing: coalitions get the dominant partner's family
(SPOLU → Conservative, NUPES/UG → Radical left, GL-PvdA → Social democratic,
Trzecia Droga → Agrarian/center); NO/CH/IS/CY/TR mainstream parties are
hand-coded (outside CHES coverage); PT PSD is coded Liberal.

The PopuList join is **country-guarded**: a Partyfacts id that would link a
party to a PopuList entry in a different country is dropped with a warning
rather than applied. Partyfacts ids are also pinned by hand where a source
label is ambiguous, chiefly for coalition and cartel lists whose name is
shared with a constituent party, and for the Danish ballot-letter codes,
whose single letters collide with other parties' abbreviations.

## Sources, per country (post-2020 extensions)

| Country | Election(s) | Source & mapping |
|---|---|---|
| AT | 2024 | Gemeinde-level results aggregated Gemeinde→NUTS-3 via the Eurostat LAU-2024 correspondence. Covers ~97 % of the official vote (some postal-card votes only exist at district/Land level); national shares deviate ≤ 0.2 pp from official. |
| BE | 2024 | IBZ `api.electionresults.belgium.be`; 11 constituencies = provinces/Brussels = NUTS-2. |
| BG | 2021×3–2023 | CLEA (MIR constituencies = NUTS-3). |
| BG | 2024 Jun + Oct | CIK machine-readable section-level export; section code prefix = MIR/oblast = NUTS-3; Sofia MIRs 23/24/25 → BG411; abroad → BGZZZ. |
| CH | 2023 | CLEA; cantons = NUTS-3. **Votes are list votes** (each voter casts as many votes as the canton has seats), so national shares deviate up to ~2 pp from the official "Wählerstärke" statistic. |
| CZ | 2021 / 2025 | CLEA / volby.cz results XML; kraje = NUTS-3. |
| DE | 2021 / 2025 | Kreis-harmonised Zweitstimmen (400 Kreise → NUTS-3 via LAU) in the finest/nuts3 tables. 2025 matches the official kerg2 result; 2021 is the original result (pre-2024 Berlin partial repeat), 0.3 % below the post-repeat total. |
| DK | 2022 | DST valg XML; 92 opstillingskredse → landsdele (NUTS-3), Sjælland kredse assigned by municipality. |
| EE | 2023 | valimised.ee county XML; district-minus-county residual (foreign votes) → EEZZZ. |
| ES | 2023 | CLEA; provinces = NUTS-3. PSOE's regional sister lists (PSC-PSOE, PSdeG-PSOE, PSE-EE) are separate rows, as in the official result. |
| FI | 2023 | Statistics Finland PxWeb (party × municipality). |
| FR | 2022 / 2024 | CLEA, **first-round** votes (SMD system; round 1 best reflects party support). |
| GB | 2024 | House of Commons Library CBP-10009; ONS regions → NUTS-1. Absent from `*_2024` files (UK not in NUTS-2024). |
| GR | 2023×2 | CLEA; nomoi = NUTS-3 + Attica at NUTS-2. |
| HU | 2022 | CLEA; party-**list** votes summed over SMDs + `HUZZZ` diaspora residual. |
| IS | 2021 / 2024 | Statistics Iceland PxWeb; constituencies → IS001/IS002. Iceland is not in EU-NED — new to this database. |
| IT | 2022 | Eligendo comune-level (proportional list votes); Aosta Valley appended; Estero → ITZZZ. |
| LT | 2024 | VRK open data; the proportional tier is one national constituency, so per-polling-district points are spatially joined to NUTS-3 2016 boundaries. Domestic votes only (~1.22 M). |
| LU | 2023 | data.public.lu. **Suffrages convention** (EU-NED-consistent): `partyvote` and `validvote` are panachage votes (~29 per ballot), `totalvote` is ballots. |
| LV | 2022 | CVK via data.gov.lv; municipality-level nodes mapped to NUTS-3 via the Eurostat LAU-2021 table (the 5 electoral regions do not match NUTS-3); abroad → LVZZZ. |
| NL | 1994–2025 | Kiesraad gemeente-level results, gemeente → COROP (= NUTS-3) per election year via CBS. Replaces EU-NED's NUTS-2 Netherlands series entirely. Postal bureaus → NLZZZ. |
| NO | 2021 / 2025 | CLEA / valgresultat.no API; 19 pre-2020 fylke districts. |
| PL | 2023 | CLEA; okręgi → NUTS-2 (Poland is NUTS-2-based from 2001 onward, as in EU-NED). |
| PT | 2022–2025 | MAI freguesia data, concelho → NUTS-3. The two foreign circles are missing (~2–5 % of the vote). |
| RO | 2020 / 2024 | AEP prezenta.roaep.ro JSON (Chamber); counties + Bucharest = NUTS-3, diaspora → ROZZZ. |
| SE | 2022 | CLEA; constituencies → NUTS-3. |
| SI | 2022 | DVK archive JSON; single national row (SI is one NUTS unit at level 1 here). |
| SK | 2023 | SUSR open data; kraje = NUTS-3; foreign votes → SKZZZ. |

## Caveats

- **Regional totals** (`electorate`/`totalvote`) are NaN for several
  extensions that publish party votes only: RO, NL 2021, EE, PT, IS, FI 2023,
  BG 2024, LT 2024, IT (VdA/Estero rows), and CLEA Bulgaria waves.
- A handful of source-inherited vote-logic anomalies exist and are left as
  delivered (documented in `validation/build_validation_report.txt`):
  party sums slightly exceed `validvote` in 7 regions (FR/GR/IT/SE);
  `validvote` > `totalvote` in 5 regions (IT 2022 ITC33/ITG19, RO 2004 RO321,
  TR 2015 TR100/TR211); a few Swiss low-turnout region-years.
- Bulgaria CLEA 2022/2023 constituency names were garbled at source and
  repaired (`NOISY`→Vidin, `SEEN`→Shumen, inferred alphabetically).
- GB 2024 is NUTS-1 (12 regions) while earlier GB elections are NUTS-2
  (41 regions) — the `finest` partition changes size there.
- Hungary 2022 list-vote convention and the `HUZZZ` residual mean SMD-level
  candidate votes are not represented.
- `weighted` conversion rows (≈ 4–5 % of rows in the 2021/2024 vintages)
  split votes by population or area shares; avoid relying on them alone for
  small-area estimates. The LV007 Pierīga split into the 2024 regions is
  area-based and approximate.
- Legacy pre-2016 codes inside EU-NED were fixed at build time
  (NO061+NO062→NO060; Spanish island provinces ES530/ES701/ES702 split into
  island NUTS-3 by 2001 population, flagged `weighted`).
- **One upstream PopuList inconsistency is left as delivered.** The strict
  flags are otherwise a subset of the inclusive ones, but PopuList gives
  Lithuania's *Tvarka ir teisingumas* an empty inclusive eurosceptic window
  (2100–2100, i.e. never) alongside an open strict one (1900–2100, i.e.
  always). Consequently 48 rows (LT 2008) carry `eurosceptic = 0` beside
  `eurosceptic_strict = 1`. The independent audit asserts this is the only
  such case in the database.
- Where CHES and PopuList disagree about a party (HU Fidesz, BG ABC), the
  database reports both: CHES drives `party_family`, PopuList drives the flags.
- CLEA-sourced rows still have no `partyfacts_id` from the source; their ids
  come from the classification build's name matching (`partyfacts_id_matched`).
