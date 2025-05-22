import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.domain.entities.payment import PaymentDb, PaymentStatus
from app.adapters.api.payment_router import get_payment_use_cases
from datetime import datetime
from decimal import Decimal

client = TestClient(app)
API_PREFIX = "/api/v1/payments"

@pytest.fixture
def mock_service_client():
    with patch('app.adapters.api.payment_router.ServiceClient') as MockServiceClient:
        instance = MockServiceClient.return_value
        instance.get_order = AsyncMock(return_value={"id": 1, "status": "PENDING"})
        instance.update_order_payment_status = AsyncMock(return_value=None)
        yield instance

@pytest.fixture
def mock_use_cases():
    with patch('app.adapters.api.payment_router.get_payment_use_cases') as mock_dep:
        mock = MagicMock()
        mock_dep.return_value = mock
        yield mock

def test_get_all_payments(mock_use_cases):
    now = datetime.utcnow()
    mock_use_cases.get_all_payments.return_value = [
        PaymentDb(id=1, order_id=1, amount=Decimal('10.0'), status=PaymentStatus.PENDING, external_id='PAY-1', created_at=now, updated_at=now)
    ]
    response = client.get(f"{API_PREFIX}/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_payment_by_id_found(mock_use_cases):
    now = datetime.utcnow()
    mock_payment = PaymentDb(id=1, order_id=1, amount=Decimal('10.0'), status=PaymentStatus.PENDING, external_id='PAY-1', created_at=now, updated_at=now)
    mock_use_cases.get_payment_by_id.return_value = mock_payment
    
    # Override the dependency
    app.dependency_overrides[get_payment_use_cases] = lambda: mock_use_cases
    
    try:
        response = client.get(f"{API_PREFIX}/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1
    finally:
        # Clean up the dependency override
        app.dependency_overrides.clear()

def test_get_payment_by_id_not_found(mock_use_cases):
    mock_use_cases.get_payment_by_id.return_value = None
    response = client.get(f"{API_PREFIX}/999")
    assert response.status_code == 404

def test_create_payment_order_not_found(mock_use_cases):
    with patch('app.adapters.api.payment_router.ServiceClient') as MockServiceClient:
        instance = MockServiceClient.return_value
        instance.get_order = AsyncMock(return_value=None)
        payload = {"order_id": 999, "amount": 10.0, "status": "Pending", "external_id": "PAY-1"}
        response = client.post(f"{API_PREFIX}/", json=payload)
        assert response.status_code == 400

def test_generate_qr_code_success(mock_use_cases, mock_service_client):
    mock_use_cases.generate_qr_code.return_value = "PAY-QR-123"
    payload = {"description": "desc", "total": 10.0, "order_id": 1}
    response = client.post(f"{API_PREFIX}/qrcode", json=payload)
    assert response.status_code == 200
    assert "qr_code" in response.json()

def test_update_payment_status_success(mock_use_cases, mock_service_client):
    now = datetime.utcnow()
    mock_use_cases.update_payment_status.return_value = PaymentDb(id=1, order_id=1, amount=Decimal('10.0'), status=PaymentStatus.APPROVED, external_id='PAY-1', created_at=now, updated_at=now)
    response = client.patch(f"{API_PREFIX}/1/status/Approved")
    assert response.status_code == 200
    assert response.json()["status"] == "Approved"

def test_update_payment_status_not_found(mock_use_cases, mock_service_client):
    mock_use_cases.update_payment_status.return_value = None
    response = client.patch(f"{API_PREFIX}/999/status/Approved")
    assert response.status_code == 404

def test_payment_webhook_not_found(mock_use_cases, mock_service_client):
    mock_use_cases.process_payment_callback.return_value = None
    response = client.post(f"{API_PREFIX}/webhook", params={"external_id": "PAY-999", "is_approved": True})
    assert response.status_code == 404 