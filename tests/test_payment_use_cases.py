import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from app.application.use_cases.payment_use_cases import PaymentUseCases
from app.domain.entities.payment import Payment, PaymentDb, PaymentStatus, QRCodeRequest
from app.domain.interfaces.payment_repository import PaymentRepository


class TestPaymentUseCases:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=PaymentRepository)
        self.use_cases = PaymentUseCases(self.mock_repo)

    def test_get_all_payments(self):
        now = datetime.utcnow()
        payments = [
            PaymentDb(
                id=1, order_id=1, amount=Decimal("25.98"),
                status=PaymentStatus.PENDING, external_id="PAY-123",
                created_at=now, updated_at=now
            ),
            PaymentDb(
                id=2, order_id=2, amount=Decimal("15.99"),
                status=PaymentStatus.APPROVED, external_id="PAY-456",
                created_at=now, updated_at=now
            )
        ]
        self.mock_repo.get_all.return_value = payments

        result = self.use_cases.get_all_payments()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        self.mock_repo.get_all.assert_called_once()

    def test_get_payment_by_id(self):
        now = datetime.utcnow()
        payment = PaymentDb(
            id=1, order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.PENDING, external_id="PAY-123",
            created_at=now, updated_at=now
        )
        self.mock_repo.get_by_id.return_value = payment

        result = self.use_cases.get_payment_by_id(1)

        assert result.id == 1
        assert result.order_id == 1
        assert result.status == PaymentStatus.PENDING
        self.mock_repo.get_by_id.assert_called_once_with(1)
        
    def test_get_payment_by_order_id(self):
        now = datetime.utcnow()
        order_id = 1
        payment = PaymentDb(
            id=1, order_id=order_id, amount=Decimal("25.98"),
            status=PaymentStatus.PENDING, external_id="PAY-123",
            created_at=now, updated_at=now
        )
        self.mock_repo.get_by_order_id.return_value = payment

        result = self.use_cases.get_payment_by_order_id(order_id)

        assert result.id == 1
        assert result.order_id == order_id
        self.mock_repo.get_by_order_id.assert_called_once_with(order_id)
        
    def test_create_payment(self):
        now = datetime.utcnow()
        payment = Payment(
            order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.APPROVED,  # Should be overridden to PENDING
            external_id="PAY-123"
        )
        
        created_payment = PaymentDb(
            id=1, order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.PENDING,  # Should always be created as PENDING
            external_id="PAY-123", created_at=now, updated_at=now
        )
        
        self.mock_repo.create.return_value = created_payment

        result = self.use_cases.create_payment(payment)

        assert result.id == 1
        assert result.status == PaymentStatus.PENDING
        
        create_call_args = self.mock_repo.create.call_args[0][0]
        assert create_call_args.status == PaymentStatus.PENDING
        
    def test_update_payment_status(self):
        now = datetime.utcnow()
        payment_id = 1
        new_status = PaymentStatus.APPROVED
        
        updated_payment = PaymentDb(
            id=payment_id, order_id=1, amount=Decimal("25.98"),
            status=new_status, external_id="PAY-123",
            created_at=now, updated_at=now
        )
        
        self.mock_repo.update_status.return_value = updated_payment

        result = self.use_cases.update_payment_status(payment_id, new_status)

        assert result.status == new_status
        self.mock_repo.update_status.assert_called_once_with(payment_id, new_status)
        
    @patch('uuid.uuid4')
    def test_generate_qr_code_new_payment(self, mock_uuid4):
        mock_uuid4.return_value = "test-uuid-4321"
        now = datetime.utcnow()
        request = QRCodeRequest(
            description="Test payment",
            total=Decimal("25.98"),
            order_id=1
        )
        
        self.mock_repo.get_by_order_id.return_value = None
        
        created_payment = PaymentDb(
            id=1, order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.PENDING, external_id="PAY-test-uuid-4321",
            created_at=now, updated_at=now
        )
        
        self.mock_repo.create.return_value = created_payment

        result = self.use_cases.generate_qr_code(request)

        assert result == "PAY-test-uuid-4321"
        self.mock_repo.get_by_order_id.assert_called_once_with(1)
        self.mock_repo.create.assert_called_once()
        
    @patch('uuid.uuid4')
    def test_generate_qr_code_existing_payment(self, mock_uuid4):
        mock_uuid4.return_value = "test-uuid-5678"
        now = datetime.utcnow()
        request = QRCodeRequest(
            description="Test payment",
            total=Decimal("25.98"),
            order_id=1
        )
        
        existing_payment = PaymentDb(
            id=1, order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.PENDING, external_id="PAY-old-id",
            created_at=now, updated_at=now
        )
        
        self.mock_repo.get_by_order_id.return_value = existing_payment
        
        result = self.use_cases.generate_qr_code(request)

        assert result == "PAY-test-uuid-5678"
        self.mock_repo.get_by_order_id.assert_called_once_with(1)
        self.mock_repo.update_external_id.assert_called_once_with(1, "PAY-test-uuid-5678")
        self.mock_repo.create.assert_not_called()
        
    def test_process_payment_callback_approved(self):
        now = datetime.utcnow()
        external_id = "PAY-test-123"
        is_approved = True
        
        payments = [
            PaymentDb(
                id=1, order_id=1, amount=Decimal("25.98"),
                status=PaymentStatus.PENDING, external_id=external_id,
                created_at=now, updated_at=now
            ),
            PaymentDb(
                id=2, order_id=2, amount=Decimal("15.99"),
                status=PaymentStatus.PENDING, external_id="PAY-other",
                created_at=now, updated_at=now
            )
        ]
        
        updated_payment = PaymentDb(
            id=1, order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.APPROVED, external_id=external_id,
            created_at=now, updated_at=now
        )
        
        self.mock_repo.get_all.return_value = payments
        self.mock_repo.update_status.return_value = updated_payment

        result = self.use_cases.process_payment_callback(external_id, is_approved)

        assert result.status == PaymentStatus.APPROVED
        self.mock_repo.update_status.assert_called_once_with(1, PaymentStatus.APPROVED)
        
    def test_process_payment_callback_denied(self):
        now = datetime.utcnow()
        external_id = "PAY-test-123"
        is_approved = False
        
        payments = [
            PaymentDb(
                id=1, order_id=1, amount=Decimal("25.98"),
                status=PaymentStatus.PENDING, external_id=external_id,
                created_at=now, updated_at=now
            )
        ]
        
        updated_payment = PaymentDb(
            id=1, order_id=1, amount=Decimal("25.98"),
            status=PaymentStatus.DENIED, external_id=external_id,
            created_at=now, updated_at=now
        )
        
        self.mock_repo.get_all.return_value = payments
        self.mock_repo.update_status.return_value = updated_payment

        result = self.use_cases.process_payment_callback(external_id, is_approved)

        assert result.status == PaymentStatus.DENIED
        self.mock_repo.update_status.assert_called_once_with(1, PaymentStatus.DENIED)
        
    def test_process_payment_callback_not_found(self):
        external_id = "PAY-nonexistent"
        is_approved = True
        
        self.mock_repo.get_all.return_value = []

        result = self.use_cases.process_payment_callback(external_id, is_approved)

        assert result is None
        self.mock_repo.update_status.assert_not_called() 