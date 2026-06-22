
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import torch
# import timesfm
import streamlit as st
from pathlib import Path

from utils.utilities import (
    read_dataset,
    process_record_by_transactions_type,
    unique_product_group_name,
    products_of_seller,
    net_alt_stock
)



# =========================
# PAGE CONFIG
# =========================


st.set_page_config(
    page_title="📦 Inventory Health Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📦 Inventory Health Dashboard")
st.caption("AI-powered stock analytics, demand forecasting & reorder intelligence")

# =========================
# DATA LOAD
# =========================

# path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/stocks.xlsx'

THIS_DIR = Path(__file__).parent.parent
path = THIS_DIR / 'stocks.xlsx'

df = read_dataset(path=path)
current_transactions = process_record_by_transactions_type(dataframe=df)

# =========================
# MAIN UI
# =========================
try:
    product_group_names = unique_product_group_name(current_transactions)

    # =========================
    # SIDEBAR CONTROLS
    # =========================
    st.sidebar.header("🎛️ Controls")

    selected_group = st.sidebar.selectbox(
        "📁 Product Group Name",
        product_group_names
    )

    products = products_of_seller(current_transactions, selected_group)

    selected_product = st.sidebar.selectbox(
        "📦 Product",
        products
    )

    lead_days = st.sidebar.number_input(
        "🚚 Lead Days",
        min_value=1,
        max_value=365,
        value=75,
        step=1,
        help="Expected supplier lead time in days"
    )

    max_lead_days = st.sidebar.number_input(
        "⏳ Maximum Lead Days",
        min_value=1,
        max_value=365,
        value=80,
        step=1,
        help="Maximum observed lead time"
    )

    # =========================
    # FILTER DATA
    # =========================
    use_col = ['date','transaction_type', 'uom', 'invoice_number', 'batch',
               'mfg_date','exp_date', 'alt_quantity', 'quantity', 'value']

    product_df = current_transactions[current_transactions['product'] == selected_product][use_col]
    sorted_product = product_df.sort_values(by='date')
    last_sale = sorted_product.iloc[-1].date

    net_alt_stock_balance = round(net_alt_stock(sorted_product), 2)
    batches = sorted_product['batch'].unique()

    # =========================
    # BATCH ANALYSIS
    # =========================
    batch_record = []

    for batch in batches:
        filtered_df = sorted_product[sorted_product['batch'] == batch].sort_values(by='date')
        first_record_date = filtered_df['date'].iloc[0]
        last_record_date = filtered_df['date'].iloc[-1]
        net_stock = net_alt_stock(filtered_df)

        batch_record.append({
            'batch': batch,
            'first_record_date': first_record_date,
            'last_record_date': last_record_date,
            'net_stock': round(net_stock, 2),
            'days_in_inventory': (last_record_date - first_record_date).days
        })

    batch_df = pd.DataFrame(batch_record)
    batch_average_days_in_inventory = math.ceil(batch_df['days_in_inventory'].mean())

    # =========================
    # EXPIRY CALCULATION
    # =========================
    if pd.notna(sorted_product['exp_date'].iloc[0]):
        days_to_expire = (sorted_product['exp_date'].iloc[0] - pd.Timestamp('today')).days
    else:
        days_to_expire = 99999

    # =========================
    # STOCK + SALES LOGIC
    # =========================
    stock_in_hand = net_alt_stock(product_df)
    total_fiscal_days = (sorted_product['date'].iloc[-1] - sorted_product['date'].iloc[0]).days
    product_sales = sorted_product[sorted_product['transaction_type'] == 'sales'].sort_values(by='date')

    if not product_sales.empty:

        total_alt_sales = product_sales['alt_quantity'].sum()

        average_alt_sales_during_fiscal_days = (
            round((total_alt_sales / total_fiscal_days), 2)
            if total_fiscal_days > 0 else 0.0
        )

        per_day_sales = average_alt_sales_during_fiscal_days

        product_sales_series = product_sales.sort_values(by='date')[['date','quantity']]
        product_sales_series = product_sales_series.groupby('date')['quantity'].sum().reset_index()

        monthly_df = product_sales_series.groupby(pd.Grouper(key='date', freq='ME')).sum().reset_index()
        o_monthly_df = monthly_df.copy()

        # extend forecast baseline
        for i in range(2):
            monthly_df.loc[len(monthly_df)] = [
                monthly_df['date'].iloc[-1] + pd.Timedelta(days=30),
                monthly_df['quantity'].mean()
            ]

        pm1_avg, pm2_avg = monthly_df['quantity'].iloc[-2], monthly_df['quantity'].iloc[-1]

        lead_days_sales = lead_days * per_day_sales
        stock_until_lead_days = round((stock_in_hand - lead_days_sales), 2)

        order_point = pm1_avg + pm2_avg - stock_until_lead_days

        # =========================
        # HEADER METRICS
        # =========================
        st.subheader("📊 Key Inventory Insights")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("📦 Stock in Hand", round(stock_in_hand, 2))
        c2.metric("🚚 Lead Day Stock Buffer", stock_until_lead_days)
        c3.metric("⏳ Days to Expiry", days_to_expire)
        c4.metric("📉 Avg Inventory Days", batch_average_days_in_inventory)

        # =========================
        # SALES CHART
        # =========================
        st.subheader("📈 Monthly Sales Trend")

        st.line_chart(o_monthly_df.set_index('date'))

        # =========================
        # BATCH ANALYSIS
        # =========================
        st.subheader("📦 Batch Performance")

        # colA, colB = st.columns([2, 1])

        # with colA:
        st.dataframe(batch_df, use_container_width=True)

        # with colB:
        #     st.bar_chart(batch_df.set_index('batch')['net_stock'])

        # =========================
        # ORDER POINT INFO
        # =========================
        st.subheader("📍 Order Planning Indicators")

        basic_result = {
            'product': [selected_product],
            'batch_average_days_in_inventory': [batch_average_days_in_inventory],
            'days_to_expire': [days_to_expire],
            'stock_in_hand': [round(stock_in_hand, 2)],
            'stock_until_lead_days': [stock_until_lead_days],
            'total_fiscal_days': [total_fiscal_days],
            'total_alt_sales': [total_alt_sales],
            'first_month': [monthly_df['date'].iloc[-2]],
            'second_month': [monthly_df['date'].iloc[-1]],
            'pm1': [pm1_avg],
            'pm2': [pm2_avg],
            'order_point_by_sales_average': [order_point]
        }

        # =========================
        # FORECASTING (TimesFM)
        # =========================
        # st.subheader("🤖 Demand Forecasting (AI Model)")

        # print("Loading pre-trained TimesFM 2.5 weights from HuggingFace...")

        # monthly_df = product_sales_series.groupby(pd.Grouper(key='date', freq='ME')).sum()

        # full_range = pd.date_range(start=monthly_df.index.min(),
        #                            end=monthly_df.index.max(),
        #                            freq='ME')

        # monthly_df = monthly_df.reindex(full_range, fill_value=0)
        # final_df = monthly_df.reset_index()

        # sales_history = final_df['quantity'].to_numpy(dtype="float32")

        # torch.set_float32_matmul_precision("high")

        # model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
        #     "google/timesfm-2.5-200m-pytorch",
        # )

        # model.compile(timesfm.ForecastConfig(
        #     max_context=512,
        #     max_horizon=32,
        #     infer_is_positive=True,
        # ))

        # point_forecast, quantile_forecast = model.forecast(
        #     horizon=2,
        #     inputs=[sales_history]
        # )

        # next_month_1 = point_forecast[0][0]
        # next_month_2 = point_forecast[0][1]

        # order_point_forecasted = (next_month_1 + next_month_2) - stock_until_lead_days

        # basic_result['order_point_forecasted'] = [order_point_forecasted]

        result_df = pd.DataFrame(basic_result)

        st.dataframe(result_df, use_container_width=True)

        # =========================
        # RAW DATA (EXPANDER)
        # =========================
        with st.expander("🔍 View Monthly Aggregation Data"):
            st.dataframe(monthly_df)
            

    else:
        st.warning("⚠️ No Sales Record Found for this Product")

except Exception as e:
    st.error("❌ Error occurred while processing data")
    st.exception(e)