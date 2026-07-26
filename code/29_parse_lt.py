"""Lithuania Seimas 2024 proportional (daugiamandatė) vote -> NUTS-3.

The proportional tier is one national constituency, so it can't be split by the
single-member apygardos. VRK's open-data layer reports it per polling district
(apylinkė) with polygon geometry; we spatially join each district's centroid to
the NUTS-3 2016 boundaries. Party votes are in ranked slots PARTk_*, so we key
by party name, not slot."""
import json
import pandas as pd
import numpy as np
import geopandas as gpd

BASE = r"D:\EU LFS\eu-parliamentary-elections"
GPKG = r"D:\EU LFS\DATA\06_Geo_Crosswalks\NUTS_Boundaries\NUTS_RG_20M_2016_3035.gpkg"

g = gpd.read_file(rf"{BASE}\raw\lt2024_prop.geojson")
print("districts:", len(g), "| crs:", g.crs)

# long-format party votes keyed by name (slots present are non-contiguous)
gi = g.reset_index()
slots = sorted(int(c[4:-5]) for c in gi.columns
               if c.startswith("PART") and c.endswith("_NAME")
               and c[4:-5].isdigit())
recs = []
for k in slots:
    sub = gi[["index", f"PART{k}_NAME", f"PART{k}_VOTES"]].copy()
    sub.columns = ["idx", "party_native", "partyvote"]
    recs.append(sub)
long = pd.concat(recs, ignore_index=True).dropna(subset=["party_native"])
long = long[long.partyvote.fillna(0) > 0]

# NUTS-3 for each district via centroid-in-polygon
nuts = gpd.read_file(GPKG)
nuts = nuts[(nuts.LEVL_CODE == 3) & (nuts.CNTR_CODE == "LT")][["NUTS_ID", "geometry"]]
cent = gi[["index", "geometry"]].copy()
cent["geometry"] = cent.geometry.to_crs(3035).representative_point()
cent = gpd.GeoDataFrame(cent, geometry="geometry", crs=3035)
# nearest handles both interior points and any coastal-boundary slivers
joined = gpd.sjoin_nearest(cent, nuts.to_crs(3035), how="left")
idx_nuts = joined.drop_duplicates("index").set_index("index").NUTS_ID
print("districts without NUTS3:", idx_nuts.isna().sum())

long["nuts_code"] = long.idx.map(idx_nuts)
long = long.dropna(subset=["nuts_code"])
out = (long.groupby(["nuts_code", "party_native"], as_index=False)
       .partyvote.sum())
out["validvote"] = out.groupby("nuts_code").partyvote.transform("sum")
out["electorate"] = np.nan
out["totalvote"] = np.nan
out["country"], out["country_code"] = "Lithuania", "LT"
out["year"], out["month"] = 2024, 10
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "VRK open data (proportional vote, polling districts -> NUTS3)"
out.to_csv(rf"{BASE}\raw\ext_lt2024.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS3,",
      f"votes {out.partyvote.sum():,.0f}")
