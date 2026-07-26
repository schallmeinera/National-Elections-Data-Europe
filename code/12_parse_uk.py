"""UK 2024 general election (HoC Library CBP-10009, via Wayback) -> NUTS-1.
ONS region IDs map 1:1 to former-GOR NUTS-1 units. UK exists only in the 2016
and 2021 vintages (dropped from NUTS 2024)."""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
REG_NUTS1 = {"E12000001": "UKC", "E12000002": "UKD", "E12000003": "UKE",
             "E12000004": "UKF", "E12000005": "UKG", "E12000006": "UKH",
             "E12000007": "UKI", "E12000008": "UKJ", "E12000009": "UKK",
             "W92000004": "UKL", "S92000003": "UKM", "N92000002": "UKN"}
PARTIES = {"Con": "Conservative", "Lab": "Labour", "LD": "Liberal Democrats",
           "RUK": "Reform UK", "Green": "Green", "SNP": "SNP",
           "PC": "Plaid Cymru", "DUP": "DUP", "SF": "Sinn Féin",
           "SDLP": "SDLP", "UUP": "UUP", "APNI": "Alliance",
           "All other candidates": "other parties"}

d = pd.read_csv(rf"{BASE}\raw\uk2024_hoc.csv")
d["nuts_code"] = d["ONS region ID"].map(REG_NUTS1)
assert d.nuts_code.notna().all(), d[d.nuts_code.isna()]["Region name"].unique()

agg = d.groupby("nuts_code").agg(
    electorate=("Electorate", "sum"), validvote=("Valid votes", "sum"),
    invalid=("Invalid votes", "sum"),
    **{c: (c, "sum") for c in PARTIES})
agg["totalvote"] = agg.validvote + agg.invalid

long = (agg.reset_index().melt(
    id_vars=["nuts_code", "electorate", "totalvote", "validvote"],
    value_vars=list(PARTIES), var_name="abbr", value_name="partyvote"))
long = long[long.partyvote > 0]
long["party_abbreviation"] = long.abbr
long["party_english"] = long.abbr.map(PARTIES)
long["party_native"] = long.party_english

out = long.drop(columns="abbr")
out["country"], out["country_code"] = "United Kingdom", "GB"
out["year"], out["month"] = 2024, 7
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "House of Commons Library CBP-10009"
out.to_csv(rf"{BASE}\raw\ext_uk2024.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS1,",
      f"valid {agg.validvote.sum():,.0f}")
