import pandas as pd
import streamlit as st
from utils.utilities import (
    read_dataset,
    process_record_by_transactions_type,
    unique_product_group_name,
    products_of_seller,
    get_net_stock_balance
)

path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'
sheet = 2
current_df = read_dataset(path=path,sheet=sheet)
current_transactions = process_record_by_transactions_type(current_df)

# suppliers information
product_group_names = unique_product_group_name(current_transactions)
selected_group = st.selectbox(
    label="Select Product Group Name:",
    options=product_group_names,
    index=0  
)

# products sold by suppliers
products = products_of_seller(current_transactions,selected_group)
record = []
for product in products:
    try:
        # select specific product  and sort it by date
        use_col = ['date','transaction_type', 'uom', 'batch', 'mfg_date', 'exp_date', 'quantity','value', 'unit_price']
        product_df = current_transactions[current_transactions['product'] == product][use_col]
        stock_in_hand = get_net_stock_balance(product_df)
        sorted_product = product_df.sort_values(by='date')
        # filter product sales transactions
        product_sales = sorted_product[sorted_product['transaction_type']=='sales']
        last_sale_date = product_sales.iloc[-1].date
        #prepare series for analysis
        product_sales_series = product_sales.sort_values(by='date')[['date','quantity']]
        product_sales_series = product_sales_series.groupby('date')['quantity'].sum().reset_index()
        # aggegate sales monthly
        monthly_df = product_sales_series.groupby(pd.Grouper(key='date', freq='ME')).sum().reset_index()

        total_sales = monthly_df['quantity'].sum()
        duration = len(monthly_df)

        # sales projection for next 2 months
        for i in range(2):
            monthly_df.loc[len(monthly_df)] = [
                monthly_df['date'].iloc[-1]+pd.Timedelta(days=30),\
                monthly_df['quantity'].tail(duration).mean()
            ]

        pm1,pm2 = monthly_df['quantity'].iloc[-2],monthly_df['quantity'].iloc[-1]
        per_day_sales = (total_sales)/ (duration*30)

        lead_days = 75
        max_lead_days = 80

        lead_days_sales = lead_days * per_day_sales
        stock_until_lead_days = (stock_in_hand)- (lead_days_sales)

        order_point_with_lead = pm1 + pm2 - (stock_until_lead_days)
        order_point_without_lead = pm1+pm2

        reorder = {
            'product': [product],
            'net_stock': round(stock_in_hand,2),
            'number_of_days_since_last_sale': (pd.Timestamp('today') - last_sale_date).days,
            monthly_df['date'].iloc[-2]: [monthly_df['quantity'].iloc[-2]],
            monthly_df['date'].iloc[-1]: [monthly_df['quantity'].iloc[-1]],
            'order_point_with_lead': [round(order_point_with_lead,2)],
            'order_point_without_lead': [round(order_point_without_lead,2)],
        }
        # record.append(reorder)
    except Exception as e:
        reorder = {
            'product': [product],
            'net_stock': [0],
            'order_point_with_lead': [0],
            'order_point_without_lead': [0],
        }
    record.append(reorder)
    
    

    
reorder_df = pd.DataFrame(record)
st.write(reorder_df)






# indi page 

import pandas as pd
import streamlit as st
from utils.utilities import (
    read_dataset,
    process_record_by_transactions_type,
    unique_product_group_name,
    products_of_seller,
    get_net_stock_balance
)

path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'
sheet = 2
current_df = read_dataset(path=path,sheet=sheet)
current_transactions = process_record_by_transactions_type(current_df)

# suppliers information
product_group_names = unique_product_group_name(current_transactions)
selected_group = st.selectbox(
    label="Select Product Group Name:",
    options=product_group_names,
    index=0  
)

# products sold by suppliers
products = products_of_seller(current_transactions,selected_group)
selected_product = st.selectbox(
    label="Select Product:",
    options=products
)

# select specific product  and sort it by date
use_col = ['date','transaction_type', 'uom', 'batch', 'mfg_date', 'exp_date', 'quantity','value', 'unit_price']
product_df = current_transactions[current_transactions['product'] == selected_product][use_col]
stock_in_hand = get_net_stock_balance(product_df)
sorted_product = product_df.sort_values(by='date')
st.write(sorted_product)
# filter product sales transactions
product_sales = sorted_product[sorted_product['transaction_type']=='sales']

# last_sale_date = product_sales.iloc[-1].date
#prepare series for analysis
product_sales_series = product_sales.sort_values(by='date')[['date','quantity']]
product_sales_series = product_sales_series.groupby('date')['quantity'].sum().reset_index()
# aggegate sales monthly
monthly_df = product_sales_series.groupby(pd.Grouper(key='date', freq='ME')).sum().reset_index()

total_sales = monthly_df['quantity'].sum()
duration = len(monthly_df)

# sales projection for next 2 months
for i in range(2):
    monthly_df.loc[len(monthly_df)] = [
        monthly_df['date'].iloc[-1]+pd.Timedelta(days=30),\
        monthly_df['quantity'].tail(duration).mean()
    ]

pm1,pm2 = monthly_df['quantity'].iloc[-2],monthly_df['quantity'].iloc[-1]
per_day_sales = (total_sales)/ (duration*30)

lead_days = 75
max_lead_days = 80

lead_days_sales = lead_days * per_day_sales
stock_until_lead_days = (stock_in_hand)- (lead_days_sales)

order_point_with_lead = pm1 + pm2 - (stock_until_lead_days)
order_point_without_lead = pm1+pm2

reorder = {
    'product': [selected_product],
    'net_stock': stock_in_hand,
    # 'number_of_days_since_last_sale': (pd.Timestamp('today') - last_sale_date).days,
    monthly_df['date'].iloc[-2]: [monthly_df['quantity'].iloc[-2]],
    monthly_df['date'].iloc[-1]: [monthly_df['quantity'].iloc[-1]],
    'order_point_with_lead': [order_point_with_lead],
    'order_point_without_lead': [order_point_without_lead],

}
    
reorder_df = pd.DataFrame(reorder)
st.write(reorder_df)






