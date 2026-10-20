
"""
Script: 03_segmented_regression.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Compare segmented debt trends with 0, 1, or 2
    breakpoints and examine serial correlation.

Input:
    DATA/portfolio_clean.csv

Outputs:
    OUTPUT/segmented_model_comparison.csv
    OUTPUT/segmented_regression_slopes.csv
    OUTPUT/selected_breakpoints.csv
    OUTPUT/segmented_regression_fit.png
    OUTPUT/quarterly_debt_changes.png
    OUTPUT/regression_diagnostics.txt

Packages:
    numpy, pandas, matplotlib, statsmodels

Note:
    Breakpoints and p-values are exploratory.
    HAC does not correct for breakpoint selection.
"""

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson


# 1. Locate the project files
ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "DATA" / "portfolio_clean.csv"
OUT = ROOT / "OUTPUT"
OUT.mkdir(exist_ok=True)


# 2. Load quarterly observations
# Annual records before FY2013 are excluded.
df = pd.read_csv(INPUT, parse_dates=["period_end"])

quarterly = df[
    df["quarter"].fillna("").astype(str).str.fullmatch(r"Q[1-4]")
].copy()

quarterly = quarterly.sort_values(
    "period_end"
).reset_index(drop=True)

MIN_SEGMENT = 8
N = len(quarterly)

if N < 3 * MIN_SEGMENT:
    raise ValueError("Not enough quarterly observations.")

t = np.arange(N, dtype=float)
y = quarterly["total_debt_billions"].to_numpy(dtype=float)


# 3. Define continuous segmented regression
# Additional hinge terms permit slope changes
# while keeping the fitted trend continuous.

def design_matrix(breaks):
    columns = [np.ones(N), t]

    for b in breaks:
        columns.append(np.maximum(0, t - b))

    return np.column_stack(columns)


def fit_model(breaks):
    return sm.OLS(y, design_matrix(breaks)).fit()


def quarter_label(index):
    row = quarterly.iloc[index]
    return f"FY{int(row['fiscal_year'])} {row['quarter']}"


# 4. Compare models with 0, 1, and 2 breakpoints
# BIC is used for descriptive model selection.
# At least eight observations are required
# in every segment.

best = {0: ((), fit_model(()))}

for count in (1, 2):
    possible = range(
        MIN_SEGMENT,
        N - MIN_SEGMENT + 1
    )

    for breaks in combinations(possible, count):
        boundaries = (0,) + breaks + (N,)

        if min(np.diff(boundaries)) < MIN_SEGMENT:
            continue

        candidate = fit_model(breaks)

        if (
            count not in best
            or candidate.bic < best[count][1].bic
        ):
            best[count] = (breaks, candidate)


comparison_rows = []

for count, (breaks, model) in best.items():
    comparison_rows.append({
        "breakpoint_count": count,
        "BIC": model.bic,
        "R_squared": model.rsquared,
        "RMSE_billions": np.sqrt(
            np.mean(model.resid ** 2)
        ),
        "breakpoints": "; ".join(
            quarter_label(b) for b in breaks
        ) or "None"
    })

winner_count = min(
    best,
    key=lambda k: best[k][1].bic
)

breaks, selected = best[winner_count]

comparison = pd.DataFrame(comparison_rows)

comparison["selected"] = (
    comparison["breakpoint_count"] == winner_count
)

comparison.to_csv(
    OUT / "segmented_model_comparison.csv",
    index=False
)


# 5. Use HAC (Newey-West) standard errors
# Four lags cover approximately one year.
# These estimates remain conditional on the
# breakpoints selected from the data.

hac = selected.get_robustcov_results(
    cov_type="HAC",
    maxlags=4,
    use_t=True
)

segment_rows = []
boundaries = (0,) + breaks + (N,)

