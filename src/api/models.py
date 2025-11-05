from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthCheck(BaseModel):
    """Response model for health check."""
    status: str

class SalesSummary(BaseModel):
    """Response model for sales_summary table."""
    customer_unique_id: str
    customer_id: str
    region: Optional[str]
    total_orders: int
    total_sales: float
    avg_order_value: float
    last_order_date: Optional[datetime]

    class Config:
        orm_mode = True # Deprecated, but use `from_attributes = True` for Pydantic v2
        from_attributes = True


class DeliveryPerformance(BaseModel):
    """Response model for delivery_performance table."""
    region: str
    total_orders: int
    delivered_count: int
    pending_count: int
    avg_delivery_days: Optional[float]
    total_late: int
    percent_late: Optional[float]
    percent_pending: Optional[float]

    class Config:
        orm_mode = True
        from_attributes = True
