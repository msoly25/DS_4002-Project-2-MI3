
"""
Script: 05_loan_composition.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Analyze Direct, FFEL, and Perkins debt, recipient
    counts, loan shares, and within-category,
    composition, and overlap effects.

Inputs:
    DATA/portfolio_clean.csv
    OUTPUT/selected_breakpoints.csv

Outputs:
    OUTPUT/loan_category_changes.csv
    OUTPUT/loan_category_reconciliation.csv
    OUTPUT/average_balance_composition.csv
    OUTPUT/loan_category_shares.png
    OUTPUT/average_balance_effects.png
    OUTPUT/loan_composition_validation.txt

Required packages:
    numpy, pandas, matplotlib

Notes:
    Recipients may appear in multiple loan programs.
    Breakpoints are exploratory.
    Results are descriptive, not causal.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# 1. Set up file paths

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "DATA" / "portfolio_clean.csv"
BREAKS = ROOT / "OUTPUT" / "selected_breakpoints.csv"
OUT = ROOT / "OUTPUT"

OUT.mkdir(exist_ok=True)

loans = {
    "Direct": (
        "direct_debt_billions",
        "direct_recipients_millions"
    ),
    "FFEL": (
        "ffel_debt_billions",
        "ffel_recipients_millions"
    ),
    "Perkins": (
        "perkins_debt_billions",
        "perkins_recipients_millions"
    )
}


# 2. Load cleaned data and breakpoint dates

df = pd.read_csv(
    DATA,
    parse_dates=["period_end"]
)

df = df.sort_values("period_end").reset_index(drop=True)

breaks = pd.read_csv(
    BREAKS,
    parse_dates=["period_end"]
).sort_values("period_end")

quarterly = df[
    df["quarter"].isin(["Q1", "Q2", "Q3", "Q4"])
].copy()

if df["period_end"].duplicated().any() or quarterly.empty:
    raise ValueError("Invalid reporting dates.")


# 3. Define the periods to compare

def fiscal_label(row):
    q = row["quarter"]
    label = f"FY{int(row['fiscal_year'])}"

    if pd.notna(q):
        label += f" {q}"

    return label


periods = [
    (
        "Full period",
        df.iloc[0],
        df.iloc[-1]
    )
]

dates = (
    [quarterly.iloc[0]["period_end"]]
    + breaks["period_end"].tolist()
    + [quarterly.iloc[-1]["period_end"]]
)

lookup = quarterly.set_index("period_end")

if len(set(dates)) != len(dates) or dates != sorted(dates):
    raise ValueError("Invalid breakpoint ordering.")

for i, (start_date, end_date) in enumerate(
    zip(dates[:-1], dates[1:]),
    1
):

    if start_date not in lookup.index:
        raise ValueError("Start date missing.")

    if end_date not in lookup.index:
        raise ValueError("End date missing.")

    start = lookup.loc[start_date]
    end = lookup.loc[end_date]

    periods.append(
        (
            f"Segment {i}: "
            f"{fiscal_label(start)} to {fiscal_label(end)}",
            start,
            end
        )
    )


# 4. Calculate category-level measures
#
# Loan category recipient counts can overlap.
# Each loan's average is debt / recipients.
#
# Category weights use the sum of category
# recipient counts, NOT unique recipients.
#
# The overlap factor adjusts this sum against
# the reported unduplicated recipient total.

def metrics(row):

    debts = np.array([
        float(row[debt_col])
        for debt_col, _ in loans.values()
    ])

    recipients = np.array([
        float(row[recipient_col])
        for _, recipient_col in loans.values()
    ])

    total_debt = float(row["total_debt_billions"])

    unique = float(row["total_recipients_millions"])

    if (recipients <= 0).any() or unique <= 0:
        raise ValueError("Invalid recipient counts.")

    recipient_sum = recipients.sum()

    weights = recipients / recipient_sum

    averages = debts / recipients

    weighted_average = np.dot(
        weights,
        averages
    )

    multiplicity = recipient_sum / unique

    reporting_gap = (
        total_debt - debts.sum()
    ) / unique

    return {
        "debts": debts,
        "recipients": recipients,
        "weights": weights,
        "averages": averages,
        "weighted_average": weighted_average,
        "multiplicity": multiplicity,
        "reporting_gap": reporting_gap,
        "total_debt": total_debt,
        "total_avg": total_debt / unique
    }


# 5. Analyze debt changes by loan category

category_rows = []
debt_checks = []
balance_rows = []

for period_name, start, end in periods:

    x = metrics(start)
    z = metrics(end)

    debt_change = (
        z["total_debt"] - x["total_debt"]
    )

    category_changes = z["debts"] - x["debts"]

    gap_start = (
        x["total_debt"] - x["debts"].sum()
    )

    gap_end = (
        z["total_debt"] - z["debts"].sum()
    )

    gap_change = gap_end - gap_start

    if abs(debt_change) > 1e-12:
        coverage = 100 * (
            1 - abs(gap_change) / abs(debt_change)
        )
    else:
        coverage = np.nan

    for j, name in enumerate(loans):

        category_rows.append({
            "period": period_name,
            "category": name,

            "start_debt_billions": x["debts"][j],
            "end_debt_billions": z["debts"][j],

            "change_debt_billions": category_changes[j],

            "contribution_pct_total_change": (
                100 * category_changes[j] / debt_change
                if abs(debt_change) > 1e-12
                else np.nan
            ),

            "start_recipients_millions":
                x["recipients"][j],

            "end_recipients_millions":
                z["recipients"][j],

            "change_recipients_millions":
                z["recipients"][j] - x["recipients"][j],

            "start_avg_balance_thousands":
                x["averages"][j],

            "end_avg_balance_thousands":
                z["averages"][j],

            "change_avg_balance_thousands":
                z["averages"][j] - x["averages"][j],

            "start_debt_share_pct":
                100 * x["debts"][j] / x["total_debt"],

            "end_debt_share_pct":
                100 * z["debts"][j] / z["total_debt"]
        })

    debt_error = debt_change - (
        category_changes.sum() + gap_change
    )

    debt_checks.append({
        "period": period_name,
        "total_debt_change_billions": debt_change,
        "sum_category_changes_billions":
            category_changes.sum(),
        "change_reporting_gap_billions": gap_change,
        "category_coverage_pct": coverage,
        "reconciliation_error_billions": debt_error
    })


    # 6. Decompose changes in average balance
    #
    # Total average debt =
    # overlap factor * weighted category average
    # + reporting gap per unique recipient.
    #
    # Midpoint decomposition separates changes
    # into within-category, composition, overlap,
    # and reporting-gap effects.

    midpoint_m = (
        x["multiplicity"] + z["multiplicity"]
    ) / 2

    midpoint_weights = (
        x["weights"] + z["weights"]
    ) / 2

    midpoint_averages = (
        x["averages"] + z["averages"]
    ) / 2

    within = midpoint_m * np.dot(
        midpoint_weights,
        z["averages"] - x["averages"]
    )

    composition = midpoint_m * np.dot(
        midpoint_averages,
        z["weights"] - x["weights"]
    )

    overlap = (
        (x["weighted_average"] + z["weighted_average"])
        / 2
        * (z["multiplicity"] - x["multiplicity"])
    )

    gap_effect = (
        z["reporting_gap"] - x["reporting_gap"]
    )

    average_change = (
        z["total_avg"] - x["total_avg"]
    )

    average_error = average_change - (
        within + composition + overlap + gap_effect
    )

    balance_rows.append({
        "period": period_name,

        "start_total_avg_thousands":
            x["total_avg"],

        "end_total_avg_thousands":
            z["total_avg"],

        "change_avg_thousands":
            average_change,

        "within_category_effect_thousands":
            within,

        "composition_effect_thousands":
            composition,

        "overlap_effect_thousands":
            overlap,

        "reporting_gap_effect_thousands":
            gap_effect,

        "starting_overlap_factor":
            x["multiplicity"],

        "ending_overlap_factor":
            z["multiplicity"],

        "reconciliation_error_thousands":
            average_error
    })


# 7. Save the three analysis tables

cats = pd.DataFrame(category_rows)
debt = pd.DataFrame(debt_checks)
bal = pd.DataFrame(balance_rows)

cats.to_csv(
    OUT / "loan_category_changes.csv",
    index=False
)

debt.to_csv(
    OUT / "loan_category_reconciliation.csv",
    index=False
)

bal.to_csv(
    OUT / "average_balance_composition.csv",
    index=False
)


# 8. Validate the MI2 success requirements

coverage_pass = bool(
    (debt["category_coverage_pct"] >= 99).all()
)

debt_check_pass = bool(
    (
        debt["reconciliation_error_billions"].abs()
        < 1e-8
    ).all()
)

balance_check_pass = bool(
    (
        bal["reconciliation_error_thousands"].abs()
        < 1e-8
    ).all()
)

with open(
    OUT / "loan_composition_validation.txt",
    "w"
) as file:

    file.write(
        "Loan category and composition validation\n\n"
    )

    file.write(
        f"Category coverage >= 99%: {coverage_pass}\n"
    )

    file.write(
        f"Debt reconciliation passed: {debt_check_pass}\n"
    )

    file.write(
        "Average-balance reconciliation passed: "
        f"{balance_check_pass}\n\n"
    )

    file.write(
        "Category recipient counts overlap.\n"
        "Overlap factor = sum of category counts / "
        "unduplicated recipients.\n"
        "Reporting-gap effect accounts for differences "
        "between reported total and category sums.\n"
        "Breakpoints are exploratory.\n"
        "Decomposition is descriptive, not causal.\n"
    )

if not (
    coverage_pass
    and debt_check_pass
    and balance_check_pass
):
    raise ValueError(
        "Loan composition validation failed."
    )


# 9. Create a graph of category debt shares

fig, ax = plt.subplots(figsize=(11, 5))

for name, (debt_col, _) in loans.items():

    ax.plot(
        df["period_end"],
        100 * df[debt_col] / df["total_debt_billions"],
        label=name
    )

ax.set_title(
    "Federal Student Debt by Loan Category: Share of Total"
)

ax.set_xlabel("Reporting Date")
ax.set_ylabel("Share of Outstanding Debt (%)")

ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()

fig.savefig(
    OUT / "loan_category_shares.png",
    dpi=300
)

plt.close(fig)


# 10. Create the average-balance effects graph

fig, ax = plt.subplots(figsize=(12, 6))

effect_columns = [
    "within_category_effect_thousands",
    "composition_effect_thousands",
    "overlap_effect_thousands",
    "reporting_gap_effect_thousands"
]

effect_labels = [
    "Within-category",
    "Category mix",
    "Overlap adjustment",
    "Reporting gap"
]

positions = np.arange(len(bal))
width = 0.2

for i, (column, label) in enumerate(
    zip(effect_columns, effect_labels)
):

    ax.bar(
        positions + (i - 1.5) * width,
        bal[column],
        width,
        label=label
    )

ax.set_xticks(positions)

ax.set_xticklabels(
    ["Full period"] + [
        f"Segment {i}"
        for i in range(1, len(bal))
    ]
)

ax.axhline(0, color="black", linewidth=1)

ax.set_title(
    "Changes in Average Debt per Recipient"
)

ax.set_xlabel("Comparison Period")

ax.set_ylabel(
    "Contribution ($ Thousands per Recipient)"
)

ax.legend()
ax.grid(axis="y", alpha=0.3)

fig.tight_layout()

fig.savefig(
    OUT / "average_balance_effects.png",
    dpi=300
)

plt.close(fig)


# 11. Print results for review

print("Loan category and composition analysis completed.")

print("\nCATEGORY DEBT RECONCILIATION")

print(
    debt.round(4).to_string(index=False)
)

print("\nAVERAGE-BALANCE DECOMPOSITION")

print(
    bal[
        [
            "period",
            "within_category_effect_thousands",
            "composition_effect_thousands",
            "overlap_effect_thousands",
            "reporting_gap_effect_thousands",
            "change_avg_thousands"
        ]
    ].round(4).to_string(index=False)
)

print("\nALL VALIDATIONS PASSED:", (
    coverage_pass
    and debt_check_pass
    and balance_check_pass
))

print("\nResults saved in:", OUT)
