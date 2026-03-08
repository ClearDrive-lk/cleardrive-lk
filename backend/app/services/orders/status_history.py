# backend/app/services/orders/status_history.py

"""
Order status history service.
Author: Parindra Gallage
Story: CD-32.3 - Track status changes
"""

from sqlalchemy.orm import Session
from typing import Optional, Union
from uuid import UUID

from app.modules.orders.models import Order, OrderStatusHistory, OrderStatus
from app.modules.auth.models import User


class OrderStatusHistoryService:
    """
    Service for managing order status history.

    Story: CD-32.1, CD-32.3
    """

    @staticmethod
    def create_history_entry(
        db: Session,
        order: Order,
        from_status: Optional[OrderStatus],
        to_status: OrderStatus,
        changed_by: User,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrderStatusHistory:
        """
        Create status history entry.

        Args:
            db: Database session
            order: Order object
            from_status: Previous status (None for initial)
            to_status: New status
            changed_by: User who made the change
            notes: Optional notes/reason
            ip_address: User's IP address
            user_agent: User's browser/agent

        Returns:
            Created OrderStatusHistory record
        """

        history = OrderStatusHistory(
            order_id=order.id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            changed_by=changed_by.id,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(history)

        print("📝 Status History Created:")
        print(f"   Order: {order.id}")
        print(f"   Change: {from_status.value if from_status else 'None'} -> {to_status.value}")
        print(f"   By: {changed_by.email}")

        return history

    @staticmethod
    def get_order_timeline(db: Session, order_id: Union[UUID, str]) -> list[OrderStatusHistory]:
        """
        Get complete order timeline.

        Args:
            db: Database session
            order_id: Order UUID

        Returns:
            List of status history records (chronological)
        """

        history = (
            db.query(OrderStatusHistory)
            .filter(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.created_at.asc())
            .all()
        )

        return history


# Global instance
status_history_service = OrderStatusHistoryService()
