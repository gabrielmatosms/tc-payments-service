from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pymongo.collection import Collection

from app.adapters.models.nosql.connection import payment_collection
from app.domain.entities.payment import Payment, PaymentDb, PaymentStatus
from app.domain.interfaces.payment_repository import PaymentRepository


class NoSQLPaymentRepository(PaymentRepository):
    def __init__(self, collection: Collection = payment_collection):
        self.collection = collection

    def get_all(self) -> List[PaymentDb]:
        payments = list(self.collection.find())
        return [self._map_to_entity(payment) for payment in payments]

    def get_by_id(self, payment_id: int) -> Optional[PaymentDb]:
        payment = self.collection.find_one({"_id": payment_id})
        return self._map_to_entity(payment) if payment else None

    def get_by_order_id(self, order_id: int) -> Optional[PaymentDb]:
        payment = self.collection.find_one({"order_id": order_id})
        return self._map_to_entity(payment) if payment else None

    def create(self, payment: Payment) -> PaymentDb:
        # Find the highest id to simulate auto-increment
        last_payment = self.collection.find_one(sort=[("_id", -1)])
        next_id = 1 if not last_payment else last_payment["_id"] + 1
        
        now = datetime.utcnow()
        payment_dict = {
            "_id": next_id,
            "order_id": payment.order_id,
            "amount": float(payment.amount),
            "status": payment.status,
            "external_id": payment.external_id,
            "created_at": now,
            "updated_at": now
        }
        
        self.collection.insert_one(payment_dict)
        return self._map_to_entity(payment_dict)

    def update_status(self, payment_id: int, status: PaymentStatus) -> Optional[PaymentDb]:
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": payment_id},
            {"$set": {"status": status, "updated_at": now}}
        )
        
        if result.modified_count == 0:
            return None
            
        return self.get_by_id(payment_id)
    
    def update_external_id(self, payment_id: int, external_id: str) -> Optional[PaymentDb]:
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": payment_id},
            {"$set": {"external_id": external_id, "updated_at": now}}
        )
        
        if result.modified_count == 0:
            return None
            
        return self.get_by_id(payment_id)
    
    def _map_to_entity(self, data: dict) -> PaymentDb:
        return PaymentDb(
            id=data["_id"],
            order_id=data["order_id"],
            amount=Decimal(str(data["amount"])),
            status=PaymentStatus(data["status"]),
            external_id=data.get("external_id"),
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        ) 