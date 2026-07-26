"""Germany 2021 + 2025 at NUTS-3 from federal_cty_harm.rds (Kreis-level
Zweitstimmen shares x valid votes; boundary-harmonized, so the 400 counties
map cleanly to NUTS-3 via the LAU table). Replaces the Land-level kerg rows
for those two elections (historical 1990-2017 stay EU-NED NUTS-3)."""
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

d = pd.read_csv(rf"{BASE}\raw\de_federal_cty_harm.csv",
                dtype={"county_code": str, "state": str}, low_memory=False)
d = d[d.election_year.isin([2021, 2025])].copy()
d["county_code"] = d.county_code.str.zfill(5)

DERIVED = ["total_votes", "cdu_csu", "far_right", "far_left",
           "far_left_w_linke", "nichtwaehler"]
META = ["county_code", "election_year", "state", "eligible_voters",
        "number_voters", "valid_votes", "invalid_votes", "turnout",
        "election_date", "area", "population",
        "flag_unsuccessful_naive_merge"]
pcols = [c for c in d.columns if c not in META + DERIVED]

NAMES = {"cdu": "CDU", "csu": "CSU", "spd": "SPD", "gruene": "GRÜNE",
         "fdp": "FDP", "linke_pds": "DIE LINKE / PDS", "afd": "AfD",
         "npd": "NPD", "rep": "REP", "dvu": "DVU", "piraten": "PIRATEN",
         "freie_waehler": "FREIE WÄHLER", "tierschutz": "Tierschutzpartei",
         "die_partei": "Die PARTEI", "oedp": "ÖDP", "volt": "Volt",
         "bsw": "BSW", "die_basis": "dieBasis", "ssw": "SSW",
         "familie": "FAMILIE", "bp": "Bayernpartei", "mlpd": "MLPD",
         "werteunion": "WerteUnion", "buendnis_deutschland":
         "BÜNDNIS DEUTSCHLAND", "mera25": "MERA25", "zentrum": "ZENTRUM",
         "team_todenhoefer": "Team Todenhöfer",
         "gesundheitsforschung": "Gesundheitsforschung",
         "menschliche_welt": "Menschliche Welt",
         "die_humanisten": "Die Humanisten", "iii_weg": "III. Weg",
         "die_rechte": "Die Rechte", "buendnis_c": "Bündnis C",
         "graue": "Graue Panther", "dkp": "DKP", "sgp": "SGP",
         "lkr": "LKR", "pdv": "PdV", "bge": "BGE",
         "v_partei3": "V-Partei³", "du": "DiB",
         "verjuengungsforschung": "Partei für Verjüngungsforschung"}

# Kreis -> NUTS-3 via LAU (gemeinde AGS first 5 digits; unique per Kreis)
lau = pd.read_excel(rf"{BASE}\crosswalks\EU-27-LAU-2023-NUTS-2021.xlsx",
                    sheet_name="DE")
ncol = "NUTS 3 CODE" if "NUTS 3 CODE" in lau.columns else "NUTS3"
lau = lau.dropna(subset=[ncol, "LAU CODE"])
lau["kreis"] = (lau["LAU CODE"].astype("int64").astype(str)
                .str.zfill(8).str[:5])
amb = lau.groupby("kreis")[ncol].nunique()
assert (amb == 1).all(), amb[amb > 1]
lk = lau.drop_duplicates("kreis").set_index("kreis")[ncol]

d["nuts_code"] = d.county_code.map(lk)
un = d[d.nuts_code.isna()].county_code.unique()
assert not len(un), un[:10]
# DE NUTS-3 identical in 2016 and 2021 vintages -> codes usable as input

long = d.melt(id_vars=["nuts_code", "election_year", "eligible_voters",
                       "number_voters", "valid_votes"],
              value_vars=pcols, var_name="pcol", value_name="share")
long["partyvote"] = (long.share * long.valid_votes).round(1)
long = long[long.partyvote > 0]
long["party_native"] = long.pcol.map(NAMES).fillna(
    long.pcol.str.replace("_", " ").str.upper())

g = (long.groupby(["nuts_code", "election_year", "party_native"],
                  as_index=False)
     .agg(partyvote=("partyvote", "sum"),
          electorate=("eligible_voters", "first"),
          totalvote=("number_voters", "first"),
          validvote=("valid_votes", "first")))
g["year"] = g.election_year
g["month"] = g.year.map({2021: 9, 2025: 2})
g = g.drop(columns="election_year")
g["country"], g["country_code"] = "Germany", "DE"
g["party_abbreviation"] = np.nan
g["party_english"] = np.nan
g["partyfacts_id"] = np.nan
g["regionname"] = np.nan
g["source"] = "federal_cty_harm (Kreis-harmonized, Mating Markets package)"
g.to_csv(rf"{BASE}\raw\ext_de_nuts3.csv", index=False)
for y in (2021, 2025):
    s = g[g.year == y]
    print(y, ":", len(s), "rows,", s.nuts_code.nunique(), "NUTS3,",
          f"votes {s.partyvote.sum():,.0f}")
