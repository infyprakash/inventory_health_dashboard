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
    page_title="Product Health Analysis",
    page_icon="📦",
    layout="wide"
)

# --------------------------------------------------
# GLOBAL STYLES (same design language)
# --------------------------------------------------
st.markdown("""
<style>

.metric-box {
    background: #F8FFF8;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #D6EFD6;
}

.section-header {
    background: linear-gradient(90deg,#E8F5E9,#C8E6C9);
    padding: 14px;
    border-radius: 12px;
    border-left: 6px solid #2E7D32;
    margin-top: 10px;
    margin-bottom: 10px;
}

.product-card {
    background: white;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("""
<div style="
    background: linear-gradient(90deg,#E8F5E9,#C8E6C9);
    padding:18px;
    border-radius:14px;
    border-left:6px solid #2E7D32;
    margin-bottom:20px;
">
    <h2 style="margin:0;color:#1B5E20;">
        📦 Product Health Analysis Dashboard
    </h2>
    <p style="margin-top:6px;color:#33691E;">
        Inventory aging • Batch health • Forecasting • Safety stock • Reorder planning
    </p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
# file_path = '/Users/prakash/infography_projects/project-2.0/inventory_health_dashboard/katyani stock as on -3 years.xlsx'

THIS_DIR = Path(__file__).parent.parent
file_path = THIS_DIR / 'katyani stock as on -3 years.xlsx'


current_df = read_dataset(path=file_path, sheet=2)
current_df.loc[current_df['opening_qty'] > 0, 'date'] = '7/17/2025'
current_df['formatted_date'] = pd.to_datetime(current_df['date'], format='%m/%d/%Y')

current_transactions = process_record_by_transactions_type(current_df)

product_group_names = unique_product_group_name(current_transactions)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.header("⚙️ Filters")

    selected_group = st.selectbox(
        "📂 Product Group Name",
        product_group_names
    )

    products = products_of_seller(current_transactions, selected_group)

    selected_product = st.selectbox(
        "📦 Product",
        products
    )

    st.divider()

    st.info("""
    📊 Metrics included:

    • Stock Position  
    • Inventory Aging  
    • Batch Movement  
    • Forecast Demand  
    • Safety Stock  
    • Reorder Levels
    """)

# --------------------------------------------------
# PRODUCT CARD
# --------------------------------------------------
st.markdown(f"""
<div class="product-card">
<b>📂 Group:</b> {selected_group} <br>
<b>📦 Product:</b> {selected_product}
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# MAIN LOGIC (UNCHANGED)
# --------------------------------------------------
try:

    use_col = ['date','transaction_type','uom','batch','mfg_date','exp_date',
               'quantity','value','unit_price']

    product_df = current_transactions[
        current_transactions['product'] == selected_product
    ][use_col]

    sorted_product = product_df.sort_values(by='date')

    product_sales = sorted_product[
        sorted_product['transaction_type'] == 'sales'
    ]

    last_sale = product_sales.iloc[-1].date

    batches = sorted_product['batch'].unique()

    batch_record = []

    for batch in batches:
        filtered_df = sorted_product[sorted_product['batch'] == batch].sort_values(by='date')

        if not filtered_df.empty:
            filtered_sales_df = filtered_df[filtered_df['transaction_type'] == 'sales']

            if not filtered_sales_df.empty:
                last_batch_sales = filtered_sales_df.iloc[-1]['date']
                opening_date = filtered_df.iloc[0]['date']
                f_net_stock = get_net_stock_balance(filtered_df)

                if int(f_net_stock) == 0:
                    batch_record.append({
                        'batch': batch,
                        'opening_date': opening_date,
                        'net_stock': round(f_net_stock, 2),
                        'days_in_inventory': (last_batch_sales - opening_date).days
                    })
                else:
                    batch_record.append({
                        'batch': batch,
                        'opening_date': opening_date,
                        'net_stock': round(f_net_stock, 2),
                        'days_in_inventory': (last_sale - opening_date).days
                    })

    batch_df = pd.DataFrame(batch_record)

    average_days_in_inventory = round(batch_df['days_in_inventory'].mean(), 2)

    first_sale_date = product_sales.iloc[0].date
    last_sale_date = product_sales.iloc[-1].date

    stock_in_hand = get_net_stock_balance(product_df)

    product_sales_series = product_sales.sort_values(by='date')[['date','quantity']]
    product_sales_series = product_sales_series.groupby('date')['quantity'].sum().reset_index()

    total_sale_days = (last_sale_date - first_sale_date).days

    monthly_df = product_sales_series.groupby(pd.Grouper(key='date', freq='ME')).sum().reset_index()

    total_sales = monthly_df['quantity'].sum()
    duration = len(monthly_df)

    for i in range(2):
        monthly_df.loc[len(monthly_df)] = [
            monthly_df['date'].iloc[-1] + pd.Timedelta(days=30),
            monthly_df['quantity'].tail(duration).mean()
        ]

    pm1, pm2 = monthly_df['quantity'].iloc[-2], monthly_df['quantity'].iloc[-1]

    per_day_sales = total_sales / total_sale_days

    lead_days = 75
    max_lead_days = 80

    lead_days_sales = lead_days * per_day_sales

    safety_stock = (
        product_sales_series['quantity'].max() * max_lead_days
    ) - lead_days_sales

    stock_until_lead_days = stock_in_hand - lead_days_sales

    order_point_with_lead = pm1 + pm2 - stock_until_lead_days
    order_point_without_lead = pm1 + pm2

    # --------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📦 Stock", round(stock_in_hand,2))

    with col2:
        st.metric("⏳ Aging", average_days_in_inventory)

    with col3:
        st.metric("📈 M+1", round(pm1,2))

    with col4:
        st.metric("📈 M+2", round(pm2,2))

    with col5:
        st.metric("🛡️ Safety Stock", round(safety_stock,2))

    # --------------------------------------------------
    # BATCH TABLE
    # --------------------------------------------------
    st.markdown("""
    <div class="section-header">
        📋 Batch Inventory Analysis
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(batch_df, use_container_width=True, height=250)

    # --------------------------------------------------
    # REORDER METRICS
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.metric("📦 Reorder (Lead)", round(order_point_with_lead,2))

    with col2:
        st.metric("📦 Reorder (No Lead)", round(order_point_without_lead,2))

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------
    if stock_in_hand != 0:
        reorder = {
            'product': [selected_product],
            'net_stock': round(stock_in_hand,2),
            'days_in_inventory': total_sale_days,
            'average_days_in_inventory_by_batch': average_days_in_inventory,
            'days_to_expire': 0,
            monthly_df['date'].iloc[-2]: [monthly_df['quantity'].iloc[-2]],
            monthly_df['date'].iloc[-1]: [monthly_df['quantity'].iloc[-1]],
            'order_point_with_lead': [round(order_point_with_lead,2)],
            'order_point_without_lead': [round(order_point_without_lead,2)],
            'safety_stock': safety_stock,
        }
    else:
        reorder = {
            'product': [selected_product],
            'net_stock': round(stock_in_hand,2),
            'days_in_inventory': (pd.Timestamp('today') - last_sale_date).days,
            'average_days_in_inventory_by_batch': average_days_in_inventory,
            'days_to_expire': (sorted_product.iloc[-1]['exp_date'] - pd.Timestamp('today')).days,
            monthly_df['date'].iloc[-2]: [monthly_df['quantity'].iloc[-2]],
            monthly_df['date'].iloc[-1]: [monthly_df['quantity'].iloc[-1]],
            'order_point_with_lead': [round(order_point_with_lead,2)],
            'order_point_without_lead': [round(order_point_without_lead,2)],
            'safety_stock': safety_stock,
        }

except Exception:
    reorder = {
        'product': [selected_product],
        'net_stock': [0],
        'days_in_inventory': [0],
        'average_days_in_inventory_by_batch': [0],
        'days_to_expire': [0],
    }

# --------------------------------------------------
# FINAL TABLE
# --------------------------------------------------
record = pd.DataFrame(reorder)

st.markdown("""
<div class="section-header">
    📊 Product Health Summary
</div>
""", unsafe_allow_html=True)

st.dataframe(record, use_container_width=True)

# --------------------------------------------------
# INFO SECTION (IMPORTANT)
# --------------------------------------------------
with st.expander("ℹ️ How These Metrics Are Calculated"):

    st.markdown("""
### 📦 Stock In Hand
Net inventory available at any point.

**Formula:** Purchases − Sales

---

### ⏳ Inventory Aging
Average time stock remains in warehouse.

**Formula:** Mean(Batch Closing Date − Batch Opening Date)

---

### 📈 Forecast (M+1, M+2)
Based on historical monthly average sales.

---

### 🛡️ Safety Stock
Buffer stock for demand & supply uncertainty.

**Formula:**
(Max Daily Sales × Max Lead Days) − Lead Time Demand

---

### 📦 Reorder Point (Lead Time)
Demand during lead time + forecast adjustment.

---

### 📦 Reorder Point (No Lead Time)
Simple forecast-based demand estimate.

---

### 📅 Days in Inventory
Time between first and last sale.

---

### 📅 Days to Expiry
Only calculated when stock is zero.
""")