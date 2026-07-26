# Independent audit of the national elections NUTS panel (run 2026-07-26).
# Written from scratch against the released files; shares no code with the
# build-time validator (code/30_validate.py). Run from anywhere:
#   python validation/independent_audit.py
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
XW = os.path.join(HERE, "..", "crosswalks")
KEY = ["country_code", "year", "month"]
report = []
def log(s=""):
    print(s); report.append(str(s))

tables = {}
for t in ("finest", "nuts2", "nuts1", "nuts3"):
    for v in (2016, 2021, 2024):
        tables[(t, v)] = pd.read_parquet(os.path.join(OUT, f"national_{t}_{v}.parquet"))
allf = pd.read_parquet(os.path.join(OUT, "national_all.parquet"))

log("=== 1. HEADLINE COUNTS vs README claims ===")
f16 = tables[("finest", 2016)]
elec = f16[KEY].drop_duplicates()
cy = f16[["country_code", "year"]].drop_duplicates()
log(f"finest_2016: {len(f16):,} rows, {f16.country_code.nunique()} countries, "
    f"{len(elec)} election events, {len(cy)} country-years, "
    f"years {f16.year.min()}-{f16.year.max()}")
log(f"national_all rows: {len(allf):,} (README claims 506,163)")
log(f"national_all election events: {len(allf[allf.table=='finest'][KEY].drop_duplicates())}")
n3 = tables[("nuts3", 2016)]
log(f"nuts3_2016: {n3.country_code.nunique()} countries, "
    f"{len(n3[KEY].drop_duplicates())} elections (README claims 26 / 208)")

log("\n=== 2. CSV/PARQUET AGREEMENT (spot: finest_2016, nuts3_2024) ===")
for t, v in [("finest", 2016), ("nuts3", 2024)]:
    c = pd.read_csv(os.path.join(OUT, f"national_{t}_{v}.csv.gz"))
    p = tables[(t, v)]
    log(f"{t}_{v}: shape match={c.shape == p.shape}, "
        f"partyvote total match={abs(c.partyvote.sum() - p.partyvote.sum()) < 0.5}")

log("\n=== 3. CONSOLIDATED FILE vs SLICE FILES ===")
ok = True
for t in ("finest", "nuts2", "nuts1"):
    for v in (2016, 2021, 2024):
        s = allf[(allf.table == t) & (allf.nuts_vintage == v)]
        p = tables[(t, v)]
        if len(s) != len(p) or abs(s.partyvote.sum() - p.partyvote.sum()) > 0.5:
            ok = False
            log(f"MISMATCH {t}_{v}: all={len(s)}/{s.partyvote.sum():.0f} "
                f"slice={len(p)}/{p.partyvote.sum():.0f}")
log("consolidated == slices: " + ("PASS" if ok else "FAIL"))

log("\n=== 4. NATIONAL TOTAL INVARIANCE across all 12 tables ===")
base = tables[("finest", 2016)].groupby(KEY).partyvote.sum()
worst = 0.0
for k, df in tables.items():
    s = df.groupby(KEY).partyvote.sum()
    j = pd.concat([base.rename("b"), s.rename("s")], axis=1, join="inner")
    worst = max(worst, (j.b - j.s).abs().max())
log(f"worst national-total deviation across tables: {worst:.2f} votes "
    + ("PASS" if worst <= 0.51 else "FAIL"))

log("\n=== 5. KEYS, NUTS VALIDITY, PARTITION INTEGRITY ===")
codes = {v: set(pd.read_csv(os.path.join(XW, f"nuts_codes_{v}.csv")).code)
         for v in (2016, 2021, 2024)}
probs = 0
for (t, v), df in tables.items():
    dup = df.duplicated(subset=KEY + ["nuts_code", "party_abbreviation",
                                      "party_english", "party_native",
                                      "partyfacts_id"]).sum()
    bad = {c for c in set(df.nuts_code) - codes[v] if not c.endswith("Z")}
    lvl = (df.nuts_level != df.nuts_code.str.len() - 2).sum()
    if t == "nuts3" and (df.nuts_level != 3).any():
        probs += 1; log(f"{t}_{v}: non-NUTS3 rows in pure table")
    if dup or bad or lvl:
        probs += 1
        log(f"{t}_{v}: dup={dup} badcodes={sorted(bad)[:6]} lvlmismatch={lvl}")
log("key/code/level checks: " + ("PASS" if probs == 0 else f"{probs} problems"))

log("\n=== 6. nuts3 TABLE == finest RESTRICTED (2016) ===")
f16nz = f16[~f16.nuts_code.str.endswith("Z")]
lvlok = f16nz.groupby(KEY).nuts_level.agg(lambda s: set(s) == {3})
elig = set(lvlok[lvlok].index)
have = set(map(tuple, n3[KEY].drop_duplicates().values))
log(f"eligible all-NUTS3 elections in finest: {len(elig)}; in nuts3 table: {len(have)}")
log(f"eligible-but-missing: {sorted(elig - have)[:8]}")
log(f"in-table-but-not-eligible: {sorted(have - elig)[:8]}")
sub = f16[f16[KEY].apply(tuple, axis=1).isin(have)]
d = (sub.groupby(KEY).partyvote.sum() - n3.groupby(KEY).partyvote.sum()).abs().max()
log(f"vote-total match finest-restricted vs nuts3: max dev {d:.2f}")

