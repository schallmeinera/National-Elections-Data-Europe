"""Map CLEA post-2020 European national elections to NUTS-2016 units.

Only countries whose constituencies nest exactly into NUTS units are included:
  NUTS-3 : ES CH CZ NO SE FR HU BG GR MT  (GR: Attica constituencies -> EL30
           level-2, matching EU-NED's own Greek structure)
  NUTS-2 : PL (okreg -> voivodeship)
Excluded here (documented in README): DE (official source, separate script),
IT PT FI DK EE IE HR SK SI BE LU CY RO LT NL IS LV UK.

Output: raw/clea_mapped_nuts2016.csv with EU-NED-compatible columns.
"""
import re
import sys
import unicodedata
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

d = pd.read_csv(rf"{BASE}\raw\clea_europe_2021plus.csv")
ned = pd.read_csv(r"D:\EU LFS\DATA\03_Elections\EU_NED\eu_ned_joint.csv")
ned = ned[ned.type == "Parliament"]


TRANSLIT = str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE",
                          "œ": "oe", "ß": "ss", "ð": "d", "þ": "th",
                          "ł": "l", "Ł": "L", "đ": "d"})


def norm(s):
    if pd.isna(s):
        return ""
    s = str(s).translate(TRANSLIT)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("’", "'").replace("–", "-")
    s = re.sub(r"[^a-z0-9']+", " ", s).strip()
    return s


def ned_lookup(cc):
    sub = ned[ned.country_code == cc]
    latest = sub[sub.year == sub.year.max()]
    lk = latest[["nuts2016", "regionname"]].drop_duplicates()
    return {norm(r): c for c, r in lk.values}


# ---------------- per-country constituency -> NUTS mapping ----------------
maps = {}      # country_code -> {cst_key: nuts_code}
errors = []

# --- Spain: bilingual names + islands as electoral provinces (legacy codes
# ES530/ES701/ES702 kept; backbone splits them by population) ---
es_lk = ned_lookup("ES")
ES_FIX = {"alacant alicante": "alicante alacant", "araba alava": "alava araba",
          "castello castellon": "castellon castello",
          "valencia valencia": "valencia valencia",
          "illes balears": "balears", "bizkaia": "vizcaya bizkaia",
          "gipuzkoa": "guipuzcoa gipuzkoa", "navarra": "navarra nafarroa",
          "la rioja": "rioja la"}
es = {}
for c in d[d.ctr_n == "Spain"].cst_n.unique():
    k = ES_FIX.get(norm(c), norm(c))
    code = es_lk.get(k)
    if code is None:
        # try uniquely containing match
        hits = [v for kk, v in es_lk.items() if k.split()[0] in kk]
        code = hits[0] if len(hits) == 1 else None
    if code is None:
        errors.append(("ES", c))
    es[c] = code
maps["ES"] = es

# --- Switzerland: cantons; CLEA German/French names vs EU-NED ---
ch_lk = ned_lookup("CH")
CH_FIX = {"fribourg": "freiburg", "geneva": "geneve", "lucerne": "luzern",
          "st gallen": "sankt gallen", "grisons": "graubunden",
          "ticino": "tessin"}
ch = {}
for c in d[d.ctr_n == "Switzerland"].cst_n.unique():
    k = norm(c)
    code = ch_lk.get(k) or ch_lk.get(CH_FIX.get(k, ""))
    if code is None:
        hits = [v for kk, v in ch_lk.items() if k[:6] in kk or kk[:6] in k]
        code = hits[0] if len(hits) == 1 else None
    if code is None:
        errors.append(("CH", c))
    ch[c] = code
maps["CH"] = ch

# --- Czechia: kraje, names match EU-NED ---
cz_lk = ned_lookup("CZ")
CZ_FIX = {"kraj vysocina": "vysocina"}
cz = {}
for c in d[d.ctr_n == "Czech Republic"].cst_n.unique():
    k = norm(c)
    code = cz_lk.get(k) or cz_lk.get(CZ_FIX.get(k, ""))
    if code is None:
        errors.append(("CZ", c))
    cz[c] = code
maps["CZ"] = cz

