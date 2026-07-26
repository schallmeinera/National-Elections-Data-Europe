"""Bulgaria parliamentary elections June 2024 + October 2024 (CIK open data,
section-level votes.txt) -> NUTS-3.

Section code (9 digits) = MIR(2) + obshtina(2) + adm-rayon(2) + section(3).
The first 2 digits are the MIR (multi-mandate constituency) number, which maps
1:1 to an oblast NUTS-3 (Sofia city MIRs 23/24/25 -> BG411; MIR 32 abroad ->
BGZZZ). votes.txt fields: form; section; adminId; then repeating
(party_num; valid; paper; machine)."""
import glob
import pandas as pd
import numpy as np

BASE = r"D:\EU LFS\eu-parliamentary-elections"

# MIR number -> NUTS-3 (2016), standard Bulgarian constituency numbering
MIR_NUTS3 = {
    1: "BG413", 2: "BG341", 3: "BG331", 4: "BG321", 5: "BG311", 6: "BG313",
    7: "BG322", 8: "BG332", 9: "BG425", 10: "BG415", 11: "BG315", 12: "BG312",
    13: "BG423", 14: "BG414", 15: "BG314", 16: "BG421", 17: "BG421",
    18: "BG324", 19: "BG323", 20: "BG325", 21: "BG342", 22: "BG424",
    23: "BG411", 24: "BG411", 25: "BG411", 26: "BG412", 27: "BG344",
    28: "BG334", 29: "BG422", 30: "BG333", 31: "BG343", 32: "BGZZZ"}

ELECTIONS = {
    (2024, 6): rf"{BASE}\raw\bg2024jun\Актуализирана база данни - НС",
    (2024, 10): rf"{BASE}\raw\bg2024oct\Актуализирана база данни",
}

frames = []
for (yr, mo), folder in ELECTIONS.items():
    parties = {}
    for line in open(glob.glob(rf"{folder}\cik_parties_*.txt")[0],
                     encoding="utf-8"):
        num, name = line.rstrip("\n").split(";", 1)
        parties[int(num)] = name

    rows = {}
    vfile = glob.glob(rf"{folder}\votes_*.txt")[0]
    for line in open(vfile, encoding="utf-8"):
        f = line.rstrip("\n").split(";")
        section = f[1]
        mir = int(section[:2])
        nuts = MIR_NUTS3[mir]
        rest = f[3:]
        for k in range(0, len(rest), 4):
            pnum = int(rest[k])
            valid = int(rest[k + 1])
            rows[(nuts, pnum)] = rows.get((nuts, pnum), 0) + valid

    df = pd.DataFrame([(n, parties.get(p, str(p)), v)
                       for (n, p), v in rows.items()],
                      columns=["nuts_code", "party_native", "partyvote"])
    df = df[df.partyvote > 0]
    df["validvote"] = df.groupby("nuts_code").partyvote.transform("sum")
    df["year"], df["month"] = yr, mo
    frames.append(df)
    print(f"{yr}-{mo:02d}: {df.partyvote.sum():,} votes, "
          f"{df.nuts_code.nunique()} regions, {df.party_native.nunique()} parties")

out = pd.concat(frames, ignore_index=True)
out["electorate"] = np.nan
out["totalvote"] = np.nan
out["country"], out["country_code"] = "Bulgaria", "BG"
out["party_abbreviation"] = np.nan
out["party_english"] = np.nan
out["partyfacts_id"] = np.nan
out["regionname"] = np.nan
out["source"] = "CIK results.cik.bg open data (section votes)"
out.to_csv(rf"{BASE}\raw\ext_bg2024.csv", index=False)
print("written:", len(out), "rows")
