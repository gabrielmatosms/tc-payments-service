from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DENIED = "Denied"
    REJECTED = "Rejected"
    UNKNOWN = "Unknown"


class QRCodeRequest(BaseModel):
    description: str
    total: Decimal
    order_id: int


class Payment(BaseModel):
    order_id: int
    amount: Decimal
    status: PaymentStatus
    external_id: Optional[str] = None


class PaymentDb(Payment):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 