# --- Norway: 19 old fylker = NUTS-3 2016 (incl. legacy NO061/NO062) ---
no_lk = ned_lookup("NO")
NO_FIX = {"finnmark finnmarku": "finnmark", "sor trondelag": "sor trondelag",
          "troms romsa": "troms"}
no = {}
for c in d[d.ctr_n == "Norway"].cst_n.unique():
    k = norm(c)
    code = no_lk.get(k) or no_lk.get(NO_FIX.get(k, ""))
    if code is None:
        hits = [v for kk, v in no_lk.items() if kk.split()[0] == k.split()[0]]
        code = hits[0] if len(hits) == 1 else None
    if code is None:
        errors.append(("NO", c))
    no[c] = code
maps["NO"] = no

# --- Sweden: 29 constituencies -> 21 lan ---
se_lk = ned_lookup("SE")
SE_CITY = {"stockholms kommun": "stockholms lan",
           "goteborgs kommun": "vastra gotalands lan",
           "malmo kommun": "skane lan"}
se = {}
for c in d[d.ctr_n == "Sweden"].cst_n.unique():
    k = norm(c)
    k = SE_CITY.get(k, k)
    # split constituencies: 'vastra gotalands lans vastra' etc.
    base = re.sub(r" lans? .*$", " lan", k)
    code = se_lk.get(k) or se_lk.get(base)
    if code is None:
        errors.append(("SE", c))
    se[c] = code
maps["SE"] = se

# --- France: departement from 'Name-N'; COM + abroad -> FRZZZ ---
fr_lk = ned_lookup("FR")
FR_EXTRA = {"francais etablis hors de france", "wallis et futuna",
            "polynesie francaise", "nouvelle caledonie",
            "saint pierre et miquelon", "saint martin saint barthelemy",
            "saint barthelemy et saint martin"}
FR_FIX = {"essone": "essonne", "ille et villaine": "ille et vilaine"}
fr = {}
for c in d[d.ctr_n == "France"].cst_n.unique():
    dept = c.rsplit("-", 1)[0]
    k = norm(dept)
    if k in FR_EXTRA:
        fr[c] = "FRZZZ"
        continue
    code = fr_lk.get(k) or fr_lk.get(FR_FIX.get(k, ""))
    if code is None:
        errors.append(("FR", c))
    fr[c] = code
maps["FR"] = fr

# --- Hungary: county prefix; national list row dropped after validation ---
hu_lk = ned_lookup("HU")
hu = {}
for c in d[d.ctr_n == "Hungary"].cst_n.unique():
    pref = c.rsplit(" ", 1)[0]
    if pref.lower().startswith("national"):
        hu[c] = "DROP_NATIONAL"
        continue
    k = norm(pref)
    k = {"csongrad csanad": "csongrad"}.get(k, k)
    code = hu_lk.get(k)
    if code is None:
        errors.append(("HU", c))
    hu[c] = code
maps["HU"] = hu

# --- Bulgaria: per-wave name repair; canonical 31 MIRs -> oblast NUTS-3 ---
bg_lk = ned_lookup("BG")
BG_CANON = {  # MIR canonical name -> NUTS-3
    "blagoevgrad": "BG413", "burgas": "BG341", "varna": "BG331",
    "veliko tarnovo": "BG321", "vidin": "BG311", "vratsa": "BG313",
    "gabrovo": "BG322", "dobrich": "BG332", "kardzhali": "BG425",
    "kyustendil": "BG415", "lovech": "BG315", "montana": "BG312",
    "pazardzhik": "BG423", "pernik": "BG414", "pleven": "BG314",
    "plovdiv city": "BG421", "plovdiv region": "BG421", "razgrad": "BG324",
    "ruse": "BG323", "silistra": "BG325", "sliven": "BG342",
    "smolyan": "BG424", "sofia 23": "BG411", "sofia 24": "BG411",
    "sofia 25": "BG411", "sofia region": "BG412", "stara zagora": "BG344",
    "targovishte": "BG334", "haskovo": "BG422", "shumen": "BG333",
    "yambol": "BG343"}
