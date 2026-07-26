"""Netherlands TK 1994-2017 at NUTS-3 (replaces EU-NED's NUTS-2 series).

- Results per gemeente: Kiesraad verkiezingsuitslagen.nl CSV exports
  (1994/1998/2002/2003/2006) + data.overheid zips (2010/2012/2017).
- Gemeente -> COROP per election year: CBS OData 'Gebieden in Nederland'
  (year-specific tables back to 1996; 1994 uses the 1996 table with
  merger-union fallback).
- COROP -> NUTS-3 2016: derived empirically (LAU2023 gemeente->NUTS3-2021
  joined to CBS 2006 gemeente->COROP; NL COROP == NUTS-3; backward-recoded
  to 2016 codes by dominant weight).

Output: raw/ext_nl_hist.csv
"""
import json
import subprocess
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
XW = BASE + r"\crosswalks"

CBS_TABLES = {1996: "GIR96", 1998: "7249PCR", 2002: "60049GIN",
              2003: "70174NED", 2006: "71110NED", 2010: "80397ned",
              2012: "81498ned", 2017: "83553NED"}


def fetch_cbs(table):
    url = (f"https://opendata.cbs.nl/ODataApi/odata/{table}/TypedDataSet"
           f"?$format=json")
    j = json.loads(subprocess.run(["curl.exe", "-sL", url],
                                  capture_output=True).stdout
                   .decode("utf-8-sig"))
    df = pd.DataFrame(j["value"])
    # gemeente code column: 4-digit codes, ~n_gemeenten unique; COROP code
    # column: exactly 40 unique values
    code_cols = [c for c in df.columns if c.startswith("Code_")]
    gem_col, cor_col = None, None
    for c in code_cols:
        vals = df[c].astype(str).str.strip()
        nun = vals.nunique()
        if nun == 40 and cor_col is None and c != "Code_1":
            cor_col = c
        if c == "Code_1":
            gem_col = c
    assert gem_col and cor_col, (table, code_cols,
                                 {c: df[c].nunique() for c in code_cols})
    out = pd.DataFrame({
        "gem": df[gem_col].astype(str).str.extract(r"(\d+)")[0].str.zfill(4),
        "corop": df[cor_col].astype(str).str.extract(r"(\d+)")[0]
                 .astype(int)})
    return out.dropna().drop_duplicates("gem").set_index("gem").corop


maps = {y: fetch_cbs(t) for y, t in CBS_TABLES.items()}
for y, m in maps.items():
    print(f"CBS {y}: {len(m)} gemeenten, {m.nunique()} COROPs")

# COROP -> NUTS3-2021 empirically via LAU2023 + CBS2006 overlap
lau = pd.read_excel(rf"{XW}\EU-27-LAU-2023-NUTS-2021.xlsx", sheet_name="NL")
ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
lau["gem"] = (lau["LAU CODE"].astype(str).str.replace("GM", "", regex=False)
              .str.zfill(4))
lau_map = lau.set_index("gem")[ncol]
join = pd.DataFrame({"corop": maps[2017]}).join(
    lau_map.rename("nuts3")).dropna()
cor_nuts = join.groupby("corop").nuts3.agg(lambda s: s.mode()[0])
# COROP 2 (Delfzijl en omgeving): its gemeenten merged into Eemsdelta in 2021
# and are absent from LAU2023 -> fill known NUTS-3 code
cor_nuts.loc[2] = "NL112"
cor_nuts = cor_nuts.sort_index()
assert cor_nuts.nunique() == 40 and len(cor_nuts) == 40, cor_nuts
# backward 2021 -> 2016 dominant
fw = pd.read_csv(rf"{XW}\nuts3_2016_2021.csv")
fw = fw[fw.from_code.str.startswith("NL")].sort_values("weight")
back = dict(zip(fw.drop_duplicates("to_code", keep="last").to_code,
                fw.drop_duplicates("to_code", keep="last").from_code))
cor_nuts16 = cor_nuts.map(lambda c: back.get(c, c))

