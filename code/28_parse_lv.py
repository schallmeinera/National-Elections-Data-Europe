"""Latvia 14th Saeima 2022 (data.gov.lv CVK JSON) -> NUTS-3.

The 5 electoral regions don't match NUTS-3 (Pierīga is split across the Rīga
and Vidzeme constituencies), so we use the municipality-level department nodes
(Type 2) and map each novads to NUTS-3 via the Eurostat LAU2021 table
(LAU CODE = department Code * 100). Foreign department -> LVZZZ."""
import json
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

deps = json.load(open(rf"{BASE}\raw\lv2022_departments.json", encoding="utf-8-sig"))
res = json.load(open(rf"{BASE}\raw\lv2022_deptresults.json", encoding="utf-8-sig"))

lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2021-NUTS-2021.xlsx",
                    sheet_name="LV")
lau["dep4"] = (lau["LAU CODE"].astype(int) // 100).astype(str).str.zfill(4)
lau_map = dict(zip(lau.dep4, lau["NUTS 3 CODE"]))

# municipality nodes (Type 2), keyed by Id -> NUTS3
muni_nuts = {}
for d in deps:
    if d["Type"] != 2:
        continue
    code = str(d["Code"]).zfill(4)
    if d["Id"] == "arzemes":
        muni_nuts[d["Id"]] = "LVZZZ"
    else:
        nuts = lau_map.get(code)
        assert nuts, (d["Id"], code, d["Name"])
        muni_nuts[d["Id"]] = nuts

resmap = {r["Department"]["Id"]: r for r in res}
rows, regs = [], []
for mid, nuts in muni_nuts.items():
    r = resmap.get(mid)
    if not r:
        print("no results for", mid)
        continue
    regs.append((nuts, r["Department"]["VoterCount"],
                 r["VotedVoterCount"]["Count"], r["ValidEnvelopeCount"]["Count"]))
    for cl in r["CandidateLists"]:
        v = cl["ValidMarkCount"]["Count"]
        if v > 0:
            rows.append((nuts, cl["Name"], v))
regdf = (pd.DataFrame(regs, columns=["nuts_code", "electorate", "totalvote",
                                     "validenv"]).groupby("nuts_code").sum())

out = (pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote"])
       .groupby(["nuts_code", "party_native"], as_index=False).sum())
out["validvote"] = out.groupby("nuts_code").partyvote.transform("sum")
out["electorate"] = out.nuts_code.map(regdf.electorate)
out["totalvote"] = out.nuts_code.map(regdf.totalvote)
out["country"], out["country_code"] = "Latvia", "LV"
out["year"], out["month"] = 2022, 10
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "CVK via data.gov.lv (municipality results)"
out.to_csv(rf"{BASE}\raw\ext_lv2022.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS3,",
      f"votes {out.partyvote.sum():,.0f}")
