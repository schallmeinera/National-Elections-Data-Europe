"""Build the backbone national-parliamentary-election panel from EU-NED.

EU-NED v1.1 (elections 1990-2020, NUTS-2016 codes) reports each election as a
complete national partition of MIXED-level units (e.g. Greece = nomoi at
NUTS-3 + Attica whole at NUTS-2; Spain = provinces at NUTS-3 + legacy island
province codes; Slovenia national only).

Outputs per vintage V in {2016, 2021, 2024}:
- national_finest_V   : finest available partition, native level per row
- national_nuts2_V    : complete NUTS-2 partition (countries with base >= 2)
- national_nuts1_V    : complete NUTS-1 partition (all countries)

Legacy electoral-province codes (ES530/ES701/ES702) are split into their
NUTS-2016 island NUTS-3s by ARDECO population (2001), so they aggregate
correctly to ES53/ES70 at NUTS-2.
"""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
XW = BASE + r"\crosswalks"
OUT = BASE + r"\output"
ARDECO_POP = (r"D:\EU LFS\DATA\05_Context_Aggregates\Ardeco\ardeco_nuts3_available"
              r"\parquet\SNPTN__age=TOTAL__sex=TOTAL__unit=NR.parquet")

ned = pd.read_csv(r"D:\EU LFS\DATA\03_Elections\EU_NED\eu_ned_joint.csv")
ned = ned[ned.type == "Parliament"].copy()
# EU-NED's Netherlands series (1994-2017, NUTS-2) is superseded by the
# Kiesraad gemeente-level NUTS-3 rebuild (ext_nl_hist.csv)
ned = ned[ned.country_code != "NL"]
ned = ned.rename(columns={"nuts2016": "nuts_code"})
ned["nuts_code"] = ned.nuts_code.astype(str).str.strip()
ned["source"] = "EU-NED v1.1"
ned["month"] = np.nan

# --- append post-2020 extensions (CLEA-mapped + German official) ---
CORE = ["country", "country_code", "year", "month", "nuts_code", "regionname",
        "party_abbreviation", "party_english", "party_native", "partyfacts_id",
        "partyvote", "electorate", "totalvote", "validvote", "source"]
import glob
# DE 2021/2025 come from ext_de_nuts3.csv (Kreis level); the Land-level kerg
# file (de_official_nuts1.csv) is superseded and no longer loaded
ext_files = ([rf"{BASE}\raw\clea_mapped_nuts2016.csv",
              rf"{BASE}\raw\at_official_nuts3.csv"]
             + sorted(glob.glob(rf"{BASE}\raw\ext_*.csv")))
parts = []
for f in ext_files:
    e = pd.read_csv(f)
    for c in CORE:
        if c not in e.columns:
            e[c] = np.nan
    parts.append(e[CORE])
ext = pd.concat(parts, ignore_index=True)
ned = pd.concat([ned[CORE], ext], ignore_index=True)
print("rows: EU-NED + extensions =", len(ned),
      f"(ext {len(ext)}: {ext.country_code.nunique()} countries)")

# --- legacy fix-up ---------------------------------------------------------
pop = pd.read_parquet(ARDECO_POP)
pop01 = pop[pop.YEAR == 2001].groupby("TERRITORY_ID").VALUE.mean()

LEGACY_SPLITS = {  # electoral province -> constituent NUTS-2016 NUTS-3 islands
    "ES530": ["ES531", "ES532", "ES533"],
    "ES701": ["ES704", "ES705", "ES708"],
    "ES702": ["ES703", "ES706", "ES707", "ES709"],
}
legacy_rows = []
for src, tgts in LEGACY_SPLITS.items():
    p = np.array([pop01[t] for t in tgts])
    for t, w in zip(tgts, p / p.sum()):
        legacy_rows.append((src, t, w))
legacy_rows += [("NO061", "NO060", 1.0), ("NO062", "NO060", 1.0)]
legacy = pd.DataFrame(legacy_rows, columns=["nuts_code", "new_code", "lw"])
print("legacy fix-up:\n", legacy.to_string(index=False))

ned["legacy_weighted"] = ned.nuts_code.isin(
    legacy[legacy.lw < 1].nuts_code.unique())
ned = ned.merge(legacy, on="nuts_code", how="left")
split = ned.new_code.notna()
for c in ["partyvote", "electorate", "totalvote", "validvote"]:
    ned.loc[split, c] = ned.loc[split, c] * ned.loc[split, "lw"]
ned.loc[split, "nuts_code"] = ned.loc[split, "new_code"]
ned = ned.drop(columns=["new_code", "lw"])

ned["nutslevel"] = ned.nuts_code.str.len() - 2
ned.loc[ned.nuts_code.str.endswith("ZZZ"), "nutslevel"] = 3  # extra-regio
ned["month"] = ned.month.fillna(0).astype(int)  # 0 = month not recorded

names = {v: pd.read_csv(rf"{XW}\nuts_codes_{v}.csv").set_index("code")["name"]
         for v in (2016, 2021, 2024)}
xw = {(l, v): pd.read_csv(rf"{XW}\nuts{l}_2016_{v}.csv")
      for l in (1, 2, 3) for v in (2021, 2024)}

KEY = ["country", "country_code", "year", "month"]
PARTY = ["party_abbreviation", "party_english", "party_native", "partyfacts_id"]
TOTS = ["electorate", "totalvote", "validvote"]


