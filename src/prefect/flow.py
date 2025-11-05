from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text  # <-- IMPORTED
from typing import List, Dict, Any
from dotenv import load_dotenv

import src.api.crud as crud
import src.api.models as models
from src.api.database import get_db

# Load env variables (e.g., for DATABASE_URL)
load_dotenv()

app = FastAPI(
    title="Olist Analytics API",
    description="API to serve analytics data from the Olist dataset.",
    version="1.0.0"
)

def map_row_to_dict(row) -> Dict[str, Any]:
    """Converts a SQLAlchemy Row object to a dictionary."""
    return dict(row._mapping)


@app.get("/", response_model=models.HealthCheck, tags=["Health"])
def read_root(db: Session = Depends(get_db)):  # <-- ADDED DB DEPENDENCY
    """
    Performs a simple health check, including a database connection test.
    """
    # --- MODIFIED HEALTH CHECK ---
    try:
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        # If DB connection fails, return a 503 error
        raise HTTPException(
            status_code=503,
            detail=f"Service Unavailable: Database connection failed. Error: {str(e)}"
        )
    # --- END OF MODIFICATION ---


@app.get("/sales_summary", response_model=List[models.SalesSummary], tags=["Analytics"])
def read_sales_summary(
    page: int = 1, 
    page_size: int = Query(default=10, le=100, ge=1), 
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of sales summary data, sorted by total sales.
    """
    try:
        sales_rows = crud.get_sales_summary(db, page=page, page_size=page_size)
        # Manually map rows to dictionaries for Pydantic validation
        sales_list = [map_row_to_dict(row) for row in sales_rows]
        return sales_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/delivery_performance", response_model=List[models.DeliveryPerformance], tags=["Analytics"])
def read_delivery_performance(db: Session = Depends(get_db)):
    """
    Get delivery performance metrics for all regions.
    """
    try:
        delivery_rows = crud.get_delivery_performance(db)
        delivery_list = [map_row_to_dict(row) for row in delivery_rows]
        return delivery_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/sales_summary/{region}", response_model=List[models.SalesSummary], tags=["Analytics"])
def read_sales_summary_by_region(region: str, db: Session = Depends(get_db)):
    """
    Get sales summary data for a specific region (case-sensitive state code, e.g., 'SP').
    """
    try:
        sales_rows = crud.get_sales_summary_by_region(db, region=region)
        if not sales_rows:
            raise HTTPException(status_code=404, detail=f"No data found for region: {region}")
        sales_list = [map_row_to_dict(row) for row in sales_rows]
        return sales_list
    except HTTPException:
        raise # Re-raise 404
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

