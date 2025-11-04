# app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Olist Orders API")

ORDERS_CSV = "data/olist_orders_dataset.csv"

@app.on_event("startup")
def load_orders():
    global orders_df
    try:
        # load and lightly clean
        orders_df = pd.read_csv(ORDERS_CSV)
        orders_df.columns = orders_df.columns.str.strip().str.lower()
        # parse datetimes (coerce bad values)
        date_cols = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
        for c in date_cols:
            if c in orders_df.columns:
                orders_df[c] = pd.to_datetime(orders_df[c], errors='coerce', infer_datetime_format=True)
    except Exception as e:
        orders_df = pd.DataFrame()
        print("Failed to load orders CSV:", e)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = None,
    order_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    if orders_df.empty:
        raise HTTPException(status_code=500, detail="Orders data not loaded")

    d = orders_df.copy()

    if customer_id:
        d = d[d['customer_id'].astype(str) == customer_id]

    if order_status:
        d = d[d['order_status'].astype(str).str.lower() == order_status.lower()]

    # filter by purchase date range if given (ISO strings expected)
    if date_from:
        try:
            df = pd.to_datetime(date_from)
            d = d[d['order_purchase_timestamp'] >= df]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date_from format; use ISO YYYY-MM-DD")
    if date_to:
        try:
            dt = pd.to_datetime(date_to)
            d = d[d['order_purchase_timestamp'] <= dt]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date_to format; use ISO YYYY-MM-DD")

    total = len(d)
    start = (page - 1) * page_size
    end = start + page_size
    records = d.iloc[start:end].fillna(None).to_dict(orient="records")
    return JSONResponse({
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": records
    })