ELECTIONS = {  # year -> (month, source kind); all from the site export
    # (the data.overheid gemeente zips are incomplete for 2010/2017)
    1994: (5, "site"), 1998: (5, "site"), 2002: (5, "site"),
    2003: (1, "site"), 2006: (11, "site"),
    2010: (6, "site"), 2012: (9, "site"), 2017: (3, "site")}

# municipalities dissolved 1994-96 (before the earliest CBS table) + postal
MANUAL_NUTS3 = {
    "0648": "NL341", "0713": "NL341",             # Aardenburg, Sluis
    "0682": "NL342", "0712": "NL342",             # Kortgene, St. Philipsland
    "0314": "NL310", "0325": "NL310",             # Cothen, Langbroek
    "0761": "NL413", "0752": "NL413", "0768": "NL413",  # Cuijk eSA, Berlicum,
    "0776": "NL413", "0791": "NL413", "0795": "NL413",  # Den Dungen, Esch,
    "0806": "NL413", "0839": "NL414",             # Heesch, Helvoirt, Liempde,
                                                  # Rosmalen (-> Den Bosch)
    "0956": "NL422",                              # Posterholt (M-Limburg)
    "1691": "NL413",                              # St.Anthonis
    "0727": "NL342",                              # Wissenkerke
    "9999": "NLZZZ",                              # Briefstemmen (postal)
}
MAP_YEAR = {1994: 1996, 1998: 1998, 2002: 2002, 2003: 2003, 2006: 2006,
            2010: 2010, 2012: 2012, 2017: 2017}

frames = []
for y, (mo, kind) in ELECTIONS.items():
    if kind == "site":
        d = pd.read_csv(rf"{BASE}\raw\nl{y}_gemeenten.csv", sep=";")
        d = d.rename(columns={"Partij": "party_native",
                              "AantalStemmen": "partyvote"})
        d["gem"] = d.Code.astype(str).str.extract(r"(\d+)")[0].str.zfill(4)
        d["gname"] = d.Gemeente
    else:
        d = pd.read_csv(
            rf"{BASE}\raw\nl{y}_csv\TK{y}_Stemmen_Per_Lijst_Per_Gemeente.csv",
            sep=";")
        d = d.rename(columns={"PartijNaam": "party_native",
                              "AantalStemmen": "partyvote"})
        d["gem"] = d.GemeenteCode.astype(int).astype(str).str.zfill(4)
        d["gname"] = d.GemeenteNaam
    lk = maps[MAP_YEAR[y]]
    d["corop"] = d.gem.map(lk)
    # fallback: any other CBS year (union, oldest first)
    for fy in sorted(maps):
        miss = d.corop.isna()
        if not miss.any():
            break
        d.loc[miss, "corop"] = d.loc[miss, "gem"].map(maps[fy])
    d["nuts_code"] = d.corop.map(cor_nuts16)
    miss = d.nuts_code.isna()
    d.loc[miss, "nuts_code"] = d.loc[miss, "gem"].map(MANUAL_NUTS3)
    un = d[d.nuts_code.isna()].drop_duplicates("gem")
    if len(un):
        print(f"{y}: UNMATCHED gemeenten:",
              un[["gem", "gname"]].values.tolist()[:15])
    d = d.dropna(subset=["nuts_code"])
    g = (d.groupby(["nuts_code", "party_native"], as_index=False)
         .partyvote.sum())
    g = g[g.partyvote > 0]
    g["validvote"] = g.groupby("nuts_code").partyvote.transform("sum")
    g["year"], g["month"] = y, mo
    frames.append(g)
    print(f"{y}: {g.partyvote.sum():,.0f} votes, {g.nuts_code.nunique()} "
          f"NUTS3, {d.gem.nunique()} gemeenten")

out = pd.concat(frames, ignore_index=True)
out["electorate"] = np.nan
out["totalvote"] = np.nan
out["country"], out["country_code"] = "Netherlands", "NL"
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "Kiesraad verkiezingsuitslagen.nl (gemeente CSV)"
out.to_csv(rf"{BASE}\raw\ext_nl_hist.csv", index=False)
print("written:", len(out), "rows")
