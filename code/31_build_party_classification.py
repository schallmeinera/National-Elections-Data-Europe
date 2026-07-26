"""Build party-family classification for every distinct party in the database.

Taxonomy: CHES 11-family labels (Radical right, Conservative, Liberal,
Christian democratic, Social democratic, Radical left, Green, Regionalist,
No family, Confessional/agrarian/other, Agrarian/center)
+ PopuList 4.0 dummies (farright, farleft, populist, eurosceptic).

Sources (priority order for family):
 1. EP NUTS-3 panel (manually corrected assignments, partyfacts-keyed)
 2. ESS classified build (family_ches_corrected, partyfacts-keyed)
 3. CHES trend file via Partyfacts external links
 4. PopuList-implied (farright -> Radical right, farleft -> Radical left)
 5. Manual table (hand-coded, mostly recent parties)

Partyfacts ids for extension parties are recovered by name matching against
Partyfacts core + PopuList + CHES names within country.

Output: crosswalks/party_classification.csv (one row per distinct party
identity tuple as it appears in the output tables).
"""
import re
import unicodedata
import numpy as np
import pandas as pd

BASE = r"D:\EU LFS\eu-parliamentary-elections"
DATA = r"D:\EU LFS\DATA"

ISO3 = {"AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
        "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "ES": "ESP",
        "FI": "FIN", "FR": "FRA", "GB": "GBR", "GR": "GRC", "HR": "HRV",
        "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU",
        "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR",
        "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN",
        "SK": "SVK", "TR": "TUR"}
CNAME = {"AT": "Austria", "BE": "Belgium", "BG": "Bulgaria",
         "CH": "Switzerland", "CY": "Cyprus", "CZ": "Czech Republic",
         "DE": "Germany", "DK": "Denmark", "EE": "Estonia", "ES": "Spain",
         "FI": "Finland", "FR": "France", "GB": "United Kingdom",
         "GR": "Greece", "HR": "Croatia", "HU": "Hungary", "IE": "Ireland",
         "IS": "Iceland", "IT": "Italy", "LT": "Lithuania",
         "LU": "Luxembourg", "LV": "Latvia", "MT": "Malta",
         "NL": "Netherlands", "NO": "Norway", "PL": "Poland",
         "PT": "Portugal", "RO": "Romania", "SE": "Sweden", "SI": "Slovenia",
         "SK": "Slovakia", "TR": "Turkey"}


def norm(s):
    if pd.isna(s):
        return ""
    s = str(s).translate(str.maketrans({"ø": "o", "Ø": "O", "æ": "ae",
                                        "Æ": "AE", "ß": "ss", "ł": "l",
                                        "Ł": "L", "đ": "d", "ð": "d",
                                        "þ": "th", "ı": "i"}))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("’", "'").replace("–", "-")
    s = re.sub(r"[^a-z0-9а-яёα-ω]+", " ", s).strip()
    return s


# ---------------- 1. distinct parties in the database ----------------
f = pd.read_parquet(rf"{BASE}\output\national_finest_2016.parquet")
PIDC = ["country_code", "party_abbreviation", "party_english", "party_native",
        "partyfacts_id"]
nat = f.groupby(["country_code", "year", "month"], dropna=False).partyvote.sum()
f = f.join(nat.rename("nat_total"), on=["country_code", "year", "month"])
parties = (f.groupby(PIDC, dropna=False)
           .agg(votes=("partyvote", "sum"),
                max_share=("partyvote", "size"),
                last_year=("year", "max"),
                share=("partyvote", lambda s: np.nan))
           .reset_index())
sh = (f.assign(sh=f.partyvote / f.nat_total)
      .groupby(PIDC, dropna=False).sh.max().reset_index(name="max_nat_share"))
parties = parties.drop(columns=["max_share", "share"]).merge(
    sh, on=PIDC, how="left")
parties["pname"] = parties.party_native.where(
    parties.party_native.notna(),
    parties.party_english.where(parties.party_english.notna(),
                                parties.party_abbreviation))
parties["nname"] = parties.pname.map(norm)
parties["nabbr"] = parties.party_abbreviation.map(norm)
parties["neng"] = parties.party_english.map(norm)
print("distinct parties:", len(parties),
      "| with partyfacts_id:", parties.partyfacts_id.notna().sum())