log("\n=== 7. PARTY CLASSIFICATION COVERAGE ===")
cl = f16[f16.party_family.notna() & (f16.party_family != "")]
log(f"vote-weighted family coverage: {cl.partyvote.sum() / f16.partyvote.sum() * 100:.2f}% "
    f"(README claims 96.7%)")
bycc = (f16.assign(c=f16.party_family.notna() & (f16.party_family != ""))
        .groupby("country_code")
        .apply(lambda g: g.loc[g.c, "partyvote"].sum() / g.partyvote.sum() * 100,
               include_groups=False))
low = bycc[bycc < 92]
log(f"countries below 92% coverage: {dict(low.round(1)) if len(low) else 'none'}")

log("\n=== 8. FRESH EXTERNAL SPOT CHECKS (parties NOT in 30_validate.py) ===")
# (cc, year, month|None, regex over 3 name cols, official %, tol pp)
# Values marked * are adjusted to the dataset's representation convention
# (see VALIDATION.md): ES sums PSOE + regional sister lists; PT is the
# domestic valid-vote share; CH is the list-vote share.
CHECKS = [
    ("DE", 2025, None, r"^CDU$|Christlich Demokratische Union", 22.6, 0.5),
    ("DE", 2021, None, r"^CDU$|Christlich Demokratische Union", 18.9, 0.5),
    ("AT", 2024, None, r"^SPÖ$|Sozialdemokratische Partei Österreichs", 21.1, 0.5),
    ("ES", 2023, None, r"SOCIALIST", 31.7, 0.9),
    ("IT", 2022, None, r"PARTITO DEMOCRATICO", 19.1, 0.7),
    ("NL", 2023, None, r"^VVD$", 15.2, 0.5),
    ("PL", 2023, None, r"Koalicja Obywatelska|KOALICYJNY.*OBYWATELSK", 30.7, 0.7),
    ("SE", 2022, None, r"Arbetarepartiet-Socialdemokraterna|^S$", 30.3, 0.7),
    ("DK", 2022, None, r"V\. Venstre", 13.3, 0.5),
    ("FI", 2023, None, r"Kansallinen Kokoomus|^KOK", 20.8, 0.5),
    ("PT", 2024, 3, r"^PS$|Partido Socialista", 29.4, 1.0),   # *
    ("FR", 2024, 6, r"^Ensemble", 20.0, 1.5),
    ("GB", 2024, 7, r"Conservative", 23.7, 0.5),
    ("HU", 2022, None, r"Egységben Magyarországért|United for Hungary", 34.5, 1.5),
    ("BE", 2024, None, r"^N-VA$", 16.7, 0.7),
    ("CH", 2023, None, r"Sozialdemokratische Partei", 20.1, 1.0),   # *
    ("GR", 2023, 6, r"SYNASPISMOS RIZOSPASTIKIS", 17.8, 1.0),
    ("CZ", 2021, None, r"SPOLU|Občanská demokratická", 27.8, 1.0),
    ("RO", 2020, None, r"^PARTIDUL SOCIAL DEMOCRAT$|^PSD$", 28.9, 1.0),
    ("IS", 2021, None, r"Sjálfstæðisflokkur", 24.4, 0.7),
]
fails = 0
for cc, yr, mo, pat, official, tol in CHECKS:
    sub = f16[(f16.country_code == cc) & (f16.year == yr)]
    if mo is not None:
        sub = sub[sub.month == mo]
    if not len(sub):
        log(f"  *** {cc} {yr}: NOT FOUND"); fails += 1; continue
    m = (sub[["party_native", "party_english", "party_abbreviation"]]
         .astype(str)
         .apply(lambda r: r.str.contains(pat, case=False, regex=True))
         .any(axis=1))
    share = sub.loc[m, "partyvote"].sum() / sub.partyvote.sum() * 100
    ok = abs(share - official) <= tol
    fails += (not ok)
    log(f"  {'OK ' if ok else '***'} {cc} {yr}{'-' + str(mo) if mo else ''}: "
        f"{share:5.2f}% vs {official}% (tol {tol}) [{pat[:35]}]")
log(f"fresh spot checks: {len(CHECKS) - fails}/{len(CHECKS)} pass")

log("\n=== 9. VINTAGE CONVERSION SANITY ===")
for v in (2021, 2024):
    log(f"finest_{v} conversion mix: "
        f"{tables[('finest', v)].conversion.value_counts(normalize=True).round(3).to_dict()}")
g24 = tables[("finest", 2024)]
log(f"GB in 2024 vintage (should be absent): {(g24.country_code == 'GB').sum()} rows")
log(f"GB in 2016 vintage: {(f16.country_code == 'GB').sum()} rows")

with open(os.path.join(HERE, "independent_audit_report.txt"), "w", encoding="utf8") as fh:
    fh.write("\n".join(report))
print("\nreport written to validation/independent_audit_report.txt")
