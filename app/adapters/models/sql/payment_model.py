from sqlalchemy import Column, Integer, Numeric, String

from app.adapters.models.sql.base import BaseModel


class PaymentModel(BaseModel):
    __tablename__ = "payments"

    order_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    status = Column(String, nullable=False)
    external_id = Column(String, nullable=True) 