"""Slovenia DZ 2022 (DVK archive JSON) -> SI0 national row (EU-NED reports
Slovenia at level 1 only)."""
import json
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
r = json.load(open(rf"{BASE}\raw\si2022_rezultati.json", encoding="utf-8-sig"))
u = json.load(open(rf"{BASE}\raw\si2022_udelezba.json", encoding="utf-8-sig"))

rows = [{"party_abbreviation": p["knaz"], "party_native": p["naz"],
         "partyvote": p["gl"]} for p in r["slovenija"]]
out = pd.DataFrame(rows)
out = out[out.partyvote > 0]
out["nuts_code"] = "SI0"
out["electorate"] = u["slovenija"]["upr"]
out["totalvote"] = r["glas"]
out["validvote"] = r["velj"]
out["country"], out["country_code"] = "Slovenia", "SI"
out["year"], out["month"] = 2022, 4
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "DVK dz2022 archive"
out.to_csv(rf"{BASE}\raw\ext_si2022.csv", index=False)
print("written:", len(out), "parties; votes", out.partyvote.sum(),
      "valid", r["velj"], "cast", r["glas"])
