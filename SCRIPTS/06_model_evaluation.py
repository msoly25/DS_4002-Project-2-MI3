
"""
Script: 06_model_evaluation.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Consolidate model diagnostics, decomposition
    checks, and quantitative MI2 finish-line criteria.

Inputs:
    DATA/portfolio_clean.csv
    OUTPUT/segmented_model_comparison.csv
    OUTPUT/segmented_regression_slopes.csv
    OUTPUT/selected_breakpoints.csv
    OUTPUT/seasonal_ar_model_comparison.csv
    OUTPUT/seasonal_ar_coefficients.csv
    OUTPUT/debt_growth_decomposition.csv
    OUTPUT/loan_category_reconciliation.csv
    OUTPUT/average_balance_composition.csv

Outputs:
    OUTPUT/final_evaluation_checklist.csv
    OUTPUT/final_evaluation_report.txt
    OUTPUT/final_model_comparison.png

Packages:
    pandas, matplotlib

Note:
    Breakpoint selection and inference are exploratory.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# 1. Locate project files

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "DATA"
OUT = ROOT / "OUTPUT"

OUT.mkdir(exist_ok=True)


# 2. Load previous analysis results

def read_output(filename):
    return pd.read_csv(OUT / filename)


raw = pd.read_csv(DATA / "portfolio_clean.csv")

ols = read_output("segmented_model_comparison.csv")
slopes = read_output("segmented_regression_slopes.csv")
breaks = read_output("selected_breakpoints.csv")

seasonal = read_output("seasonal_ar_model_comparison.csv")
coefficients = read_output("seasonal_ar_coefficients.csv")

growth = read_output("debt_growth_decomposition.csv")
category = read_output("loan_category_reconciliation.csv")
composition = read_output("average_balance_composition.csv")


# 3. Identify selected models

best_ols = ols.loc[ols["BIC"].idxmin()]

# Only consider models that converged.
seasonal_valid = seasonal[
    seasonal["converged"]
].copy()

if seasonal_valid.empty:
    raise ValueError("No seasonal AR model converged.")

best_seasonal = seasonal_valid.loc[
    seasonal_valid["BIC"].idxmin()
]

# Do not compare BIC directly across the two
# model families: their outcomes differ.


# 4. Review decomposition accuracy

growth_error = growth[
    "reconciliation_error_pct"
].abs().max()

category_coverage = category[
    "category_coverage_pct"
].min()

category_error = category[
    "reconciliation_error_billions"
].abs().max()

composition_error = composition[
    "reconciliation_error_thousands"
].abs().max()


# 5. Check the MI2 finish-line requirements

expected_models = {0, 1, 2}

checks = {
    "Three segmented regression models evaluated":
        set(ols["breakpoint_count"]) == expected_models,

    "Three seasonal AR models evaluated":
        set(seasonal["breakpoint_count"]) == expected_models,

    "All seasonal AR models converged":
        bool(seasonal["converged"].all()),

    "Segment slopes and HAC intervals reported":
        (
            len(slopes) ==
            int(best_ols["breakpoint_count"]) + 1
            and slopes[
                ["HAC_CI_lower", "HAC_CI_upper"]
            ].notna().all().all()
        ),

    "Selected breakpoints documented":
        len(breaks) == int(best_ols["breakpoint_count"]),

    "Debt decomposition error <= 0.1%":
        bool(growth_error <= 0.1),

    "Loan category coverage >= 99%":
        bool(category_coverage >= 99),

    "Loan category debt reconciliation":
        bool(category_error < 1e-8),

    "Average balance effects reconcile":
        bool(composition_error < 1e-8),

    "Seasonal residual diagnostics reported":
        bool(
            pd.notna(best_seasonal["Ljung_Box_p_lag4"])
            and pd.notna(best_seasonal["Ljung_Box_p_lag8"])
        )
}

checklist = pd.DataFrame([
    {"requirement": name, "passed": bool(value)}
    for name, value in checks.items()
])

checklist.to_csv(
    OUT / "final_evaluation_checklist.csv",
    index=False
)

all_passed = all(checks.values())


# 6. Extract key results

full_growth = growth[
    growth["period"] == "Full period"
].iloc[0]

full_composition = composition[
    composition["period"] == "Full period"
].iloc[0]

break_names = "; ".join(
    breaks["fiscal_quarter"].astype(str)
)

# Assess the conditional confidence interval
# for the second seasonal-model growth shift.
second_shift = coefficients[
    coefficients["parameter"] == "after_break_2"
]

if second_shift.empty:
    second_shift_text = (
        "No second-break coefficient available."
    )
else:
    estimate = second_shift.iloc[0]

    lower = float(estimate["CI_lower"])
    upper = float(estimate["CI_upper"])

    includes_zero = lower <= 0 <= upper

    second_shift_text = (
        f"Second growth-shift estimate: "
        f"{estimate['estimate']:.3f} billion/quarter\n"
        f"Conditional 95% CI: "
        f"[{lower:.3f}, {upper:.3f}]\n"
        f"Interval includes zero: {includes_zero}"
    )


# 7. Create the evaluation report

report = [
    "U.S. Federal Student Debt Analysis",
    "Final Model Evaluation Report",
    "=" * 55,
    "",
    "1. DATA",
    f"Total observations: {len(raw)}",
    "Quarterly observations: "
    f"{raw['quarter'].isin(['Q1','Q2','Q3','Q4']).sum()}",
    "",
    "2. SEGMENTED REGRESSION",
    f"Selected breakpoints: {break_names}",
    f"Debt-level model BIC: {best_ols['BIC']:.3f}",
    f"Debt-level RMSE ($B): {best_ols['RMSE_billions']:.3f}",
    "",
    "3. SEASONALLY ADJUSTED MODEL",
    f"Selected breakpoint count: "
    f"{int(best_seasonal['breakpoint_count'])}",
    f"Seasonal AR BIC: {best_seasonal['BIC']:.3f}",
    "Residual Ljung-Box p-value, lag 4: "
    f"{best_seasonal['Ljung_Box_p_lag4']:.4f}",
    "Residual Ljung-Box p-value, lag 8: "
    f"{best_seasonal['Ljung_Box_p_lag8']:.4f}",
    "",
    second_shift_text,
    "",
    "4. TOTAL DEBT GROWTH DECOMPOSITION",
    "Observed debt increase ($B): "
    f"{full_growth['debt_change_billions']:.3f}",
    "Recipient contribution ($B): "
    f"{full_growth['recipient_effect_billions']:.3f}",
    "Average-balance contribution ($B): "
    f"{full_growth['balance_effect_billions']:.3f}",
    f"Maximum reconciliation error (%): {growth_error:.10f}",
    "",
    "5. LOAN CATEGORY AND COMPOSITION",
    f"Minimum category coverage (%): "
    f"{category_coverage:.4f}",
    "Within-category effect ($thousands): "
    f"{full_composition['within_category_effect_thousands']:.4f}",
    "Loan composition effect ($thousands): "
    f"{full_composition['composition_effect_thousands']:.4f}",
    "Overlap effect ($thousands): "
    f"{full_composition['overlap_effect_thousands']:.4f}",
    "Maximum composition reconciliation error: "
    f"{composition_error:.12f}",
    "",
    "6. MI2 FINISH-LINE CHECKLIST"
]

for name, passed in checks.items():
    report.append(
        f"{'PASS' if passed else 'FAIL'}: {name}"
    )

report.extend([
    "",
    f"ALL QUANTITATIVE CHECKS PASSED: {all_passed}",
    "",
    "7. INTERPRETATION AND LIMITATIONS",
    "The analysis describes associations and",
    "accounting contributions, not causal effects.",
    "Debt outstanding is a persistent cumulative series.",
    "The original regression has autocorrelated errors.",
    "The seasonal AR model adjusts for quarterly",
    "seasonality and autoregressive dependence.",
    "Residual tests do not detect significant remaining",
    "autocorrelation at the evaluated lags, but cannot",
    "establish that residuals are independent.",
    "Breakpoint dates were selected from the same data.",
    "BIC preference does not establish structural breaks.",
    "Conditional confidence intervals do not account",
    "for the uncertainty of breakpoint selection.",
    "Annual FY2007-2012 observations are not included",
    "in the quarterly regression.",
    "Category recipients can overlap across programs."
])

(OUT / "final_evaluation_report.txt").write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)


# 8. Plot seasonal-model BIC comparison
# Only compare BIC values within the same family.

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    seasonal["breakpoint_count"],
    seasonal["BIC"],
    marker="o",
    linewidth=2
)

ax.set_xticks([0, 1, 2])
ax.set_xlabel("Number of Candidate Breakpoints")
ax.set_ylabel("Seasonal AR BIC (lower is better)")

ax.set_title(
    "Seasonally Adjusted Model Comparison"
)

ax.grid(alpha=0.3)

fig.tight_layout()

fig.savefig(
    OUT / "final_model_comparison.png",
    dpi=300
)

plt.close(fig)


# 9. Display final results

print("FINAL MODEL EVALUATION")

print("\nMI2 finish-line checks:")
print(checklist.to_string(index=False))

print("\nAll checks passed:", all_passed)

print("\nFinal results saved in:", OUT)

if not all_passed:
    raise ValueError(
        "One or more finish-line criteria failed. "
        "Review the evaluation checklist."
    )
