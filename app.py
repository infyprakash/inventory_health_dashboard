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
    page_title="📦 Multi-Product Inventory Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("📦 Inventory Intelligence Dashboard (Multi-Product)")
st.caption("Batch-wise stock analytics + demand forecasting + reorder intelligence")

# =========================
# LOAD DATA
# ========================= 
# path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/stocks.xlsx'

THIS_DIR = Path(__file__).parent
path = THIS_DIR / 'stocks.xlsx'

df = read_dataset(path=path)
current_transactions = process_record_by_transactions_type(dataframe=df)

# =========================
# SIDEBAR CONTROLS
# =========================
st.sidebar.header("🎛️ Filters")

product_group_names = unique_product_group_name(current_transactions)

selected_group = st.sidebar.selectbox(
    "📁 Product Group Name",
    product_group_names
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
    step=1
)

products = products_of_seller(current_transactions, selected_group)

st.info(f"📦 Total Products in Group: **{len(products)}**")

# =========================
# RESULT STORAGE
# =========================
store = []

# =========================
# MAIN PROCESSING
# =========================
try:
    progress_bar = st.progress(0)

    for idx, product in enumerate(products):

        use_col = [
            'date','transaction_type','uom','invoice_number','batch',
            'mfg_date','exp_date','alt_quantity','quantity','value'
        ]

        product_df = current_transactions[current_transactions['product'] == product][use_col]
        sorted_product = product_df.sort_values(by='date')
        last_sale = sorted_product.iloc[-1].date

        batches = sorted_product['batch'].unique()

        # =========================
        # BATCH ANALYSIS
        # =========================
        batch_record = []

        for batch in batches:
            filtered_df = sorted_product[sorted_product['batch'] == batch].sort_values(by='date')

            batch_record.append({
                'batch': batch,
                'first_record_date': filtered_df['date'].iloc[0],
                'last_record_date': filtered_df['date'].iloc[-1],
                'net_stock': round(net_alt_stock(filtered_df), 2),
                'days_in_inventory': (filtered_df['date'].iloc[-1] - filtered_df['date'].iloc[0]).days
            })

        batch_df = pd.DataFrame(batch_record)
        batch_average_days_in_inventory = math.ceil(batch_df['days_in_inventory'].mean())

        # =========================
        # EXPIRY
        # =========================
        if pd.notna(sorted_product['exp_date'].iloc[0]):
            days_to_expire = (sorted_product['exp_date'].iloc[0] - pd.Timestamp('today')).days
        else:
            days_to_expire = 99999

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

            product_sales_series = product_sales[['date','quantity']].groupby('date').sum().reset_index()

            monthly_df = product_sales_series.groupby(pd.Grouper(key='date', freq='ME')).sum().reset_index()

            o_monthly_df = monthly_df.copy()

            # extend trend
            for i in range(2):
                monthly_df.loc[len(monthly_df)] = [
                    monthly_df['date'].iloc[-1] + pd.Timedelta(days=30),
                    monthly_df['quantity'].mean()
                ]

            pm1_avg, pm2_avg = monthly_df['quantity'].iloc[-2], monthly_df['quantity'].iloc[-1]

            lead_days_sales = lead_days * per_day_sales
            stock_until_lead_days = round(stock_in_hand - lead_days_sales, 2)

            order_point = pm1_avg + pm2_avg - stock_until_lead_days

            # =========================
            # FORECAST MODEL
            # =========================
            # monthly_df_model = product_sales_series.groupby(
            #     pd.Grouper(key='date', freq='ME')
            # ).sum()

            # full_range = pd.date_range(
            #     start=monthly_df_model.index.min(),
            #     end=monthly_df_model.index.max(),
            #     freq='ME'
            # )

            # monthly_df_model = monthly_df_model.reindex(full_range, fill_value=0)

            # final_df = monthly_df_model.reset_index()

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

            # point_forecast, _ = model.forecast(
            #     horizon=2,
            #     inputs=[sales_history]
            # )

            # next_month_1 = point_forecast[0][0]
            # next_month_2 = point_forecast[0][1]

            # order_point_forecasted = (next_month_1 + next_month_2) - stock_until_lead_days

            # =========================
            # STORE RESULT
            # =========================
            number_of_days_since_last_sale = (last_sale - product_sales['date'].iloc[-1] ).days
            store.append({
                'product': product,
                'number_of_days_since_last_sale':number_of_days_since_last_sale,
                'batch_avg_inventory_days': batch_average_days_in_inventory,
                'days_to_expire': days_to_expire,
                'stock_in_hand': round(stock_in_hand, 2),
                'stock_until_lead_days': stock_until_lead_days,
                'total_sales': total_alt_sales,
                'order_point_avg': order_point,
                # 'order_point_forecasted': order_point_forecasted
            })

        else:
            st.warning(f"⚠️ No sales record for: {product}")

        # progress
        progress_bar.progress((idx + 1) / len(products))

    # =========================
    # FINAL OUTPUT
    # =========================
    result_df = pd.DataFrame(store)

    st.subheader("📊 Group-Level Inventory Summary")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📦 Products Processed", len(result_df))
    c2.metric("⚠️ Avg Expiry Risk (days)", round(result_df['days_to_expire'].mean(), 2))
    c3.metric("📉 Avg Stock", round(result_df['stock_in_hand'].mean(), 2))
    # c4.metric("📊 Avg Forecast Order Point", round(result_df['order_point_forecasted'].mean(), 2))

    # =========================
    # CHARTS
    # =========================
    st.subheader("📈 Inventory Insights Visualization")

    st.write('stock in hand')
    st.bar_chart(result_df.set_index('product')[['stock_in_hand']])
    st.write('forecasted order point')
    # st.bar_chart(result_df.set_index('product')[['order_point_forecasted']])

    # =========================
    # RAW DATA
    # =========================
    with st.expander("🔍 View Full Product-Level Table"):
        st.dataframe(result_df, use_container_width=True)

except Exception as e:
    st.error("❌ Error occurred while processing")
    st.exception(e)