"""Iceland Althingi 2021 + 2024 (Hagstofa PxWeb) -> NUTS-3.
Constituencies: Reykjavik N/S + Sudvestur = capital region IS001;
Nordvestur/Nordaustur/Sudur = rest IS002. Iceland is absent from EU-NED, so
this is its first appearance in the database (1 country added)."""
import json
import subprocess
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
TABLES = {2024: ("KOS02018.px", 11), 2021: ("KOS02019.px", 9)}
KJOR_NUTS = {"Norðvesturkjördæmi": "IS002", "Norðausturkjördæmi": "IS002",
             "Suðurkjördæmi": "IS002", "Suðvesturkjördæmi": "IS001",
             "Reykjavíkurkjördæmi suður": "IS001",
             "Reykjavíkurkjördæmi norður": "IS001"}

frames = []
for year, (tab, month) in TABLES.items():
    url = ("https://px.hagstofa.is/pxis/api/v1/is/Ibuar/kosningar/althingi/"
           "althurslit/" + tab)
    meta = json.loads(subprocess.run(["curl.exe", "-sL", url],
                                     capture_output=True).stdout.decode("utf-8-sig"))
    vmap = {v["code"]: v for v in meta["variables"]}
    atr = vmap["Atriði"]
    valid_code = atr["values"][atr["valueTexts"].index("Gild atkvæði")]
    q = {"query": [{"code": "Atriði", "selection": {
            "filter": "item", "values": [valid_code]}}],
         "response": {"format": "json-stat2"}}
    qf = rf"{BASE}\raw\is_query.json"
    json.dump(q, open(qf, "w"))
    j = json.loads(subprocess.run(
        ["curl.exe", "-sL", "-X", "POST", "-H",
         "Content-Type: application/json", "-d", "@" + qf, url],
        capture_output=True).stdout.decode("utf-8-sig"))
    dims, order, sizes = j["dimension"], j["id"], j["size"]
    import itertools
    axes = [list(dims[d]["category"]["index"].keys()) for d in order]
    labels = {d: dims[d]["category"]["label"] for d in order}
    recs = []
    for combo, v in zip(itertools.product(*axes), j["value"]):
        if v is None:
            continue
        rec = dict(zip(order, combo))
        party = labels["Flokkur"][rec["Flokkur"]]
        kjor = labels["Kjördæmi"][rec["Kjördæmi"]]
        recs.append((kjor, party, v))
    df = pd.DataFrame(recs, columns=["kjor", "party", "votes"])
    df = df[(df.kjor != "Alls") & (df.party != "Alls")]
    df["nuts_code"] = df.kjor.map(KJOR_NUTS)
    assert df.nuts_code.notna().all(), df[df.nuts_code.isna()].kjor.unique()
    g = (df.groupby(["nuts_code", "party"], as_index=False).votes.sum()
         .rename(columns={"party": "party_native", "votes": "partyvote"}))
    g = g[g.partyvote > 0]
    g["validvote"] = g.groupby("nuts_code").partyvote.transform("sum")
    g["year"], g["month"] = year, month
    frames.append(g)
    print(year, ":", f"{g.partyvote.sum():,.0f} votes")

out = pd.concat(frames, ignore_index=True)
out["party_abbreviation"] = out.party_native.str.extract(r"\(([A-Z])\)")
out["party_native"] = (out.party_native.str.replace(r"\s*\([A-Z]\)\s*$", "",
                                                    regex=True).str.strip())
out["electorate"] = np.nan
out["totalvote"] = np.nan
out["country"], out["country_code"] = "Iceland", "IS"
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "Statistics Iceland PxWeb"
out.to_csv(rf"{BASE}\raw\ext_is.csv", index=False)
print("written:", len(out), "rows")
