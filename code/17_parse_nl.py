"""Netherlands TK 2021 + 2023 (Kiesraad open data, per gemeente) -> NUTS-3.

Gemeente -> NUTS3-2021 via Eurostat LAU tables (year-matched), then NUTS3-2021
-> NUTS3-2016 backward recode (NL changes 2016->2021 are 1:1 recodes) so the
rows enter the pipeline in its NUTS-2016 input vintage.
"""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
XW = BASE + r"\crosswalks"

# backward recode 2021 -> 2016 from the forward crosswalk: for each 2021 code
# take the dominant 2016 source (NL 1:N weights are tiny LAU boundary shifts)
fw = pd.read_csv(rf"{XW}\nuts3_2016_2021.csv")
fw = fw[fw.from_code.str.startswith("NL")]
fw = fw.sort_values("weight").drop_duplicates("to_code", keep="last")
back = dict(zip(fw.to_code, fw.from_code))


def lau_map(f):
    lau = pd.read_excel(f, sheet_name="NL")
    ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
    lau["gem"] = (lau["LAU CODE"].astype(str).str.strip()
                  .str.replace("GM", "", regex=False).str.zfill(4))
    return lau.set_index("gem")[ncol]


def to16(nuts21):
    return back.get(nuts21, nuts21)


out_all = []

# ---- TK2021 (simple per-gemeente party file, no totals) ----
d21 = pd.read_csv(rf"{BASE}\raw\nl2021_csv\TK2021_Stemmen_Per_Lijst_Per_Gemeente.csv",
                  sep=";")
lk21 = lau_map(rf"{XW}\EU-27-LAU-2021-NUTS-2021.xlsx")
d21["gem"] = d21.GemeenteCode.astype(int).astype(str).str.zfill(4)
d21["nuts21"] = d21.gem.map(lk21)
d21.loc[d21.gem == "1979", "nuts21"] = "NL112"  # Eemsdelta (2021 merger)
un = d21[d21.nuts21.isna()].drop_duplicates("gem")
print("2021 unmatched:", un[["gem", "GemeenteNaam"]].values.tolist())
d21 = d21.dropna(subset=["nuts21"])
d21["nuts_code"] = d21.nuts21.map(to16)
g = (d21.groupby(["nuts_code", "PartijNaam"], as_index=False)
     .AantalStemmen.sum()
     .rename(columns={"PartijNaam": "party_native",
                      "AantalStemmen": "partyvote"}))
g["validvote"] = g.groupby("nuts_code").partyvote.transform("sum")
g["electorate"] = np.nan
g["totalvote"] = np.nan
g["year"], g["month"] = 2021, 3
out_all.append(g)

# ---- TK2023 + TK2025 (long uitslag files with gemeente rows + totals) ----
lk23 = lau_map(rf"{XW}\EU-27-LAU-2023-NUTS-2021.xlsx")
for yy, mo in [(2023, 11), (2025, 10)]:
    dd = pd.read_csv(rf"{BASE}\raw\nl{yy}_csv\TK{yy}_uitslag.csv", sep=";",
                     low_memory=False)
    gm = dd[dd.RegioCode.str.match(r"G\d+", na=False)].copy()
    gm["gem"] = gm.RegioCode.str[1:].str.zfill(4)
    gm["nuts21"] = gm.gem.map(lk23)
    gm.loc[gm.gem == "1992", "nuts21"] = "NL33C"  # Voorne aan Zee (2023)
    gm.loc[gm.gem == "9010", "nuts21"] = "NLZZZ"  # briefstembureaus (abroad)
    un = gm[gm.nuts21.isna()].drop_duplicates("gem")
    print(f"{yy} unmatched:", un[["gem", "Regio"]].values.tolist())
    gm = gm.dropna(subset=["nuts21"])
    gm["nuts_code"] = gm.nuts21.map(to16)

    votes = gm[(gm.VeldType == "LijstAantalStemmen")]
    p = (votes.groupby(["nuts_code", "LijstNaam"], as_index=False).Waarde.sum()
         .rename(columns={"LijstNaam": "party_native", "Waarde": "partyvote"}))
    tots = (gm[gm.VeldType.isin(["AantalGeldigeStemmen", "Kiesgerechtigden",
                                 "Opkomst"])]
            .pivot_table(index="nuts_code", columns="VeldType", values="Waarde",
                         aggfunc="sum"))
    p["validvote"] = p.nuts_code.map(tots["AantalGeldigeStemmen"])
    p["electorate"] = p.nuts_code.map(tots["Kiesgerechtigden"])
    p["totalvote"] = p.nuts_code.map(tots["Opkomst"])
    p["year"], p["month"] = yy, mo
    out_all.append(p)

out = pd.concat(out_all, ignore_index=True)
out = out[out.partyvote > 0]
out["country"], out["country_code"] = "Netherlands", "NL"
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "Kiesraad open data (data.overheid.nl)"
out.to_csv(rf"{BASE}\raw\ext_nl.csv", index=False)
for y in (2021, 2023, 2025):
    s = out[out.year == y]
    print(y, ":", len(s), "rows,", s.nuts_code.nunique(), "NUTS3,",
          f"votes {s.partyvote.sum():,.0f}")
