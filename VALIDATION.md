# Validation

Two independent layers. Full machine output for both is in `validation/`.

## 1. Build-time validator

`code/30_validate.py` → `validation/build_validation_report.txt`.

- **Structural:** unique keys (`country_code, year, month, nuts_code, party
  names, partyfacts_id`); all NUTS codes valid for their vintage; `nuts_level`
  consistent with code length; pure tables really pure. PASS.
- **Cross-table agreement:** NUTS-1 regional totals exactly equal the finest
  table aggregated to NUTS-1. PASS (exact).
- **External spot checks:** 33 national party shares vs official results
  (≥1 per country, tolerance 0.3–1.5 pp). 33/33 PASS.
- **Vote logic:** flags a small set of source-inherited anomalies, left as
  delivered and documented in the codebook: party sums > `validvote` in
  7 regions (FR 2022/2024, GR, IT, SE 2022); `validvote` > `totalvote` in
  5 regions (IT 2022 ×2, RO 2004, TR 2015 ×2); 8 sub-25 %-turnout Swiss
  region-years (real — Switzerland has very low turnout in some cantons).
- **Partition stability:** GB 2024 has 12 regions vs the country mode of 41
  (intended — the 2024 source is NUTS-1, earlier GB elections NUTS-2).

The build-time validation round caught three ingestion bugs before release:
CLEA candidate-level rows duplicating party totals (SE/CH/PL/CZ/MT/FR —
31,793 rows deduplicated), Belgium 2024 party names (wrong API field), and
Norway 2025 ("Andre" rollup and blank ballots counted as parties).

## 2. Independent audit

`validation/independent_audit.py` → `validation/independent_audit_report.txt`.
Written from scratch against the released files only; shares no code with the
build validator. Sections 10 and 11 target the party layer specifically.

| check | result |
|---|---|
| Headline counts (32 countries, 258 events, 254 country-years, 506,163 consolidated rows, 26/208 in nuts3 tables) | match README exactly |
| CSV ↔ parquet agreement (spot: finest_2016, nuts3_2024) | identical shape + vote totals |
| Consolidated `national_all` ↔ 9 slice files | identical row counts + vote totals |
| National party totals invariant across all 12 tables × vintages | max deviation 0.00 votes |
| Duplicate keys, invalid NUTS codes, level mismatches, purity of pure tables | none |
| nuts3 tables = finest restricted to all-NUTS-3 elections | exact (0 missing, 0 extra, 0.00 vote deviation) |
| Vote-weighted party-family coverage | 99.13 % (README: 99.1 %); weakest country GB at 97.87 % |
| 20 fresh external spot checks, deliberately on **different parties** than the build validator (CDU ×2, SPÖ, PD, VVD, KO, S, Venstre, Kokoomus, Ensemble, Conservatives, United-for-Hungary, N-VA, SPOLU, PSD-RO-2020, Sjálfstæðisflokkurinn, …) | 20/20 pass |
| GB correctly absent from 2024-vintage files; present in 2016/2021 | pass |
| `party_abbreviation` non-null in all 12 tables; `native`-sourced labels identical to `party_native` | pass |
| strict flags share the inclusive flags' NaN pattern and are a subset of them | pass, with one documented upstream exception (below) |
| 8 party-identity checks on labels known to be ambiguous or collision-prone (BE N-VA/CD&V, BE 2024 far-right share, DK ballot letter A, SI Združena levica, IT Lega, NL SP, DE BSW) | 8/8 pass |

Four of the 20 spot checks use a reference value adjusted to this database's
representation conventions rather than the headline official percentage. The
adjustments are listed below, since the same conventions apply to any
comparison against official national figures.

### Upstream exception

The strict PopuList flags are a subset of the inclusive ones everywhere except
Lithuania's *Tvarka ir teisingumas*, for which PopuList publishes an empty
inclusive eurosceptic window (2100–2100) alongside an open strict one
(1900–2100). 48 rows (LT 2008) therefore carry `eurosceptic = 0` beside
`eurosceptic_strict = 1`. The values are left as PopuList delivers them,
consistent with how this database handles other source-inherited anomalies.
The audit fails if any other such case appears.

### The four adjusted reference values

None is a data error; all are representation conventions documented in the
codebook:

1. **ES 2023, PSOE 22.6 % vs official 31.7 %** — the official 31.7 % includes
   PSOE's separately-listed regional sister parties (PSC-PSOE 4.96 %,
   PSdeG-PSOE 1.96 %, PSE-EE), which are separate rows here as in the
   official source. Summing them reproduces the official figure.
2. **GR 2023, SYRIZA "0 %"** — name stored transliterated
   ("SYNASPISMOS RIZOSPASTIKIS ARISTERAS-PROODEFTIKI SYMMACHIA", 17.74 % vs
   official 17.83 %); the Greek-script regex simply didn't match.
3. **CH 2023, SP 20.1 % vs official 18.3 %** — Swiss rows are **list votes**
   (multi-vote ballots; 38.7 M total votes), not the official
   "Wählerstärke" party-strength statistic; shares can deviate ~2 pp.
4. **PT 2024, PS 29.4 % vs official 28.0 %** — shares here are of domestic
   valid party votes; the official percentage is of all ballots including
   blanks/nulls and the two foreign circles (absent from the source).

## Reproducing the audit

```bash
python validation/independent_audit.py   # edit OUT/XW paths at the top
```
