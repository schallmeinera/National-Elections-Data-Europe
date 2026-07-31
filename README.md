# European National Elections at NUTS Level, 1983–2025

Party-level results of **national parliamentary (lower-chamber) elections** for
**32 European countries, 254 elections (258 election events), 1983–2025**,
harmonised to **NUTS territorial units** in three NUTS vintages (2016, 2021,
2024) and provided at several levels of aggregation (finest available,
pure NUTS-3, pure NUTS-2, pure NUTS-1).

Every row carries a party-family classification (CHES 11-family taxonomy),
time-aware PopuList dummies (`populist`, `farright`, `farleft`, `eurosceptic`)
in both a borderline-inclusive and a strict variant, and a Partyfacts id where
recoverable. 99.1 % of all votes are family-classified, with no country below
97.9 %.

Two conventions govern the party columns:

- `party_abbreviation` is populated on every row and is the party identifier.
  Outside the EU-NED backbone it holds the source's own party string, which is
  a full name in the CLEA-sourced countries (`Rassemblement National`) and an
  abbreviation elsewhere (`AfD`). `party_label_source` records which.
- The PopuList flags come in two variants. `farright` follows PopuList's
  borderline-inclusive window, `farright_strict` its strict one, and the two
  can differ substantially: Norway 2021 is 12.7 % far right inclusive and
  1.1 % strict. See § Borderline flags below.

The database extends **EU-NED v1.1** (Schraff, Vergioglou & Demirci 2022),
which ends in 2020, with 25 post-2020 elections parsed from official
national sources, plus finer-grained replacements for Germany (Kreis level)
and the Netherlands (municipality → COROP for the full 1994–2025 series),
and adds Iceland (absent from EU-NED).

## Quick start

```python
import pandas as pd

# one slice: finest partition, NUTS-2016 codes
df = pd.read_parquet("data/national_finest_2016.parquet")

# or the consolidated file — filter BOTH `table` and `nuts_vintage` first,
# otherwise you will double-count (each slice repeats the same votes)
allf = pd.read_parquet("data/national_all.parquet")
df = allf[(allf.table == "finest") & (allf.nuts_vintage == 2016)]

# far-right vote share by NUTS region, 2020s
d = df[df.year >= 2020]
fr = (d.assign(fr=d.partyvote * (d.farright == 1))
        .groupby(["country_code", "year", "month", "nuts_code"])
        .agg(fr=("fr", "sum"), total=("partyvote", "sum")))
fr["share"] = fr.fr / fr.total
```

```r
library(arrow); library(dplyr)
df <- read_parquet("data/national_finest_2016.parquet")
```

CSV users: every table is also shipped as `.csv.gz` with identical content.

## Files (`data/`)

| file | content |
|---|---|
| `national_finest_{2016,2021,2024}` | Finest available partition per election. Mixed NUTS levels within a country are possible; `nuts_level` flags each row (e.g. Greece = nomoi at level 3 + Attica at level 2; Slovenia = one national unit; Germany 2021/2025 also available at Kreis/NUTS-3). Each country-election is a **complete national partition** — rows never overlap. |
| `national_nuts3_{vintage}` | Subset of `finest` restricted to country-elections whose partition is entirely NUTS-3. Countries/elections with a coarser base (SI, GB, IE, PL, BE, parts of GR/NL history) are absent — 26 countries, 208 elections per vintage. |
| `national_nuts2_{vintage}` | Pure NUTS-2 partition. Countries coarser than NUTS-2 (SI always; DE 2021/2025 base) absent. |
| `national_nuts1_{vintage}` | Pure NUTS-1 partition, complete for all countries/elections. |
| `national_all` | All finest/nuts2/nuts1 slices stacked (506,163 rows), identified by leading `table` + `nuts_vintage` columns. The pure-NUTS-3 tables are *not* in this file. |
| `coverage_by_country.csv` | Per-country summary: years covered, number of elections, base NUTS levels, sources. |

Each table exists as `.parquet` and `.csv.gz` (identical content).
Column definitions: see [CODEBOOK.md](CODEBOOK.md).

**The United Kingdom does not exist in the NUTS-2024 classification**, so GB
elections are absent from all `*_2024` files (intended, not a gap).

## Borderline flags: `farright` vs `farright_strict`

