# U.S. Federal Student Debt Analysis

## Contents of the Repository

This DS 4002 project studies how federal student debt changed from fiscal year 2007 through the third quarter of fiscal year 2026. It examines changes in debt growth, borrower counts, average balances, and the mix of Direct, FFEL, and Perkins loans.

The data comes from the Federal Student Aid Portfolio Summary [1]. It contains 61 observations: six annual observations and 55 quarterly observations. The statistical models use only the quarterly observations. The analysis describes historical patterns; it does not establish causes or forecast future debt.

`DATA/` holds the original and cleaned data, `SCRIPTS/` holds the analysis code, and `OUTPUT/` holds the tables, figures, and reports.

## 1. Software and Platform

The analysis uses Python and the five packages below. Excel is not required because Python reads the original spreadsheet directly.

The table lists the latest stable releases as of October 21, 2026 [2]–[7]. These versions have not been tested together on this project and are not a record of the versions used to generate the saved results.

| Software or package | Exact version | Purpose |
|---|---|---|
| Python | 3.15.1 | Runs the scripts |
| NumPy | 2.5.4 | Performs numerical calculations |
| pandas | 3.0.6 | Cleans data and works with tables |
| Matplotlib | 3.11.2 | Creates figures |
| statsmodels | 0.15.0 | Fits and checks statistical models |
| xlrd | 2.0.2 | Reads the original `.xls` file |

The current computer uses Windows, version 25H2, build 26200.9711. The metadata file was exported from Google Colab, but the platform used to generate the saved analysis results is not recorded.

## 2. Map of the Documentation

```text
DS_4002-Project-2-MI3/
|-- README.md
|-- LICENSE
|-- DATA/
|   |-- PortfolioSummary.xls
|   |-- portfolio_clean.csv
|   `-- project_2_metadata.py
|-- SCRIPTS/
|   |-- 01_clean_data.py
|   |-- 02_debt_trends.py
|   |-- 03_segmented_regression.py
|   |-- 04_debt_decomposition.py
|   |-- 05_loan_composition.py
|   |-- 06_model_evaluation.py
|   |-- 07_plot_debt_by_category.py
|   `-- 08_plot_average_balance_per_recipient.py
`-- OUTPUT/
    |-- average_balance_composition.csv
    |-- average_balance_effects.png
    |-- average_outstanding_balance_per_recipient.png
    |-- debt_decomposition_contributions.png
    |-- debt_growth_decomposition.csv
    |-- debt_growth_rates.csv
    |-- debt_over_time.png
    |-- debt_yoy_growth.png
    |-- decomposition_validation.txt
    |-- federal_student_debt_by_loan_category.png
    |-- final_evaluation_checklist.csv
    |-- final_evaluation_report.txt
    |-- final_model_comparison.png
    |-- loan_category_changes.csv
    |-- loan_category_reconciliation.csv
    |-- loan_category_shares.png
    |-- loan_composition_validation.txt
    |-- quarterly_debt_changes.png
    |-- regression_diagnostics.txt
    |-- seasonal_ar_coefficients.csv
    |-- seasonal_ar_diagnostics.txt
    |-- seasonal_ar_model_comparison.csv
    |-- seasonal_ar_quarterly_fit.png
    |-- segmented_model_comparison.csv
    |-- segmented_regression_fit.png
    |-- segmented_regression_slopes.csv
    `-- selected_breakpoints.csv
```

`PortfolioSummary.xls` is the original data. `portfolio_clean.csv` is the cleaned data used in the analysis. `project_2_metadata.py` contains the data description, source, ethical statements, data dictionary, and explanatory plots exported from Colab. It does not need to be run.

Output files ending in `.csv` are tables, `.png` files are figures, and `.txt` files are reports or calculation checks.

## 3. Instructions for Reproducing the Results

### Step 1: Download the repository

