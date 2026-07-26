"""Inspect Eurostat NUTS correspondence tables to learn their layout."""
import pandas as pd

P = r"D:\EU LFS\eu-parliamentary-elections\crosswalks"

d = pd.read_excel(P + r"\NUTS2016-NUTS2021.xlsx",
                  sheet_name="Changes detailed NUTS 2016-2021", header=None)
print("=== 2016-2021 'Changes detailed' shape", d.shape, "===")
print(d.head(20).to_string())

for sheet in ["Changes NUTS-1", "Changes NUTS-2", "Changes NUTS-3"]:
    d = pd.read_excel(P + r"\NUTS2016-NUTS2021.xlsx", sheet_name=sheet, header=None)
    print(f"\n=== 2016-2021 '{sheet}' shape {d.shape} ===")
    print(d.head(12).to_string())

d = pd.read_excel(P + r"\NUTS2021-NUTS2024.xlsx", sheet_name="NUTS2021- NUTS2024", header=None)
print("\n=== 2021-2024 correspondence shape", d.shape, "===")
print(d.head(15).to_string())
