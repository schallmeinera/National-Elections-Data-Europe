"""Build NUTS-3/2/1 crosswalks 2016->2021, 2021->2024, 2016->2024.

Sources:
- JRC conversion matrices (R `nuts` package export) for 2016->2021, weighted by
  2018 population (pop18).
- Eurostat NUTS2021-NUTS2024.xlsx correspondence for 2021->2024 (recodes paired
  by label; true splits weighted by ARDECO population 2021; LV007 by boundary
  overlay area shares).
- NUTS boundary gpkg files (2016/2021/2024) for definitive code lists and the
  LV overlay.

Outputs (crosswalks/): nuts{1,2,3}_2016_2021.csv, _2021_2024.csv, _2016_2024.csv
with columns from_code, to_code, weight, method.
"""
import re
import sys
import pandas as pd
import numpy as np
import geopandas as gpd

XW = r"D:\EU LFS\eu-parliamentary-elections\crosswalks"
GPKG = r"D:\EU LFS\DATA\06_Geo_Crosswalks\NUTS_Boundaries"
ARDECO_POP = (r"D:\EU LFS\DATA\05_Context_Aggregates\Ardeco\ardeco_nuts3_available"
              r"\parquet\SNPTN__age=TOTAL__sex=TOTAL__unit=NR.parquet")

# ---------- definitive code lists per vintage ----------
def codes_from_gpkg(year):
    g = gpd.read_file(rf"{GPKG}\NUTS_RG_20M_{year}_3035.gpkg")
    return g[["NUTS_ID", "LEVL_CODE", "CNTR_CODE", "NAME_LATN"]].rename(
        columns={"NUTS_ID": "code", "LEVL_CODE": "level", "CNTR_CODE": "cc",
                 "NAME_LATN": "name"})

codes16 = codes_from_gpkg(2016)
codes21 = codes_from_gpkg(2021)
codes24 = codes_from_gpkg(2024)
print("codes per vintage:", len(codes16), len(codes21), len(codes24))

pop = pd.read_parquet(ARDECO_POP)
pop21 = (pop[pop.YEAR == 2021].groupby("TERRITORY_ID").VALUE.mean())  # any version

# ---------- 2016 -> 2021 (JRC, pop18-weighted) ----------
jrc = pd.read_csv(rf"{XW}\nutsRpkg_cross_walks.csv")
xw1621_3 = jrc[(jrc.from_version == 2016) & (jrc.to_version == 2021) & (jrc.level == 3)].copy()
xw1621_3["weight"] = xw1621_3.pop18 / xw1621_3.groupby("from_code").pop18.transform("sum")
xw1621_3 = xw1621_3[["from_code", "to_code", "weight"]]
xw1621_3["method"] = "jrc_pop18"

# JRC lacks non-EU/EFTA extras present in gpkg (e.g. AL/RS/TR?) -> identity where code unchanged
have = set(xw1621_3.from_code)
n3_16 = codes16[codes16.level == 3].code
n3_21 = set(codes21[codes21.level == 3].code)
missing = [c for c in n3_16 if c not in have]
ident = pd.DataFrame({"from_code": [c for c in missing if c in n3_21]})
ident["to_code"] = ident.from_code
ident["weight"] = 1.0
ident["method"] = "identity_fill"
unresolved16 = [c for c in missing if c not in n3_21]
# Northern Ireland pure recodes UKN10..UKN16 -> UKN0A..UKN0G (verified by
# identical NAME_LATN in the 2016/2021 gpkg attribute tables)
ukn = pd.DataFrame({
    "from_code": ["UKN10", "UKN11", "UKN12", "UKN13", "UKN14", "UKN15", "UKN16"],
    "to_code":   ["UKN0A", "UKN0B", "UKN0C", "UKN0D", "UKN0E", "UKN0F", "UKN0G"],
})
ukn["weight"] = 1.0
ukn["method"] = "manual_recode"
unresolved16 = [c for c in unresolved16 if c not in set(ukn.from_code)]
print("2016->2021: JRC rows", len(xw1621_3), "| identity fill", len(ident),
      "| UKN recodes", len(ukn), "| unresolved", unresolved16)
xw1621_3 = pd.concat([xw1621_3, ident, ukn], ignore_index=True)

