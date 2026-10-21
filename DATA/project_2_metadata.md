
PROJECT 2: METADATA


### **DATA SUMMARY**

The project uses a data set from the Federal Student Aid (FSA) Portfolio Summary, a single spreadsheet with 61 time points (annual for FY2007–2012, quarterly from FY2013 Q1 to FY2026 Q3) and no missing values. For Direct Loans, FFEL and Perkins Loans, it reports dollars outstanding and recipients, plus totals, which map to the debt, borrower-count, average-balance and loan-composition parts of our research question. Total debt grew from $516.0B to $1,724.5B, and Direct Loans went from about 21% to 91% of it.

The final processed dataset has filled in missing fiscal-year values, converted reporting periods to period-end dates, standardized column names and data types, and calculated average balance per recipient.

**PROVENANCE**

The data originally comes from the Federal Student Aid (FSA) Portfolio Summary, published through the FSA Data Center by the U.S. Department of Education and compiled from the National Student Loan Data System (NSLDS). The workbook has one row per period and reports outstanding debt (in billions) and recipients (in millions) for Direct Loans, FFEL, and Perkins Loans, along with total debt and total recipients.

**LICENSE**

Data produced by a U.S. federal agency is generally a U.S. Government work in the public domain (17 U.S.C. §105), so it can be reused and redistributed freely.

**ETHICAL** **STATEMENTS**

The data is aggregated by loan category and quarter and contains no personally identifiable information. A “recipient” is the student who benefits, and on Parent PLUS loans the borrower is the parent. National totals also hide differences across demographic and institutional groups. Findings will be descriptive and point to changes external events.

# Data Dictionary

The cleaned dataset is saved as `portfolio_clean.csv`.

| Feature / Column | Description | Type / Format | Example / Uncertainty |
|---|---|---|---|
| `fiscal_year` | Fiscal year associated with the observation | Integer | `2007` |
| `quarter` | Reporting quarter; blank values represent annual observations | Categorical Text | `Q1`, `Q2`, `Q3`, `Q4`, or blank for annual data |
| `period_end` | Date marking the end of the reporting period | Date stored as text (`YYYY-MM-DD`) | `2007-09-30` |
| `direct_debt_billions` | Outstanding debt for the Direct Loan program | Numeric (Float) | Billions of US dollars |
| `direct_recipients_millions` | Reported number of Direct Loan recipients | Numeric (Float) | Millions of recipients; may overlap with other program counts |
| `ffel_debt_billions` | Outstanding debt for the Federal Family Education Loan (FFEL) Program | Numeric (Float) | Billions of US dollars |
| `ffel_recipients_millions` | Reported number of FFEL recipients | Numeric (Float) | Millions of recipients; may overlap with other program counts |
| `perkins_debt_billions` | Outstanding debt for the Perkins Loan Program | Numeric (Float) | Billions of US dollars |
| `perkins_recipients_millions` | Reported number of Perkins Loan recipients | Numeric (Float) | Millions of recipients; may overlap with other program counts |
| `total_debt_billions` | Total outstanding federal student loan debt | Numeric (Float) | Billions of US dollars |
| `total_recipients_millions` | Total unduplicated number of recipients | Numeric (Float) | Millions of unique recipients |
| `direct_avg_balance_thousands` | Direct Loan debt divided by Direct Loan recipients | Numeric (Float) | Thousands of US dollars per recipient |
| `ffel_avg_balance_thousands` | FFEL debt divided by FFEL recipients | Numeric (Float) | Thousands of US dollars per recipient |
| `perkins_avg_balance_thousands` | Perkins debt divided by Perkins recipients | Numeric (Float) | Thousands of US dollars per recipient |
| `total_avg_balance_thousands` | Total debt divided by total recipients | Numeric (Float) | Thousands of US dollars per recipient |

**EXPLANATORY** **PLOTS**


Federal Student Debt by Loan Category
<img width="1356" height="755" alt="Federal Student Debt By Loan Category" src="https://github.com/user-attachments/assets/c2ea5117-8bfc-4fb2-9321-8c58b05d7afa" />

Average Outstanding Balance Per Recipient
<img width="1069" height="617" alt="Average Outstanding Balance per Recipient" src="https://github.com/user-attachments/assets/973c7be3-57c5-404f-9c8e-52300911cc29" />


