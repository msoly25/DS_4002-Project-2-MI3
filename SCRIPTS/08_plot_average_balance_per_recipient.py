import pandas as pd
import matplotlib.pyplot as plt

# Load cleaned data
df = pd.read_csv("DATA/portfolio_clean.csv")

# Convert reporting dates to datetime
df["period_end"] = pd.to_datetime(df["period_end"])
df = df.sort_values("period_end")

# Create line graph
plt.figure(figsize=(14, 8))

plt.plot(
    df["period_end"],
    df["direct_avg_balance_thousands"],
    label="Direct Loans"
)

plt.plot(
    df["period_end"],
    df["ffel_avg_balance_thousands"],
    label="FFEL"
)

plt.plot(
    df["period_end"],
    df["perkins_avg_balance_thousands"],
    label="Perkins"
)

plt.plot(
    df["period_end"],
    df["total_avg_balance_thousands"],
    label="Total Average",
    color="red",
    linestyle="--",
    linewidth=2.5
)

# Add title and labels
plt.title("Average Outstanding Balance per Recipient")
plt.xlabel("Reporting Date")
plt.ylabel("Average Balance ($ Thousands)")

# Format graph
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# Display graph
plt.show()
