"""Inspect the NUTS 2021->2024 changes sheets."""
import pandas as pd

F = r"D:\EU LFS\eu-parliamentary-elections\crosswalks\NUTS2021-NUTS2024.xlsx"

for sheet in ["Changes overview", "Changes NUTS-1", "Changes NUTS-2", "Changes NUTS-3"]:
    d = pd.read_excel(F, sheet_name=sheet, header=None)
    print(f"\n===== {sheet} shape {d.shape} =====")
    print(d.to_string(max_rows=200, max_colwidth=60))
