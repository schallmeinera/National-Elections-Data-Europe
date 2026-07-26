"""Deep validation of the election database.

A. Structural: unique keys, valid NUTS codes per vintage, level consistency.
B. Vote logic: partyvote>=0, party sums vs validvote, validvote<=totalvote<=
   electorate (where present), turnout plausibility.
C. Partition stability: region count per country-election vs country mode.
D. Cross-table agreement: nuts1 regional totals == finest aggregated to NUTS1.
E. External spot checks: national party shares vs official reference values.

Writes output/validation_report.txt and prints a summary.
"""
import io
import sys
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
OUT = BASE + r"\output"
XW = BASE + r"\crosswalks"

rep = io.StringIO()
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    rep.write(s + "\n")

issues = 0
def flag(cond, msg, detail=None):
    global issues
    if cond:
        issues += 1
        log("ISSUE:", msg)
        if detail is not None:
            log(detail if isinstance(detail, str) else detail.to_string())

codes = {v: set(pd.read_csv(rf"{XW}\nuts_codes_{v}.csv").code)
         for v in (2016, 2021, 2024)}

KEY = ["country_code", "year", "month"]
tables = {}
for t in ("finest", "nuts2", "nuts1"):
    for v in (2016, 2021, 2024):
        tables[(t, v)] = pd.read_parquet(rf"{OUT}\national_{t}_{v}.parquet")

# ---------------- A. structural ----------------
log("=" * 70)
log("A. STRUCTURAL")
for (t, v), df in tables.items():
    dup = df.duplicated(subset=KEY + ["nuts_code", "party_abbreviation",
                                      "party_english", "party_native",
                                      "partyfacts_id"]).sum()
    flag(dup > 0, f"{t}_{v}: {dup} duplicate party rows")
    badc = set(df.nuts_code) - codes[v]
    badc = {c for c in badc if not c.endswith("Z")}
    flag(bool(badc), f"{t}_{v}: invalid NUTS codes {sorted(badc)[:8]}")
    # level column matches code length
    lvl_bad = (df.nuts_level != df.nuts_code.str.len() - 2).sum()
    flag(lvl_bad > 0, f"{t}_{v}: {lvl_bad} rows with nuts_level != code length")
    # pure-level tables really are pure
    if t in ("nuts2", "nuts1"):
        want = 2 if t == "nuts2" else 1
        flag((df.nuts_level != want).any(), f"{t}_{v}: mixed levels in pure table")
log("structural checks done")

# ---------------- B. vote logic ----------------
log("=" * 70)
log("B. VOTE LOGIC")
f16 = tables[("finest", 2016)]
flag((f16.partyvote < 0).any(), "negative partyvote")
reg = (f16.groupby(KEY + ["nuts_code"], dropna=False)
       .agg(psum=("partyvote", "sum"), valid=("validvote", "first"),
            total=("totalvote", "first"), elig=("electorate", "first"))
       .reset_index())
has_v = reg.dropna(subset=["valid"])
r = has_v.psum / has_v.valid
over = has_v[r > 1.001]
# Luxembourg suffrages: psum == valid by construction; general tolerance
flag(len(over) > 0,
     f"party sums exceed validvote in {len(over)} regions "
     f"({over.country_code.value_counts().to_dict()})",
     over.nlargest(5, "psum")[KEY + ["nuts_code", "psum", "valid"]])
low = has_v[r < 0.85]
log(f"regions where party sum < 85% of validvote: {len(low)} "
    f"({low.country_code.value_counts().to_dict() if len(low) else ''})")
tv = reg.dropna(subset=["valid", "total"])
tv = tv[~tv.country_code.eq("LU")]  # LU: valid in suffrages > total ballots
flag((tv.valid > tv.total * 1.001).any(), "validvote > totalvote",
     tv[tv.valid > tv.total * 1.001].head()[KEY + ["nuts_code", "valid", "total"]])
te = reg.dropna(subset=["total", "elig"])
bad_t = te[te.total > te.elig * 1.02]
flag(len(bad_t) > 0, f"turnout > 102% in {len(bad_t)} regions",
     bad_t.head()[KEY + ["nuts_code", "total", "elig"]])
lo_t = te[(te.total / te.elig < 0.25) & ~te.nuts_code.str.endswith("Z")]
log(f"turnout < 25% (non-extra-regio): {len(lo_t)}"
    + ("" if not len(lo_t) else " -> " + str(lo_t[KEY + ['nuts_code']].values[:5])))

# ---------------- C. partition stability ----------------
log("=" * 70)
log("C. PARTITION STABILITY (regions per election vs country mode, finest 2016)")
rc = (f16[~f16.nuts_code.str.endswith("Z")]
      .groupby(KEY).nuts_code.nunique().rename("n").reset_index())
for cc, g in rc.groupby("country_code"):
    mode = g.n.mode()[0]
    odd = g[(g.n - mode).abs() > max(2, mode * 0.1)]
    if len(odd):
        log(f"  {cc}: mode {mode} regions; deviating elections:",
            odd[["year", "month", "n"]].to_dict("records"))

# ---------------- D. cross-table agreement ----------------
log("=" * 70)
log("D. CROSS-TABLE AGREEMENT (finest->NUTS1 vs nuts1 table, 2016 vintage)")
f = f16.copy()
f["n1"] = f.nuts_code.str[:3]
a = f.groupby(KEY + ["n1"]).partyvote.sum()
b = tables[("nuts1", 2016)].groupby(KEY + ["nuts_code"]).partyvote.sum()
b.index = b.index.set_names(["country_code", "year", "month", "n1"])
cmpd = pd.concat([a.rename("from_finest"), b.rename("nuts1_table")], axis=1)
mism = cmpd[(cmpd.from_finest - cmpd.nuts1_table).abs() > 0.5]
flag(len(mism) > 0, f"{len(mism)} NUTS1 regional totals disagree",
     mism.head(10))
