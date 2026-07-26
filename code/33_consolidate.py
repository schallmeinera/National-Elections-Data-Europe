"""Stack the 9 output tables into one consolidated file.

Adds `table` (finest / nuts2 / nuts1) as the first column; `nuts_vintage`
already distinguishes vintages. Written as parquet and csv.gz to output/.
A row is uniquely identified by (table, nuts_vintage, country_code, year,
month, nuts_code, party identity).
"""
import pandas as pd

OUT = r"D:\EU LFS\eu-parliamentary-elections\output"

parts = []
for t in ("finest", "nuts2", "nuts1"):
    for v in (2016, 2021, 2024):
        df = pd.read_parquet(rf"{OUT}\national_{t}_{v}.parquet")
        df.insert(0, "table", t)
        parts.append(df)
full = pd.concat(parts, ignore_index=True)

key = ["table", "nuts_vintage", "country_code", "year", "month", "nuts_code",
       "party_abbreviation", "party_english", "party_native", "partyfacts_id"]
dup = full.duplicated(subset=key).sum()
assert dup == 0, f"{dup} duplicate keys"

full.to_parquet(rf"{OUT}\national_all.parquet", index=False)
full.to_csv(rf"{OUT}\national_all.csv.gz", index=False, compression="gzip")
print(f"rows {len(full):,} | countries {full.country_code.nunique()} | "
      f"elections {full.groupby(['country_code','year','month']).ngroups}")
print(full.groupby(['table', 'nuts_vintage']).size().unstack().to_string())
