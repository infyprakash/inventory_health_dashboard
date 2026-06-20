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

# def process_inventory_state(transaction_df):
#     balance = []
#     for (sub_group,batch),group in transaction_df.groupby(['sub_group','batch']):
#         net = 0.0
#         for idx,row in group.iterrows():
#             if row['transaction_type'] in ['opening','purchase','sales_return']:
#                 net += row['quantity']
#             elif row['transaction_type'] == 'sales':
#                 net -= row['quantity']
#             elif row['transaction_type'] == 'adjustment':
#                 net += row['quantity']

#         last_row = group.iloc[-1]
#         balance.append({
#             'product_group_name': last_row['product_group_name'],
#             'sub_group':sub_group,
#             'product': last_row['product'],
#             'uom':last_row['uom'],
#             'batch':batch,
#             'mfg_date':last_row['mfg_date'],
#             'exp_date':last_row['exp_date'],
#             'current_stock_qty':net
#             })
#     inventory_state = pd.DataFrame(balance)
#     return inventory_state

def process_inventory_state(transaction_df,group_col='sub_group'):
    balance = []
    for (sub_group,batch),group in transaction_df.groupby([group_col,'batch']):
        net = 0.0
        for idx,row in group.iterrows():
            if row['transaction_type'] in ['opening','purchase','sales_return']:
                net += row['quantity']
            elif row['transaction_type'] == 'sales':
                net -= row['quantity']
            elif row['transaction_type'] == 'adjustment':
                net += row['quantity']

        last_row = group.iloc[-1]
        if group_col=='sub_group':
          balance.append({
              'product_group_name': last_row['product_group_name'],
              'sub_group':sub_group,
              'product': last_row['product'],
              'uom':last_row['uom'],
              'batch':batch,
              'mfg_date':last_row['mfg_date'],
              'exp_date':last_row['exp_date'],
              'current_stock_qty':net
              })
        elif group_col=='product_group_name':
            balance.append({
              'product_group_name': sub_group,
              'sub_group':last_row['sub_group'],
              'product': last_row['product'],
              'uom':last_row['uom'],
              'batch':batch,
              'mfg_date':last_row['mfg_date'],
              'exp_date':last_row['exp_date'],
              'current_stock_qty':net
              })
        else:
            balance.append({
              'product_group_name': last_row['product_group_name'],
              'sub_group':last_row['sub_group'],
              'product': sub_group,
              'uom':last_row['uom'],
              'batch':batch,
              'mfg_date':last_row['mfg_date'],
              'exp_date':last_row['exp_date'],
              'current_stock_qty':net
              })
           
    inventory_state = pd.DataFrame(balance)
    return inventory_state

def abc_analysis(transaction_df,group_col='sub_group'):
  sales_df = transaction_df[transaction_df['transaction_type']=='sales'].copy()
  sales_df = sales_df.groupby(group_col)['value'].sum().reset_index().sort_values(by='value',ascending=False)
  sales_df.columns = [group_col,'total_sales']
  total_sales = sales_df['total_sales'].sum()
  sales_df['cum_percent'] = (sales_df['total_sales'].cumsum()/total_sales)*100
  def assign_abc_class(cum_pct):
    if cum_pct <= 70:
      return 'A'
    elif cum_pct <= 90:
      return 'B'
    else:
      return 'C'
  sales_df['ABC_class'] = sales_df['cum_percent'].apply(assign_abc_class)
  return sales_df



def xyz_analysis(transaction_df, group_col='sub_group'):
    """
    XYZ Analysis based on demand variability (quantity over time).
    Ensures missing months are padded with 0 before calculating CV.
    """
    sales_df = transaction_df[transaction_df['transaction_type'] == 'sales'].copy()
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    sales_df['month'] = sales_df['date'].dt.to_period('M')
    
    monthly = sales_df.groupby([group_col, 'month'])['quantity'].sum().reset_index()
    
    full_data = []
    for key, group in monthly.groupby(group_col):
        all_months = pd.period_range(group['month'].min(), group['month'].max(), freq='M')
        
        temp = group.set_index('month')['quantity'].reindex(all_months, fill_value=0).reset_index()
        temp.columns = ['month', 'quantity']
        temp[group_col] = key
        full_data.append(temp)
    
    monthly_full = pd.concat(full_data, ignore_index=True)
    demand_stats = monthly_full.groupby(group_col)['quantity'].agg(['mean', 'std', 'count']).reset_index()
    
    demand_stats['cv'] = demand_stats['std'] / demand_stats['mean'].replace(0, np.nan)
    
    def classify(row):
        cv = row['cv']
        count = row['count']
        
        if pd.isna(cv) or count <= 1:
            return 'Z'   # No demand variation trackable or single month data
        elif cv <= 0.5:
            return 'X'   # Stable demand
        elif cv <= 1.0:
            return 'Y'   # Moderate variation
        else:
            return 'Z'   # Highly irregular demand

    demand_stats['XYZ_class'] = demand_stats.apply(classify, axis=1)
    return demand_stats.drop(columns=['count'])

def get_product_daywise_sales(sales_df,selected_column,selected_value):
   product_sales_df = sales_df[sales_df[selected_column]==selected_value]
   product_sales_df = product_sales_df.sort_values(by='date').reset_index(drop=True)
   daywise_sales_df = product_sales_df.groupby(['date'])['quantity'].sum()
   daywise_sales_df = daywise_sales_df.asfreq('D',fill_value=0).reset_index()
   daywise_sales_df.columns = ['date','total_sales']
   return daywise_sales_df

def get_monthwise_sales(daywise_df):
  df = daywise_df.set_index('date')
  monthly_sales = df.resample('MS')['total_sales'].sum()
  return monthly_sales

