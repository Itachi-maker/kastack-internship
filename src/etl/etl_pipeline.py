import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('root')

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DATA_PATH = os.getenv("DATA_PATH")

if not DATABASE_URL:
    logger.error("DATABASE_URL not set. Check your .env file.")
    raise ValueError("DATABASE_URL not set.")
if not DATA_PATH:
    logger.error("DATA_PATH not set. Check your .env file.")
    raise ValueError("DATA_PATH not set.")

engine = create_engine(DATABASE_URL)

def extract():
    """Extracts data from CSV files."""
    try:
        customers_df = pd.read_csv(os.path.join(DATA_PATH, "olist_customers_dataset.csv"))
        items_df = pd.read_csv(os.path.join(DATA_PATH, "olist_order_items_dataset.csv"))
        payments_df = pd.read_csv(os.path.join(DATA_PATH, "olist_order_payments_dataset.csv"))
        orders_df = pd.read_csv(os.path.join(DATA_PATH, "olist_orders_dataset.csv"))
        
        logger.info("Data extracted successfully.")
        return customers_df, items_df, payments_df, orders_df
    except FileNotFoundError as e:
        logger.error(f"Error extracting data: {e}. Make sure CSV files are in {DATA_PATH}.")
        raise

def transform(customers_df, items_df, payments_df, orders_df):
    """Transforms dataframes and creates the raw_orders table."""
    
    # --- 1. Create raw_orders table ---
    # Merge all datasets into one denormalized table
    df = pd.merge(orders_df, customers_df, on="customer_id", how="left")
    df = pd.merge(df, items_df, on="order_id", how="left")
    df = pd.merge(df, payments_df, on="order_id", how="left")

    # Drop duplicates that might arise from joins (e.g., multiple payments for one item)
    # We keep the first instance of each unique item-payment combination
    df = df.drop_duplicates(subset=['order_id', 'order_item_id', 'payment_sequential'])

    # Clean and parse date columns
    date_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date', 'shipping_limit_date'
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
    # Handle potential nulls in key financial columns before aggregation
    df['price'] = df['price'].fillna(0)
    df['freight_value'] = df['freight_value'].fillna(0)
    df['payment_value'] = df['payment_value'].fillna(0)

    # This is our main 'raw_orders' table, one row per item-payment entry
    raw_orders_df = df.copy()

    # --- 2. Create Analytics Table: sales_summary ---
    
    # We need one row per *order* to calculate sales totals correctly.
    # Group payments by order_id to get total payment_value per order.
    order_payments = payments_df.groupby('order_id')['payment_value'].sum().reset_index()
    
    # Merge orders, customers, and aggregated payments
    base_df = pd.merge(orders_df, customers_df, on='customer_id', how='left')
    base_df = pd.merge(base_df, order_payments, on='order_id', how='left')

    base_df['order_purchase_timestamp'] = pd.to_datetime(base_df['order_purchase_timestamp'], errors='coerce')
    base_df['payment_value'] = base_df['payment_value'].fillna(0)

    # Aggregate by customer
    sales_summary = base_df.groupby('customer_unique_id').agg(
        customer_id=('customer_id', 'first'),
        region=('customer_state', 'first'),
        total_orders=('order_id', 'nunique'),
        total_sales=('payment_value', 'sum'),
        last_order_date=('order_purchase_timestamp', 'max')
    ).reset_index()

    sales_summary['avg_order_value'] = (sales_summary['total_sales'] / sales_summary['total_orders']).fillna(0)

    # --- 3. Create Analytics Table: delivery_performance ---
    
    # Use the 'base_df' which is one-row-per-order
    deliv_df = base_df.copy()
    
    # Parse dates
    deliv_df['order_purchase_timestamp'] = pd.to_datetime(deliv_df['order_purchase_timestamp'], errors='coerce')
    deliv_df['order_delivered_customer_date'] = pd.to_datetime(deliv_df['order_delivered_customer_date'], errors='coerce')
    deliv_df['order_estimated_delivery_date'] = pd.to_datetime(deliv_df['order_estimated_delivery_date'], errors='coerce')

    # Calculate metrics
    deliv_df['delivery_days'] = (deliv_df['order_delivered_customer_date'] - deliv_df['order_purchase_timestamp']).dt.days
    deliv_df['is_late'] = (deliv_df['order_delivered_customer_date'] > deliv_df['order_estimated_delivery_date']).astype(int)
    deliv_df['is_delivered'] = deliv_df['order_delivered_customer_date'].notna().astype(int)
    
    # Define 'pending' as not delivered and not in a final error/cancel state
    pending_statuses = ['delivered', 'canceled', 'unavailable']
    deliv_df['is_pending'] = (
        (deliv_df['order_delivered_customer_date'].isna()) &
        (~deliv_df['order_status'].isin(pending_statuses))
    ).astype(int)

    # Aggregate by region (customer_state)
    delivery_performance = deliv_df.groupby('customer_state').agg(
        total_orders=('order_id', 'nunique'),
        delivered_count=('is_delivered', 'sum'),
        pending_count=('is_pending', 'sum'),
        avg_delivery_days=('delivery_days', 'mean'), # 'mean' ignores NaNs by default
        total_late=('is_late', 'sum')
    ).reset_index()
    
    delivery_performance = delivery_performance.rename(columns={'customer_state': 'region'})

    # Calculate percentages, handling division by zero
    delivery_performance['percent_late'] = (
        (delivery_performance['total_late'] / delivery_performance['delivered_count']) * 100
    ).fillna(0)
    
    delivery_performance['percent_pending'] = (
        (delivery_performance['pending_count'] / delivery_performance['total_orders']) * 100
    ).fillna(0)

    logger.info("Data transformed successfully.")
    return raw_orders_df, sales_summary, delivery_performance

def load(df, table_name):
    """Loads a DataFrame into a PostgreSQL table."""
    try:
        # Use if_exists='replace' to create/recreate the table on each run
        df.to_sql(table_name, engine, if_exists='replace', index=False, chunksize=1000)
        logger.info(f"Loaded table '{table_name}' ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Error loading table {table_name}: {e}")
        raise

def run_etl():
    """Main ETL function to run all steps."""
    logger.info("Starting ETL process...")
    
    customers, items, payments, orders = extract()
    
    raw_orders, sales_summary, delivery_performance = transform(
        customers, items, payments, orders
    )
    
    load(raw_orders, 'raw_orders')
    load(sales_summary, 'sales_summary')
    load(delivery_performance, 'delivery_performance')
    
    logger.info("ETL process completed successfully.")