# ---------------- 2. reference lookups ----------------
# EP panel: partyfacts -> family (modal), + far-right flag
ep = pd.read_csv(rf"{DATA}\03_Elections\EP_NUTS3_Panel"
                 r"\ep_nuts3_party_family_panel.csv",
                 usecols=["partyfacts_id", "party_family"], low_memory=False)
ep = ep.dropna()
ep_fam = (ep.groupby("partyfacts_id").party_family
          .agg(lambda s: s.mode()[0]))

# ESS classified build: partyfacts -> corrected CHES family
cb = pd.read_csv(rf"{DATA}\04_Party_Classification\ESS_Party_Classified"
                 r"\ches_family_codebook.csv")
fam_label = dict(zip(cb.family_ches, cb.family_label))
ess = pd.read_csv(rf"{DATA}\04_Party_Classification\ESS_Party_Classified"
                  r"\full_ess_party_classified.csv.gz",
                  usecols=["partyfacts_final", "family_ches_corrected"])
ess = ess.dropna()
ess_fam = (ess.groupby("partyfacts_final").family_ches_corrected
           .agg(lambda s: s.mode()[0]).map(fam_label))

# CHES trend via partyfacts external links
ext = pd.read_csv(rf"{BASE}\raw\partyfacts_external.csv", low_memory=False)
ches_link = ext[(ext.dataset_key == "ches") & ext.partyfacts_id.notna()]
ches_link = ches_link[["dataset_party_id", "partyfacts_id"]].copy()
ches_link["ches_id"] = pd.to_numeric(ches_link.dataset_party_id,
                                     errors="coerce")
ches = pd.read_csv(rf"{DATA}\04_Party_Classification\CHES"
                   r"\1999-2024_CHES_dataset_means.csv",
                   usecols=["party_id", "year", "family"])
ches = ches.dropna(subset=["family"]).sort_values("year")
ches_fam_by_id = ches.groupby("party_id").family.last().map(
    lambda x: fam_label.get(int(x)))
ches_link["family"] = ches_link.ches_id.map(ches_fam_by_id)
ches_fam = (ches_link.dropna(subset=["family"])
            .groupby("partyfacts_id").family.first())

# PopuList 4.0
pop = pd.read_csv(rf"{DATA}\04_Party_Classification\PopuList"
                  r"\The PopuList 4.0.csv", sep=";", encoding="utf-8-sig")
pop.columns = [c.replace("﻿", "") for c in pop.columns]
pop["nn"] = pop.party_name.map(norm)
pop["nne"] = pop.party_name_english.map(norm)
pop["nns"] = pop.party_name_short.map(norm)
FLAG_COLS = []
for fl in ["populist", "farright", "farleft", "eurosceptic"]:
    FLAG_COLS += [fl, fl + "_start", fl + "_end"]
pop_pf = (pop.dropna(subset=["partyfacts_id"])
          .drop_duplicates("partyfacts_id").set_index("partyfacts_id")
          [FLAG_COLS])

# Partyfacts core for name matching
core = pd.read_csv(rf"{BASE}\raw\partyfacts_core.csv", low_memory=False)
core = core[core.country.isin(set(ISO3.values()))]
core["nn"] = core.name.map(norm)
core["nne"] = core.name_english.map(norm)
core["nns"] = core.name_short.map(norm)
core_share = core.set_index("partyfacts_id")["share"]

# ESS partyfacts crosswalk: extra name variants per country
essx = pd.read_csv(rf"{DATA}\04_Party_Classification\ESS_Party_Classified"
                   r"\ess_partyfacts_crosswalk.csv")
essx["nn"] = essx.party.map(norm)
essx = essx.dropna(subset=["partyfacts_id"])

# the database's own EU-NED rows: 3 name variants per known partyfacts_id
self_pool = parties[parties.partyfacts_id.notna()]

