"""Merge the party classification into the 9 output tables.

Adds: party_family, family_source, populist, farright, farleft, eurosceptic,
partyfacts_id_matched (recovered id incl. name matches; the original
partyfacts_id column from EU-NED is left untouched).
"""
import numpy as np
import pandas as pd

BASE = r"D:\EU LFS\eu-parliamentary-elections"
OUT = BASE + r"\output"

cls = pd.read_csv(rf"{BASE}\crosswalks\party_classification.csv")
KEYS = ["country_code", "party_abbreviation", "party_english", "party_native"]
FLAGS = ["populist", "farright", "farleft", "eurosceptic"]
PER = [f + s for f in FLAGS
       for s in ("_start", "_end", "_startnobl", "_endnobl")]
STRICT = [f + "_strict" for f in FLAGS]
ADD = ["party_family", "family_source"] + FLAGS + STRICT
cls_m = cls.rename(columns={"partyfacts_id": "partyfacts_id_matched"})
cls_m = cls_m[KEYS + ["partyfacts_id_matched"] + ["party_family",
                                                  "family_source"]
              + FLAGS + PER].drop_duplicates(KEYS)

for t in ("finest", "nuts2", "nuts1"):
    for v in (2016, 2021, 2024):
        stem = rf"{OUT}\national_{t}_{v}"
        df = pd.read_parquet(stem + ".parquet")
        df = df.drop(columns=[c for c in ADD + PER
                              + ["partyfacts_id_matched"]
                              if c in df.columns])
        m = df.merge(cls_m, on=KEYS, how="left")
        assert len(m) == len(df)
        # time-aware flags: PopuList classifications carry validity periods
        # (e.g. HDZ far right only in the 1990s); evaluate at election year.
        # Two series per flag: the plain one uses PopuList's borderline-
        # INCLUSIVE window, `_strict` uses its *nobl window, which excludes
        # borderline cases (19 of PopuList's 133 far-right parties are far
        # right only as borderline -- NO FrP, NL BBB, BE N-VA, LU ADR,
        # FR LR, BG BSP among them).
        for fl in FLAGS:
            ever = m[fl]
            active = ((ever == 1)
                      & (m[fl + "_start"].fillna(1900) <= m.year)
                      & (m[fl + "_end"].fillna(2100) >= m.year))
            strict = ((ever == 1)
                      & (m[fl + "_startnobl"].fillna(1900) <= m.year)
                      & (m[fl + "_endnobl"].fillna(2100) >= m.year))
            m[fl + "_strict"] = np.where(strict, 1.0,
                                         np.where(ever.notna(), 0.0, np.nan))
            m[fl] = np.where(active, 1.0,
                             np.where(ever.notna(), 0.0, np.nan))
        m = m.drop(columns=PER)
        m.to_parquet(stem + ".parquet", index=False)
        m.to_csv(stem + ".csv", index=False)
        cov = m.party_family.notna().mean()
        vshare = (m.loc[m.party_family.notna(), "partyvote"].sum()
                  / m.partyvote.sum())
        print(f"{t}_{v}: family coverage {cov:.1%} of rows, "
              f"{vshare:.1%} of votes")

# per-country coverage summary (finest 2016)
f = pd.read_parquet(rf"{OUT}\national_finest_2016.parquet")
cc = (f.assign(cl=f.party_family.notna())
      .groupby("country_code")
      .apply(lambda g: pd.Series({
          "vote_share_classified": g.loc[g.cl, "partyvote"].sum()
                                   / g.partyvote.sum(),
          "rows_classified": g.cl.mean()}), include_groups=False))
print("\nper-country classified vote share (finest 2016):")
print((cc.vote_share_classified * 100).round(1).sort_values().to_string())
