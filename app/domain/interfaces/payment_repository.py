from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.payment import Payment, PaymentDb, PaymentStatus


class PaymentRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[PaymentDb]:
        pass

    @abstractmethod
    def get_by_id(self, payment_id: int) -> Optional[PaymentDb]:
        pass

    @abstractmethod
    def get_by_order_id(self, order_id: int) -> Optional[PaymentDb]:
        pass

    @abstractmethod
    def create(self, payment: Payment) -> PaymentDb:
        pass

    @abstractmethod
    def update_status(self, payment_id: int, status: PaymentStatus) -> Optional[PaymentDb]:
        pass 