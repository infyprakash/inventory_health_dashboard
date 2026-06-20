import pandas as pd
import streamlit as st

from utils.utilities import (
    read_dataset,
    process_record_by_transactions_type,
    unique_product_group_name,
    products_of_seller,
    get_net_stock_balance
)

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Inventory Health Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("📦 Inventory Health Dashboard")
st.caption("Inventory Planning • Stock Health • Reorder Recommendation")

st.divider()

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'
sheet = 2

current_df = read_dataset(path=path, sheet=sheet)
current_transactions = process_record_by_transactions_type(current_df)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    product_group_names = unique_product_group_name(current_transactions)

    selected_group = st.selectbox(
        "🏭 Product Group",
        options=product_group_names,
        index=0
    )

    st.divider()

    st.markdown("### 📊 Analysis Parameters")

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

    st.info(
        f"""
        Lead Days: {lead_days}

        Max Lead Days: {max_lead_days}

        Forecast Horizon: 2 Months
        """
    )

# ---------------------------------------------------
# PRODUCTS
# ---------------------------------------------------
products = products_of_seller(current_transactions, selected_group)

record = []

for product in products:
    try:
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
            current_transactions['product'] == product
        ][use_col]

        stock_in_hand = get_net_stock_balance(product_df)

        sorted_product = product_df.sort_values(by='date')

        product_sales = sorted_product[
            sorted_product['transaction_type'] == 'sales'
        ]

        last_sale_date = product_sales.iloc[-1].date

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

        # ---------------------------------------------------
        # Forecast next 2 months
        # ---------------------------------------------------
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
        stock_until_lead_days = stock_in_hand - lead_days_sales

        order_point_with_lead = pm1 + pm2 - stock_until_lead_days
        order_point_without_lead = pm1 + pm2

        reorder = {
            'product': product,
            'net_stock': round(stock_in_hand, 2),
            'number_of_days_since_last_sale':
                (pd.Timestamp('today') - last_sale_date).days,
            'forecast_month_1': round(pm1, 2),
            'forecast_month_2': round(pm2, 2),
            'order_point_with_lead':
                round(order_point_with_lead, 2),
            'order_point_without_lead':
                round(order_point_without_lead, 2),
        }

    except Exception:

        reorder = {
            'product': product,
            'net_stock': 0,
            'number_of_days_since_last_sale': 0,
            'forecast_month_1': 0,
            'forecast_month_2': 0,
            'order_point_with_lead': 0,
            'order_point_without_lead': 0,
        }

    record.append(reorder)

# ---------------------------------------------------
# RESULT DATAFRAME
# ---------------------------------------------------
reorder_df = pd.DataFrame(record)

# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------
st.subheader("📈 Inventory Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "📦 Products",
        len(reorder_df)
    )

with c2:
    st.metric(
        "🏭 Product Group",
        selected_group
    )

with c3:
    st.metric(
        "📊 Total Stock",
        f"{reorder_df['net_stock'].sum():,.0f}"
    )

with c4:
    st.metric(
        "🛒 Total Reorder Qty",
        f"{reorder_df['order_point_with_lead'].sum():,.0f}"
    )

st.divider()

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab1, tab2 = st.tabs(
    [
        "📋 Reorder Recommendations",
        "📊 Summary"
    ]
)

# ---------------------------------------------------
# TAB 1
# ---------------------------------------------------
with tab1:

    st.subheader("📦 Product Reorder Planning")

    st.dataframe(
        reorder_df,
        use_container_width=True,
        height=600
    )

    st.download_button(
        label="⬇️ Download Recommendations",
        data=reorder_df.to_csv(index=False),
        file_name="inventory_reorder_recommendations.csv",
        mime="text/csv"
    )

# ---------------------------------------------------
# TAB 2
# ---------------------------------------------------
with tab2:

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Average Stock",
            round(reorder_df["net_stock"].mean(), 2)
        )

        st.metric(
            "Average Reorder Point",
            round(
                reorder_df["order_point_with_lead"].mean(),
                2
            )
        )

    with col2:
        st.metric(
            "Max Stock",
            round(
                reorder_df["net_stock"].max(),
                2
            )
        )

        st.metric(
            "Max Reorder Point",
            round(
                reorder_df["order_point_with_lead"].max(),
                2
            )
        )

    with st.expander("ℹ️ Reorder Logic"):

        st.markdown(
            """
            **Forecast Horizon**
            - Next 2 months average sales projection

            **Order Point Without Lead**
            - Forecast Month 1 + Forecast Month 2

            **Order Point With Lead**
            - Forecast Demand adjusted using stock available during lead time

            **Lead Days**
            - 75 Days
            """
        )