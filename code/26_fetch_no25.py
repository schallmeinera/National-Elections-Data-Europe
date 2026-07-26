"""Norway Storting 2025 (valgresultat.no API) -> NUTS-3 2016 (19 old-fylke
electoral districts, same mapping as EU-NED/CLEA; Trondelag pair -> NO060 via
the pipeline's legacy fix)."""
import json
import subprocess
import unicodedata
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

ned = pd.read_csv(r"D:\EU LFS\DATA\03_Elections\EU_NED\eu_ned_joint.csv")
no = ned[(ned.country_code == "NO") & (ned.type == "Parliament")]
no = no[no.year == no.year.max()][["nuts2016", "regionname"]].drop_duplicates()
TR = str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "å": "a",
                    "Å": "A"})


def norm(s):
    s = str(s).translate(TR)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


lk = {norm(r): c for c, r in no.values}
FIX = {"troms romsa": "troms", "finnmark finnmarku": "finnmark"}


def get(url):
    return json.loads(subprocess.run(["curl.exe", "-sL", url],
                                     capture_output=True).stdout)


nat = get("https://valgresultat.no/api/2025/st")
rows, regs = [], []
import time
for rel in nat["_links"]["related"]:
    for attempt in range(4):
        j = get("https://valgresultat.no/api" + rel["href"])
        if "stemmer" in j:
            break
        time.sleep(2)
    else:
        raise RuntimeError((rel["href"], list(j)))
    name = rel["navn"]
    k = norm(name)
    nuts = lk.get(k) or lk.get(FIX.get(k, ""))
    assert nuts, name
    regs.append((nuts, j.get("antallsb"), j["stemmer"]["total"]))
    for p in j["partier"]:
        # partikategori 0 = 'Andre' rollup (duplicates the small parties);
        # 'BLANKE' = blank ballots, not a party
        if p["id"]["partikategori"] == 0 or p["id"]["partikode"] == "BLANKE":
            continue
        v = p["stemmer"]["resultat"]["antall"]["total"]
        if v and v > 0:
            rows.append((nuts, p["id"]["navn"], p["id"]["partikode"], v))

out = (pd.DataFrame(rows, columns=["nuts_code", "party_native",
                                   "party_abbreviation", "partyvote"])
       .groupby(["nuts_code", "party_native", "party_abbreviation"],
                as_index=False).sum())
reg = pd.DataFrame(regs, columns=["nuts_code", "electorate", "totalvote"])
reg = reg.groupby("nuts_code").sum(min_count=1)
out["electorate"] = out.nuts_code.map(reg.electorate)
out["totalvote"] = out.nuts_code.map(reg.totalvote)
out["validvote"] = out.groupby("nuts_code").partyvote.transform("sum")
out["country"], out["country_code"] = "Norway", "NO"
out["year"], out["month"] = 2025, 9
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "valgresultat.no API"
out.to_csv(rf"{BASE}\raw\ext_no2025.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "districts,",
      f"votes {out.partyvote.sum():,.0f}")
