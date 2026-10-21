import pandas as pd
import matplotlib.pyplot as plt

# Load cleaned data
df = pd.read_csv("DATA/portfolio_clean.csv")

# Convert reporting dates to datetime
df["period_end"] = pd.to_datetime(df["period_end"])
df = df.sort_values("period_end")

# Create line graph
plt.figure(figsize=(14, 8))

plt.plot(df["period_end"], df["direct_outstanding_billions"], label="Direct Loans")
plt.plot(df["period_end"], df["ffel_outstanding_billions"], label="FFEL")
plt.plot(df["period_end"], df["perkins_outstanding_billions"], label="Perkins")

# Add labels and formatting
plt.title("Federal Student Debt by Loan Category")
plt.xlabel("Reporting Date")
plt.ylabel("Outstanding Debt ($ Billions)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# Display graph
plt.show()