# cross-check hand table against EU-NED lookup by name
for k, v in BG_CANON.items():
    base = k.replace(" city", "").replace(" region", "").replace(" 23", "") \
            .replace(" 24", "").replace(" 25", "")
    if base == "sofia":
        continue
    ned_code = bg_lk.get(base)
    if ned_code and ned_code != v:
        print(f"BG MISMATCH {k}: hand {v} vs EU-NED {ned_code}")
        BG_CANON[k] = ned_code
BG_TYPO = {"kurdzhali": "kardzhali", "pazardzik": "pazardzhik",
           "plovoid city": "plovdiv city", "plovoid region": "plovdiv region",
           "plovdiv district": "plovdiv region", "viden": "vidin",
           "sofia 23 mir": "sofia 23", "sofia 24 mir": "sofia 24",
           "sofia 25 mir": "sofia 25",
           # 2022-10 garbled names: wave is alphabetical; SEEN sits between
           # RUSE and SILISTRA -> Shumen; NOISY -> Vidin by elimination
           "seen": "shumen", "noisy": "vidin"}
bg = d[d.ctr_n == "Bulgaria"]
bg_map = {}   # (yr, mn, cst) -> nuts
for (y, m), g in bg.groupby(["yr", "mn"]):
    waves = g[["cst", "cst_n"]].drop_duplicates().sort_values("cst")
    assigned, unknown = {}, []
    for cst, name in waves.values:
        k = norm(name)
        k = BG_TYPO.get(k, k)
        if k in BG_CANON:
            assigned[cst] = k
        else:
            unknown.append((cst, name))
    used = set(assigned.values())
    missing = [k for k in BG_CANON if k not in used]
    if len(unknown) == 1 and len(missing) == 1:
        assigned[unknown[0][0]] = missing[0]
        print(f"BG {y}-{m}: inferred {unknown[0][1]!r} -> {missing[0]!r}")
    elif unknown:
        # infer by alphabetical position among that wave's sorted names
        for cst, name in unknown:
            cand = [mk for mk in missing]
            print(f"BG {y}-{m}: UNRESOLVED {name!r} (cst {cst}); "
                  f"missing candidates {cand}")
            errors.append(("BG", f"{y}-{m} {name}"))
    for cst, k in assigned.items():
        bg_map[(y, m, cst)] = BG_CANON[k]

# --- Greece: nomoi (grouped NUTS-3) + Attica -> EL30; Overseas -> ELZZZ ---
gr_lk = ned_lookup("GR")   # includes comma-grouped names
GR_MANUAL = {
    "athens a": "EL30", "athens b1 north": "EL30", "athens b2 west": "EL30",
    "athens b3 south": "EL30", "piraeus a": "EL30", "piraeus b": "EL30",
    "east attica": "EL30", "west attica": "EL30",
    "thessaloniki a": "EL522", "thessaloniki b": "EL522",
    "dodecanese": "EL421", "cyclades": "EL422",
    "corfu": "EL622", "kefallonia": "EL623", "lefkada": "EL624",
    "zakynthos": "EL621", "archaea": "EL632", "achaea": "EL632",
    "boeotia": "EL641", "euboea": "EL642", "evrytania": "EL643",
    "fthiotida": "EL644", "fokida": "EL645",
    "corinthia": "EL652", "laconia": "EL653", "arcadia": "EL651",
    "argolida": "EL651", "messinia": "EL653", "ilia": "EL633",
    "overseas": "ELZZZ",
    "national constituency": "DROP_NATIONAL",
}
gr_raw = ned[(ned.country_code == "GR")]
gr_raw = gr_raw[gr_raw.year == gr_raw.year.max()][
    ["nuts2016", "regionname"]].drop_duplicates()
gr_parts = {}
for code, rname in gr_raw.values:
    for part in str(rname).split(","):
        gr_parts.setdefault(norm(part), set()).add(code)
gr = {}
for c in d[d.ctr_n == "Greece"].cst_n.unique():
    k = norm(c)
    code = GR_MANUAL.get(k) or gr_lk.get(k)
    if code is None and k in gr_parts and len(gr_parts[k]) == 1:
        code = next(iter(gr_parts[k]))
    if code is None:
        errors.append(("GR", c))
    gr[c] = code
maps["GR"] = gr

