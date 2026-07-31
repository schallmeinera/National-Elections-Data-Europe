"""Guarantee a non-null party identifier on every row.

Only the EU-NED backbone (and the AT/SI/GB/LU/NO parsers, plus most DK/IS
rows) populate `party_abbreviation`. CLEA has no abbreviation field at all
(only `pty_n`), and the per-country extension parsers put the party
identifier in `party_native` and write `party_abbreviation` / `party_english`
as NaN. Since EU-NED ends in 2020, any consumer that keys on
`party_abbreviation` silently loses 48 election events in 23 countries -- in
21 of them the 3-8 most recent years, and the Netherlands entirely.

This step fills, never overwrites:

  party_abbreviation  <- party_native  where NULL
  party_label_source  <- 'source' | 'native'      (new column, provenance)
  pf_name_short       <- Partyfacts name_short    (new column)
  pf_name_english     <- Partyfacts name_english  (new column)

`party_abbreviation` is filled from the source's own string, not from
Partyfacts, so that no judgement enters the identifier. The Partyfacts id
match is itself imperfect -- BE "CD&V" resolves to id 756, the 2004-07
CD&V/N-VA cartel; FR "Regionalistes" resolves to a party Partyfacts calls
"1 percent" -- and a wrong id must not be able to rewrite a party's name.
For the same reason `party_english` is left alone: it means "English name as
supplied by the source", and silently topping it up from a fallible id match
would make source-given and match-derived labels indistinguishable. The
Partyfacts labels are exposed in their own prefixed columns instead, and the
distinct mappings behind them are written to
crosswalks/party_label_audit.csv with a resemblance flag so the bad ones can
be found.

`party_native` is left verbatim in every case.

Run after 32_apply_classification.py and before 38_build_nuts3.py --
the classification merge keys on (country_code, party_abbreviation,
party_english, party_native) and would stop matching once the NULLs are
filled.
"""
import re
import unicodedata

import numpy as np
import pandas as pd

BASE = r"D:\EU LFS\eu-parliamentary-elections"
OUT = BASE + r"\output"

# Partyfacts `country` is ISO-3; the panel uses ISO-2 (GR for Greece,
# GB for the UK). Guard the join so a mis-matched id cannot import a
# label from another country.
ISO3 = {"AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
        "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "ES": "ESP",
        "FI": "FIN", "FR": "FRA", "GB": "GBR", "GR": "GRC", "HR": "HRV",
        "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU",
        "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR",
        "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN",
        "SK": "SVK", "TR": "TUR"}

core = pd.read_csv(rf"{BASE}\raw\partyfacts_core.csv", low_memory=False)
core = (core[["partyfacts_id", "country", "name_short", "name",
              "name_english"]]
        .dropna(subset=["partyfacts_id"])
        .drop_duplicates("partyfacts_id"))
core["partyfacts_id"] = core.partyfacts_id.astype(float)
# older Partyfacts vintages code Romania ROM
core.loc[core.country == "ROM", "country"] = "ROU"

NEW = ["party_label_source", "pf_name_short", "pf_name_english"]


def norm(s):
    """Lowercase, strip accents and everything that is not alphanumeric.

    Digits are kept: several party labels are alphanumeric (D66, M5S, 50PLUS)
    and dropping them collapses the string to noise.
    """
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def acronym(s):
    if not isinstance(s, str):
        return ""
    return norm("".join(w[0] for w in re.split(r"[\s\-/,.]+", s) if w))


def resembles(sources, pf_labels):
    """Does the Partyfacts entry look like the same party as the source?

    True if any Partyfacts label shares a containment relation with any
    source string the panel holds for that party (native name and/or
    abbreviation), or if a source string is an acronym of a Partyfacts long
    name. Purely a triage flag for the audit file -- nothing downstream keys
    on it, and a False is a prompt to look, not a verdict.
    """
    srcs = [norm(s) for s in sources]
    srcs = [s for s in srcs if len(s) >= 2]
    if not srcs:
        return False
    cands = [norm(c) for c in pf_labels]
    acrs = [acronym(c) for c in pf_labels]
    for n in srcs:
        for c in cands:
            if len(c) >= 2 and (c in n or n in c):
                return True
        for a in acrs:
            if len(a) >= 2 and a == n:
                return True
    return False


