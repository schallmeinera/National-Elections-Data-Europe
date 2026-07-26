"""Italy Camera 2022 (onData/Eligendo comune-level) -> NUTS-3.

- proportional list votes per comune (camera-italia-comune.csv, deduplicated
  to one row per comune x list)
- Valle d'Aosta SMD candidate-list votes (vda-camera.csv)
- Estero (abroad) list votes -> ITZZZ
Comune -> NUTS-3 via ISTAT code (LAU2023; IT NUTS-3 identical 2016/2021).
"""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

com = pd.read_csv(rf"{BASE}\raw\it2022_camera_comune.csv")
ana = pd.read_csv(rf"{BASE}\raw\it2022_camera_anagrafica.csv",
                  dtype={"CODICE ISTAT": str})

lists = com[["codice", "desc_lis", "voti"]].drop_duplicates(
    subset=["codice", "desc_lis"])
ana = ana.rename(columns={"CODICE ISTAT": "istat"})
meta = ana.set_index("codice")[["istat", "ele_t", "vot_t", "tot_vot_prop",
                                "desc_com", "cod_prov"]]
lists = lists.join(meta, on="codice")
print("comuni:", lists.codice.nunique(), "| list-votes:",
      f"{lists.voti.sum():,.0f}")

lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2023-NUTS-2021.xlsx",
                    sheet_name="IT")
ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
lau["istat"] = lau["LAU CODE"].astype(str).str.strip().str.zfill(6)
lk = lau.set_index("istat")[ncol]
lists["istat"] = lists.istat.astype(str).str.zfill(6)
lists["nuts_code"] = lists.istat.map(lk)
# LAU carries NUTS-2021 codes; map back to NUTS-2016 by dominant weight
# (Sardinia was recoded ITG25-29 -> ITG2D-2H in 2021)
fw = pd.read_csv(rf"{BASE}\crosswalks\nuts3_2016_2021.csv")
fw = fw[fw.from_code.str.startswith("IT")].sort_values("weight")
back = dict(zip(fw.drop_duplicates("to_code", keep="last").to_code,
                fw.drop_duplicates("to_code", keep="last").from_code))
lists["nuts_code"] = lists.nuts_code.map(lambda c: back.get(c, c))
un = lists[lists.nuts_code.isna()].drop_duplicates("istat")
print("unmatched comuni:", len(un), un[["istat", "desc_com"]].head(12).values.tolist())
lists = lists.dropna(subset=["nuts_code"])

p = (lists.groupby(["nuts_code", "desc_lis"], as_index=False).voti.sum()
     .rename(columns={"desc_lis": "party_native", "voti": "partyvote"}))
reg = (lists.drop_duplicates("codice").groupby("nuts_code")
       .agg(electorate=("ele_t", "sum"), totalvote=("vot_t", "sum"),
            validvote=("tot_vot_prop", "sum")))
p["electorate"] = p.nuts_code.map(reg.electorate)
p["totalvote"] = p.nuts_code.map(reg.totalvote)
p["validvote"] = p.nuts_code.map(reg.validvote)
p["year"], p["month"] = 2022, 9

# Valle d'Aosta (ITC20): candidate votes by list
vda = pd.read_csv(rf"{BASE}\raw\it2022_vda.csv")
v = (vda.groupby("lista", as_index=False).voti.sum()
     .rename(columns={"lista": "party_native", "voti": "partyvote"}))
v["nuts_code"] = "ITC20"
v["electorate"] = np.nan
v["totalvote"] = np.nan
v["validvote"] = v.partyvote.sum()
v["year"], v["month"] = 2022, 9
print("VdA votes:", v.partyvote.sum())

# Estero -> ITZZZ
est = pd.read_csv(rf"{BASE}\raw\it2022_estero.csv", sep=";")
e = (est.groupby("Lista", as_index=False)["Voti Liste"].sum()
     .rename(columns={"Lista": "party_native", "Voti Liste": "partyvote"}))
e["nuts_code"] = "ITZZZ"
e["electorate"] = np.nan
e["totalvote"] = np.nan
e["validvote"] = e.partyvote.sum()
e["year"], e["month"] = 2022, 9
print("Estero votes:", e.partyvote.sum())

out = pd.concat([p, v, e], ignore_index=True)
out = out[out.partyvote > 0]
out["country"], out["country_code"] = "Italy", "IT"
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "Eligendo via onData (Camera, proportional list votes)"
out.to_csv(rf"{BASE}\raw\ext_it2022.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS3,",
      f"votes {out.partyvote.sum():,.0f}")
