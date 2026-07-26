"""Belgium Chamber 2024 via api.electionresults.belgium.be:
11 constituencies = provinces/Brussels = NUTS-2."""
import json
import subprocess
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"
CONST_NUTS2 = {  # election-level id -> NUTS2 (2016)
    250987: "BE21", 250990: "BE10", 250993: "BE24", 250995: "BE31",
    250997: "BE25", 250999: "BE23", 251002: "BE32", 251007: "BE33",
    251011: "BE22", 251013: "BE34", 251016: "BE35"}


def api(path):
    b = subprocess.run(["curl.exe", "-sL",
                        "https://api.electionresults.belgium.be" + path],
                       capture_output=True).stdout
    return json.loads(b.decode("utf-8-sig"))


rows = []
for lid, nuts in CONST_NUTS2.items():
    j = api(f"/election-level/{lid}")
    label = [x["label"] for x in j["labels"] if x["language"] == "Dutch"]
    valid = j["nrOfValidVotes"]
    blank = j["nrOfBlankVotes"] or 0
    elig = j["nrOfEligibleVoters"]
    total = valid + blank  # blank+invalid reported jointly as blank votes
    for pl in j["electionLists"]:
        name = pl.get("partyLabel")
        votes = pl.get("nrOfVotes")
        if votes and votes > 0:
            rows.append((nuts, name, votes, elig, total, valid))
    print(lid, nuts, label[0] if label else "?", valid, len(j["electionLists"]))

out = pd.DataFrame(rows, columns=["nuts_code", "party_native", "partyvote",
                                  "electorate", "totalvote", "validvote"])
out["country"], out["country_code"] = "Belgium", "BE"
out["year"], out["month"] = 2024, 6
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "IBZ api.electionresults.belgium.be (Chamber)"
out.to_csv(rf"{BASE}\raw\ext_be2024.csv", index=False)
print("written:", len(out), "rows,", out.nuts_code.nunique(), "NUTS2,",
      f"votes {out.partyvote.sum():,.0f}")