On the [GitHub repository page](https://github.com/msoly25/DS_4002-Project-2-MI3), select **Code > Download ZIP**, then extract the ZIP file. Keep the folder names and file names unchanged.

Use the included `DATA/PortfolioSummary.xls` file. Downloading a newer version from the source could change the results.

### Step 2: Set up Python

Install Python 3.15.1 [2] and open a terminal in the extracted project folder, where `README.md` is located. In Windows, you can open that folder in File Explorer, type `powershell` in the address bar, and press Enter.

Check that Python is available:

```powershell
python --version
```

Create a separate environment for the project:

```powershell
python -m venv .venv
```

Install the required packages into that environment:

```powershell
.\.venv\Scripts\python.exe -m pip install numpy==2.5.4 pandas==3.0.6 matplotlib==3.11.2 statsmodels==0.15.0 xlrd==2.0.2
```

This command installs the exact package versions listed above. Other required dependencies are installed automatically. Results may differ from the saved outputs because the original software versions were not recorded.

### Step 3: Run the scripts in order

Run each command below separately. Wait for it to finish before running the next one. If a command reports an error, resolve it before continuing. These commands replace the cleaned data and generated outputs.

```powershell
.\.venv\Scripts\python.exe SCRIPTS/01_clean_data.py
.\.venv\Scripts\python.exe SCRIPTS/02_debt_trends.py
.\.venv\Scripts\python.exe SCRIPTS/03_segmented_regression.py
.\.venv\Scripts\python.exe SCRIPTS/04_debt_decomposition.py
.\.venv\Scripts\python.exe SCRIPTS/05_loan_composition.py
.\.venv\Scripts\python.exe SCRIPTS/06_model_evaluation.py
```

| Script | What it does |
|---|---|
| `01_clean_data.py` | Cleans the spreadsheet, checks the data, and calculates average balances. Saves `DATA/portfolio_clean.csv`. |
| `02_debt_trends.py` | Calculates yearly growth rates and plots total debt over time. |
| `03_segmented_regression.py` | Fits connected trend lines to find changes in debt growth. Also checks quarterly changes while accounting for seasonal patterns and dependence between quarters. |
| `04_debt_decomposition.py` | Divides debt growth into changes in borrower counts and changes in average balances. |
| `05_loan_composition.py` | Examines changes across loan programs and accounts for recipients who appear in more than one program. |
| `06_model_evaluation.py` | Compares model results, checks that the calculations add up, and creates a final report and checklist. |

Scripts 4 and 5 need the breakpoint file created by script 3. Script 6 needs the results from the earlier scripts. Script 3 may take longer because it fits several models.

### Step 4: Review the results

Open `OUTPUT/final_evaluation_report.txt` for the main results and `OUTPUT/final_evaluation_checklist.csv` for the checks. The current saved checklist has `True` for every requirement. Script 6 stops with an error if any requirement fails.

The saved results provide these comparison points:

- The cleaned data has 61 observations, including 55 quarterly observations.
- Total debt rises from $516.0 billion to $1,724.5 billion.
- The selected trend breakpoints are FY2020 Q4 and FY2024 Q4.
- Over the full period, borrower-count changes account for about $413.0 billion of the increase, and average-balance changes account for about $795.5 billion.

Open the `.png` files in `OUTPUT/` to view the figures. Start with `debt_over_time.png`, `segmented_regression_fit.png`, and `debt_decomposition_contributions.png`.

Passing the checklist means the required calculations and reporting checks passed. It does not prove that the selected breakpoints are certain or that the models predict future debt accurately.

## References

[1] U.S. Department of Education, Federal Student Aid, "Federal Student Loan Portfolio," Federal Student Aid Data Center. [Online]. Available: https://studentaid.gov/data-center/student/portfolio. [Accessed: Oct. 21, 2026].

[2] Python Software Foundation, "Download Python." [Online]. Available: https://www.python.org/downloads/. [Accessed: Oct. 21, 2026].

[3] NumPy Developers, "numpy," Python Package Index. [Online]. Available: https://pypi.org/project/numpy/. [Accessed: Oct. 21, 2026].

[4] pandas Developers, "pandas," Python Package Index. [Online]. Available: https://pypi.org/project/pandas/. [Accessed: Oct. 21, 2026].

[5] Matplotlib Developers, "matplotlib," Python Package Index. [Online]. Available: https://pypi.org/project/matplotlib/. [Accessed: Oct. 21, 2026].

[6] statsmodels Developers, "statsmodels," Python Package Index. [Online]. Available: https://pypi.org/project/statsmodels/. [Accessed: Oct. 21, 2026].

[7] xlrd Developers, "xlrd," Python Package Index. [Online]. Available: https://pypi.org/project/xlrd/. [Accessed: Oct. 21, 2026].
