
Input:
    PortfolioSummary.xlsx

Output:
    DATA/portfolio_clean.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd


# 1. Set up project folders
ROOT = Path("/content/drive/MyDrive/DS Project 2")
DATA_DIR = ROOT / "DATA"
SCRIPTS_DIR = ROOT / "SCRIPTS"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Look for the original Excel file in either location.
possible_files = [
    DATA_DIR / "PortfolioSummary.xlsx",
    ROOT / "PortfolioSummary.xlsx",
]
INPUT_FILE = next((file for file in possible_files if file.exists()), None)
OUTPUT_FILE = DATA_DIR / "portfolio_clean.csv"

if INPUT_FILE is None:
    raise FileNotFoundError(
        "Could not find PortfolioSummary.xlsx. Place it in either "
        "the DS Project 2 folder or its DATA folder in Google Drive."
    )

print("Original Excel file found:", INPUT_FILE)


# 2. Read the original Excel file
raw = pd.read_excel(INPUT_FILE, header=None, engine="openpyxl")
print("Original file dimensions:", raw.shape)

# Assumes observations occupy zero-based rows 6 through 66
# and the first 10 columns.
df = raw.iloc[6:67, :10].copy()


# 3. Standardize column names
columns = [
    "fiscal_year",
    "quarter",
    "direct_debt_billions",
    "direct_recipients_millions",
    "ffel_debt_billions",
    "ffel_recipients_millions",
    "perkins_debt_billions",
    "perkins_recipients_millions",
    "total_debt_billions",
    "total_recipients_millions",
]

if df.shape[1] != len(columns):
    raise ValueError(
        f"Expected 10 columns, but found {df.shape[1]}. "
        "Check the original Excel file layout."
    )

df.columns = columns
df = df.dropna(how="all").copy()


# 4. Clean fiscal years and numeric columns
df["fiscal_year"] = pd.to_numeric(
    df["fiscal_year"], errors="coerce"
).ffill()

df["quarter"] = (
    df["quarter"].fillna("").astype(str).str.strip().str.upper()
)

numeric_columns = columns[2:]
for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Remove rows without a usable fiscal year or total debt value.
df = df.dropna(
    subset=["fiscal_year", "total_debt_billions"]
).copy()
df["fiscal_year"] = df["fiscal_year"].astype(int)


# 5. Convert fiscal periods into reporting dates
def get_period_end(fiscal_year, quarter):
    """Return the calendar date for a fiscal reporting period."""
    fy = int(fiscal_year)
    q = str(quarter).strip().upper()

    if q in {"", "A", "ANNUAL", "YEAR", "FY"}:
        return pd.Timestamp(fy, 9, 30)

    quarter_dates = {
        "Q1": (fy - 1, 12, 31),
        "Q2": (fy, 3, 31),
        "Q3": (fy, 6, 30),
        "Q4": (fy, 9, 30),
    }

    if q not in quarter_dates:
        raise ValueError(
            f"Unrecognized quarter label: {quarter!r}. "
            "Check the original Excel file before continuing."
        )

    year, month, day = quarter_dates[q]
    return pd.Timestamp(year, month, day)


df["period_end"] = [
    get_period_end(year, quarter)
    for year, quarter in zip(df["fiscal_year"], df["quarter"])
]


# 6. Calculate average outstanding balance per recipient
# Debt is in billions of dollars and recipient counts are in
# millions, so the result is thousands of dollars per recipient.
balance_pairs = [
    ("direct_debt_billions", "direct_recipients_millions",
     "direct_avg_balance_thousands"),
    ("ffel_debt_billions", "ffel_recipients_millions",
     "ffel_avg_balance_thousands"),
    ("perkins_debt_billions", "perkins_recipients_millions",
     "perkins_avg_balance_thousands"),
    ("total_debt_billions", "total_recipients_millions",
     "total_avg_balance_thousands"),
]

for debt_column, recipient_column, new_column in balance_pairs:
    recipients = df[recipient_column].replace(0, np.nan)
    df[new_column] = df[debt_column] / recipients


# 7. Sort and validate the cleaned data
df = df.sort_values("period_end").reset_index(drop=True)

print("\n--- Data Validation Report ---")
print("Number of observations:", len(df))
print("First reporting date:", df["period_end"].min())
print("Last reporting date:", df["period_end"].max())

duplicate_dates = int(df["period_end"].duplicated().sum())
print("Duplicate reporting dates:", duplicate_dates)

print("\nMissing values by column:")
print(df.isna().sum().to_string())

if duplicate_dates > 0:
    raise ValueError("Duplicate reporting dates found. Investigate before saving.")

if df["period_end"].isna().any():
    raise ValueError("Some reporting dates are missing.")

if df[numeric_columns].isna().any().any():
    raise ValueError(
        "Missing or non-numeric values remain in required numeric columns. "
        "Investigate before saving."
    )

average_columns = [
    "direct_avg_balance_thousands",
    "ffel_avg_balance_thousands",
    "perkins_avg_balance_thousands",
    "total_avg_balance_thousands",
]
print("\nMissing values in calculated average-balance columns:")
print(df[average_columns].isna().sum().to_string())


# 8. Save the cleaned dataset
df["period_end"] = df["period_end"].dt.strftime("%Y-%m-%d")
df.to_csv(OUTPUT_FILE, index=False)

print("\nCleaned dataset saved successfully:")
print(OUTPUT_FILE)
print("\nFirst five rows:")
print(df.head().to_string(index=False))