log("regional cross-check done" + ("" if len(mism) else " — exact agreement"))

# ---------------- E. external spot checks ----------------
log("=" * 70)
log("E. EXTERNAL SPOT CHECKS (national shares vs official reference)")
# (country, year, month-or-None, party-substring-regex, official share %, tol pp)
CHECKS = [
    ("DE", 2021, None, r"^SPD|Sozialdemokratische Partei Deutschlands$", 25.7, 0.5),
    ("DE", 2025, None, r"^AfD|Alternative für Deutschland$", 20.8, 0.3),
    ("ES", 2023, None, r"PARTIDO POPULAR|^PP$", 33.1, 0.7),
    ("FR", 2022, 6, r"Rassemblement National", 18.7, 0.7),
    ("IT", 2022, None, r"FRATELLI D'ITALIA", 26.0, 0.5),
    ("NL", 2023, None, r"PVV", 23.5, 0.5),
    ("NL", 2025, None, r"Democraten 66|D66", 16.9, 0.5),
    ("SE", 2022, None, r"Sverigedemokraterna", 20.5, 0.5),
    ("PL", 2023, None, r"Prawo i Sprawiedliwo", 35.4, 0.7),
    ("AT", 2024, None, r"^FPÖ$", 28.8, 0.5),
    ("PT", 2024, 3, r"^CH$|^CHEGA$", 18.1, 1.0),
    ("FI", 2023, None, r"^PS$|Perussuomalaiset", 20.1, 0.5),
    ("DK", 2022, None, r"A\. Socialdemokratiet", 27.5, 0.5),
    ("BG", 2024, 10, r"ГЕРБ", 26.4, 1.0),
    ("RO", 2024, 12, r"UNIREA ROM", 18.0, 1.5),
    ("RO", 2020, 12, r"UNIREA ROM", 9.08, 0.5),
    ("RO", 2020, 12, r"^PARTIDUL SOCIAL DEMOCRAT$", 28.9, 0.5),
    ("CZ", 2025, 10, r"ANO", 34.5, 0.7),
    ("NO", 2025, 9, r"Arbeiderpartiet", 28.2, 0.5),
    ("UK", 2024, 7, r"^Labour$", 33.7, 0.5) if False else
    ("GB", 2024, 7, r"^Labour$", 33.7, 0.5),
    ("HU", 2022, None, r"FIDESZ", 54.1, 1.0),
    ("GR", 2023, 6, r"ΝΕΑ ΔΗΜΟΚΡΑΤΙΑ|NEA DIMOKRATIA|New Democracy", 40.6, 1.0),
    ("CH", 2023, None, r"Schweizerische Volkspartei|Union Démocratique du Centre|SVP", 27.9, 1.0),
    ("EE", 2023, None, r"Eesti Reformierakond", 31.2, 0.7),
    ("LV", 2022, None, r"Jaunā VIENOTĪBA", 18.97, 0.5),
    ("LT", 2024, None, r"socialdemokratų", 19.4, 1.5),
    ("SK", 2023, None, r"SMER", 22.9, 0.7),
    ("SI", 2022, None, r"GIBANJE SVOBODA", 34.5, 0.7),
    ("BE", 2024, None, r"VLAAMS BELANG", 13.8, 0.7),
    ("IS", 2024, None, r"Samfylkingin", 20.8, 0.7),
    ("CY", 2021, None, r"ΔΗΜΟΚΡΑΤΙΚΟΣ ΣΥΝΑΓΕΡΜΟΣ", 27.8, 0.5),
    ("LU", 2023, None, r"^CSV", 29.2, 0.7),
    ("RO", 2024, 12, r"^PARTIDUL SOCIAL DEMOCRAT$", 21.9, 1.0),
    ("UA", 0, None, "", 0, 0)][:-1]

for cc, yr, mo, pat, official, tol in CHECKS:
    sub = f16[(f16.country_code == cc) & (f16.year == yr)]
    if mo is not None:
        sub = sub[sub.month == mo]
    if not len(sub):
        log(f"  {cc} {yr}: NOT FOUND in data"); continue
    tot = sub.partyvote.sum()
    pv = sub[sub.party_native.fillna(sub.party_english.fillna(
        sub.party_abbreviation)).astype(str).str.contains(pat, case=False,
                                                          regex=True)]
    if not len(pv):
        pv = sub[sub[["party_native", "party_english", "party_abbreviation"]]
                 .astype(str).apply(lambda r: r.str.contains(pat, case=False,
                                                             regex=True))
                 .any(axis=1)]
    share = pv.partyvote.sum() / tot * 100
    ok = abs(share - official) <= tol
    log(f"  {'OK ' if ok else '***'} {cc} {yr}"
        f"{'-' + str(mo) if mo else ''}: {share:5.2f}% vs official "
        f"{official}% (tol {tol})  [{pat[:30]}]")
    flag(not ok, f"external mismatch {cc} {yr}")

log("=" * 70)
log(f"TOTAL ISSUES FLAGGED: {issues}")
open(rf"{OUT}\validation_report.txt", "w", encoding="utf8").write(rep.getvalue())
