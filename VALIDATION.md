# Validation

Two independent layers. Full machine output for both is in `validation/`.

## 1. Build-time validator (2026-07-14)

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

The build-time validation round caught and fixed three bugs before release:
CLEA candidate-level rows duplicating party totals (SE/CH/PL/CZ/MT/FR —
31,793 rows deduplicated), Belgium 2024 party names (wrong API field), and
Norway 2025 ("Andre" rollup and blank ballots counted as parties).

## 2. Independent audit (2026-07-26)

`validation/independent_audit.py` → `validation/independent_audit_report.txt`.
Written from scratch against the released files only; shares no code with the
build validator.

| check | result |
|---|---|
| Headline counts (32 countries, 258 events, 254 country-years, 506,163 consolidated rows, 26/208 in nuts3 tables) | match README exactly |
| CSV ↔ parquet agreement (spot: finest_2016, nuts3_2024) | identical shape + vote totals |
| Consolidated `national_all` ↔ 9 slice files | identical row counts + vote totals |
| National party totals invariant across all 12 tables × vintages | max deviation 0.00 votes |
| Duplicate keys, invalid NUTS codes, level mismatches, purity of pure tables | none |
| nuts3 tables = finest restricted to all-NUTS-3 elections | exact (0 missing, 0 extra, 0.00 vote deviation) |
| Vote-weighted party-family coverage | 96.67 % (README: 96.7 %); no country below 92 % |
| 20 fresh external spot checks, deliberately on **different parties** than the build validator (CDU ×2, SPÖ, PD, VVD, KO, S, Venstre, Kokoomus, Ensemble, Conservatives, United-for-Hungary, N-VA, SPOLU, PSD-RO-2020, Sjálfstæðisflokkurinn, …) | 16/20 exact; 4 deviations all explained below |
| GB correctly absent from 2024-vintage files; present in 2016/2021 | pass |

### The four explained deviations

None is a data error; all are representation conventions now documented in
the codebook:

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
