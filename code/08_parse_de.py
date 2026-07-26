"""Parse Bundeswahlleiterin kerg2 files (2021 incl. Berlin repeat, 2025) to
Land-level (NUTS-1) Zweitstimmen results in the database schema."""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
LAND_NUTS1 = {1: "DEF", 2: "DE6", 3: "DE9", 4: "DE5", 5: "DEA", 6: "DE7",
              7: "DEB", 8: "DE1", 9: "DE2", 10: "DEC", 11: "DE3", 12: "DE4",
              13: "DE8", 14: "DED", 15: "DEE", 16: "DEG"}

out = []
for year, month, f in [(2021, 9, "btw2021_kerg2.csv"),
                       (2025, 2, "btw2025_kerg2.csv")]:
    d = pd.read_csv(rf"{BASE}\raw\{f}", sep=";", skiprows=9,
                    encoding="utf-8-sig", decimal=",")
    land = d[d.Gebietsart == "Land"].copy()
    land["Stimme"] = pd.to_numeric(land.Stimme, errors="coerce")
    land["nuts_code"] = land.Gebietsnummer.astype(int).map(LAND_NUTS1)
    assert land.nuts_code.notna().all()

    sysrows = land[(land.Gruppenart == "System-Gruppe")
                   & (land.Stimme.isna() | (land.Stimme == 2))]
    sys_ = sysrows.pivot_table(
        index="nuts_code", columns="Gruppenname", values="Anzahl",
        aggfunc="first")
    party = land[(land.Gruppenart == "Partei") & (land.Stimme == 2)
                 & land.Anzahl.notna()].copy()
    g = party[["nuts_code", "Gruppenname", "Anzahl"]].rename(
        columns={"Gruppenname": "party_native", "Anzahl": "partyvote"})
    g["year"], g["month"] = year, month
    g["electorate"] = g.nuts_code.map(sys_["Wahlberechtigte"])
    g["totalvote"] = g.nuts_code.map(sys_["Wählende"])
    # valid second votes
    vcol = [c for c in sys_.columns if "ltige" in c and "Zweitstimmen" in c]
    g["validvote"] = g.nuts_code.map(
        sys_["Gültige"] if "Gültige" in sys_.columns else sys_[vcol[0]])
    out.append(g)
    print(year, ":", len(g), "party rows,",
          f"votes {g.partyvote.sum():,.0f}")

res = pd.concat(out, ignore_index=True)
res["country"], res["country_code"] = "Germany", "DE"
res["party_abbreviation"] = np.nan
res["party_english"] = np.nan
res["partyfacts_id"] = np.nan
res["source"] = np.where(res.year == 2021,
                         "Bundeswahlleiterin kerg2 (2021 final incl. 2024 "
                         "Berlin repeat)", "Bundeswahlleiterin kerg2 (2025)")
res.to_csv(rf"{BASE}\raw\de_official_nuts1.csv", index=False)
print("written", len(res), "rows")
