import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Customer Purchasing & Sales Performance Dashboard")
st.markdown(
    "Analyze customer value, product combinations, regional performance "
    "and customer retention."
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    sales = pd.read_csv("sales_data.csv")
    churn = pd.read_csv("customer_churn.csv")

    sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce")

    sales["Total_Sales"] = pd.to_numeric(
        sales["Total_Sales"], errors="coerce"
    ).fillna(0)

    sales["Quantity"] = pd.to_numeric(
        sales["Quantity"], errors="coerce"
    ).fillna(0)

    sales["Price"] = pd.to_numeric(
        sales["Price"], errors="coerce"
    ).fillna(0)

    churn["Churn"] = pd.to_numeric(
        churn["Churn"], errors="coerce"
    ).fillna(0)

    return sales, churn


sales, churn = load_data()

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("🔎 Dashboard Filters")

regions = sorted(sales["Region"].dropna().unique())
products = sorted(sales["Product"].dropna().unique())

selected_regions = st.sidebar.multiselect(
    "Select Region",
    regions,
    default=regions
)

selected_products = st.sidebar.multiselect(
    "Select Product",
    products,
    default=products
)

filtered_sales = sales[
    sales["Region"].isin(selected_regions)
    & sales["Product"].isin(selected_products)
].copy()

# ---------------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------------
total_sales = filtered_sales["Total_Sales"].sum()
total_orders = len(filtered_sales)
total_quantity = filtered_sales["Quantity"].sum()
unique_customers = filtered_sales["Customer_ID"].nunique()

average_order_value = (
    total_sales / total_orders if total_orders > 0 else 0
)

overall_churn_rate = churn["Churn"].mean() * 100

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "💰 Total Sales",
    f"₹{total_sales:,.0f}"
)

col2.metric(
    "🛒 Transactions",
    f"{total_orders:,}"
)

col3.metric(
    "📦 Quantity Sold",
    f"{total_quantity:,.0f}"
)

col4.metric(
    "👥 Customers",
    f"{unique_customers:,}"
)

col5.metric(
    "📉 Churn Rate",
    f"{overall_churn_rate:.1f}%"
)

st.divider()

# =========================================================
# 1. MOST VALUABLE CUSTOMERS
# =========================================================

st.header("1️⃣ Most Valuable Customers")

customer_sales = (
    filtered_sales
    .groupby("Customer_ID", as_index=False)
    .agg(
        Total_Sales=("Total_Sales", "sum"),
        Total_Quantity=("Quantity", "sum"),
        Transactions=("Product", "count")
    )
    .sort_values("Total_Sales", ascending=False)
)

top_10_customers = customer_sales.head(10)

col1, col2 = st.columns([1.5, 1])

with col1:
    fig_customer = px.bar(
        top_10_customers.sort_values("Total_Sales"),
        x="Total_Sales",
        y="Customer_ID",
        orientation="h",
        title="Top 10 Customers by Sales",
        text_auto=".2s"
    )

    fig_customer.update_layout(
        xaxis_title="Total Sales",
        yaxis_title="Customer"
    )

    st.plotly_chart(
        fig_customer,
        use_container_width=True
    )