audit = []
for t in ("finest", "nuts2", "nuts1"):
    for v in (2016, 2021, 2024):
        stem = rf"{OUT}\national_{t}_{v}"
        df = pd.read_parquet(stem + ".parquet")
        # Idempotent: on a re-run the NULLs are already filled, so recover
        # which rows they were from the provenance column written last time.
        prior = (df.party_label_source.eq("native")
                 if "party_label_source" in df.columns else None)
        df = df.drop(columns=[c for c in NEW if c in df.columns])

        assert not (df.party_abbreviation.isna()
                    & df.party_native.isna()).any(), \
            f"{t}_{v}: rows with neither abbreviation nor native name"

        # --- fill the identifier ----------------------------------------
        miss = df.party_abbreviation.isna() if prior is None else prior
        df["party_label_source"] = np.where(miss, "native", "source")
        df.loc[miss, "party_abbreviation"] = df.loc[miss, "party_native"]
        assert df.party_abbreviation.notna().all(), f"{t}_{v}: NULL remains"

        # --- Partyfacts labels, country-guarded, in their own columns ---
        lab = df[["country_code", "partyfacts_id_matched"]].merge(
            core, how="left",
            left_on="partyfacts_id_matched", right_on="partyfacts_id")
        ok = lab.country.eq(df.country_code.map(ISO3).values).values
        df["pf_name_short"] = np.where(ok, lab.name_short, np.nan)
        df["pf_name_english"] = np.where(ok, lab.name_english, np.nan)

        df.to_parquet(stem + ".parquet", index=False)
        df.to_csv(stem + ".csv", index=False)

        if t == "finest" and v == 2016:
            a = df.loc[ok, ["country_code", "party_abbreviation",
                            "party_native", "partyfacts_id_matched"]].copy()
            a["pf_name_short"] = lab.name_short[ok].values
            a["pf_name"] = lab.name[ok].values
            a["pf_name_english"] = lab.name_english[ok].values
            a["votes"] = df.loc[ok, "partyvote"].values
            audit.append(a)
            ev = df.groupby(["country_code", "year", "month"]).ngroups
            rec = (df[df.party_label_source == "native"]
                   .groupby(["country_code", "year", "month"]).ngroups)
            print(f"{t}_{v}: {miss.sum():,} identifiers filled from "
                  f"party_native ({miss.mean():.1%} of rows, "
                  f"{df.loc[miss,'partyvote'].sum()/df.partyvote.sum():.1%} "
                  f"of votes); {rec} of {ev} election events recovered")
            print(f"{t}_{v}: pf_name_short populated on "
                  f"{df.pf_name_short.notna().mean():.1%} of rows")
        else:
            print(f"{t}_{v}: {miss.sum():,} identifiers filled")

# ---------------------------------------------------------------- audit ----
au = pd.concat(audit, ignore_index=True)
au = (au.groupby(["country_code", "party_abbreviation", "party_native",
                  "partyfacts_id_matched", "pf_name_short", "pf_name",
                  "pf_name_english"], dropna=False)
        .votes.sum().reset_index())
au["resembles_source"] = [
    resembles((ab, nv), (sh, nm, en)) for ab, nv, sh, nm, en in
    zip(au.party_abbreviation, au.party_native, au.pf_name_short,
        au.pf_name, au.pf_name_english)]
au = au.sort_values(["resembles_source", "votes"], ascending=[True, False])
au.to_csv(rf"{BASE}\crosswalks\party_label_audit.csv", index=False)
bad = ~au.resembles_source
print(f"\nparty_label_audit.csv: {len(au):,} distinct Partyfacts mappings, "
      f"{bad.sum():,} flagged as not resembling the source name "
      f"({au.loc[bad,'votes'].sum()/au.votes.sum():.1%} of matched votes)")
print("\ndone -- rerun 38_build_nuts3.py, 33_consolidate.py, 30_validate.py")