def collapse(d):
    """Party votes + region totals for a df whose nuts_code is final."""
    party = (d.groupby(KEY + ["nuts_code", "nutslevel"] + PARTY, dropna=False,
                       as_index=False)
             .agg(partyvote=("partyvote", "sum"),
                  legacy_weighted=("legacy_weighted", "max"),
                  source=("source", "first")))
    # dedup party-repeated region totals; include TOTS in the subset so that
    # merged source units with NaN regionname (e.g. legacy NO061+NO062 ->
    # NO060 in extension data) are both kept and summed
    reg = (d.drop_duplicates(subset=KEY + ["nuts_code", "regionname"] + TOTS)
           .groupby(KEY + ["nuts_code"], dropna=False)[TOTS]
           .sum(min_count=1).reset_index())
    return party, reg


def truncated(df, level):
    d = df[df.nutslevel >= level].copy()
    d["nuts_code"] = d.nuts_code.str[: 2 + level]
    d["nutslevel"] = level
    return d


def convert(party, reg, vintage):
    """Convert mixed-level tables 2016 -> vintage using the level-appropriate
    crosswalk per row; extra-regio Z-codes pass through."""
    if vintage == 2016:
        m = party.merge(reg, on=KEY + ["nuts_code"], how="left")
        m["conversion"] = np.where(m.legacy_weighted, "weighted", "native")
    else:
        parts_p, parts_r = [], []
        lv = party[["nuts_code", "nutslevel"]].drop_duplicates()
        for level in sorted(party.nutslevel.unique()):
            w = xw[(min(int(level), 3), vintage)] if level >= 1 else None
            codes = lv[lv.nutslevel == level].nuts_code
            zid = pd.DataFrame({"from_code": [c for c in codes if c.endswith("Z")]})
            zid["to_code"] = zid.from_code
            zid["weight"] = 1.0
            wfull = pd.concat([w[["from_code", "to_code", "weight"]], zid],
                              ignore_index=True)
            p = (party[party.nutslevel == level]
                 .merge(wfull, left_on="nuts_code", right_on="from_code"))
            r = (reg[reg.nuts_code.isin(codes)]
                 .merge(wfull, left_on="nuts_code", right_on="from_code"))
            parts_p.append(p)
            parts_r.append(r)
        p = pd.concat(parts_p, ignore_index=True)
        r = pd.concat(parts_r, ignore_index=True)
        dropped = set(party.nuts_code) - set(p.nuts_code)
        if dropped:
            print(f"  v{vintage}: unmapped codes dropped: {sorted(dropped)[:6]} "
                  f"({len(dropped)})")
        exact = p.groupby("nuts_code").to_code.transform("nunique") == 1
        p["conversion"] = np.where((p.weight > 0.9999) & exact
                                   & ~p.legacy_weighted, "exact", "weighted")
        p["partyvote"] = p.partyvote * p.weight
        for c in ["electorate", "totalvote", "validvote"]:
            r[c] = r[c] * r.weight
        p = (p.assign(nuts_code=p.to_code)
             .groupby(KEY + ["nuts_code", "nutslevel"] + PARTY, dropna=False,
                      as_index=False)
             .agg(partyvote=("partyvote", "sum"),
                  conversion=("conversion", "max"),  # any 'weighted' wins
                  source=("source", "first")))
        r = (r.assign(nuts_code=r.to_code)
             .groupby(KEY + ["nuts_code"], dropna=False)[TOTS]
             .sum(min_count=1).reset_index())
        m = p.merge(r, on=KEY + ["nuts_code"], how="left")
    m["regionname"] = m.nuts_code.map(names[vintage])
    m.loc[m.nuts_code.str.endswith("Z"), "regionname"] = "Extra-regio"
    m["nuts_vintage"] = vintage
    m["election_type"] = "parliament"
    return m


COLS = ["country", "country_code", "year", "month", "election_type",
        "nuts_code", "nutslevel", "nuts_vintage", "regionname",
        "party_abbreviation", "party_english", "party_native", "partyfacts_id",
        "partyvote", "electorate", "totalvote", "validvote", "conversion",
        "source"]

tables = {"finest": collapse(ned),
          "nuts2": collapse(truncated(ned, 2)),
          "nuts1": collapse(truncated(ned, 1))}

for tname, (party, reg) in tables.items():
    for vintage in (2016, 2021, 2024):
        m = convert(party, reg, vintage)
        m = (m[COLS].rename(columns={"nutslevel": "nuts_level"})
             .sort_values(KEY + ["nuts_code", "party_abbreviation"]))
        stem = rf"{OUT}\national_{tname}_{vintage}"
        m.to_csv(stem + ".csv", index=False)
        m.to_parquet(stem + ".parquet", index=False)
        print(f"{tname} v{vintage}: {len(m):,} rows, "
              f"{m.country_code.nunique()} countries, "
              f"{m.nuts_code.nunique()} regions, "
              f"{m.groupby(['country_code','year']).ngroups} elections")

# consistency: national vote totals invariant across tables and vintages
chk = []
for tname in tables:
    for vintage in (2016, 2021, 2024):
        m = pd.read_parquet(rf"{OUT}\national_{tname}_{vintage}.parquet")
        chk.append(m.groupby(["country_code", "year"]).partyvote.sum()
                   .rename(f"{tname}_v{vintage}"))
chk = pd.concat(chk, axis=1)
rel = chk.divide(chk["finest_v2016"], axis=0)
mask = (rel.sub(1).abs() > 1e-6)
# UK absent from NUTS-2024: expected NaN, ignore
bad = rel[mask.any(axis=1)]
bad = bad[~(bad.index.get_level_values(0) == "GB") | bad.notna().all(axis=1)]
print("\nviolations:")
print(bad.to_string() if len(bad) else "none")