# ---------------- 3. recover partyfacts ids by name ----------------
def build_pool(cc):
    iso3, cname = ISO3[cc], CNAME[cc]
    pools = []
    c = core[core.country == iso3]
    for col in ["nn", "nne", "nns"]:
        pools.append(c[[col, "partyfacts_id"]].rename(columns={col: "key"}))
    pl = pop[pop.country_name == cname]
    for col in ["nn", "nne", "nns"]:
        pools.append(pl[[col, "partyfacts_id"]].rename(columns={col: "key"}))
    ex = essx[essx.cntry == cc]
    pools.append(ex[["nn", "partyfacts_id"]].rename(columns={"nn": "key"}))
    sp = self_pool[self_pool.country_code == cc]
    for col in ["nname", "neng", "nabbr"]:
        pools.append(sp[[col, "partyfacts_id"]].rename(columns={col: "key"}))
    pool = pd.concat(pools, ignore_index=True).dropna()
    pool = pool[pool.key != ""]
    # resolve ambiguous keys by the core vote share of the candidate ids
    pool["sh"] = pool.partyfacts_id.map(core_share).fillna(0)
    pool = (pool.sort_values("sh").drop_duplicates("key", keep="last"))
    return pool.set_index("key").partyfacts_id


matched = 0
for cc in parties.country_code.unique():
    pool = build_pool(cc)
    m = parties.country_code == cc
    for keycol in ["nname", "neng", "nabbr"]:
        need = m & parties.partyfacts_id.isna() & (parties[keycol] != "")
        hit = parties.loc[need, keycol].map(pool)
        parties.loc[need, "partyfacts_id"] = hit
        matched += hit.notna().sum()
print("partyfacts ids recovered by name:", matched,
      "| now with id:", parties.partyfacts_id.notna().sum())

# containment fallback: unique pool key that contains / is contained in the
# party name (catches suffix variants and coalition supersets); min length 8
cont = 0
for cc in parties.country_code.unique():
    pool = build_pool(cc)
    keys = [k for k in pool.index if len(k) >= 8]
    m = (parties.country_code == cc) & parties.partyfacts_id.isna()
    for i in parties[m].index:
        nm = parties.at[i, "nname"]
        if len(nm) < 8:
            continue
        hits = {pool[k] for k in keys if k in nm or nm in k}
        if len(hits) == 1:
            parties.at[i, "partyfacts_id"] = hits.pop()
            cont += 1
print("containment matches:", cont,
      "| now with id:", parties.partyfacts_id.notna().sum())

# ---------------- 4. assign family + flags ----------------
parties["party_family"] = pd.Series(np.nan, index=parties.index, dtype=object)
parties["family_source"] = pd.Series(np.nan, index=parties.index, dtype=object)
pf = parties.partyfacts_id
for src, lk in [("ep_panel", ep_fam), ("ess_build", ess_fam),
                ("ches_link", ches_fam)]:
    need = parties.party_family.isna() & pf.notna()
    got = pf[need].map(lk)
    parties.loc[need, "party_family"] = got
    parties.loc[need & got.reindex(parties.index).notna(),
                "family_source"] = src

for flag in ["populist", "farright", "farleft", "eurosceptic"]:
    parties[flag] = pf.map(pop_pf[flag])
    parties[flag] = parties[flag].map(
        {True: 1, False: 0, "TRUE": 1, "FALSE": 0, 1: 1, 0: 0})
    parties[flag + "_start"] = pf.map(pop_pf[flag + "_start"])
    parties[flag + "_end"] = pf.map(pop_pf[flag + "_end"])

# PopuList-implied family where none yet
need = parties.party_family.isna() & (parties.farright == 1)
parties.loc[need, ["party_family", "family_source"]] = ["Radical right",
                                                        "populist_implied"]
need = parties.party_family.isna() & (parties.farleft == 1)
parties.loc[need, ["party_family", "family_source"]] = ["Radical left",
                                                        "populist_implied"]

# ---------------- 5. generic catch-alls + manual table ----------------
generic = parties.pname.astype(str).str.match(
    r"^\s*(others?|other parties|andre2?|autres|overige|übrige|"
    r"independents?|independent candidates|ind|alliance|blancs|"
    r"extra-regio)\s*$", case=False)
need = generic & parties.party_family.isna()
parties.loc[need, ["party_family", "family_source"]] = ["No family",
                                                        "generic"]

from party_manual import MANUAL  # (cc, regex, family, populist_key)