PopuList publishes each of its four flags twice: a borderline-**inclusive**
window and a **strict** window that excludes parties it marks as borderline
cases. 19 of PopuList's 133 far-right parties qualify only as borderline,
among them NO FrP, NL BBB, BE N-VA, LU ADR, FR LR, HR HDSSB, CY Solidarity
and BG BSP. Both series are shipped: `farright` is the inclusive one,
`farright_strict` the strict one, likewise for `populist`, `farleft` and
`eurosceptic`.

The two variants diverge widely in some country-elections: Norway 2021 is
12.7 % far right on the inclusive flag and 1.1 % on the strict one, Belgium
2024 is 30.5 % against 13.8 %, and Poland 2005 is 36.5 % against 9.5 %.
Hand-coded radical-right and radical-left families carry identical inclusive
and strict windows, since a hand assignment has no borderline qualifier.

The borderline cases also account for most rows where `farright = 1` sits
beside a `party_family` other than "Radical right". The remaining such rows
reflect disagreement between the two upstream sources, chiefly HU Fidesz,
which CHES places as Conservative and PopuList codes far right from 2010.

## Coverage

AT, BE, BG, CH, CY, CZ, DE, DK, EE, ES, FI, FR, GB, GR, HR, HU, IE, IS, IT,
LT, LU, LV, MT, NL, NO, PL, PT, RO, SE, SI, SK, TR.

Post-2020 elections included for: AT 2024, BE 2024, BG 2021×3/2022/2023/2024×2,
CH 2023, CZ 2021/2025, DE 2021/2025, DK 2022, EE 2023, ES 2023, FI 2023,
FR 2022/2024, GB 2024, GR 2023×2, HU 2022, IS 2021/2024, IT 2022, LT 2024,
LU 2023, LV 2022, MT 2022, NL 2021/2023/2025, NO 2021/2025, PL 2023,
PT 2022/2024/2025, RO 2020/2024, SE 2022, SI 2022, SK 2023.

