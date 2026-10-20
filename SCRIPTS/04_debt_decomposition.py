
"""
Script: 04_debt_decomposition.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Decompose total federal student debt growth into
    recipient-count and average-balance effects using
    the midpoint decomposition method.

Inputs:
    DATA/portfolio_clean.csv
    OUTPUT/selected_breakpoints.csv

Outputs:
    OUTPUT/debt_growth_decomposition.csv
    OUTPUT/debt_decomposition_contributions.png
    OUTPUT/decomposition_validation.txt

Required packages:
    pandas, numpy, matplotlib

Note:
    This is an accounting decomposition, not a
    causal analysis or statistical significance test.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# 1. Locate the repository and input files

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "DATA" / "portfolio_clean.csv"
BREAKPOINT_FILE = ROOT / "OUTPUT" / "selected_breakpoints.csv"
OUTPUT_DIR = ROOT / "OUTPUT"

OUTPUT_DIR.mkdir(exist_ok=True)


# 2. Load cleaned data and selected breakpoints

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["period_end"]
)

df = df.sort_values("period_end").reset_index(drop=True)

breakpoints = pd.read_csv(
    BREAKPOINT_FILE,
    parse_dates=["period_end"]
)

break_dates = sorted(breakpoints["period_end"].tolist())


# 3. Define a function to label fiscal periods

def fiscal_label(row):
    year = int(row["fiscal_year"])
    quarter = row["quarter"]

    if pd.notna(quarter) and str(quarter).startswith("Q"):
        return f"FY{year} {quarter}"

    return f"FY{year}"


# 4. Define midpoint decomposition
#
# Total debt (billions) =
# recipients (millions) * average balance (thousands)
#
# Recipient effect:
# change in R * midpoint of A
#
# Average-balance effect:
# change in A * midpoint of R

def decompose(start, end, period_name):

    d0 = float(start["total_debt_billions"])
    d1 = float(end["total_debt_billions"])

    r0 = float(start["total_recipients_millions"])
    r1 = float(end["total_recipients_millions"])

    if min(r0, r1) <= 0:
        raise ValueError("Recipient counts must be positive.")

    # Average outstanding balance, in thousands
    a0 = d0 / r0
    a1 = d1 / r1

    debt_change = d1 - d0

    # Midpoint contributions, in billions
    recipient_effect = (
        (r1 - r0) * (a0 + a1) / 2
    )

    balance_effect = (
        (a1 - a0) * (r0 + r1) / 2
    )

    combined = recipient_effect + balance_effect
    error = debt_change - combined

    # Handle the possibility of zero total change
    if abs(debt_change) > 1e-10:
        recipient_pct = 100 * recipient_effect / debt_change
        balance_pct = 100 * balance_effect / debt_change
        error_pct = 100 * abs(error) / abs(debt_change)
    else:
        recipient_pct = np.nan
        balance_pct = np.nan
        error_pct = 0.0 if abs(error) < 1e-10 else np.inf

    return {
        "period": period_name,
        "start_date": start["period_end"].date().isoformat(),
        "end_date": end["period_end"].date().isoformat(),
        "start_debt_billions": d0,
        "end_debt_billions": d1,
        "start_recipients_millions": r0,
        "end_recipients_millions": r1,
        "debt_change_billions": debt_change,
        "recipient_effect_billions": recipient_effect,
        "balance_effect_billions": balance_effect,
        "recipient_share_pct": recipient_pct,
        "balance_share_pct": balance_pct,
        "reconciliation_error_billions": error,
        "reconciliation_error_pct": error_pct
    }


# 5. Decompose growth across the full dataset

results = []

results.append(
    decompose(
        df.iloc[0],
        df.iloc[-1],
        "Full period"
    )
)


# 6. Decompose quarterly growth between breakpoints
#
# The breakpoint dates are read from Step 2 instead
# of being entered manually.
#
# Each segment uses its two endpoint observations.
# The shared endpoints prevent gaps in accounting.

quarterly = df[
    df["quarter"].isin(["Q1", "Q2", "Q3", "Q4"])
].copy()

quarterly = quarterly.sort_values(
    "period_end"
).reset_index(drop=True)

boundaries = (
    [quarterly.iloc[0]["period_end"]]
    + break_dates
    + [quarterly.iloc[-1]["period_end"]]
)

for i in range(len(boundaries) - 1):

    start_date = boundaries[i]
    end_date = boundaries[i + 1]

    if start_date >= end_date:
        raise ValueError("Invalid breakpoint ordering.")

    start_match = quarterly[
        quarterly["period_end"] == start_date
    ]

    end_match = quarterly[
        quarterly["period_end"] == end_date
    ]

    if start_match.empty or end_match.empty:
        raise ValueError(
            "A breakpoint is missing from quarterly data."
        )

    start = start_match.iloc[0]
    end = end_match.iloc[0]

    results.append(
        decompose(
            start,
            end,
            f"Segment {i + 1}: "
            f"{fiscal_label(start)} to {fiscal_label(end)}"
        )
    )


# 7. Save results as a CSV table

summary = pd.DataFrame(results)

summary.to_csv(
    OUTPUT_DIR / "debt_growth_decomposition.csv",
    index=False
)


# 8. Validate reconciliation against MI2 goal
#
# Each decomposition must reproduce the observed
# change in total debt within 0.1%.

max_error = summary[
    "reconciliation_error_pct"
].max()

validation_passed = bool(max_error <= 0.1)

if not validation_passed:
    raise ValueError(
        "Midpoint decomposition failed reconciliation. "
        "Check input units and calculations."
    )

validation_report = [
    "Debt Growth Decomposition Validation",
    "",
    "Method: midpoint decomposition",
    "Required reconciliation tolerance: 0.1%",
    f"Maximum reconciliation error: {max_error:.10f}%",
    f"Validation passed: {validation_passed}",
    "",
    "Recipient counts use unduplicated total recipients.",
    "This is an accounting decomposition, not causal.",
    "Period breakpoints are exploratory.",
    "",
    "The full-history row starts in FY2007.",
    "Quarterly segments start in FY2013 Q1.",
    "Therefore, quarterly segments do not sum to",
    "the full-history change."
]

(OUTPUT_DIR / "decomposition_validation.txt").write_text(
    "\n".join(validation_report) + "\n",
    encoding="utf-8"
)


# 9. Create a figure comparing contributions

x = np.arange(len(summary))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(
    x - width / 2,
    summary["recipient_effect_billions"],
    width,
    label="Recipient-count effect"
)

ax.bar(
    x + width / 2,
    summary["balance_effect_billions"],
    width,
    label="Average-balance effect"
)

ax.axhline(0, color="black", linewidth=1)

ax.set_xticks(x)
ax.set_xticklabels(
    summary["period"],
    rotation=15,
    ha="right"
)

ax.set_ylabel("Contribution to Debt Change ($ Billions)")
ax.set_title(
    "Federal Student Debt Growth Decomposition"
)

ax.legend()
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "debt_decomposition_contributions.png",
    dpi=300
)

plt.close()


# 10. Print summary for verification

print("Debt decomposition completed.")

print("\nContribution summary:")
print(
    summary[
        [
            "period",
            "debt_change_billions",
            "recipient_effect_billions",
            "balance_effect_billions",
            "reconciliation_error_pct"
        ]
    ].round(4).to_string(index=False)
)

print("\nMaximum reconciliation error (%):")
print(round(max_error, 10))

print("\nValidation passed:", validation_passed)

print("\nFiles saved in:", OUTPUT_DIR)
