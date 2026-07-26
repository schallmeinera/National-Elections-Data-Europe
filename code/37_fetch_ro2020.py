"""Fetch Romanian 2020 parliamentary results (Chamber of Deputies) from
prezenta.roaep.ro, solving the site's SHA-1 proof-of-work cookie challenge.

Unlike the 2024 app (11_fetch_ro.py, single pv_aggregated.json), the 2020 app
serves one pv_{county_code}_part.json per county; the completed count lives in
stages.PART -> scopes.CNTY -> categories.CD. PV fields: a = registered voters
(electorate), b = voters who turned out (totalvote), e = valid votes.
Bucharest sectors (S1-S6) are skipped (covered by B = municipality); SR
(strainatate/diaspora) -> ROZZZ.
"""
import hashlib
import json
import re
import subprocess

BASE = r"D:\EU LFS\eu-parliamentary-elections"
ROOT = "https://prezenta.roaep.ro/parlamentare06122020"


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

    counties = json.loads(get(ROOT + "/data/json/sicpv/lists/counties.json"))

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
    for c in counties:
        code, cname = c["code"], c["county_name"]
        k = norm(cname)
        if "sector" in k:          # Bucharest sectors: covered by municipality
            continue
        k = k.replace("municipiul ", "")
        nuts = ("ROZZZ" if k in ("strainatate", "diaspora")
                else lk.get(k))
        if nuts is None:
            print("UNMATCHED county:", cname)
            continue
        pv = json.loads(get(f"{ROOT}/data/json/sicpv/pv/pv_{code.lower()}"
                            "_part.json"))
        stage = pv["stages"]["PART"]
        assert stage["enabled"], f"{code}: PART stage not enabled"
        cd = stage["scopes"]["CNTY"]["categories"]["CD"]["table"]
        assert len(cd) == 1, f"{code}: {len(cd)} CNTY entries"
        entry = next(iter(cd.values()))
        # diaspora PV reports 'XXXXX' for fields without a defined value
        fields = {}
        for f in entry["fields"]:
            try:
                fields[f["name"]] = float(f["value"])
            except (TypeError, ValueError):
                fields[f["name"]] = np.nan
        for cand in entry["votes"]:
            rows.append((nuts, cand["candidate"], float(cand["votes"]),
                         fields.get("a"), fields.get("b"), fields.get("e")))
        print(code, nuts, "parties:", len(entry["votes"]))
    out = pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote",
                                      "electorate", "totalvote", "validvote"])
    out = (out.groupby(["nuts_code", "party_native"], as_index=False)
           .agg(partyvote=("partyvote", "sum"),
                electorate=("electorate", "first"),
                totalvote=("totalvote", "first"),
                validvote=("validvote", "first")))
    out["country"], out["country_code"] = "Romania", "RO"
    out["year"], out["month"] = 2020, 12
    out["party_abbreviation"] = np.nan
    out["party_english"] = np.nan
    out["partyfacts_id"] = np.nan
    out["regionname"] = np.nan
    out["source"] = "AEP prezenta.roaep.ro (Chamber of Deputies)"
    out.to_csv(rf"{BASE}\raw\ext_ro2020.csv", index=False)
    psum = out.groupby("nuts_code").partyvote.sum()
    valid = out.groupby("nuts_code").validvote.first()
    print("party-sum vs validvote max rel diff:",
          float(((psum - valid).abs() / valid).max()))
    print("written:", len(out), "rows,", out.nuts_code.nunique(), "regions,",
          f"total votes {out.partyvote.sum():,.0f}")