# ---------- 2021 -> 2024 (Eurostat correspondence) ----------
corr = pd.read_excel(rf"{XW}\NUTS2021-NUTS2024.xlsx", sheet_name="NUTS2021- NUTS2024",
                     header=0)
corr.columns = ["n", "cc", "code21", "code24", "l1", "l2", "l3", "change",
                "level", "corder", "ro21", "ro24"]
corr = corr[corr.level == 3].copy()
corr["label"] = corr[["l1", "l2", "l3"]].bfill(axis=1).iloc[:, 0]

both = corr.dropna(subset=["code21", "code24"])
direct = both[["code21", "code24"]].rename(columns={"code21": "from_code",
                                                    "code24": "to_code"})
direct["weight"] = 1.0
direct["method"] = "eurostat_direct"

# discontinued / new rows -> pair by (cc, label)
disc = corr[corr.code24.isna() & corr.code21.notna()][["cc", "code21", "label"]]
new = corr[corr.code21.isna() & corr.code24.notna()][["cc", "code24", "label"]]
pair = disc.merge(new, on=["cc", "label"], how="outer", indicator=True)
paired = pair[pair._merge == "both"][["code21", "code24"]].rename(
    columns={"code21": "from_code", "code24": "to_code"})
paired["weight"] = 1.0
paired["method"] = "label_pair"
un_disc = pair[pair._merge == "left_only"][["cc", "code21", "label"]]
un_new = pair[pair._merge == "right_only"][["cc", "code24", "label"]]
print("2021->2024 direct:", len(direct), "| label-paired:", len(paired))
print("unpaired discontinued:\n", un_disc.to_string())
print("unpaired new:\n", un_new.to_string())

# explicit splits, weighted by ARDECO population 2021
SPLITS = {
    "PT170": ["PT1A0", "PT1B0"],
    "NO074": ["NO072", "NO073"],
    "NO082": ["NO083", "NO084", "NO085"],
    "NO091": ["NO093", "NO094"],
}
rows = []
for src, tgts in SPLITS.items():
    p = np.array([pop21.get(t, np.nan) for t in tgts])
    assert not np.isnan(p).any(), (src, tgts, p)
    for t, w in zip(tgts, p / p.sum()):
        rows.append((src, t, w, "split_pop_ardeco"))
splits = pd.DataFrame(rows, columns=["from_code", "to_code", "weight", "method"])
print(splits.to_string())

# LV007 (Pieriga) -> overlay with 2024 polygons, area shares
g21 = gpd.read_file(rf"{GPKG}\NUTS_RG_20M_2021_3035.gpkg")
g24 = gpd.read_file(rf"{GPKG}\NUTS_RG_20M_2024_3035.gpkg")
lv007 = g21[g21.NUTS_ID == "LV007"][["NUTS_ID", "geometry"]]
lv24 = g24[(g24.LEVL_CODE == 3) & (g24.CNTR_CODE == "LV")][["NUTS_ID", "geometry"]]
inter = gpd.overlay(lv007, lv24, how="intersection")
inter["area"] = inter.geometry.area
inter["weight"] = inter.area / inter.area.sum()
inter = inter[inter.weight > 0.005]
inter["weight"] = inter.weight / inter.weight.sum()
lv_rows = pd.DataFrame({"from_code": "LV007", "to_code": inter.NUTS_ID_2,
                        "weight": inter.weight, "method": "overlay_area"})
print("LV007 overlay:\n", lv_rows.to_string())

# DEG0N (Eisenach) merged into Wartburgkreis (ex-DEG0P -> DEG0R)
merge_de = pd.DataFrame({"from_code": ["DEG0N"], "to_code": ["DEG0R"],
                         "weight": [1.0], "method": ["manual_merge"]})

xw2124_3 = pd.concat([direct, paired, splits, lv_rows, merge_de],
                     ignore_index=True)

# identity fill: codes present in both the 2021 and 2024 gpkg lists but absent
# from the Eurostat EU-only correspondence sheet (CH, NO unchanged, RS, TR, AL,
# IS, ME, MK, LI). UK is deliberately absent from NUTS 2024 -> stays unmapped.
n3_24 = set(codes24[codes24.level == 3].code)
have21 = set(xw2124_3.from_code)
fill = [c for c in codes21[codes21.level == 3].code
        if c not in have21 and c in n3_24]
