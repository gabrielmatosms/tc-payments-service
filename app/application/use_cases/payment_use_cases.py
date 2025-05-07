import uuid
from decimal import Decimal
from typing import List, Optional

from app.domain.entities.payment import Payment, PaymentDb, PaymentStatus, QRCodeRequest
from app.domain.interfaces.payment_repository import PaymentRepository


class PaymentUseCases:
    def __init__(self, repository: PaymentRepository):
        self.repository = repository

    def get_all_payments(self) -> List[PaymentDb]:
        return self.repository.get_all()

    def get_payment_by_id(self, payment_id: int) -> Optional[PaymentDb]:
        return self.repository.get_by_id(payment_id)
    
    def get_payment_by_order_id(self, order_id: int) -> Optional[PaymentDb]:
        return self.repository.get_by_order_id(order_id)

    def create_payment(self, payment: Payment) -> PaymentDb:
        # Ensure payment has pending status
        payment_with_status = Payment(
            order_id=payment.order_id,
            amount=payment.amount,
            status=PaymentStatus.PENDING,
            external_id=payment.external_id
        )
        return self.repository.create(payment_with_status)

    def update_payment_status(self, payment_id: int, status: PaymentStatus) -> Optional[PaymentDb]:
        return self.repository.update_status(payment_id, status)
    
    def generate_qr_code(self, request: QRCodeRequest) -> str:
        """
        Generate a QR code for payment.
        In a real application, this might integrate with a payment gateway.
        """
        # In a real application, this would generate a QR code with payment gateway
        # Here we simulate it by generating a UUID
        external_id = f"PAY-{uuid.uuid4()}"
        
        # Check if there's an existing payment for this order
        existing_payment = self.repository.get_by_order_id(request.order_id)
        
        if existing_payment:
            # Update existing payment with the external ID
            self.repository.update_external_id(existing_payment.id, external_id)
        else:
            # Create a new payment
            self.repository.create(
                Payment(
                    order_id=request.order_id,
                    amount=request.total,
                    status=PaymentStatus.PENDING,
                    external_id=external_id
                )
            )
        
        # Return a simulated QR code (just the UUID in this mock implementation)
        return external_id
    
    def process_payment_callback(self, external_id: str, is_approved: bool) -> Optional[PaymentDb]:
        """
        Process payment gateway callback.
        This would be called when the payment gateway notifies about payment status.
        """
        # Find all payments to look for the external ID (in a real app, this would use an index)
        payments = self.repository.get_all()
        matching_payment = next(
            (p for p in payments if p.external_id == external_id), 
            None
        )
        
        if not matching_payment:
            return None
            
        # Update the payment status
        new_status = PaymentStatus.APPROVED if is_approved else PaymentStatus.DENIED
        return self.repository.update_status(matching_payment.id, new_status) 