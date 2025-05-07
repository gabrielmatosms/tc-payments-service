from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.domain.entities.payment import PaymentStatus


class ServiceClient:
    def __init__(self):
        self.orders_url = settings.ORDERS_SERVICE_URL
    
    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order information from the orders service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.orders_url}/api/v1/orders/{order_id}")
                if response.status_code == 200:
                    return response.json()
                return None
            except httpx.RequestError:
                return None
    
    async def update_order_payment_status(self, order_id: int, payment_status: PaymentStatus) -> bool:
        """Update payment status in the orders service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.orders_url}/api/v1/orders/{order_id}/payment-status/{payment_status}"
                )
                return response.status_code == 200
            except httpx.RequestError:
                return False 