FLAGS = ["populist", "farright", "farleft", "eurosceptic"]
pop["nshort"] = pop.party_name_short.astype(str)
for cc, pat, fam, popkey in MANUAL:
    m = (parties.country_code == cc) & parties.pname.astype(str).str.contains(
        pat, case=False, regex=True)
    if not m.any():
        print("MANUAL no match:", cc, pat)
        continue
    need = m & parties.party_family.isna()
    parties.loc[need, ["party_family", "family_source"]] = [fam, "manual"]
    if popkey is not None:
        pr = pop[(pop.country_name == CNAME[cc])
                 & ((pop.nshort == popkey)
                    | (pop.party_name_english == popkey)
                    | (pop.party_name == popkey))]
        if len(pr) == 1:
            fill = m & parties[FLAGS[0]].isna()
            for fl in FLAGS:
                parties.loc[fill, fl] = int(pr.iloc[0][fl])
                parties.loc[fill, fl + "_start"] = pr.iloc[0][fl + "_start"]
                parties.loc[fill, fl + "_end"] = pr.iloc[0][fl + "_end"]
            pfid = pr.iloc[0]["partyfacts_id"]
            if pd.notna(pfid):
                parties.loc[m & parties.partyfacts_id.isna(),
                            "partyfacts_id"] = pfid
        else:
            print("MANUAL popkey ambiguous/missing:", cc, popkey, len(pr))

# explicit overrides (applied unconditionally)
OVERRIDE = [("GR", r"NIKI", "Radical right")]
for cc, pat, fam in OVERRIDE:
    m = (parties.country_code == cc) & parties.pname.astype(str).str.contains(
        pat, case=False, regex=True)
    parties.loc[m, ["party_family", "family_source"]] = [fam, "manual_override"]

# harmonize across name variants of the same party within a country:
# same normalized name -> same family (first non-null) and max flags
grp = parties.groupby(["country_code", "nname"])
fam_fill = grp.party_family.transform(
    lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)
fill_mask = parties.party_family.isna() & fam_fill.notna()
parties.loc[fill_mask, "party_family"] = fam_fill[fill_mask]
parties.loc[fill_mask, "family_source"] = "variant_harmonized"
for fl in ["populist", "farright", "farleft", "eurosceptic"]:
    mx = grp[fl].transform("max")
    take = mx.notna() & (parties[fl].isna() | (parties[fl] < mx))
    for c in [fl, fl + "_start", fl + "_end"]:
        src = grp[c].transform("max")
        parties.loc[take, c] = src[take]

# manual-source Radical right/left families without a PopuList row: imply the
# corresponding flag for the party's full lifespan
man = parties.family_source.isin(["manual", "manual_override"])
need = man & parties.farright.isna() & (parties.party_family == "Radical right")
parties.loc[need, ["farright", "farright_start", "farright_end"]] = [1, 1900,
                                                                     2100]
need = man & parties.farleft.isna() & (parties.party_family == "Radical left")
parties.loc[need, ["farleft", "farleft_start", "farleft_end"]] = [1, 1900,
                                                                  2100]

# PopuList is a positive list (populist/FR/FL/eurosceptic parties only), so
# for identified parties in covered countries (EU + IS/NO/CH/GB, not TR)
# absence from PopuList means the flags are 0, not missing.
covered = parties.country_code != "TR"
identified = parties.partyfacts_id.notna() | parties.party_family.notna()
for fl in ["populist", "farright", "farleft", "eurosceptic"]:
    parties.loc[covered & identified & parties[fl].isna(), fl] = 0

# ---------------- 6. report + write ----------------
tot = parties.votes.sum()
cls = parties.party_family.notna()
print(f"\nclassified: {cls.sum()}/{len(parties)} parties "
      f"({parties.loc[cls, 'votes'].sum() / tot * 100:.1f}% of all votes)")
print(parties.family_source.value_counts().to_string())

unc = parties[~cls & (parties.max_nat_share >= 0.01)]
unc = unc.sort_values("max_nat_share", ascending=False)
print(f"\nUNCLASSIFIED with >=1% national share ({len(unc)}):")
print(unc[["country_code", "pname", "last_year", "max_nat_share"]]
      .head(80).to_string(index=False))

out = parties[PIDC + ["pname", "votes", "last_year", "max_nat_share",
                      "party_family", "family_source"] + FLAG_COLS]
out.to_csv(rf"{BASE}\crosswalks\party_classification.csv", index=False)
print("\nwritten:", len(out), "rows -> crosswalks/party_classification.csv")