def get_product_quarterly_sales(daywise_sales_df):
   q_sales_df = daywise_sales_df.set_index('date')
   
   def get_fiscal_quarter(date):
    adjusted_date = date - pd.Timedelta(days = 16)
    month = adjusted_date.month
    if month in [7,8,9]:
      q = 'Q1'
    elif month in [10,11,12]:
      q = 'Q2'
    elif month in [1,2,3]:
      q = 'Q3'
    else:
      q = 'Q4'
    
    fiscal_year = (adjusted_date.year if month < 7 else adjusted_date.year+1)
    return f'FY{fiscal_year}-{q}'
   
   q_sales_df['fiscal_period'] = q_sales_df.index.map(get_fiscal_quarter)
   agg_q_sales_df = q_sales_df.groupby('fiscal_period')['total_sales'].sum()
   return q_sales_df,agg_q_sales_df

def classify_sku(abc_df, xyz_df,on='sub_group'):
    df = abc_df.merge(xyz_df, on=on, how='inner')
    df['SKU_class'] = df['ABC_class'] + df['XYZ_class']
    return df



def generate_reorder_recommendations(
    df,
    group_col='sub_group',
    lead_time=7,
    review_period=30,
    service_level_mapping=None,
    default_cv_mapping=None,
    output_all=False
):
    """
    Improved reorder system:
    - ABC-XYZ aware demand adjustment
    - CV-weighted safety stock
    - demand dampening for volatile classes
    - priority-based ordering instead of binary decision
    """

    data = df[df[group_col] != 0].copy()
    data.reset_index(drop=True, inplace=True)

    # numeric cleanup
    for col in ['mean', 'std', 'cv', 'current_stock_qty']:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    data = data[data['mean'].notna() & (data['mean'] > 0)]
    data = data[data['current_stock_qty'].notna()]

    # service level mapping (ABC-XYZ aware)
    if service_level_mapping is None:
        service_level_mapping = {
            'AX': 1.65, 'AY': 1.28, 'AZ': 0.84,
            'BX': 1.28, 'BY': 1.04, 'BZ': 0.84,
            'CX': 0.84, 'CY': 0.84, 'CZ': 0.67
        }

    if default_cv_mapping is None:
        default_cv_mapping = {'X': 0.4, 'Y': 0.8, 'Z': 1.5}

    data['XYZ_class'] = data['SKU_class'].str[-1]

    # ----------------------------
    # Fill missing std
    # ----------------------------
    def fill_std(row):
        if pd.notna(row['std']) and row['std'] > 0:
            return row['std']
        if pd.notna(row['cv']) and row['cv'] > 0:
            return row['mean'] * row['cv']
        return row['mean'] * default_cv_mapping.get(row['XYZ_class'], 1.0)

    data['std_filled'] = data.apply(fill_std, axis=1)

    results = []

    for _, row in data.iterrows():

        sku_class = row['SKU_class']
        abc = row.get('ABC_class', 'C')
        xyz = row['XYZ_class']

        z = service_level_mapping.get(sku_class, service_level_mapping['CZ'])

        mean_daily = row['mean']
        std_daily = row['std_filled']
        current = row['current_stock_qty']
        cv = row['cv'] if pd.notna(row['cv']) else std_daily / mean_daily

        # ----------------------------
        # 1. Demand adjustment (IMPORTANT FIX)
        # ----------------------------
        demand_factor = 1.0

        if xyz == 'Y':
            demand_factor = 0.9
        elif xyz == 'Z':
            demand_factor = 0.75   # damp unstable demand

        if abc == 'C':
            demand_factor *= 0.9   # low priority SKUs

        adj_demand = mean_daily * demand_factor

        # ----------------------------
        # 2. CV-aware safety stock
        # ----------------------------
        cv_penalty = min(1.5, max(0.5, cv))

        safety_stock = z * std_daily * sqrt(lead_time) * cv_penalty

        rop = adj_demand * lead_time + safety_stock

        target = adj_demand * (lead_time + review_period) + safety_stock

        suggested_order = max(0, target - current)

        days_cover = current / adj_demand if adj_demand > 0 else np.nan

        stock_gap = max(0, rop - current)
        stock_gap_ratio = stock_gap / rop if rop > 0 else 0

        abc_weight = {'A': 3, 'B': 2, 'C': 1}.get(abc, 1)
        xyz_weight = {'X': 1, 'Y': 1.5, 'Z': 2}.get(xyz, 1)

        priority_score = stock_gap_ratio * abc_weight * xyz_weight * cv_penalty

        need_reorder = (current < rop) and (priority_score > 0.15)

        results.append({
            'sub_group': row[group_col],
            'SKU_class': sku_class,
            'ABC_class': abc,
            'XYZ_class': xyz,

            'current_stock_qty': current,
            'mean_daily': mean_daily,
            'adjusted_demand': round(adj_demand, 2),

            'reorder_point': round(rop, 2),
            'safety_stock': round(safety_stock, 2),
            'target_inventory': round(target, 2),

            'suggested_order_qty': round(suggested_order, 2),

            'days_of_cover': round(days_cover, 2),
            'cv': cv,

            'priority_score': round(priority_score, 4),
            'need_reorder': need_reorder
        })

    report_df = pd.DataFrame(results)

    if not output_all:
        report_df = report_df[report_df['need_reorder'] == True]

    report_df = report_df.sort_values('priority_score', ascending=False)

    return report_df



@st.cache_data
def get_transactions():
  path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'
  
  sheet_names = [0,1,2]
  dfs = []
  for sheet in sheet_names:
    dataframe = read_dataset(path=path,sheet=sheet)
    dfs.append(dataframe)
  
  dataframe = pd.concat(dfs,ignore_index=True)
  transaction_df = process_record_by_transactions_type(dataframe=dataframe)
  return transaction_df