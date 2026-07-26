"""Portugal legislativas 2022, 2024, 2025 (MAI data via RuiNelson mirror,
municipality level) -> NUTS-3 via LAU (PT NUTS-3 identical 2016/2021).
Foreign circles (Europa / Fora da Europa) are not in the source. """
import re
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2023-NUTS-2021.xlsx",
                    sheet_name="PT")
ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
# PT LAU = freguesias (6-digit DICOFRE); concelho = first 4 digits, and each
# concelho lies in exactly one NUTS-3
lau["concelho"] = (lau["LAU CODE"].astype(str).str.strip().str.zfill(6)
                   .str[:4])
amb = lau.groupby("concelho")[ncol].nunique()
assert (amb == 1).all(), amb[amb > 1]
lk = lau.drop_duplicates("concelho").set_index("concelho")[ncol]
print("concelhos in LAU:", len(lk))


def build(f, tag_map):
    """tag_map: {column-tag: (year, month)} e.g. {'2022': (2022,1)}."""
    d = pd.read_csv(f, sep="\t")
    muni = d[(d.Municipio != "*") & (d.Freguesia == "*")].copy()
    muni["dicofre"] = muni.Key.str[6:10]
    muni["nuts_code"] = muni.dicofre.map(lk)
    un = muni[muni.nuts_code.isna()]
    assert not len(un), un[["Key", "Municipio"]].values[:10]
    frames = []
    for tag, (yr, mo) in tag_map.items():
        vote_cols = [c for c in muni.columns
                     if c.endswith(f"- Votos ({tag})")]
        parties = {c: re.sub(rf"\s*-\s*Votos \({tag}\)$", "", c)
                   for c in vote_cols}
        long = muni.melt(id_vars=["nuts_code", f"Eleitores ({tag})"],
                         value_vars=vote_cols, var_name="col",
                         value_name="partyvote")
        long["party_native"] = long.col.map(parties)
        g = (long.groupby(["nuts_code", "party_native"], as_index=False)
             .partyvote.sum())
        g = g[g.partyvote > 0]
        el = muni.groupby("nuts_code")[f"Eleitores ({tag})"].sum()
        g["electorate"] = g.nuts_code.map(el)
        g["validvote"] = g.groupby("nuts_code").partyvote.transform("sum")
        g["totalvote"] = np.nan
        g["year"], g["month"] = yr, mo
        frames.append(g)
        print(f"{yr}: {g.partyvote.sum():,.0f} votes, "
              f"{g.nuts_code.nunique()} NUTS3")
    return frames


frames = build(rf"{BASE}\raw\pt2024.tsv",
               {"2022": (2022, 1), "2024": (2024, 3)})
frames += build(rf"{BASE}\raw\pt2025.tsv", {"Corrente": (2025, 5)})

out = pd.concat(frames, ignore_index=True)
out["country"], out["country_code"] = "Portugal", "PT"
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "MAI legislativas (RuiNelson/EleicoesPortuguesas mirror)"
out.to_csv(rf"{BASE}\raw\ext_pt.csv", index=False)
print("written:", len(out), "rows")
