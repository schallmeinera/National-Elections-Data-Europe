"""Finland 2023 parliamentary election via Statfin PxWeb (table 13sw:
party support by municipality) -> NUTS-3 via LAU2023.

Municipality codes in the table are 6-digit: 2-digit constituency + 4-digit
kunta (e.g. 010091 = constituency 01, Helsinki 091); x x0000 = constituency
totals (skipped)."""
import json
import subprocess
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
URL = "https://statfin.stat.fi/PXWeb/api/v1/en/StatFin/evaa/13sw.px"

query = {
    "query": [
        {"code": "timeperiod_y", "selection": {"filter": "item",
                                               "values": ["2023"]}},
        {"code": "sukupuoli_9_20180101", "selection": {"filter": "item",
                                                       "values": ["SSS"]}},
        {"code": "contentscode", "selection": {"filter": "item",
                                               "values": ["evaa_aanet"]}},
        {"code": "kunta_109_20230101", "selection": {"filter": "all",
                                                     "values": ["*"]}},
        {"code": "puolue_19_20230101", "selection": {"filter": "all",
                                                     "values": ["*"]}},
    ],
    "response": {"format": "json-stat2"},
}
qf = rf"{BASE}\raw\fi_query.json"
json.dump(query, open(qf, "w"))
out = subprocess.run(["curl.exe", "-sL", "-X", "POST", "-H",
                      "Content-Type: application/json", "-d", "@" + qf, URL],
                     capture_output=True).stdout
j = json.loads(out.decode("utf-8-sig"))
open(rf"{BASE}\raw\fi2023_13sw.json", "w", encoding="utf8").write(
    json.dumps(j))

dims = j["dimension"]
order = j["id"]
sizes = j["size"]
kdim = [d for d in order if d.startswith("kunta")][0]
pdim = [d for d in order if d.startswith("puolue")][0]
kcodes = list(dims[kdim]["category"]["index"].keys())
klabels = dims[kdim]["category"]["label"]
pcodes = list(dims[pdim]["category"]["index"].keys())
plabels = dims[pdim]["category"]["label"]
vals = j["value"]

import itertools
axes = []
for d in order:
    n = sizes[order.index(d)]
    cat = list(dims[d]["category"]["index"].keys())
    axes.append(cat)
recs = []
i = 0
for combo in itertools.product(*axes):
    v = vals[i]
    i += 1
    if v is None:
        continue
    rec = dict(zip(order, combo))
    recs.append((rec[kdim], rec[pdim], v))
df = pd.DataFrame(recs, columns=["kunta6", "party", "votes"])
df = df[(df.kunta6 != "SSS") & (df.party != "SSS")]
df["kunta"] = df.kunta6.str[2:]
df = df[df.kunta != "0000"]  # drop constituency totals
print("municipality rows:", len(df), "| municipalities:",
      df.kunta.nunique())

lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2023-NUTS-2021.xlsx",
                    sheet_name="FI")
ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
lau["kunta"] = lau["LAU CODE"].astype(str).str.strip().str.zfill(4)
lk = lau.set_index("kunta")[ncol]
df["nuts_code"] = df.kunta.map(lk)  # FI NUTS3 2021 == 2016
un = df[df.nuts_code.isna()].kunta.unique()
if len(un):
    print("unmatched kunta:", [(k, klabels.get("01" + k, k)) for k in un])
df = df.dropna(subset=["nuts_code"])

g = (df.groupby(["nuts_code", "party"], as_index=False).votes.sum()
     .rename(columns={"votes": "partyvote"}))
g["party_native"] = g.party.map(plabels)
g = g[g.partyvote > 0].drop(columns="party")
g["validvote"] = g.groupby("nuts_code").partyvote.transform("sum")
g["electorate"] = np.nan
g["totalvote"] = np.nan
g["country"], g["country_code"] = "Finland", "FI"
g["year"], g["month"] = 2023, 4
g["party_abbreviation"] = np.nan
g["party_english"] = np.nan
g["partyfacts_id"] = np.nan
g["regionname"] = np.nan
g["source"] = "Statistics Finland PxWeb 13sw"
g.to_csv(rf"{BASE}\raw\ext_fi2023.csv", index=False)
print("written:", len(g), "rows,", g.nuts_code.nunique(), "NUTS3,",
      f"votes {g.partyvote.sum():,.0f}")
