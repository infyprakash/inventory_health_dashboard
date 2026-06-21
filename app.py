
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
    page_title="Inventory Health Dashboard",
    page_icon="📦",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.metric-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 12px;
    border-left: 5px solid #4CAF50;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
}

.section-header {
    background-color: #0E1117;
    color: white;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("📦 Inventory Health Dashboard")
st.caption(
    "Monitor stock health, inventory aging, demand projection, safety stock, and reorder recommendations."
)

# --------------------------------------------------
# DATA LOAD
# --------------------------------------------------
# file_path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'

THIS_DIR = Path(__file__).parent
file_path = THIS_DIR / 'katyani stock as on -3 years.xlsx'

current_df = read_dataset(path=file_path, sheet=2)

current_df.loc[current_df['opening_qty'] > 0, 'date'] = '7/17/2025'
current_df['formatted_date'] = pd.to_datetime(
    current_df['date'],
    format='%m/%d/%Y'
)

current_transactions = process_record_by_transactions_type(current_df)

product_group_names = unique_product_group_name(current_transactions)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:

    st.header("⚙️ Filters")

    selected_group = st.selectbox(
        "📂 Product Group",
        options=product_group_names,
        index=0
    )

    st.divider()

    st.header("📦 Inventory Parameters")

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

    st.markdown("---")

    st.info(
        """
        **Inventory Metrics**
        
        • Current Stock
        
        • Inventory Aging
        
        • Safety Stock
        
        • Reorder Quantity
        
        • Lead-Time Planning
        """
    )

# --------------------------------------------------
# PRODUCTS
# --------------------------------------------------
products = products_of_seller(
    current_transactions,
    selected_group
)

# --------------------------------------------------
# KPI ROW
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Products",
        len(products)
    )

with col2:
    st.metric(
        "📂 Group",
        selected_group
    )

with col3:
    st.metric(
        "📑 Transactions",
        len(current_transactions)
    )

with col4:
    st.metric(
        "📅 Analysis Date",
        pd.Timestamp.today().strftime("%d-%b-%Y")
    )

st.divider()

# --------------------------------------------------
# ORIGINAL LOGIC (UNCHANGED)
# --------------------------------------------------
records = []

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

        sorted_product = product_df.sort_values(by='date')

        product_sales = sorted_product[
            sorted_product['transaction_type'] == 'sales'
        ]

        last_sale = product_sales.iloc[-1].date

        batches = sorted_product['batch'].unique()

        batch_record = []

        for batch in batches:

            filtered_df = sorted_product[
                sorted_product['batch'] == batch
            ].sort_values(by='date')

            if not filtered_df.empty:

                filtered_sales_df = filtered_df[
                    filtered_df['transaction_type'] == 'sales'
                ]

                if not filtered_sales_df.empty:

                    last_batch_sales = filtered_sales_df.iloc[-1]['date']

                    opening_date = filtered_df.iloc[0]['date']

                    f_net_stock = get_net_stock_balance(filtered_df)

                    if int(f_net_stock) == 0:

                        batch_record.append({
                            'batch': batch,
                            'opening_date': opening_date,
                            'net_stock': round(f_net_stock, 2),
                            'days_in_inventory':
                                (last_batch_sales - opening_date).days
                        })

                    else:

                        batch_record.append({
                            'batch': batch,
                            'opening_date': opening_date,
                            'net_stock': round(f_net_stock, 2),
                            'days_in_inventory':
                                (last_sale - opening_date).days
                        })

        batch_df = pd.DataFrame(batch_record)

        average_days_in_inventory = round(
            batch_df['days_in_inventory'].mean(),
            2
        )

        first_sale_date = product_sales.iloc[0].date
        last_sale_date = product_sales.iloc[-1].date

        stock_in_hand = get_net_stock_balance(product_df)

        product_sales_series = product_sales.sort_values(
            by='date'
        )[['date', 'quantity']]

        product_sales_series = product_sales_series.groupby(
            'date'
        )['quantity'].sum().reset_index()

        total_sale_days = (
            last_sale_date - first_sale_date
        ).days

        monthly_df = product_sales_series.groupby(
            pd.Grouper(key='date', freq='ME')
        ).sum().reset_index()

        total_sales = monthly_df['quantity'].sum()
        duration = len(monthly_df)

        for i in range(2):

            monthly_df.loc[len(monthly_df)] = [
                monthly_df['date'].iloc[-1] +
                pd.Timedelta(days=30),

                monthly_df['quantity']
                .tail(duration)
                .mean()
            ]

        pm1 = monthly_df['quantity'].iloc[-2]
        pm2 = monthly_df['quantity'].iloc[-1]

        per_day_sales = (
            total_sales
        ) / total_sale_days

        # lead_days = 75
        # max_lead_days = 80

        lead_days_sales = (
            lead_days * per_day_sales
        )

        safety_stock = (
            product_sales_series['quantity'].max()
            * max_lead_days
        ) - (lead_days_sales)

        stock_until_lead_days = (
            stock_in_hand
        ) - (lead_days_sales)

        order_point_with_lead = (
            pm1 + pm2 - stock_until_lead_days
        )

        order_point_without_lead = (
            pm1 + pm2
        )

        if stock_in_hand != 0:

            reorder = {
                'product': [product],
                'net_stock': round(stock_in_hand, 2),
                'days_in_inventory': total_sale_days,
                'average_days_in_inventory_by_batch':
                    average_days_in_inventory,
                'days_to_expire': 0,
                monthly_df['date'].iloc[-2]:
                    [round(pm1, 2)],
                monthly_df['date'].iloc[-1]:
                    [round(pm2, 2)],
                'order_point_with_lead':
                    [round(order_point_with_lead, 2)],
                'order_point_without_lead':
                    [round(order_point_without_lead, 2)],
                'safety_stock': safety_stock,
            }

        else:

            reorder = {
                'product': [product],
                'net_stock': round(stock_in_hand, 2),
                'days_in_inventory':
                    (pd.Timestamp('today') - last_sale_date).days,
                'average_days_in_inventory_by_batch':
                    average_days_in_inventory,
                'days_to_expire':
                    (
                        sorted_product.iloc[-1]['exp_date']
                        - pd.Timestamp('today')
                    ).days,
                monthly_df['date'].iloc[-2]:
                    [round(pm1, 2)],
                monthly_df['date'].iloc[-1]:
                    [round(pm2, 2)],
                'order_point_with_lead':
                    [round(order_point_with_lead, 2)],
                'order_point_without_lead':
                    [round(order_point_without_lead, 2)],
                'safety_stock': safety_stock,
            }

        records.append(reorder)

    except Exception:
        pass

# --------------------------------------------------
# RESULTS
# --------------------------------------------------
reorder_df = pd.DataFrame(records)

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #E3F2FD, #BBDEFB);
        padding: 14px 20px;
        border-radius: 12px;
        border-left: 6px solid #1976D2;
        margin-bottom: 15px;
    ">
        <h3 style="
            margin:0;
            color:#0D47A1;
            font-weight:600;
        ">
            📋 Inventory Health Report
        </h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.dataframe(
    reorder_df,
    use_container_width=True,
    height=650
)

# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------
csv = reorder_df.to_csv(index=False)

st.download_button(
    label="⬇️ Download Inventory Health Report",
    data=csv,
    file_name="inventory_health_report.csv",
    mime="text/csv"
)