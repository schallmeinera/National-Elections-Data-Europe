"""Fetch Romanian 2024 parliamentary results (Chamber of Deputies) from
prezenta.roaep.ro, solving the site's SHA-1 proof-of-work cookie challenge."""
import hashlib
import json
import re
import subprocess
import sys

BASE = r"D:\EU LFS\eu-parliamentary-elections"
ROOT = "https://prezenta.roaep.ro/parlamentare01122024"


def solve(challenge):
    n1 = int(challenge[0], 16)
    i = 0
    while True:
        dig = hashlib.sha1((challenge + str(i)).encode()).digest()
        if dig[n1] == 0xB0 and dig[n1 + 1] == 0x0B:
            return challenge + str(i)
        i += 1


COOKIE = None


def curl(url, cookie=None):
    cmd = ["curl.exe", "-sL", "--max-time", "120", url]
    if cookie:
        cmd += ["-H", "Cookie: res=" + cookie]
    return subprocess.run(cmd, capture_output=True).stdout


def get(url):
    global COOKIE
    for attempt in range(4):
        body = curl(url, COOKIE)
        if b"Verifying" in body[:3000] and b"a0_0x2a54" in body:
            m = re.search(rb"a0_0x2a54=\['([0-9A-F]{40})'", body)
            COOKIE = solve(m.group(1).decode())
            continue
        return body
    raise RuntimeError("challenge loop")


if __name__ == "__main__":
    import unicodedata
    import pandas as pd
    import numpy as np

    agg = json.loads(get(ROOT + "/data/json/sicpv/pv/pv_aggregated.json"))
    counties = json.loads(get(ROOT + "/data/json/sicpv/lists/counties.json"))
    cmap = {str(c["id"]): c["county_name"] for c in counties}
    print("counties:", len(cmap))

    # county name -> NUTS-3 via EU-NED's own Romanian lookup
    ned = pd.read_csv(r"D:\EU LFS\DATA\03_Elections\EU_NED\eu_ned_joint.csv")
    ro = ned[(ned.country_code == "RO") & (ned.type == "Parliament")]
    ro = ro[ro.year == ro.year.max()][["nuts2016", "regionname"]].drop_duplicates()

    def norm(s):
        s = unicodedata.normalize("NFKD", str(s))
        s = "".join(c for c in s if not unicodedata.combining(c))
        return s.lower().replace("-", " ").strip()

    lk = {norm(r): c for c, r in ro.values}
    rows = []
    for cid, entry in agg["scopes"]["CNTY"]["CD"].items():
        cname = cmap.get(str(cid))
        if cname is None:
            print("unknown county id:", cid)
            continue
        k = norm(cname)
        if "sector" in k:          # Bucharest sectors: covered by municipality
            continue
        k = k.replace("municipiul ", "")
        nuts = ("ROZZZ" if k in ("strainatate", "diaspora")
                else lk.get(k))
        if nuts is None:
            print("UNMATCHED county:", cname)
            continue
        for cand in entry["candidates"]:
            rows.append((nuts, cand["candidate"], cand["votes"]))
    out = pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote"])
    out = out.groupby(["nuts_code", "party_native"], as_index=False).sum()
    out["validvote"] = out.groupby("nuts_code").partyvote.transform("sum")
    out["electorate"] = np.nan
    out["totalvote"] = np.nan
    out["country"], out["country_code"] = "Romania", "RO"
    out["year"], out["month"] = 2024, 12
    out["party_abbreviation"] = np.nan
    out["party_english"] = np.nan
    out["partyfacts_id"] = np.nan
    out["regionname"] = np.nan
    out["source"] = "AEP prezenta.roaep.ro (Chamber of Deputies)"
    out.to_csv(rf"{BASE}\raw\ext_ro2024.csv", index=False)
    print("written:", len(out), "rows,", out.nuts_code.nunique(), "regions,",
          f"total votes {out.partyvote.sum():,.0f}")
