"""Write the per-country coverage summary for the README."""
import pandas as pd

OUT = r"D:\EU LFS\eu-parliamentary-elections\output"
m = pd.read_parquet(rf"{OUT}\national_finest_2016.parquet")

cov = (m.groupby("country_code")
       .agg(country=("country", "first"),
            first_year=("year", "min"), last_year=("year", "max"),
            n_elections=("year", lambda s: m.loc[s.index]
                         .groupby(["year", "month"]).ngroups),
            base_levels=("nuts_level", lambda s: ",".join(
                str(x) for x in sorted(s.unique()))),
            sources=("source", lambda s: " + ".join(sorted(s.unique())))))
cov = cov.sort_index()
cov.to_csv(rf"{OUT}\coverage_by_country.csv")
print(cov.to_string())