ident24 = pd.DataFrame({"from_code": fill})
ident24["to_code"] = ident24.from_code
ident24["weight"] = 1.0
ident24["method"] = "identity_fill"
xw2124_3 = pd.concat([xw2124_3, ident24], ignore_index=True)

# validation: full coverage of both sides
from_missing = sorted(set(codes21[codes21.level == 3].code) - set(xw2124_3.from_code))
to_extra = sorted(set(xw2124_3.to_code) - n3_24)
print("identity fill 2021->2024:", len(ident24))
print("2021 NUTS3 not mapped (expected: UK only):",
      sum(c.startswith("UK") for c in from_missing), "UK;",
      [c for c in from_missing if not c.startswith("UK")])
print("mapped targets not in 2024 gpkg list (ZZZ extra-regio expected):",
      [c for c in to_extra if not c.endswith("ZZZ")])
bad = xw2124_3.groupby("from_code").weight.sum()
bad = bad[(bad - 1).abs() > 1e-6]
print("weight sums != 1:", bad.to_dict())

# ---------- compose 2016 -> 2024 ----------
comp = xw1621_3.merge(xw2124_3, left_on="to_code", right_on="from_code",
                      suffixes=("_a", "_b"))
comp["weight"] = comp.weight_a * comp.weight_b
comp = (comp.groupby(["from_code_a", "to_code_b"], as_index=False).weight.sum()
        .rename(columns={"from_code_a": "from_code", "to_code_b": "to_code"}))
comp["method"] = "composed"
xw1624_3 = comp

# ---------- derive NUTS2 / NUTS1 crosswalks from NUTS3 (pop-weighted) ----------
pop_by3 = {}
for v, cl in [(2016, codes16), (2021, codes21), (2024, codes24)]:
    n3 = cl[cl.level == 3].code
    pop_by3[v] = pd.Series({c: pop21.get(c, np.nan) for c in n3})

def upper_xw(xw3, fv, pref_len):
    """Aggregate a NUTS3 crosswalk to an upper level (pref_len=3 -> NUTS1, 4 -> NUTS2)."""
    d = xw3.copy()
    d["pop"] = d.from_code.map(pop_by3[fv])
    # fallback for missing pop: equal weights
    d["pop"] = d["pop"].fillna(d.groupby("from_code").weight.transform("size") * 0 + 1)
    d["from_up"] = d.from_code.str[:pref_len]
    d["to_up"] = d.to_code.str[:pref_len]
    d["mass"] = d["pop"] * d.weight
    agg = d.groupby(["from_up", "to_up"], as_index=False).mass.sum()
    agg["weight"] = agg.mass / agg.groupby("from_up").mass.transform("sum")
    agg = agg[agg.weight > 0.001].copy()
    agg["weight"] = agg.weight / agg.groupby("from_up").weight.transform("sum")
    return agg.rename(columns={"from_up": "from_code", "to_up": "to_code"})[
        ["from_code", "to_code", "weight"]]

out = {
    "nuts3_2016_2021": xw1621_3[["from_code", "to_code", "weight", "method"]],
    "nuts3_2021_2024": xw2124_3[["from_code", "to_code", "weight", "method"]],
    "nuts3_2016_2024": xw1624_3[["from_code", "to_code", "weight", "method"]],
    "nuts2_2016_2021": upper_xw(xw1621_3, 2016, 4),
    "nuts2_2021_2024": upper_xw(xw2124_3, 2021, 4),
    "nuts2_2016_2024": upper_xw(xw1624_3, 2016, 4),
    "nuts1_2016_2021": upper_xw(xw1621_3, 2016, 3),
    "nuts1_2021_2024": upper_xw(xw2124_3, 2021, 3),
    "nuts1_2016_2024": upper_xw(xw1624_3, 2016, 3),
}
for name, df in out.items():
    df.to_csv(rf"{XW}\{name}.csv", index=False)
    n_split = (df.groupby("from_code").size() > 1).sum()
    print(f"{name}: {len(df)} rows, {df.from_code.nunique()} sources, {n_split} 1:N")

# vintage code lists
for v, cl in [(2016, codes16), (2021, codes21), (2024, codes24)]:
    cl.to_csv(rf"{XW}\nuts_codes_{v}.csv", index=False)
print("done")
