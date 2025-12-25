import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Sales Performance Dashboard", layout="wide")
st.title("📊 Sales Performance & Upselling Dashboard")
st.caption("Upload your sales dataset to view KPIs, daily product mix, and upselling performance by time of day.")

# -----------------------------
# REQUIRED SCHEMA (STRICT)
# -----------------------------
REQUIRED_COLUMNS = [
    "Date",
    "Time of Day",
    "Service Type",
    "Ad Channel",
    "Customer Type",
    "Ad Spend ($)",
    "Conversions",
    "Daily Revenue ($)",
]

# -----------------------------
# SIDEBAR: FILE UPLOAD
# -----------------------------
st.sidebar.header("📤 Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload the Excel file (.xlsx) used for this dashboard",
    type=["xlsx"],
    accept_multiple_files=False
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Privacy note: This app processes your file in memory for this session. "
    "It does not require the dataset to be stored in GitHub."
)

# -----------------------------
# LOAD + VALIDATE
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data_from_excel(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    return df


def validate_schema(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    return missing, extra


if not uploaded_file:
    st.warning("Please upload the Excel dataset to start.")
    st.stop()

try:
    raw_df = load_data_from_excel(uploaded_file)
except Exception as e:
    st.error("Could not read the uploaded Excel file. Please upload a valid .xlsx file.")
    st.exception(e)
    st.stop()

missing_cols, extra_cols = validate_schema(raw_df)

if missing_cols:
    st.error("❌ Uploaded file does not match the required dataset structure.")
    st.write("Missing required columns:")
    st.code("\n".join(missing_cols))
    st.write("Expected columns:")
    st.code("\n".join(REQUIRED_COLUMNS))
    st.stop()

# Optional: warn about extra columns (we will ignore them if present)
if extra_cols:
    st.warning("⚠️ The file contains extra columns. They will be ignored:")
    st.write(extra_cols)

# Keep only required columns (privacy + consistency)
df = raw_df[REQUIRED_COLUMNS].copy()

# -----------------------------
# DATA PREP
# -----------------------------
# Normalize Date
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

if df["Date"].isna().any():
    st.error("❌ Some rows have invalid Date values. Please fix the Date column and re-upload.")
    st.stop()

# Ensure numeric columns are numeric
for col in ["Ad Spend ($)", "Conversions", "Daily Revenue ($)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df[["Ad Spend ($)", "Conversions", "Daily Revenue ($)"]].isna().any().any():
    st.error("❌ Some rows have invalid numeric values in Ad Spend, Conversions, or Daily Revenue. Please fix and re-upload.")
    st.stop()

# Derived metrics
df["Revenue per Conversion"] = df.apply(
    lambda r: (r["Daily Revenue ($)"] / r["Conversions"]) if r["Conversions"] > 0 else 0,
    axis=1
)
df["Is Bundled"] = df["Service Type"].astype(str).str.strip().str.lower().eq("bundled")

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔎 Filters")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

time_filter = st.sidebar.multiselect(
    "Time of Day",
    options=sorted(df["Time of Day"].dropna().unique()),
    default=sorted(df["Time of Day"].dropna().unique())
)

service_filter = st.sidebar.multiselect(
    "Service Type",
    options=sorted(df["Service Type"].dropna().unique()),
    default=sorted(df["Service Type"].dropna().unique())
)

cust_filter = st.sidebar.multiselect(
    "Customer Type",
    options=sorted(df["Customer Type"].dropna().unique()),
    default=sorted(df["Customer Type"].dropna().unique())
)

channel_filter = st.sidebar.multiselect(
    "Ad Channel",
    options=sorted(df["Ad Channel"].dropna().unique()),
    default=sorted(df["Ad Channel"].dropna().unique())
)

# Validate date_range shape
if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
    st.error("Please select a valid start and end date.")
    st.stop()

start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1])

filtered_df = df[
    (df["Date"] >= start_date) &
    (df["Date"] <= end_date) &
    (df["Time of Day"].isin(time_filter)) &
    (df["Service Type"].isin(service_filter)) &
    (df["Customer Type"].isin(cust_filter)) &
    (df["Ad Channel"].isin(channel_filter))
].copy()

st.write(f"✅ Loaded {len(df):,} rows. Showing {len(filtered_df):,} rows after filters.")

st.divider()

# -----------------------------
# KPI CALCULATIONS
# -----------------------------
total_revenue = filtered_df["Daily Revenue ($)"].sum()
total_conversions = int(filtered_df["Conversions"].sum())
avg_rev_per_conv = (
    filtered_df.loc[filtered_df["Conversions"] > 0, "Revenue per Conversion"].mean()
    if (filtered_df["Conversions"] > 0).any()
    else 0
)
total_ad_spend = filtered_df["Ad Spend ($)"].sum()
roas = (total_revenue / total_ad_spend) if total_ad_spend > 0 else 0

# -----------------------------
# KPI DISPLAY
# -----------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
c2.metric("🛒 Conversions", f"{total_conversions:,}")
c3.metric("📈 Avg Rev / Conversion", f"${avg_rev_per_conv:,.2f}")
c4.metric("📢 Ad Spend", f"${total_ad_spend:,.0f}")
c5.metric("🎯 ROAS", f"{roas:.2f}")

# -----------------------------
# DAILY REVENUE TREND
# -----------------------------
st.subheader("📅 Daily Revenue Trend")
daily_revenue = filtered_df.groupby("Date", as_index=False)["Daily Revenue ($)"].sum()

fig_daily = px.line(daily_revenue, x="Date", y="Daily Revenue ($)", markers=True)
st.plotly_chart(fig_daily, use_container_width=True)

# -----------------------------
# PRODUCT MIX ANALYSIS
# -----------------------------
st.subheader("📦 Daily Product Mix (Revenue by Service Type)")
product_mix = (
    filtered_df.groupby(["Date", "Service Type"], as_index=False)["Daily Revenue ($)"]
    .sum()
)

fig_mix = px.bar(
    product_mix,
    x="Date",
    y="Daily Revenue ($)",
    color="Service Type",
    barmode="stack"
)
st.plotly_chart(fig_mix, use_container_width=True)

st.divider()

# -----------------------------
# UPSELLING PERFORMANCE
# -----------------------------
st.subheader("🧑‍💼 Upselling Performance by Time of Day (Bundled Share)")

upsell = filtered_df.groupby("Time of Day").agg(
    Revenue=("Daily Revenue ($)", "sum"),
    Conversions=("Conversions", "sum"),
    Avg_Revenue_per_Conversion=("Revenue per Conversion", "mean"),
    Bundled_Share=("Is Bundled", "mean")
).reset_index()

# Order time of day nicely if present
time_order = ["Morning", "Afternoon", "Evening", "Night"]
upsell["Time of Day"] = pd.Categorical(upsell["Time of Day"], categories=time_order, ordered=True)
upsell = upsell.sort_values("Time of Day")

fig_upsell = px.bar(
    upsell,
    x="Time of Day",
    y="Bundled_Share",
    text=upsell["Bundled_Share"].apply(lambda x: f"{x:.1%}"),
    title="Bundled Share (Upselling Proxy)"
)
fig_upsell.update_traces(textposition="outside")
st.plotly_chart(fig_upsell, use_container_width=True)

st.dataframe(
    upsell.assign(
        Bundled_Share=upsell["Bundled_Share"].map(lambda x: f"{x:.1%}")
    ),
    use_container_width=True
)

# -----------------------------
# ACTIONABLE INSIGHTS
# -----------------------------
st.subheader("🚀 Actionable Insights")

if len(upsell) >= 2:
    best = upsell.loc[upsell["Bundled_Share"].astype(float).idxmax()]
    worst = upsell.loc[upsell["Bundled_Share"].astype(float).idxmin()]

    st.success(f"✅ Best upselling shift: **{best['Time of Day']}** ({best['Bundled_Share']:.1%} bundled share).")
    st.warning(f"⚠️ Needs improvement: **{worst['Time of Day']}** ({worst['Bundled_Share']:.1%} bundled share).")
else:
    st.info("Not enough time-of-day categories in the filtered data to compare upselling performance.")

st.markdown("""
### Recommended Actions
- Replicate the best shift’s upselling approach (scripts, offers, timing) across other shifts  
- Set a **minimum bundled share target** (example: **35%**) and track it daily  
- Coach underperforming shifts on upgrading customers from **Premium → Bundled**  
- Review days with high **Basic** mix to reduce revenue volatility
""")