# --- Malta: districts 1-12 -> MT001, 13 (Gozo) -> MT002 ---
mt = {c: ("MT002" if c.strip().endswith("13") else "MT001")
      for c in d[d.ctr_n == "Malta"].cst_n.unique()}
maps["MT"] = mt

# --- Poland: okreg nr -> voivodeship NUTS-2 (fixed since 2001) ---
PL_OKREG = {1: "PL51", 2: "PL51", 3: "PL51", 4: "PL61", 5: "PL61",
            6: "PL81", 7: "PL81", 8: "PL43", 9: "PL71", 10: "PL71",
            11: "PL71", 12: "PL21", 13: "PL21", 14: "PL21", 15: "PL21",
            16: "PL92", 17: "PL92", 18: "PL92", 19: "PL91", 20: "PL91",
            21: "PL52", 22: "PL82", 23: "PL82", 24: "PL84", 25: "PL63",
            26: "PL63", 27: "PL22", 28: "PL22", 29: "PL22", 30: "PL22",
            31: "PL22", 32: "PL22", 33: "PL72", 34: "PL62", 35: "PL62",
            36: "PL41", 37: "PL41", 38: "PL41", 39: "PL41", 40: "PL42",
            41: "PL42"}

# validate every assigned code against the NUTS-2016 list (+ legacy + ZZZ)
codes16 = set(pd.read_csv(rf"{BASE}\crosswalks\nuts_codes_2016.csv").code)
valid_extra = {"ES530", "ES701", "ES702", "NO061", "NO062"}
all_assigned = ([v for mp in maps.values() for v in mp.values()]
                + list(bg_map.values()) + list(PL_OKREG.values()))
bad_codes = {c for c in all_assigned
             if c and c != "DROP_NATIONAL" and not c.endswith("ZZZ")
             and c not in codes16 and c not in valid_extra}
if bad_codes:
    print("INVALID NUTS-2016 CODES ASSIGNED:", sorted(bad_codes))
    sys.exit(1)

# ---------------- report unresolved ----------------
if errors:
    print("\nUNRESOLVED MAPPINGS:")
    for e in errors:
        print(" ", e)
    sys.exit(1)

# ---------------- apply ----------------
CC = {"Spain": "ES", "Switzerland": "CH", "Czech Republic": "CZ",
      "Norway": "NO", "Sweden": "SE", "France": "FR", "Hungary": "HU",
      "Bulgaria": "BG", "Greece": "GR", "Malta": "MT", "Poland": "PL"}
sub = d[d.ctr_n.isin(CC)].copy()
sub["country_code"] = sub.ctr_n.map(CC)


def assign(row):
    cc = row.country_code
    if cc == "BG":
        return bg_map.get((row.yr, row.mn, row.cst))
    if cc == "PL":
        return PL_OKREG.get(int(row.cst))
    return maps[cc].get(row.cst_n)


sub["nuts_code"] = sub.apply(assign, axis=1)
assert sub.nuts_code.notna().all(), sub[sub.nuts_code.isna()][
    ["ctr_n", "yr", "cst_n"]].drop_duplicates()

# CLEA missing-value codes are negative (-990 missing, -992 n/a): -> NaN.
# Zero region totals with positive party votes are also missing-coded (BG).
for c in ["pev1", "vot1", "vv1", "pv1"]:
    n_neg = (sub[c] < 0).sum()
    if n_neg:
        print(f"cleaning {c}: {n_neg} negative (missing-coded) values -> NaN")
    sub.loc[sub[c] < 0, c] = np.nan
for c in ["pev1", "vot1", "vv1"]:
    sub.loc[sub[c] == 0, c] = np.nan
n0 = len(sub)
sub = sub[sub.pv1.notna()]
print(f"dropped {n0 - len(sub)} party rows without party votes")

# CLEA reports candidate-level rows for several countries with pv1 = the
# party's constituency total REPEATED on each candidate row (SE/CH/PL/CZ/MT,
# partly FR). Deduplicate to one row per (election, cst, party, pv1, pvs1):
# repeated party totals collapse, genuinely distinct same-code lists (e.g.
# multiple 'Divers' candidates in a French circo) are kept and summed.
n0 = len(sub)
sub = sub.drop_duplicates(subset=["country_code", "yr", "mn", "cst", "pty",
                                  "pv1", "pvs1"])