with col2:
    st.subheader("🏆 Top Customers")

    display_customers = top_10_customers.copy()

    display_customers["Total_Sales"] = (
        display_customers["Total_Sales"]
        .map(lambda x: f"₹{x:,.0f}")
    )

    display_customers.columns = [
        "Customer",
        "Sales",
        "Quantity",
        "Transactions"
    ]

    st.dataframe(
        display_customers,
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------------------------------
# CUSTOMER VALUE INSIGHT
# ---------------------------------------------------------
if len(customer_sales) > 0:
    best_customer = customer_sales.iloc[0]

    st.success(
        f"🏆 **Most valuable customer:** "
        f"{best_customer['Customer_ID']} with "
        f"₹{best_customer['Total_Sales']:,.0f} in sales."
    )

# =========================================================
# 2. PRODUCTS THAT SELL BEST TOGETHER
# =========================================================

st.header("2️⃣ Products That Sell Best Together")

st.markdown(
    "The analysis identifies products purchased by the same customer "
    "and counts their co-purchase frequency."
)

# Create customer-product sets
customer_products = (
    filtered_sales
    .groupby("Customer_ID")["Product"]
    .apply(lambda x: sorted(set(x)))
)

pair_counts = {}

for product_list in customer_products:
    if len(product_list) >= 2:
        for pair in combinations(product_list, 2):
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

pair_df = pd.DataFrame(
    [
        {
            "Product A": pair[0],
            "Product B": pair[1],
            "Co-Purchases": count
        }
        for pair, count in pair_counts.items()
    ]
)

if not pair_df.empty:

    pair_df = pair_df.sort_values(
        "Co-Purchases",
        ascending=False
    )

    top_pairs = pair_df.head(10).copy()

    top_pairs["Product Pair"] = (
        top_pairs["Product A"]
        + " + "
        + top_pairs["Product B"]
    )

    fig_pairs = px.bar(
        top_pairs.sort_values("Co-Purchases"),
        x="Co-Purchases",
        y="Product Pair",
        orientation="h",
        title="Top Product Combinations",
        text_auto=True
    )

    fig_pairs.update_layout(
        xaxis_title="Number of Customers Buying Both",
        yaxis_title="Product Combination"
    )

    st.plotly_chart(
        fig_pairs,
        use_container_width=True
    )

    st.subheader("🛍️ Product Pair Details")

    st.dataframe(
        top_pairs[
            [
                "Product A",
                "Product B",
                "Co-Purchases"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    best_pair = top_pairs.iloc[0]

    st.info(
        f"💡 **Best product combination:** "
        f"{best_pair['Product A']} + "
        f"{best_pair['Product B']} "
        f"({best_pair['Co-Purchases']} customers purchased both)."
    )

else:
    st.warning(
        "Not enough customer/product combinations to calculate "
        "product pairs."
    )

# =========================================================
# 3. REGION WITH HIGHEST SALES
# =========================================================

st.header("3️⃣ Regional Sales Performance")

region_sales = (
    filtered_sales
    .groupby("Region", as_index=False)
    .agg(
        Total_Sales=("Total_Sales", "sum"),
        Quantity=("Quantity", "sum"),
        Customers=("Customer_ID", "nunique")
    )
    .sort_values("Total_Sales", ascending=False)
)

col1, col2 = st.columns(2)

with col1:

    fig_region = px.bar(
        region_sales.sort_values("Total_Sales"),
        x="Total_Sales",
        y="Region",
        orientation="h",
        title="Sales by Region",
        text_auto=".2s"
    )

    st.plotly_chart(
        fig_region,
        use_container_width=True
    )

with col2:

    fig_pie = px.pie(
        region_sales,
        values="Total_Sales",
        names="Region",
        title="Sales Distribution by Region"
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

# ---------------------------------------------------------
# REGION TABLE
# ---------------------------------------------------------

region_display = region_sales.copy()

region_display["Total_Sales"] = (
    region_display["Total_Sales"]
    .map(lambda x: f"₹{x:,.0f}")
)

st.dataframe(
    region_display,
    use_container_width=True,
    hide_index=True
)

if len(region_sales) > 0:

    highest_region = region_sales.iloc[0]

    st.success(
        f"🌎 **Highest-sales region:** "
        f"{highest_region['Region']} with "
        f"₹{highest_region['Total_Sales']:,.0f} in sales."
    )

# =========================================================
# SALES TREND
# =========================================================

st.header("📈 Sales Trend")

daily_sales = (
    filtered_sales
    .groupby("Date", as_index=False)
    .agg(Total_Sales=("Total_Sales", "sum"))
)

fig_trend = px.line(
    daily_sales,
    x="Date",
    y="Total_Sales",
    markers=True,
    title="Sales Over Time"
)

fig_trend.update_layout(
    xaxis_title="Date",
    yaxis_title="Sales"
)

st.plotly_chart(
    fig_trend,
    use_container_width=True
)

# =========================================================
# PRODUCT PERFORMANCE
# =========================================================

st.header("📦 Product Performance")

product_sales = (
    filtered_sales
    .groupby("Product", as_index=False)
    .agg(
        Total_Sales=("Total_Sales", "sum"),
        Quantity=("Quantity", "sum")
    )
    .sort_values("Total_Sales", ascending=False)
)

fig_product = px.bar(
    product_sales,
    x="Product",
    y="Total_Sales",
    title="Sales by Product",
    text_auto=".2s"
)

st.plotly_chart(
    fig_product,
    use_container_width=True
)

if not product_sales.empty:

    best_product = product_sales.iloc[0]

    st.info(
        f"⭐ **Best-selling product:** "
        f"{best_product['Product']} with "
        f"₹{best_product['Total_Sales']:,.0f} in sales."
    )

# =========================================================
# 4. CUSTOMER RETENTION / CHURN ANALYSIS
# =========================================================

st.header("4️⃣ Customer Retention Analysis")

# Overall churn
churn_summary = (
    churn["Churn"]
    .value_counts()
    .rename(index={
        0: "Retained",
        1: "Churned"
    })
    .reset_index()
)

churn_summary.columns = [
    "Customer Status",
    "Customers"
]

col1, col2 = st.columns(2)

with col1:

    fig_churn = px.pie(
        churn_summary,
        values="Customers",
        names="Customer Status",
        title="Customer Retention vs Churn"
    )

    st.plotly_chart(
        fig_churn,
        use_container_width=True
    )

with col2:

    # Churn by contract
    contract_churn = (
        churn
        .groupby("Contract", as_index=False)
        .agg(
            Churn_Rate=("Churn", "mean"),
            Customers=("CustomerID", "count")
        )
    )

    contract_churn["Churn_Rate"] *= 100

    fig_contract = px.bar(
        contract_churn,
        x="Contract",
        y="Churn_Rate",
        title="Churn Rate by Contract",
        text_auto=".1f"
    )

    fig_contract.update_layout(
        yaxis_title="Churn Rate (%)"
    )

    st.plotly_chart(
        fig_contract,
        use_container_width=True
    )

# ---------------------------------------------------------
# CHURN BY PAYMENT METHOD
# ---------------------------------------------------------

payment_churn = (
    churn
    .groupby("PaymentMethod", as_index=False)
    .agg(
        Churn_Rate=("Churn", "mean"),
        Customers=("CustomerID", "count")
    )
)

payment_churn["Churn_Rate"] *= 100

fig_payment = px.bar(
    payment_churn.sort_values("Churn_Rate"),
    x="PaymentMethod",
    y="Churn_Rate",
    title="Churn Rate by Payment Method",
    text_auto=".1f"
)

fig_payment.update_layout(
    yaxis_title="Churn Rate (%)"
)

st.plotly_chart(
    fig_payment,
    use_container_width=True
)

# ---------------------------------------------------------
# CHURN BY TENURE
# ---------------------------------------------------------

churn["Tenure_Group"] = pd.cut(
    churn["Tenure"],
    bins=[-1, 6, 12, 24, 48, 1000],
    labels=[
        "0-6 Months",
        "7-12 Months",
        "13-24 Months",
        "25-48 Months",
        "49+ Months"
    ]
)

tenure_churn = (
    churn
    .groupby("Tenure_Group", observed=False, as_index=False)
    .agg(
        Churn_Rate=("Churn", "mean"),
        Customers=("CustomerID", "count")
    )
)

tenure_churn["Churn_Rate"] *= 100

fig_tenure = px.bar(
    tenure_churn,
    x="Tenure_Group",
    y="Churn_Rate",
    title="Churn Rate by Customer Tenure",
    text_auto=".1f"
)

fig_tenure.update_layout(
    yaxis_title="Churn Rate (%)",
    xaxis_title="Customer Tenure"
)

st.plotly_chart(
    fig_tenure,
    use_container_width=True
)

# =========================================================
# RETENTION RECOMMENDATIONS
# =========================================================

st.header("💡 Customer Retention Recommendations")

recommendations = [
    (
        "🎯 Target high-value customers",
        "Create VIP offers, loyalty rewards and personalized communication "
        "for customers generating the highest sales."
    ),
    (
        "📦 Use product bundles",
        "Bundle frequently co-purchased products together and provide "
        "small bundle discounts to increase repeat purchases."
    ),
    (
        "🔔 Focus on month-to-month customers",
        "Customers on short contracts can have higher churn risk. "
        "Encourage longer-term plans with loyalty benefits."
    ),
    (
        "💳 Improve payment experience",
        "Monitor customers using payment methods associated with higher "
        "churn and provide easier payment options or reminders."
    ),
    (
        "📅 Engage customers early",
        "Customers in their first several months should receive onboarding, "
        "product education and personalized offers."
    ),
    (
        "📧 Build personalized campaigns",
        "Use purchasing history to send relevant product recommendations "
        "instead of generic promotions."
    )
]

for title, description in recommendations:
    st.markdown(f"### {title}")
    st.write(description)

# =========================================================
# EXECUTIVE SUMMARY
# =========================================================

st.divider()

st.header("📋 Executive Summary")

if not customer_sales.empty:
    top_customer = customer_sales.iloc[0]["Customer_ID"]
    top_customer_sales = customer_sales.iloc[0]["Total_Sales"]
else:
    top_customer = "N/A"
    top_customer_sales = 0

if not region_sales.empty:
    top_region = region_sales.iloc[0]["Region"]
    top_region_sales = region_sales.iloc[0]["Total_Sales"]
else:
    top_region = "N/A"
    top_region_sales = 0

if not product_sales.empty:
    top_product = product_sales.iloc[0]["Product"]
else:
    top_product = "N/A"

st.markdown(f"""
**Key Business Findings**

- 🏆 **Most valuable customer:** {top_customer}
  with sales of **₹{top_customer_sales:,.0f}**
- 🌎 **Highest-performing region:** {top_region}
  with sales of **₹{top_region_sales:,.0f}**
- 📦 **Best-selling product:** {top_product}
- 📉 **Overall customer churn:** {overall_churn_rate:.1f}%
- 🎯 Focus retention campaigns on high-value and high-risk customers.
- 🛍️ Use product-pair analysis to create cross-selling bundles.
- 📈 Concentrate marketing resources on high-performing regions while
  developing strategies for weaker regions.
""")

# =========================================================
# DOWNLOAD DATA
# =========================================================

st.header("⬇️ Download Analysis")

csv_data = customer_sales.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Customer Analysis CSV",
    data=csv_data,
    file_name="customer_analysis.csv",
    mime="text/csv"
)

st.caption(
    "Sales dashboard built with Python, Pandas, Plotly and Streamlit."
)