for i in range(len(boundaries) - 1):
    contrast = np.zeros(len(hac.params))
    contrast[1] = 1

    if i > 0:
        contrast[2:2 + i] = 1

    test = hac.t_test(contrast)
    interval = test.conf_int(alpha=0.05)[0]

    segment_rows.append({
        "segment": i + 1,
        "start_quarter": quarter_label(boundaries[i]),
        "end_quarter": quarter_label(boundaries[i + 1] - 1),
        "slope_billions_per_quarter": test.effect.item(),
        "HAC_CI_lower": interval[0],
        "HAC_CI_upper": interval[1],
        "exploratory_HAC_p_value": test.pvalue.item()
    })

pd.DataFrame(segment_rows).to_csv(
    OUT / "segmented_regression_slopes.csv",
    index=False
)


# 6. Save selected breakpoints
# Later analysis scripts can use these periods.

breakpoint_rows = [
    {
        "break_number": i + 1,
        "quarter_index": b,
        "fiscal_quarter": quarter_label(b),
        "period_end": quarterly.iloc[b][
            "period_end"
        ].date().isoformat()
    }
    for i, b in enumerate(breaks)
]

pd.DataFrame(
    breakpoint_rows,
    columns=[
        "break_number",
        "quarter_index",
        "fiscal_quarter",
        "period_end"
    ]
).to_csv(
    OUT / "selected_breakpoints.csv",
    index=False
)


# 7. Diagnose residual autocorrelation
# Durbin-Watson near 2 suggests low first-order
# autocorrelation. Ljung-Box tests for correlation
# across multiple lags.

residuals = selected.resid

dw = durbin_watson(residuals)

lag1 = pd.Series(
    residuals
).autocorr(lag=1)

lb = acorr_ljungbox(
    residuals,
    lags=[4, 8],
    return_df=True
)

report = [
    "Segmented regression diagnostics",
    f"Quarterly observations: {N}",
    f"Selected breakpoint count: {winner_count}",
    f"Breakpoints: {', '.join(quarter_label(b) for b in breaks) or 'None'}",
    f"BIC: {selected.bic:.3f}",
    f"Durbin-Watson statistic: {dw:.3f}",
    f"Residual lag-1 autocorrelation: {lag1:.3f}",
    f"Ljung-Box p-value (lag 4): {lb.loc[4, 'lb_pvalue']:.6g}",
    f"Ljung-Box p-value (lag 8): {lb.loc[8, 'lb_pvalue']:.6g}",
    "",
    "Exploratory HAC p-values for slope changes:"
]

for i, b in enumerate(breaks):
    report.append(
        f"{quarter_label(b)}: {hac.pvalues[2 + i]:.6g}"
    )

report += [
    "",
    "CAUTION: Outstanding debt is highly persistent.",
    "Ordinary BIC may favor spurious breakpoints",
    "when regression errors are serially correlated.",
    "HAC does not correct for searching breakpoints",
    "or potential nonstationarity in debt levels.",
    "Treat breakpoints and p-values as exploratory."
]

(OUT / "regression_diagnostics.txt").write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)


# 8. Plot the selected segmented regression

plt.figure(figsize=(11, 5))

plt.plot(
    quarterly["period_end"],
    y,
    label="Observed debt",
    linewidth=2
)

plt.plot(
    quarterly["period_end"],
    selected.fittedvalues,
    label="Selected segmented fit",
    linestyle="--",
    linewidth=2
)

for i, b in enumerate(breaks):
    plt.axvline(
        quarterly.iloc[b]["period_end"],
        linestyle=":",
        color="gray",
        label="Selected breakpoint" if i == 0 else None
    )

plt.title(
    "Federal Student Debt: Exploratory Segmented Trend"
)
plt.xlabel("Reporting Date")
plt.ylabel("Outstanding Debt ($ Billions)")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    OUT / "segmented_regression_fit.png",
    dpi=300
)
plt.close()


# 9. Examine quarter-to-quarter changes
# First differences help reveal changes in growth
# without looking only at accumulated debt.
# They are not guaranteed to be independent.

quarterly["quarterly_change"] = (
    quarterly["total_debt_billions"].diff()
)