print(f"candidate-row dedup: {n0 - len(sub)} duplicate party rows removed")

# validations: GR/HU national rows vs constituency sums
for cc, lab in [("GR", "DROP_NATIONAL"), ("HU", "DROP_NATIONAL")]:
    s = sub[sub.country_code == cc]
    nat = s[s.nuts_code == lab]
    if len(nat):
        for (y, m), g in nat.groupby(["yr", "mn"]):
            rest = s[(s.nuts_code != lab) & (s.yr == y) & (s.mn == m)]
            print(f"{cc} {y}-{m}: national-row votes {g.pv1.sum():,.0f} vs "
                  f"constituency sum {rest.pv1.sum():,.0f}")
# HU: national list total exceeds SMD sum (diaspora/mail list votes without
# constituency assignment). Keep the per-party residual as HUZZZ extra-regio.
hu_all = sub[sub.country_code == "HU"]
hu_nat = hu_all[hu_all.nuts_code == "DROP_NATIONAL"]
if len(hu_nat):
    smd = (hu_all[hu_all.nuts_code != "DROP_NATIONAL"]
           .groupby(["yr", "mn", "pty_n"], as_index=False).pv1.sum())
    nat = hu_nat.groupby(["yr", "mn", "pty_n"], as_index=False).pv1.sum()
    res = nat.merge(smd, on=["yr", "mn", "pty_n"], how="left",
                    suffixes=("_nat", "_smd"))
    res["pv1"] = (res.pv1_nat - res.pv1_smd.fillna(0)).clip(lower=0)
    res = res[res.pv1 > 0]
    res["ctr_n"], res["country_code"] = "Hungary", "HU"
    res["nuts_code"], res["cst"], res["cst_n"] = "HUZZZ", 999, "extra-regio"
    res["pev1"] = res["vot1"] = res["vv1"] = np.nan
    print(f"HU extra-regio residual: {res.pv1.sum():,.0f} votes, "
          f"{len(res)} party rows")
    sub = pd.concat([sub[sub.nuts_code != "DROP_NATIONAL"],
                     res[sub.columns.intersection(res.columns)]],
                    ignore_index=True)
else:
    sub = sub[sub.nuts_code != "DROP_NATIONAL"].copy()

# aggregate constituencies -> NUTS units
sub["month"] = sub.mn
party = (sub.groupby(["country_code", "yr", "month", "nuts_code", "pty_n"],
                     dropna=False, as_index=False)
         .agg(partyvote=("pv1", "sum")))
regtot = (sub[["country_code", "yr", "month", "nuts_code", "cst",
               "pev1", "vot1", "vv1"]]
          .drop_duplicates(subset=["country_code", "yr", "month", "nuts_code",
                                   "cst"])
          .groupby(["country_code", "yr", "month", "nuts_code"], as_index=False)
          .agg(electorate=("pev1", "sum"), totalvote=("vot1", "sum"),
               validvote=("vv1", "sum")))
out = party.merge(regtot, on=["country_code", "yr", "month", "nuts_code"],
                  how="left")
# all-missing totals sum to 0 in pandas; a zero total is impossible -> NaN
for c in ["electorate", "totalvote", "validvote"]:
    out.loc[out[c] == 0, c] = np.nan

# partyfacts linkage via CLEA<->Partyfacts crosswalk
pf = pd.read_csv(r"D:\EU LFS\DATA\03_Elections\CLEA_GRED\Partyfacts Clea"
                 r"\partyfacts-clea.csv")
pfmap = None
for cand_id, cand_name in [("dataset_party_id", "partyfacts_id")]:
    if cand_id in pf.columns:
        pfmap = pf
print("partyfacts columns:", pf.columns.tolist())

out = out.rename(columns={"yr": "year", "pty_n": "party_native"})
out["country"] = out.country_code.map({v: k for k, v in CC.items()})
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "CLEA 2025-10"
out.to_csv(rf"{BASE}\raw\clea_mapped_nuts2016.csv", index=False)
print("\nwritten:", len(out), "rows")
print(out.groupby(["country_code", "year", "month"]).size())
