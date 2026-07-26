"""Build pure NUTS-3 tables from the finest tables.

national_nuts3_{vintage} = the subset of national_finest_{vintage} restricted
to country-elections whose finest partition is entirely NUTS-3 (extra-regio
Z-codes count as level 3). Countries/elections with a coarser base (SI, GB,
IE, PL, BE, parts of GR/NL history, DE 2021/2025) are absent — use the finest
or nuts1/nuts2 tables for those.

Run after 32_apply_classification.py so the classification columns carry over.
Supersedes the pre-extension nuts3 files that used to sit in output/.
"""
import pandas as pd

OUT = r"D:\EU LFS\eu-parliamentary-elections\output"
KEY = ["country_code", "year", "month"]

for v in (2016, 2021, 2024):
    f = pd.read_parquet(rf"{OUT}\national_finest_{v}.parquet")
    pure = (f.groupby(KEY).nuts_level.transform(lambda s: (s == 3).all()))
    m = f[pure].copy()
    stem = rf"{OUT}\national_nuts3_{v}"
    m.to_csv(stem + ".csv", index=False)
    m.to_parquet(stem + ".parquet", index=False)
    print(f"nuts3 v{v}: {len(m):,} rows, {m.country_code.nunique()} countries, "
          f"{m.groupby(KEY).ngroups} elections "
          f"(dropped {f.groupby(KEY).ngroups - m.groupby(KEY).ngroups} "
          f"coarser elections)")