quarterly["four_quarter_avg_change"] = (
    quarterly["quarterly_change"]
    .rolling(4)
    .mean()
)

plt.figure(figsize=(11, 5))

plt.bar(
    quarterly["period_end"],
    quarterly["quarterly_change"],
    width=60,
    alpha=0.45,
    label="Quarterly change"
)

plt.plot(
    quarterly["period_end"],
    quarterly["four_quarter_avg_change"],
    linewidth=2,
    label="4-quarter average change"
)

for b in breaks:
    plt.axvline(
        quarterly.iloc[b]["period_end"],
        linestyle=":",
        color="gray"
    )

plt.axhline(0, linewidth=1, color="black")

plt.title(
    "Quarter-to-Quarter Change in Federal Student Debt"
)
plt.xlabel("Reporting Date")
plt.ylabel("Change in Debt ($ Billions per Quarter)")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    OUT / "quarterly_debt_changes.png",
    dpi=300
)
plt.close()


# 10. Print results for review

print("Segmented regression analysis completed.")

print("\nModel comparison:")
print(comparison.to_string(index=False))

print("\nSelected breakpoints:")
print(
    ", ".join(quarter_label(b) for b in breaks)
    or "None"
)

print("\nResidual lag-1 autocorrelation:")
print(round(lag1, 3))

print("\nWARNING: Results are exploratory.")
print("Output files saved in:", OUT)


# 11. Seasonality-adjusted time-series robustness check
#
# Unlike the earlier debt-level regression, this
# analysis models changes in debt from quarter to
# quarter. Fiscal-quarter indicators account for
# seasonality. AR(1) and seasonal AR(1) errors
# account for dependence at lags 1 and 4.
#
# Breakpoint dates come from the exploratory
# debt-level model search. They are NOT treated
# as independently verified structural breaks.

from statsmodels.tsa.statespace.sarimax import SARIMAX

# Construct the quarterly-change series
changes = quarterly.iloc[1:].copy().reset_index(drop=True)

changes["change_billions"] = np.diff(y)

# Q1 is the reference fiscal quarter.
quarter_dummies = pd.get_dummies(
    changes["quarter"],
    prefix="fiscal",
    drop_first=True,
    dtype=float
)

# Fit models with zero, one, and two candidate
# breakpoints using the same seasonal AR structure.
ts_results = {}
ts_comparison = []

for count in (0, 1, 2):

    candidate_breaks = best[count][0]

    X = pd.DataFrame({
        "baseline": np.ones(len(changes))
    })

    X = pd.concat(
        [X, quarter_dummies],
        axis=1
    )

    # A slope change in the cumulative series
    # begins affecting differences AFTER its
    # breakpoint observation.
    for i, b in enumerate(candidate_breaks, 1):

        break_date = quarterly.iloc[b]["period_end"]

        X[f"after_break_{i}"] = (
            changes["period_end"] > break_date
        ).astype(float)

    # Model quarterly changes with correlated errors.
    model = SARIMAX(
        changes["change_billions"],
        exog=X,
        order=(1, 0, 0),
        seasonal_order=(1, 0, 0, 4),
        trend="n",
        enforce_stationarity=True,
        enforce_invertibility=True
    )

    fit = model.fit(
        disp=False,
        maxiter=350
    )

    ts_results[count] = fit

    # Exclude four initial residuals to reduce
    # initialization effects in diagnostics.
    residuals = fit.resid.iloc[4:]

    # Account for two estimated AR parameters
    # in the Ljung-Box degrees of freedom.
    lb = acorr_ljungbox(
        residuals,
        lags=[4, 8],
        model_df=2,
        return_df=True
    )

    ts_comparison.append({
        "breakpoint_count": count,
        "breakpoints": "; ".join(
            quarter_label(b)
            for b in candidate_breaks
        ) or "None",
        "BIC": fit.bic,
        "AIC": fit.aic,
        "converged": bool(
            fit.mle_retvals.get("converged", False)
        ),
        "Ljung_Box_p_lag4": lb.loc[4, "lb_pvalue"],
        "Ljung_Box_p_lag8": lb.loc[8, "lb_pvalue"]
    })