**Known gaps:** HR 2024 (results app not machine-accessible; non-admin
constituencies), IE 2024 (STV constituencies don't nest into NUTS-3),
TR 2023. CY 2023-? none pending.

## Sources

1. **EU-NED v1.1** (Schraff, Vergioglou & Demirci 2022, *Party Politics*;
   doi:10.7910/DVN/IQRYP5) — backbone for elections up to 2020, NUTS-2016
   codes.
2. **CLEA lower chamber, release 2025-10-15** (Kollman et al.) — post-2020
   elections whose constituencies nest exactly into NUTS units: BG (2021×3,
   2022, 2023), CH 2023, CZ 2021, ES 2023, FR 2022 + 2024 (first round),
   GR 2023×2, HU 2022, MT 2022, NO 2021, PL 2023, SE 2022.
3. **Official national sources** for the rest, each validated against
   official national totals — Bundeswahlleiterin (DE), BMI/Gemeinde data
   (AT), AEP (RO), House of Commons Library (GB), SUSR (SK), volby.cz (CZ),
   Kiesraad (NL), IBZ (BE), Eligendo (IT), MAI (PT), Statistics Finland,
   valimised.ee (EE), DST (DK), Statistics Iceland, valgresultat.no (NO),
   CIK (BG), CVK (LV), VRK (LT), data.public.lu (LU), moi.gov.cy (CY),
   DVK (SI). Full per-country detail: [CODEBOOK.md](CODEBOOK.md) § Sources.
4. **Classification sources:** CHES, PopuList, Partyfacts, plus manual coding
   (263 family entries and 13 identity or link overrides). Lookup table:
   `crosswalks/party_classification.csv` (2,244 party identities, of which
   1,021 remain unclassified, together 0.9 % of all votes and all below 1 % in
   every election they contest); provenance per row in `family_source`.
   `crosswalks/party_label_audit.csv` lists the 1,199 Partyfacts name links
   with a `resembles_source` triage flag for the 107 that do not obviously
   match their source string.

## NUTS vintage conversion (`crosswalks/`)

`nuts{1,2,3}_{2016_2021, 2016_2024, 2021_2024}.csv` give
`from_code, to_code, weight, method` used to convert between vintages:

- 2016→2021 from the JRC conversion matrices (population-weighted), with
  Northern-Ireland recodes added manually.
- 2021→2024 from the Eurostat correspondence workbook; true splits
  (PT170→PT1A0+PT1B0; NO074/NO082/NO091 reverting to pre-2020 units)
  population-weighted; the LV007 Pierīga redistribution uses boundary-overlay
  **area** shares (approximate).
- 2016→2024 composed from the two; NUTS-2/-1 versions derived from the
  NUTS-3 one by population aggregation.

`nuts_codes_{vintage}.csv` are the definitive code lists per vintage
(from GISCO boundary files). Rows converted between vintages are flagged in
the `conversion` column (`native` / `exact` / `weighted` — treat `weighted`
splits with care in small-area analyses).

## Validation

Two independent validation layers, both shipped in [`validation/`](validation/):

1. **Build-time validator** (`code/30_validate.py` →
   `build_validation_report.txt`): unique keys; valid NUTS codes per vintage;
   national party totals invariant across all tables and vintages; NUTS-1
   regional totals exactly equal the finest table aggregated; vote-logic
   checks; **33 external spot checks** of national party shares against
   official results (≥1 per country) — all pass within tolerance.
2. **Independent audit** (`independent_audit.py` →
   `independent_audit_report.txt`): re-derives headline counts, cross-file
   agreement (parquet vs CSV, consolidated vs slices, nuts3 vs finest),
   partition integrity, classification coverage, party-label integrity,
   well-formedness of the strict flags, and **20 external spot checks on
   different parties** than the build validator. All pass; the adjusted
   reference values are documented representation conventions
   (see [VALIDATION.md](VALIDATION.md)).

Known data caveats (regional-total quirks inherited from sources, Swiss
list-vote convention, Luxembourg suffrages, Portugal's missing foreign
circles, etc.) are catalogued in [CODEBOOK.md](CODEBOOK.md) § Caveats and
[VALIDATION.md](VALIDATION.md).

## Reproducibility (`code/`)

The full build pipeline is included for provenance. It is **not runnable from
this repository alone** — the raw inputs (EU-NED, CLEA, and ~500 MB of
official national files) are not redistributed here; the scripts document
exactly how every number was produced and where each raw file comes from.
Run order: `04_build_crosswalks.py` → `06_export_clea.R` → `07_map_clea.py` →
`08_parse_de.py` → `09_parse_at.py` → per-country fetch/parse scripts 11–29,
35–37 → `05_build_backbone.py` → `31_build_party_classification.py` →
`32_apply_classification.py` → `39_fill_party_labels.py` → `38_build_nuts3.py`
→ `10_coverage.py` → `33_consolidate.py` → `30_validate.py`.

Ordering constraint: `39` runs after `32`, because the classification merges on
the four name columns and stops matching the extension rows once their labels
are filled, and before `38` and `33`, which copy the finest tables forward. It
is idempotent, re-reading its own `party_label_source` column to identify the
rows it filled, and it writes no column other than `party_abbreviation`,
`party_label_source`, `pf_name_short` and `pf_name_english`.

Classification (`31`, `32`, `39`) runs on the finished territorial panel, so no
classification step alters vote counts, regional boundaries or table structure.

## Citation

If you use this database, cite it together with its two main upstream
sources (see [CITATION.cff](CITATION.cff)):

- Schraff, D., Vergioglou, I., & Demirci, B. B. (2022). The European NUTS-level
  election dataset: A tool to map European electoral geography.
  *Party Politics*. https://doi.org/10.7910/DVN/IQRYP5
- Kollman, K., Hicken, A., Caramani, D., Backer, D., & Lublin, D. (2025).
  Constituency-Level Elections Archive (release 2025-10-15). Ann Arbor, MI:
  Center for Political Studies, University of Michigan.
- Rooduijn, M., Pirro, A. L. P., Halikiopoulou, D., Froio, C., van Kessel, S.,
  de Lange, S. L., Mudde, C., & Taggart, P. (2024). The PopuList: A database
  of populist, far-left, and far-right parties using expert-informed
  qualitative comparative classification (EiQCC). *British Journal of
  Political Science*, 54(3), 969–978. (For the populist / far-right /
  far-left / eurosceptic flags and their `_strict` counterparts.)

  The flags are built from **The PopuList 4.0** (released May 2026),
  https://popu-list.org, whose own recommended dataset citation still names
  version 3.0 (2023).

## Licence

See [LICENSE.md](LICENSE.md): code MIT; compiled dataset CC BY 4.0, subject
to the attribution requirements of the upstream sources listed there.
