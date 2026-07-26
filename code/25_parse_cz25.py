"""Czechia PS 2025 (volby.cz results XML) -> NUTS-3 (kraje).
The 14 electoral kraje = NUTS-3 (CIS_KRAJ 1-14 in official order)."""
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
NS = {"v": "http://www.volby.cz/ps/"}
# CIS_KRAJ (volebni kraj) -> NUTS-3 2016
KRAJ_NUTS = {1: "CZ010", 2: "CZ020", 3: "CZ031", 4: "CZ032", 5: "CZ041",
             6: "CZ042", 7: "CZ051", 8: "CZ052", 9: "CZ053", 10: "CZ063",
             11: "CZ064", 12: "CZ071", 13: "CZ072", 14: "CZ080"}

t = ET.parse(rf"{BASE}\raw\cz2025_vysledky.xml")
root = t.getroot()

# party number -> name from the national section
pnames = {}
for s in root.findall(".//v:CR/v:STRANA", NS):
    pnames[s.get("KSTRANA")] = s.get("NAZ_STR")

rows, regs = [], []
for k in root.findall("v:KRAJ", NS):
    cis = int(k.get("CIS_KRAJ"))
    nuts = KRAJ_NUTS[cis]
    ucast = k.find("v:UCAST", NS)
    regs.append((nuts, k.get("NAZ_KRAJ"), int(ucast.get("ZAPSANI_VOLICI")),
                 int(ucast.get("VYDANE_OBALKY")),
                 int(ucast.get("PLATNE_HLASY"))))
    for s in k.findall("v:STRANA", NS):
        hc = s.find("v:HODNOTY_STRANA", NS)
        v = int(hc.get("HLASY"))
        if v > 0:
            rows.append((nuts, pnames.get(s.get("KSTRANA"),
                                          s.get("NAZ_STR") or s.get("KSTRANA")),
                         v))

reg = pd.DataFrame(regs, columns=["nuts_code", "name", "electorate",
                                  "totalvote", "validvote"]).set_index("nuts_code")
out = (pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote"])
       .groupby(["nuts_code", "party_native"], as_index=False).sum())
for c in ["electorate", "totalvote", "validvote"]:
    out[c] = out.nuts_code.map(reg[c])
out["country"], out["country_code"] = "Czech Republic", "CZ"
out["year"], out["month"] = 2025, 10
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "volby.cz PS2025 open data"
out.to_csv(rf"{BASE}\raw\ext_cz2025.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "kraje,",
      f"votes {out.partyvote.sum():,.0f} vs valid {reg.validvote.sum():,.0f}")
