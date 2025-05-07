from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.http.service_client import ServiceClient
from app.adapters.models.sql.session import get_db
from app.adapters.repositories import RepositoryType, get_payment_repository
from app.application.use_cases.payment_use_cases import PaymentUseCases
from app.domain.entities.payment import Payment, PaymentDb, PaymentStatus, QRCodeRequest

router = APIRouter()

# Helper function to get payment use cases with SQL repository
def get_payment_use_cases(db: Session = Depends(get_db)) -> PaymentUseCases:
    repository = get_payment_repository(RepositoryType.SQL, db)
    return PaymentUseCases(repository)


@router.get("/", response_model=List[PaymentDb])
def get_all_payments(use_cases: PaymentUseCases = Depends(get_payment_use_cases)):
    return use_cases.get_all_payments()


@router.get("/{payment_id}", response_model=PaymentDb)
def get_payment(payment_id: int, use_cases: PaymentUseCases = Depends(get_payment_use_cases)):
    payment = use_cases.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found"
        )
    return payment


@router.get("/order/{order_id}", response_model=PaymentDb)
def get_payment_by_order(order_id: int, use_cases: PaymentUseCases = Depends(get_payment_use_cases)):
    payment = use_cases.get_payment_by_order_id(order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment for order ID {order_id} not found"
        )
    return payment


@router.post("/", response_model=PaymentDb, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: Payment, use_cases: PaymentUseCases = Depends(get_payment_use_cases)):
    # Validate that the order exists
    service_client = ServiceClient()
    order = await service_client.get_order(payment.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order with ID {payment.order_id} not found"
        )
    
    # Check if payment already exists for this order
    existing = use_cases.get_payment_by_order_id(payment.order_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment for order ID {payment.order_id} already exists"
        )
    
    return use_cases.create_payment(payment)


@router.post("/qrcode", response_model=Dict[str, str])
async def generate_qr_code(
    request: QRCodeRequest, 
    use_cases: PaymentUseCases = Depends(get_payment_use_cases)
):
    # Validate that the order exists
    service_client = ServiceClient()
    order = await service_client.get_order(request.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order with ID {request.order_id} not found"
        )
    
    # Generate QR code
    qr_code = use_cases.generate_qr_code(request)
    return {"qr_code": qr_code}


@router.patch("/{payment_id}/status/{status_name}", response_model=PaymentDb)
async def update_payment_status(
    payment_id: int, 
    status_name: PaymentStatus, 
    use_cases: PaymentUseCases = Depends(get_payment_use_cases)
):
    updated_payment = use_cases.update_payment_status(payment_id, status_name)
    if not updated_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found"
        )
    
    # Notify the orders service about the payment status update
    service_client = ServiceClient()
    await service_client.update_order_payment_status(
        updated_payment.order_id, 
        updated_payment.status
    )
    
    return updated_payment


@router.post("/webhook", response_model=Dict[str, str])
async def payment_webhook(
    external_id: str, 
    is_approved: bool, 
    use_cases: PaymentUseCases = Depends(get_payment_use_cases)
):
    """
    Simulate a payment gateway webhook callback.
    This endpoint would receive notifications from payment gateways.
    """
    payment = use_cases.process_payment_callback(external_id, is_approved)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with external ID {external_id} not found"
        )
    
    # Notify the orders service about the payment status update
    service_client = ServiceClient()
    await service_client.update_order_payment_status(
        payment.order_id, 
        payment.status
    )
    
    return {"status": "processed", "payment_id": str(payment.id)} 