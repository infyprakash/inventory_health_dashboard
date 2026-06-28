import os

import numpy as np
import pandas as pd
import streamlit as st
import timesfm
from math import sqrt

def read_dataset(path):
  df = pd.read_excel(path,skiprows=7)
  df = df.iloc[:-1]
  df.columns = ['product_group_name', 'product_additional_group', 'product_sub_group',
       'product', 'date', 'uom', 'inv_no', 'batch', 'miti', 'batch_rate',
       'batch_buy_price', 'batch_sales_price', 'batch_mrp', 'descriptions',
       'mfg_date', 'exp_date', 'opening_alt_stock_qty', 'opening_stock_qty', 'opening_stock_value',
       'purchase_invoice_in_alt_stock_qty', 'purchase_invoice_in_stock_qty', 'purchase_invoice_in_stock_value',
       'stock_adjustment_in_alt_stock_qty', 'stock_adjustment_in_stock_qty', 'stock_adjustment_in_stock_value',
       'sales_return_in_alt_stock_qty', 'sales_return_in_stock_qty', 'sales_return_in_stock_value',
       'sales_invoice_out_alt_stock_qty', 'sales_invoice_out_stock_qty', 'sales_invoice_out_stock_value',
       'stock_adjustment_out_alt_stock_qty', 'stock_adjustment_out_stock_qty', 'stock_adjustment_out_stock_value',
       'balance_alt_stock_qty', 'balance_stock_qty', 'balance_stock_value']

  df.loc[df['opening_alt_stock_qty']>0,'date'] = '7/17/2025'
  df['formatted_date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
  df['exp_date'] = pd.to_datetime(df['exp_date'], format='%Y-%m-%d')
  return df

def process_record_by_transactions_type(dataframe):
    tran_rows = []
    for idx,row in dataframe.iterrows():
        product_group_name = row['product_group_name']
        sub_group = row['product_sub_group']
        product = row['product']
        date = row['date']
        uom = row['uom']
        invoice_number = row['inv_no']
        batch = row['batch']
        mfg_date = row['mfg_date']
        exp_date = row['exp_date']

        if (pd.notna(row['opening_alt_stock_qty']) and  row['opening_alt_stock_qty'] > 0):
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'opening',
                'uom':uom,
                'invoice_number':invoice_number,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'alt_quantity': row['opening_alt_stock_qty'],
                'quantity': row['opening_stock_qty'],
                'value': row['opening_stock_value'],
                # 'base_quantity': (row['opening_stock_qty'] / row['opening_alt_stock_qty'] if row['opening_alt_stock_qty'] >0 else np.nan),
                'unit_price': (row['opening_stock_value']/row['opening_stock_qty']) if row['opening_stock_qty'] > 0 else np.nan
            })

        if (pd.notna(row['purchase_invoice_in_alt_stock_qty']) and row['purchase_invoice_in_alt_stock_qty'] > 0):
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'purchase',
                'uom':uom,
                'invoice_number':invoice_number,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'alt_quantity': row['purchase_invoice_in_alt_stock_qty'],
                'quantity': row['purchase_invoice_in_stock_qty'],
                'value': row['purchase_invoice_in_stock_value'],
                # 'base_quantity': (row['purchase_invoice_in_stock_qty'] / row['purchase_invoice_in_alt_stock_qty'] if row['purchase_invoice_in_alt_stock_qty'] >0 else np.nan),
                'unit_price': (row['purchase_invoice_in_stock_value']/row['purchase_invoice_in_stock_qty']) if row['purchase_invoice_in_stock_qty'] > 0 else np.nan
            })

        if (pd.notna(row['stock_adjustment_in_alt_stock_qty']) and row['stock_adjustment_in_alt_stock_qty'] != 0):
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'adjustment_in',
                'uom':uom,
                'invoice_number':invoice_number,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'alt_quantity': row['stock_adjustment_in_alt_stock_qty'],
                'quantity': row['stock_adjustment_in_stock_qty'],
                'value': row['stock_adjustment_in_stock_value'],
                # 'base_quantity': (row['stock_adjustment_in_stock_qty'] / row['stock_adjustment_in_alt_stock_qty'] if row['stock_adjustment_in_alt_stock_qty'] >0 else np.nan),
                'unit_price': (row['stock_adjustment_in_stock_value']/row['stock_adjustment_in_stock_qty']) if row['stock_adjustment_in_stock_qty'] > 0 else np.nan
            })

        if (pd.notna(row['stock_adjustment_out_alt_stock_qty']) and row['stock_adjustment_out_alt_stock_qty'] != 0):
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'adjustment_out',
                'uom':uom,
                'invoice_number':invoice_number,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'alt_quantity': row['stock_adjustment_out_alt_stock_qty'],
                'quantity': row['stock_adjustment_out_stock_qty'],
                'value': row['stock_adjustment_out_stock_value'],
                # 'base_quantity': (row['stock_adjustment_out_stock_qty'] / row['stock_adjustment_out_alt_stock_qty'] if row['stock_adjustment_out_alt_stock_qty'] >0 else np.nan),
                'unit_price': (row['stock_adjustment_out_stock_value']/row['stock_adjustment_out_stock_qty']) if row['stock_adjustment_out_stock_qty'] > 0 else np.nan
            })

        if (pd.notna(row['sales_return_in_alt_stock_qty']) and row['sales_return_in_alt_stock_qty'] != 0):
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'sales_return',
                'uom':uom,
                'invoice_number':invoice_number,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'alt_quantity': row['sales_return_in_alt_stock_qty'],
                'quantity': row['sales_return_in_stock_qty'],
                'value': row['sales_return_in_stock_value'],
                # 'base_quantity': (row['sales_return_in_stock_qty'] / row['sales_return_in_alt_stock_qty'] if row['sales_return_in_alt_stock_qty'] >0 else np.nan),
                'unit_price': (row['sales_return_in_stock_value']/row['sales_return_in_stock_qty']) if row['sales_return_in_stock_qty'] > 0 else np.nan
            })

        if (pd.notna(row['sales_invoice_out_alt_stock_qty']) and row['sales_invoice_out_alt_stock_qty'] != 0):
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'sales',
                'uom':uom,
                'invoice_number':invoice_number,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'alt_quantity': row['sales_invoice_out_alt_stock_qty'],
                'quantity': row['sales_invoice_out_stock_qty'],
                'value': row['sales_invoice_out_stock_value'],
                # 'base_quantity': (row['sales_invoice_out_stock_qty'] / row['sales_invoice_out_alt_stock_qty'] if row['sales_invoice_out_alt_stock_qty'] >0 else np.nan),
                'unit_price': (row['sales_invoice_out_stock_value']/row['sales_invoice_out_stock_qty']) if row['sales_invoice_out_stock_qty'] > 0 else np.nan
            })
    transactions_df = pd.DataFrame(tran_rows)
    return transactions_df



