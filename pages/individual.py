import pandas as pd
import streamlit as st
from pathlib import Path

from utils.utilities import (
    read_dataset,
    process_record_by_transactions_type,
    unique_product_group_name,
    products_of_seller,
    get_net_stock_balance
)

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Product Health Analysis",
    page_icon="📦",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("📦 Product Health Analysis")
st.caption("Inventory Health • Sales Trend • Reorder Recommendation")

st.divider()

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
THIS_DIR = Path(__file__).parent
path = THIS_DIR / 'katyani stock as on -3 years.xlsx'
# path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'
sheet = 2

current_df = read_dataset(path=path, sheet=sheet)
current_transactions = process_record_by_transactions_type(current_df)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:

    st.header("⚙️ Product Selection")

    product_group_names = unique_product_group_name(
        current_transactions
    )

    selected_group = st.selectbox(
        "🏭 Product Group",
        options=product_group_names
    )

    products = products_of_seller(
        current_transactions,
        selected_group
    )

    selected_product = st.selectbox(
        "📦 Product",
        options=products
    )
    lead_days = st.number_input(
        "🚚 Lead Days",
        min_value=1,
        max_value=365,
        value=75,
        step=1,
        help="Expected supplier lead time in days"
    )

    max_lead_days = st.number_input(
        "⏳ Maximum Lead Days",
        min_value=1,
        max_value=365,
        value=80,
        step=1,
        help="Maximum observed lead time"
    )

# --------------------------------------------------
# PRODUCT DATA
# --------------------------------------------------
use_col = [
    'date',
    'transaction_type',
    'uom',
    'batch',
    'mfg_date',
    'exp_date',
    'quantity',
    'value',
    'unit_price'
]

product_df = current_transactions[
    current_transactions['product'] == selected_product
][use_col]

stock_in_hand = get_net_stock_balance(product_df)

sorted_product = product_df.sort_values(by='date')

product_sales = sorted_product[
    sorted_product['transaction_type'] == 'sales'
]

product_sales_series = (
    product_sales
    .sort_values(by='date')[['date', 'quantity']]
)

product_sales_series = (
    product_sales_series
    .groupby('date')['quantity']
    .sum()
    .reset_index()
)

monthly_df = (
    product_sales_series
    .groupby(pd.Grouper(key='date', freq='ME'))
    .sum()
    .reset_index()
)

total_sales = monthly_df['quantity'].sum()
duration = len(monthly_df)

# --------------------------------------------------
# FORECAST (UNCHANGED)
# --------------------------------------------------
for i in range(2):

    monthly_df.loc[len(monthly_df)] = [
        monthly_df['date'].iloc[-1] + pd.Timedelta(days=30),
        monthly_df['quantity'].tail(duration).mean()
    ]

pm1 = monthly_df['quantity'].iloc[-2]
pm2 = monthly_df['quantity'].iloc[-1]

per_day_sales = total_sales / (duration * 30)

# lead_days = 75
# max_lead_days = 80

lead_days_sales = lead_days * per_day_sales

stock_until_lead_days = (
    stock_in_hand - lead_days_sales
)

order_point_with_lead = (
    pm1 + pm2 - stock_until_lead_days
)

order_point_without_lead = (
    pm1 + pm2
)

# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------
st.subheader("📈 Product Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "📦 Stock In Hand",
        round(stock_in_hand, 2)
    )

with c2:
    st.metric(
        "📊 Total Sales",
        round(total_sales, 2)
    )

with c3:
    st.metric(
        "📅 Forecast Month 1",
        round(pm1, 2)
    )

with c4:
    st.metric(
        "📅 Forecast Month 2",
        round(pm2, 2)
    )

st.divider()

# --------------------------------------------------
# REORDER KPI
# --------------------------------------------------
st.subheader("🛒 Reorder Recommendation")

r1, r2, r3 = st.columns(3)

with r1:
    st.metric(
        "🚚 Lead Days",
        lead_days
    )

with r2:
    st.metric(
        "📦 Reorder With Lead",
        round(order_point_with_lead, 2)
    )

with r3:
    st.metric(
        "📦 Reorder Without Lead",
        round(order_point_without_lead, 2)
    )

st.divider()

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📈 Sales Trend",
        "🛒 Reorder Analysis",
        "📋 Transactions",
        "📊 Monthly Sales"
    ]
)

# --------------------------------------------------
# TAB 1
# --------------------------------------------------
with tab1:

    st.subheader("📈 Product Sales Trend")

    chart_df = monthly_df.copy()

    st.line_chart(
        chart_df.set_index('date')['quantity']
    )

# --------------------------------------------------
# TAB 2
# --------------------------------------------------
with tab2:

    reorder_df = pd.DataFrame({
        'product': [selected_product],
        'net_stock': [stock_in_hand],
        'forecast_month_1': [pm1],
        'forecast_month_2': [pm2],
        'order_point_with_lead': [
            order_point_with_lead
        ],
        'order_point_without_lead': [
            order_point_without_lead
        ]
    })

    st.dataframe(
        reorder_df,
        use_container_width=True
    )

    st.download_button(
        "⬇️ Download Recommendation",
        reorder_df.to_csv(index=False),
        file_name=f"{selected_product}_reorder.csv",
        mime="text/csv"
    )

# --------------------------------------------------
# TAB 3
# --------------------------------------------------
with tab3:

    st.subheader("📋 Transaction History")

    st.dataframe(
        sorted_product,
        use_container_width=True,
        height=500
    )

# --------------------------------------------------
# TAB 4
# --------------------------------------------------
with tab4:

    st.subheader("📊 Monthly Sales")

    st.dataframe(
        monthly_df,
        use_container_width=True
    )

# --------------------------------------------------
# EXPLAINER
# --------------------------------------------------
with st.expander("ℹ️ Inventory Planning Logic"):

    st.markdown(
        """
        ### Forecast
        - Next 2 months are projected using average historical monthly sales.

        ### Lead Time Consumption
        - Daily Sales = Total Sales / Total Days
        - Lead Time Demand = Daily Sales × Lead Days

        ### Reorder Point

        **Without Lead Time**
        ```
        Forecast Month 1 + Forecast Month 2
        ```

        **With Lead Time**
        ```
        Forecast Month 1
        + Forecast Month 2
        - Remaining Stock After Lead Time
        ```
        """
    )