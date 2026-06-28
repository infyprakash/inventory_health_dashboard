
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

# os.environ["HF_TOKEN"] = st.secrets["HF_TOKEN"]
THIS_DIR = Path(__file__).parent.parent
path = THIS_DIR / 'stocks.xlsx'

# path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/stocks.xlsx'
df = read_dataset(path=path)

transactions = get_transactions(df)

product_group_names = unique_product_group_name(transactions)

selected_group = st.sidebar.selectbox("Product Group Name",product_group_names)
products = products_of_seller(transactions, selected_group)
selected_product = st.sidebar.selectbox("Product",products)
lead_days = st.sidebar.number_input("Lead Days",min_value=1,max_value=365,value=75,step=1,help="Expected supplier lead time in days")


product = selected_product
record = {'product':product}

use_col = ['date','transaction_type', 'uom', 'invoice_number', 'batch', 'mfg_date','exp_date', 'alt_quantity', 'quantity', 'value']
product_df = transactions[transactions['product']==product]
st.write(product_df[use_col])
batches = product_df['batch'].unique()

first_transaction_date,last_transaction_date = get_first_last_transaction_date(transactions=transactions)
batch_data = []
for batch in batches:
  temp = dict()
  product_by_batch = product_df[product_df['batch']==batch].sort_values(by='date')
  temp['batch'] = batch
  temp['net_alt_quantity'] = net_alt_stock(product_by_batch)[0]
  temp['days_in_inventory'] = (last_transaction_date - product_by_batch['date'].iloc[0] ).days
  temp['days_to_last_sale'] = (product_by_batch['date'].iloc[-1] - product_by_batch['date'].iloc[0] ).days
  batch_data.append(temp)

batch_df = pd.DataFrame(batch_data)
st.write(batch_df)

record['net_alt_qty'] = round(batch_df['net_alt_quantity'].sum(),2)

# batch_df = batch_df[batch_df['net_alt_quantity'] >0]

record['average_days_in_inventory'] = math.ceil(batch_df['days_in_inventory'].mean())
record['average_days_to_last_sale'] = math.ceil(batch_df['days_to_last_sale'].mean())
record['total_alt_sales']  = get_sales_quantity(product_df,record)[0]
record['per_day_alt_sales'] = get_sales_quantity(product_df,record)[1]

product_sales_df = product_df[product_df['transaction_type']=='sales'][['date','alt_quantity']]
day_sales_df = product_sales_df.groupby('date')['alt_quantity'].sum().reset_index().sort_values(by='date')
monthly_sales_df = day_sales_df.groupby(pd.Grouper(key='date', freq='MS')).sum().reset_index()

st.write(monthly_sales_df)
st.line_chart(monthly_sales_df.set_index('date'))

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
record[forecast['date'].iloc[0].strftime('%Y-%m-%d')] = round(forecast['sales'].iloc[0],2)
record[forecast['date'].iloc[-1].strftime('%Y-%m-%d')] = round(forecast['sales'].iloc[-1],2)
record['lead_days_sales'] = lead_days * record['per_day_alt_sales']
record['alt_qty_until_lead_days'] = round((record['net_alt_qty'] - record['lead_days_sales']),2)
record['reorder_alt_qty_without_lead'] = round(forecast['sales'].sum(),2)
record['reorder_alt_qty_with_lead'] =  round((forecast['sales'].sum() - record['alt_qty_until_lead_days']),2)


# sales_history = monthly_sales_df['alt_quantity'].to_numpy(dtype="float32")
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

# record[f'{forecast['date'].iloc[0].strftime('%Y-%m-%d')}_forecast'] = next_month_1
# record[f'{forecast['date'].iloc[-1].strftime('%Y-%m-%d')}_forecast'] = next_month_2
# record['reorder_alt_qty_without_lead_forecasted'] = (next_month_1 + next_month_2)
# record['reorder_alt_qty_with_lead_forecasted'] = round(((next_month_1 + next_month_2) - record['alt_until_lead_days']),2)

st.write(record)