def unique_product_group_name(df,col='product_group_name'):
  unique_columns = df[col].unique()
  return unique_columns

def products_of_seller(df,group_name,col='product_group_name',filter_col='product'):
  products = df[df[col]==group_name]['product'].unique()
  return products

def get_first_last_transaction_date(transactions):
  sorted_transactions = transactions.sort_values(by='date')
  first_date = sorted_transactions['date'].iloc[0]
  last_date = sorted_transactions['date'].iloc[-1]
  return first_date,last_date

def net_alt_stock(product_df):
  total_opening = product_df[product_df['transaction_type']=='opening']['alt_quantity'].sum()
  total_purchase = product_df[product_df['transaction_type']=='purchase']['alt_quantity'].sum()
  total_sales_return = product_df[product_df['transaction_type']=='sales_return']['alt_quantity'].sum()
  total_adjustment_in = product_df[product_df['transaction_type']=='adjustment_in']['alt_quantity'].sum()
  total_adjustment_out = product_df[product_df['transaction_type']=='adjustment_out']['alt_quantity'].sum()
  total_sales = product_df[product_df['transaction_type']=='sales']['alt_quantity'].sum()
  net_stock_balance = (total_opening + total_purchase + total_sales_return + total_adjustment_in) - (total_sales+total_adjustment_out)
  net_sales = total_sales - total_sales_return
  return net_stock_balance,net_sales

def get_sales_quantity(product_df,record):
  total_sales = net_alt_stock(product_df)[1]
  per_day_sales = round((total_sales / record['average_days_in_inventory']),2) if record['net_alt_qty'] > 0 else round((total_sales / record['average_days_to_last_sale']),2)
  return total_sales,per_day_sales

def get_transactions(df):
   transactions = process_record_by_transactions_type(dataframe=df)
   return transactions


@st.cache_resource
def load_timesfm_model():
    os.environ["HF_TOKEN"] = st.secrets["HF_TOKEN"]
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
        "google/timesfm-2.5-200m-pytorch",
    )
    # If running on CPU (Streamlit Cloud), compilation often causes issues/slowness.
    # Try omitting model.compile() if you are just doing a few inferences.
    model.compile(timesfm.ForecastConfig(
        max_context=512, max_horizon=32, infer_is_positive=True,
    ))
    return model






