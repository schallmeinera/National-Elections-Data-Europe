"""Estonia RK 2023 (opendata.valimised.ee county-level XML) -> NUTS-3.
Sub-units = 15 maakonnad + 8 Tallinn linnaosad; each maps into one of the 5
Estonian NUTS-3 regions. Residual vs national total (foreign e-votes already
distributed; anything left) -> checked."""
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
NS = {"n": "https://opendata.valimised.ee/schemas/detailed-voting-result/"
          "greater-municipality/rk/v1/"}

# EHAK county / Tallinn-linnaosa -> NUTS-3 (2016)
EHAK_NUTS3 = {
    "0037": "EE001",  # Harju
    "0039": "EE004",  # Hiiu
    "0045": "EE007",  # Ida-Viru (Kirde-Eesti)
    "0050": "EE008",  # Jogeva
    "0052": "EE006",  # Jarva (Kesk-Eesti)
    "0056": "EE004",  # Laane
    "0060": "EE006",  # Laane-Viru
    "0064": "EE008",  # Polva
    "0068": "EE004",  # Parnu
    "0071": "EE006",  # Rapla
    "0074": "EE004",  # Saare
    "0079": "EE008",  # Tartu
    "0081": "EE008",  # Valga
    "0084": "EE008",  # Viljandi
    "0087": "EE008",  # Voru
    # Tallinn linnaosad (all Harju -> EE001)
    "0176": "EE001", "0298": "EE001", "0339": "EE001", "0387": "EE001",
    "0482": "EE001", "0524": "EE001", "0596": "EE001", "0614": "EE001",
    "0793": "EE008",  # Tartu linn (listed separately from Tartu maakond)
}

codes16 = set(pd.read_csv(rf"{BASE}\crosswalks\nuts_codes_2016.csv").code)
assert set(EHAK_NUTS3.values()) <= codes16

tree = ET.parse(rf"{BASE}\raw\ee2023_counties.xml")
root = tree.getroot()

def party_totals(node):
    out = {}
    for p in node.findall("n:votesDistributionByParties/n:party", NS):
        pname = p.find("n:partyName", NS).text
        tot = p.find(".//n:totalRow/n:votesDistributionRow/"
                     "n:votesDistributionCell/n:value", NS)
        if tot is not None:
            out[pname] = out.get(pname, 0) + int(tot.text)
    return out


rows = []
seen_ehak = set()
for dist in root.findall(".//n:district", NS):
    dtot = party_totals(dist)
    csum = {}
    for cty in dist.findall("n:counties/n:county", NS):
        ehak = cty.find("n:ehakCode", NS).text
        name = cty.find("n:countyName", NS).text
        nuts = EHAK_NUTS3.get(ehak)
        if nuts is None:
            print("UNMAPPED sub-unit:", ehak, name)
            continue
        seen_ehak.add(ehak)
        for pname, v in party_totals(cty).items():
            rows.append((nuts, pname, v))
            csum[pname] = csum.get(pname, 0) + v
    # district total minus domestic sub-units = votes from abroad -> EEZZZ
    for pname, v in dtot.items():
        res = v - csum.get(pname, 0)
        if res > 0:
            rows.append(("EEZZZ", pname, res))

out = (pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote"])
       .groupby(["nuts_code", "party_native"], as_index=False).sum())
out = out[out.partyvote > 0]

# national check
nat_valid = None
for sr in root.findall(".//n:overallStatistics/n:statisticsRow", NS):
    if sr.find("n:name", NS).text == "Kehtivaid sedeleid":
        nat_valid = int(sr.find("n:value", NS).text)
        break
print(f"sub-units seen: {len(seen_ehak)} | summed votes "
      f"{out.partyvote.sum():,} vs national valid {nat_valid:,}")

out["validvote"] = out.groupby("nuts_code").partyvote.transform("sum")
out["electorate"] = np.nan
out["totalvote"] = np.nan
out["country"], out["country_code"] = "Estonia", "EE"
out["year"], out["month"] = 2023, 3
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "opendata.valimised.ee RK_2023"
out.to_csv(rf"{BASE}\raw\ext_ee2023.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS3")
