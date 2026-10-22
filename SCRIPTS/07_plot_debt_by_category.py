"""
Script: 07_plot_debt_by_category.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Plot outstanding federal student debt by loan category.

Input:
    DATA/portfolio_clean.csv

Output:
    OUTPUT/Federal Student Debt By Loan Category.png

Required packages:
    pandas, matplotlib
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# Locate files relative to the repository, regardless of the current directory.
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "DATA" / "portfolio_clean.csv"
OUTPUT_FILE = ROOT / "OUTPUT" / "Federal Student Debt By Loan Category.png"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# Load and order the cleaned data.
df = pd.read_csv(DATA_FILE, parse_dates=["period_end"])
df = df.sort_values("period_end")

# Plot outstanding debt for the three reported loan programs.
fig, ax = plt.subplots(figsize=(14, 8))
ax.plot(df["period_end"], df["direct_debt_billions"], label="Direct Loans")
ax.plot(df["period_end"], df["ffel_debt_billions"], label="FFEL")
ax.plot(df["period_end"], df["perkins_debt_billions"], label="Perkins")

ax.set_title("Federal Student Debt by Loan Category")
ax.set_xlabel("Reporting Date")
ax.set_ylabel("Outstanding Debt ($ Billions)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(OUTPUT_FILE, dpi=300)
plt.close(fig)

print("Loan-category debt plot saved to:")
print(OUTPUT_FILE)
