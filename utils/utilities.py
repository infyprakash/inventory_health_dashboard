import numpy as np
import pandas as pd
import streamlit as st
from math import sqrt

def read_dataset(path,sheet=0):
    df = pd.read_excel(path,skiprows=7,sheet_name=sheet)
    df = df.iloc[:-1]

    df.columns = ['product_group_name', 'product_additional_group', 'sub_group',
       'product', 'date', 'uom', 'inv_no', 'batch', 'miti', 'batch_rate',
       'batch_buy_price', 'batch_sales_price', 'batch_mrp', 'descriptions',
       'mfg_date', 'exp_date', 'opening_qty', 'opening_value', 'purchase_qty', 'purchase_value', 'stock_adjust_qty_0',
       'stock_adjust_value_0', 'sales_return_qty', 'sales_return_value', 'sales_qty', 'sales_value', 'stock_adjust_qty_1',
       'stock_adjust_value_1','close_balance_qty', 'close_balance_value']
    numeric_cols = ['opening_qty', 'opening_value', 'purchase_qty',
       'purchase_value', 'stock_adjust_qty_0', 'stock_adjust_value_0',
       'sales_return_qty', 'sales_return_value', 'sales_qty', 'sales_value',
       'stock_adjust_qty_1', 'stock_adjust_value_1', 'close_balance_qty',
       'close_balance_value']

    for col in numeric_cols:
        df.loc[:,col] = df[col].fillna(0)

    df.loc[df['opening_qty']>0,'date'] = '7/17/2023'
    df['formatted_date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
    return df

def process_record_by_transactions_type(dataframe):
    tran_rows = []
    for idx,row in dataframe.iterrows():
        product_group_name = row['product_group_name']
        sub_group = row['sub_group']
        product = row['product']
        date = row['date']
        uom = row['uom']
        batch = row['batch']
        mfg_date = row['mfg_date']
        exp_date = row['exp_date']

        if row['opening_qty'] > 0:
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'opening',
                'uom':uom,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'quantity': row['opening_qty'],
                'value': row['opening_value'],
                'unit_price': (row['opening_value']/row['opening_qty']) if row['opening_qty'] > 0 else np.nan
            })

        if row['purchase_qty'] > 0:
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'purchase',
                'uom':uom,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'quantity': row['purchase_qty'],
                'value': row['purchase_value'],
                'unit_price': (row['purchase_value']/row['purchase_qty']) if row['purchase_qty'] > 0 else np.nan
            })

        if row['stock_adjust_qty_0'] != 0:
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'adjustment',
                'uom':uom,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'quantity': row['stock_adjust_qty_0'],
                'value': row['stock_adjust_value_0'],
                'unit_price': (row['stock_adjust_value_0']/row['stock_adjust_qty_0']) if row['stock_adjust_qty_0'] > 0 else np.nan
            })

        if row['stock_adjust_qty_1'] != 0:
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'adjustment',
                'uom':uom,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'quantity': row['stock_adjust_qty_1'],
                'value': row['stock_adjust_value_1'],
                'unit_price': (row['stock_adjust_value_1']/row['stock_adjust_qty_1']) if row['stock_adjust_qty_1'] > 0 else np.nan
            })

        if row['sales_return_qty'] != 0:
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'sales_return',
                'uom':uom,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'quantity': row['sales_return_qty'],
                'value': row['sales_return_value'],
                'unit_price': (row['sales_return_value']/row['sales_return_qty']) if row['sales_return_qty'] > 0 else np.nan
            })

        if row['sales_qty'] != 0:
            tran_rows.append({
                'product_group_name': product_group_name,
                'sub_group':sub_group,
                'product':product,
                'date':date,
                'transaction_type':'sales',
                'uom':uom,
                'batch':batch,
                'mfg_date':mfg_date,
                'exp_date':exp_date,
                'quantity': row['sales_qty'],
                'value': row['sales_value'],
                'unit_price': (row['sales_value']/row['sales_qty']) if row['sales_qty'] > 0 else np.nan
            })
    transactions_df = pd.DataFrame(tran_rows)
    return transactions_df

def unique_product_group_name(df,col='product_group_name'):
  unique_columns = df[col].unique()
  return unique_columns

def products_of_seller(df,group_name,col='product_group_name',filter_col='product'):
  products = df[df[col]==group_name]['product'].unique()
  return products

def get_net_stock_balance(product_df):
  total_opening = product_df[product_df['transaction_type']=='opening']['quantity'].sum()
  total_purchase = product_df[product_df['transaction_type']=='purchase']['quantity'].sum()
  total_sales_return = product_df[product_df['transaction_type']=='sales_return']['quantity'].sum()
  total_adjustment = product_df[product_df['transaction_type']=='adjustment']['quantity'].sum()
  total_sales = product_df[product_df['transaction_type']=='sales']['quantity'].sum()
  net_stock_balance = (total_opening + total_purchase + total_sales_return + total_adjustment) - (total_sales)
  return net_stock_balance


