"""Slovakia NRSR 2023 from SUSR open data (volby.statistics.sk) -> NUTS-3
(kraje; 'Cudzina' postal-abroad -> SKZZZ)."""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
KRAJ = {1: "SK010", 2: "SK021", 3: "SK022", 4: "SK023",
        5: "SK031", 6: "SK032", 7: "SK041", 8: "SK042", 9: "SKZZZ"}

v = pd.read_csv(rf"{BASE}\raw\sk2023_tab03b.csv")
t = pd.read_csv(rf"{BASE}\raw\sk2023_tab02a.csv")

v["nuts_code"] = v["Kód kraja"].map(KRAJ)
t["nuts_code"] = t["Kód kraja"].map(KRAJ)
tot = t.set_index("nuts_code")[["Počet zapísaných voličov",
                                "Počet zúčastnených voličov",
                                "Počet platných hlasov spolu"]]

out = v.rename(columns={"Názov politického subjektu": "party_native",
                        "Počet platných hlasov": "partyvote"})[
    ["nuts_code", "party_native", "partyvote"]]
out = out[out.partyvote > 0]
out["electorate"] = out.nuts_code.map(tot.iloc[:, 0])
out["totalvote"] = out.nuts_code.map(tot.iloc[:, 1])
out["validvote"] = out.nuts_code.map(tot.iloc[:, 2])
out["country"], out["country_code"] = "Slovakia", "SK"
out["year"], out["month"] = 2023, 9
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "SUSR volby.statistics.sk open data"
out.to_csv(rf"{BASE}\raw\ext_sk2023.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "regions,",
      f"votes {out.partyvote.sum():,.0f} vs valid {tot.iloc[:, 2].sum():,.0f}")
