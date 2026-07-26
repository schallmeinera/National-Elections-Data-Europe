"""Denmark FV 2022 (DST valg XML) -> NUTS-3.

Storkredse map 1:1 to landsdele (NUTS-3) except Sjaellands Storkreds, which
spans DK021/DK022; its kredse are assigned by name, and the one kreds that
crosses the boundary (Faxe = Faxe kommune DK022 + Stevns kommune DK021) is
split via its polling-district files."""
import re
import subprocess
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
IDX = "https://www.dst.dk/valg/Valg1968094/xml/fintal.xml"

STORKREDS_NUTS3 = {"10": "DK011", "11": "DK012", "12": "DK013", "13": "DK014",
                   "15": "DK031", "16": "DK032", "17": "DK042", "18": "DK041",
                   "19": "DK050"}  # 14 = Sjaelland, handled below
SJ_KREDS = {  # kreds name fragment -> NUTS3
    "Lolland": "DK022", "Guldborgsund": "DK022", "Vordingborg": "DK022",
    "Næstved": "DK022", "Holbæk": "DK022", "Kalundborg": "DK022",
    "Ringsted": "DK022", "Slagelse": "DK022",
    "Køge": "DK021", "Greve": "DK021", "Roskilde": "DK021",
    # Faxe kreds = Faxe + Stevns kommuner; per Eurostat LAU both are DK022
    "Faxe": "DK022"}


def fetch(url):
    return subprocess.run(["curl.exe", "-sL", url],
                          capture_output=True).stdout


def parse_result(xml_bytes):
    root = ET.fromstring(xml_bytes)
    elig = int(root.findtext("Stemmeberettigede") or 0)
    votes = {p.get("Navn"): int(p.get("StemmerAntal"))
             for p in root.find("Stemmer")
             if p.tag == "Parti" and p.get("StemmerAntal") is not None}
    return elig, votes


# sanity check the Sjaelland kreds assignments against LAU (kreds names are
# named after their anchor municipality)
lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2023-NUTS-2021.xlsx",
                    sheet_name="DK")
ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
lchk = lau.set_index("LAU NAME LATIN")[ncol]
for nm, nuts in SJ_KREDS.items():
    got = lchk.get(nm)
    assert got is None or got == nuts, (nm, nuts, got)

idx = fetch(IDX).decode("utf8")
kredse = re.findall(r'<Opstillingskreds[^>]*opstillingskreds_id="(\d+)"'
                    r'[^>]*storkreds_id="(\d+)"[^>]*filnavn="([^"]+)"'
                    r'[^>]*>([^<]+)', idx)
print("kredse:", len(kredse))

rows, regs = [], []
for kid, sid, url, name in kredse:
    name = name.split(". ", 1)[-1].strip()
    if sid in STORKREDS_NUTS3:
        nuts = STORKREDS_NUTS3[sid]
    else:
        frag = [k for k in SJ_KREDS if k in name]
        assert frag, (sid, name)
        nuts = SJ_KREDS[frag[0]]
    elig, votes = parse_result(fetch(url))
    for p, v in votes.items():
        rows.append((nuts, p, v))
    regs.append((nuts, elig))

out = (pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote"])
       .groupby(["nuts_code", "party_native"], as_index=False).sum())
out = out[out.partyvote > 0]
reg = (pd.DataFrame(regs, columns=["nuts_code", "electorate"])
       .groupby("nuts_code").electorate.sum())
out["electorate"] = out.nuts_code.map(reg)
out["validvote"] = out.groupby("nuts_code").partyvote.transform("sum")
out["totalvote"] = np.nan
out["country"], out["country_code"] = "Denmark", "DK"
out["year"], out["month"] = 2022, 11
out["party_abbreviation"] = out.party_native.str.extract(r"^([A-ZÆØÅ])\.")
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "DST valg XML (Valg1968094)"
out.to_csv(rf"{BASE}\raw\ext_dk2022.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS3,",
      f"votes {out.partyvote.sum():,.0f}")
