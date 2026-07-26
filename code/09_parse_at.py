"""Austria NRW 2024 (National Council) from the on-disk Gemeinde dataset,
aggregated to NUTS-3 via the Eurostat LAU2024-NUTS2024 correspondence
(Austrian NUTS-3 codes are identical across 2016/2021/2024 vintages)."""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
AT = (r"D:\EU LFS\DATA\03_Elections\Municipal\austria\output"
      r"\at_dataset_gemeinde.csv")

d = pd.read_csv(AT)
d = d[d.year == 2024].copy()
print("2024 Gemeinden:", len(d), "| valid votes:", d.valid.sum())

lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2024-NUTS-2024.xlsx",
                    sheet_name="AT")
lau["gkz"] = lau["LAU CODE"].astype(int)
lk = lau.set_index("gkz")["NUTS3"]

d["gkz"] = d.harm_id.astype(int)
d["nuts3"] = d.gkz.map(lk)
un = d[d.nuts3.isna()]
print("unmatched Gemeinden:", len(un), un.gkz.tolist()[:20])
# Vienna: municipal code 90001 vs LAU district codes 9xxxx
if len(un):
    vienna = un[un.gkz // 10000 == 9]
    d.loc[d.gkz.isin(vienna.gkz), "nuts3"] = "AT130"
    un = d[d.nuts3.isna()]
    print("after Vienna fix:", len(un), un.gkz.tolist()[:20])
# residual harmonised codes: infer NUTS3 from Bezirk prefix (first 3 digits)
if d.nuts3.isna().any():
    bez = (d.dropna(subset=["nuts3"]).assign(bez=lambda x: x.gkz // 100)
           .groupby("bez").nuts3.agg(lambda s: s.mode()[0]))
    miss = d.nuts3.isna()
    d.loc[miss, "nuts3"] = (d.loc[miss, "gkz"] // 100).map(bez)
    print("after Bezirk-prefix fix:", d.nuts3.isna().sum(), "unmatched")
assert d.nuts3.notna().all()

PARTIES = {"SPOE": "SPÖ", "OEVP": "ÖVP", "FPOE": "FPÖ", "GRUENE": "GRÜNE",
           "NEOS": "NEOS", "KPOE": "KPÖ", "BIER": "BIER", "MFG": "MFG",
           "BZOE": "BZÖ", "LIF": "LIF", "TEAM_STRONACH": "Team Stronach",
           "PILZ_JETZT": "PILZ/JETZT", "OTHER": "other parties"}
present = [c for c in PARTIES if c in d.columns and d[c].notna().any()
           and d[c].sum() > 0]
agg = d.groupby("nuts3").agg(electorate=("electorate", "sum"),
                             totalvote=("cast", "sum"),
                             validvote=("valid", "sum"),
                             **{c: (c, "sum") for c in present})
long = (agg.reset_index().melt(
    id_vars=["nuts3", "electorate", "totalvote", "validvote"],
    value_vars=present, var_name="pcol", value_name="partyvote"))
long = long[long.partyvote > 0]
long["party_abbreviation"] = long.pcol.map(PARTIES)
long["party_native"] = long.party_abbreviation

out = long.rename(columns={"nuts3": "nuts_code"}).drop(columns="pcol")
out["country"], out["country_code"] = "Austria", "AT"
out["year"], out["month"] = 2024, 9
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "AT Gemeinde dataset (eu-municipal-elections) via LAU2024"
out.to_csv(rf"{BASE}\raw\at_official_nuts3.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS3")
print("party totals:\n",
      out.groupby("party_abbreviation").partyvote.sum().sort_values(
          ascending=False).head(8).to_string())
print("share check: FPÖ",
      round(out[out.party_abbreviation == "FPÖ"].partyvote.sum()
            / out.groupby("nuts_code").validvote.first().sum() * 100, 2), "%")