# 12. Compare time-series models

ts_table = pd.DataFrame(ts_comparison)

converged = ts_table[ts_table["converged"]].copy()

if converged.empty:
    raise RuntimeError(
        "No seasonal AR model converged. "
        "Review fitting before interpreting results."
    )

selected_count = int(
    converged.loc[
        converged["BIC"].idxmin(),
        "breakpoint_count"
    ]
)

ts_table["selected"] = (
    (ts_table["breakpoint_count"] == selected_count)
    & ts_table["converged"]
)

ts_table.to_csv(
    OUT / "seasonal_ar_model_comparison.csv",
    index=False
)

selected_ts = ts_results[selected_count]


# 13. Save the selected model coefficients

conf = selected_ts.conf_int()
parameter_rows = []

for name, estimate in selected_ts.params.items():
    parameter_rows.append({
        "parameter": name,
        "estimate": estimate,
        "CI_lower": conf.loc[name].iloc[0],
        "CI_upper": conf.loc[name].iloc[1]
    })

pd.DataFrame(parameter_rows).to_csv(
    OUT / "seasonal_ar_coefficients.csv",
    index=False
)


# 14. Save residual diagnostics

selected_residuals = selected_ts.resid.iloc[4:]

selected_lb = acorr_ljungbox(
    selected_residuals,
    lags=[4, 8],
    model_df=2,
    return_df=True
)

diagnostics = [
    "Seasonality-adjusted AR model diagnostics",
    "",
    f"Selected model: {selected_count} breakpoints",
    f"BIC: {selected_ts.bic:.3f}",
    f"Converged: {selected_ts.mle_retvals.get('converged', False)}",
    f"Lag-1 residual autocorrelation: {selected_residuals.autocorr(lag=1):.3f}",
    f"Ljung-Box p-value lag 4: {selected_lb.loc[4, 'lb_pvalue']:.6g}",
    f"Ljung-Box p-value lag 8: {selected_lb.loc[8, 'lb_pvalue']:.6g}",
    "",
    "Model: quarterly changes with fiscal-quarter",
    "indicators, AR(1), and seasonal AR(1) at lag 4.",
    "",
    "CAUTION:",
    "Breakpoints were previously selected using",
    "the same underlying debt data.",
    "This is a sensitivity analysis, not independent",
    "confirmation of structural breaks.",
    "Residual tests have limited power with 54",
    "quarterly changes and a short final period.",
    "Coefficient intervals are conditional on the",
    "candidate breakpoint dates and model choice."
]

(OUT / "seasonal_ar_diagnostics.txt").write_text(
    "\n".join(diagnostics) + "\n",
    encoding="utf-8"
)


# 15. Plot observed versus fitted quarterly changes

plt.figure(figsize=(11, 5))

plt.plot(
    changes["period_end"],
    changes["change_billions"],
    label="Observed quarterly change",
    marker="o",
    markersize=3
)

plt.plot(
    changes["period_end"],
    selected_ts.fittedvalues,
    label="Seasonal AR fitted values",
    linestyle="--"
)

plt.axhline(
    0,
    color="black",
    linewidth=1
)

plt.title(
    "Quarterly Debt Changes: Seasonally Adjusted AR Fit"
)

plt.xlabel("Reporting Date")
plt.ylabel("Debt Change ($ Billions)")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    OUT / "seasonal_ar_quarterly_fit.png",
    dpi=300
)

plt.close()


# 16. Display results in Colab

print("\nSEASONALLY ADJUSTED MODEL COMPARISON")
print(ts_table.to_string(index=False))

print("\nSELECTED MODEL DIAGNOSTICS")
print("\n".join(diagnostics))

print("\nSeasonal AR analysis completed.")
