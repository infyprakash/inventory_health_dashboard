import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import timesfm
import streamlit as st
from pathlib import Path

from utils.utilities import (
    read_dataset,
    get_transactions,
    unique_product_group_name,
    products_of_seller,
    get_first_last_transaction_date,
    net_alt_stock,
    get_sales_quantity
)

# ---------------------------------------------------------
# Page Configurations & Styling
# ---------------------------------------------------------
st.set_page_config(page_title="Inventory Health Dashboard", layout="wide")

# Custom CSS for clean UI and pleasant color scheme (No Icons)
st.markdown("""
    <style>
        .reportview-container { background: #fdfdfd; }
        .metric-card {
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #0f766e;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
        .metric-label { font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
        .metric-value { font-size: 1.4rem; color: #0f172a; font-weight: 700; margin-top: 5px; }
        h1, h2, h3 { color: #0f172a; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("Inventory Health Dashboard")
st.markdown("---")

# ---------------------------------------------------------
# Data Loading & Processing (Original Logic)
# ---------------------------------------------------------
THIS_DIR = Path(__file__).parent.parent
path = THIS_DIR / 'stocks.xlsx'

df = read_dataset(path=path)
transactions = get_transactions(df)
product_group_names = unique_product_group_name(transactions)

# Sidebar organization
st.sidebar.header("Filter Options")
selected_group = st.sidebar.selectbox("Product Group Name", product_group_names)
products = products_of_seller(transactions, selected_group)
selected_product = st.sidebar.selectbox("Product", products)
lead_days = st.sidebar.number_input("Lead Days", min_value=1, max_value=365, value=75, step=1, help="Expected supplier lead time in days")

product = selected_product
record = {'product': product}

use_col = ['date', 'transaction_type', 'uom', 'invoice_number', 'batch', 'mfg_date', 'exp_date', 'alt_quantity', 'quantity', 'value']
product_df = transactions[transactions['product'] == product]
batches = product_df['batch'].unique()

first_transaction_date, last_transaction_date = get_first_last_transaction_date(transactions=transactions)
batch_data = []
for batch in batches:
    temp = dict()
    product_by_batch = product_df[product_df['batch'] == batch].sort_values(by='date')
    temp['batch'] = batch
    temp['net_alt_quantity'] = net_alt_stock(product_by_batch)[0]
    temp['days_in_inventory'] = (last_transaction_date - product_by_batch['date'].iloc[0]).days
    temp['days_to_last_sale'] = (product_by_batch['date'].iloc[-1] - product_by_batch['date'].iloc[0]).days
    batch_data.append(temp)

batch_df = pd.DataFrame(batch_data)

record['net_alt_qty'] = round(batch_df['net_alt_quantity'].sum(), 2)
record['average_days_in_inventory'] = math.ceil(batch_df['days_in_inventory'].mean())
record['average_days_to_last_sale'] = math.ceil(batch_df['days_to_last_sale'].mean())
record['total_alt_sales'] = get_sales_quantity(product_df, record)[0]
record['per_day_alt_sales'] = get_sales_quantity(product_df, record)[1]

product_sales_df = product_df[product_df['transaction_type'] == 'sales'][['date', 'alt_quantity']]
day_sales_df = product_sales_df.groupby('date')['alt_quantity'].sum().reset_index().sort_values(by='date')
monthly_sales_df = day_sales_df.groupby(pd.Grouper(key='date', freq='MS')).sum().reset_index()

number_of_months = len(monthly_sales_df)
history = monthly_sales_df["alt_quantity"].tolist()
future = []

for _ in range(2):
    pred = sum(history[- number_of_months:]) / len(history[- number_of_months:])
    future.append(pred)
    history.append(pred)

forecast = pd.DataFrame({
    "date": pd.date_range(
        df["date"].max() + pd.offsets.MonthEnd(1),
        periods=2,
        freq="ME"
    ),
    "sales": future
})

record[forecast['date'].iloc[0].strftime('%Y-%m-%d')] = round(forecast['sales'].iloc[0], 2)
record[forecast['date'].iloc[-1].strftime('%Y-%m-%d')] = round(forecast['sales'].iloc[-1], 2)
record['lead_days_sales'] = lead_days * record['per_day_alt_sales']
record['alt_qty_until_lead_days'] = round((record['net_alt_qty'] - record['lead_days_sales']), 2)
record['reorder_alt_qty_without_lead'] = round(forecast['sales'].sum(), 2)
record['reorder_alt_qty_with_lead'] = round((forecast['sales'].sum() - record['alt_qty_until_lead_days']), 2)


# ---------------------------------------------------------
# UI Layout Components
# ---------------------------------------------------------

# Top Summary Level KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Net Alt Qty</div><div class="metric-value">{record["net_alt_qty"]}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Avg Days In Inventory</div><div class="metric-value">{record["average_days_in_inventory"]}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Alt Sales</div><div class="metric-value">{record["total_alt_sales"]}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Reorder Qty (With Lead)</div><div class="metric-value">{record["reorder_alt_qty_with_lead"]}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Organize core content into clean navigation tabs
tab1, tab2, tab3 = st.tabs(["Sales Analysis & Forecast", "Batch & Transaction Logs", "Raw Records Summary"])

with tab1:
    st.subheader("Monthly Sales Trend")
    st.line_chart(monthly_sales_df.set_index('date'), color="#0f766e")
    
    st.subheader("Monthly Sales Data Breakdown")
    st.dataframe(monthly_sales_df, use_container_width=True)

with tab2:
    st.subheader("Product Transactions Log")
    st.dataframe(product_df[use_col], use_container_width=True)
    
    st.subheader("Batch Summary Log")
    st.dataframe(batch_df, use_container_width=True)

with tab3:
    st.subheader("Calculated Record Summary")
    # Presenting the dictionary records in a clean structured dataframe format instead of raw json string dump
    record_df = pd.DataFrame(list(record.items()), columns=["Metric Key", "Calculated Value"])
    st.dataframe(record_df, use_container_width=True)