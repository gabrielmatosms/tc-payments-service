from typing import List, Optional

from sqlalchemy.orm import Session

from app.adapters.models.sql.payment_model import PaymentModel
from app.domain.entities.payment import Payment, PaymentDb, PaymentStatus
from app.domain.interfaces.payment_repository import PaymentRepository


class SQLPaymentRepository(PaymentRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_all(self) -> List[PaymentDb]:
        payments = self.db_session.query(PaymentModel).all()
        return [self._map_to_entity(payment) for payment in payments]

    def get_by_id(self, payment_id: int) -> Optional[PaymentDb]:
        payment = self.db_session.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        return self._map_to_entity(payment) if payment else None

    def get_by_order_id(self, order_id: int) -> Optional[PaymentDb]:
        payment = self.db_session.query(PaymentModel).filter(PaymentModel.order_id == order_id).first()
        return self._map_to_entity(payment) if payment else None

    def create(self, payment: Payment) -> PaymentDb:
        db_payment = PaymentModel(
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status,
            external_id=payment.external_id
        )
        self.db_session.add(db_payment)
        self.db_session.commit()
        self.db_session.refresh(db_payment)
        return self._map_to_entity(db_payment)

    def update_status(self, payment_id: int, status: PaymentStatus) -> Optional[PaymentDb]:
        db_payment = self.db_session.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not db_payment:
            return None
        
        db_payment.status = status
        self.db_session.commit()
        self.db_session.refresh(db_payment)
        return self._map_to_entity(db_payment)
    
    def update_external_id(self, payment_id: int, external_id: str) -> Optional[PaymentDb]:
        db_payment = self.db_session.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not db_payment:
            return None
        
        db_payment.external_id = external_id
        self.db_session.commit()
        self.db_session.refresh(db_payment)
        return self._map_to_entity(db_payment)
    
    def _map_to_entity(self, model: PaymentModel) -> PaymentDb:
        return PaymentDb(
            id=model.id,
            order_id=model.order_id,
            amount=model.amount,
            status=PaymentStatus(model.status),
            external_id=model.external_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        ) 