# Sales Performance & Upselling Dashboard (Streamlit)

This project provides an interactive Streamlit dashboard to examine sales performance, monitor KPIs, analyze daily product-mix fluctuations, and evaluate staff upselling performance by time of day.

The dashboard is designed to **avoid data privacy issues** by requiring the user/client to **upload the Excel dataset at runtime**. The dataset is **not stored in the GitHub repository**.

---

## What This Dashboard Covers

### ✅ KPIs (Top Summary)
- Total Revenue
- Total Conversions
- Average Revenue per Conversion
- Total Ad Spend
- ROAS (Return on Ad Spend)

### ✅ Daily Fluctuations
- Daily Revenue trend
- Daily Product Mix (Revenue by Service Type)

### ✅ Upselling Performance (By Shift)
- Bundled Share by Time of Day (Upselling proxy)
- Revenue and conversion performance by time period

### ✅ Actionable Recommendations
- Highlights best/worst performing shifts based on bundled share
- Provides suggested sales improvement actions

---

## Dataset Requirements (Strict Schema)

The uploaded Excel file **must** be `.xlsx` and include **exactly** the following columns:

- `Date`
- `Time of Day`
- `Service Type`
- `Ad Channel`
- `Customer Type`
- `Ad Spend ($)`
- `Conversions`
- `Daily Revenue ($)`

If any required column is missing or key fields cannot be parsed (e.g., invalid dates), the app will stop and show an error message.

---

## Privacy & Security

- The dataset is uploaded by the client through the Streamlit sidebar.
- The app processes the dataset **in memory for the current session**.
- The dataset is **not committed to GitHub** and does not need to be stored in the repository.
- Recommended: keep the repository **private** if the dashboard itself is proprietary.

---

## Repository Structure (Recommended)

sales-dashboard/
├─ app.py
├─ requirements.txt
├─ README.md
└─ .gitignore


## Installation (Local)

1. Clone the repository:
```bash
git clone https://github.com/Mohamed-Ghannam/sales-dashboard
cd sales-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the app:
```bash
streamlit run app.py
```
4. Upload the Excel file in the sidebar to start using the dashboard.
