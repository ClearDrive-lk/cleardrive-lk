from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import User
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory
from app.modules.shipping.models import ShipmentDetails, ShipmentStatus
from app.modules.shipping.schemas import ExporterAssignment, ShippingDetailsResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/shipping", tags=["admin-shipping"])


# ===================================================================
# ENDPOINT: ASSIGN EXPORTER TO ORDER (CD-70.1)
# ===================================================================


@router.post("/{order_id}/assign", response_model=ShippingDetailsResponse)
async def assign_exporter_to_order(
    order_id: str,
    assignment: ExporterAssignment,
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """
    Assign exporter to a paid order.

    **Story**: CD-70 - Exporter Assignment

    **Permissions**: MANAGE_ORDERS (Admin only)

    **Prerequisites:**
    - Order must exist
    - Order status must be LC_APPROVED
    - Exporter user must have EXPORTER role
    - Order must not already have exporter assigned

    **Process:**
    1. Verify order exists and status is LC_APPROVED
    2. Verify exporter exists and has EXPORTER role
    3. Create shipment_details record (CD-70.3)
    4. Update order status to ASSIGNED_TO_EXPORTER (CD-70.2)
    5. Create order status history entry
    6. Send email to exporter (CD-70.4) - TODO

    **Returns:**
    - Created shipment details
    - Order status updated
    - Exporter assigned
    """

    print(f"\n{'=' * 70}")
    print("📦 EXPORTER ASSIGNMENT STARTED")
    print(f"   Admin: {current_user.email}")
    print(f"   Order ID: {order_id}")
    print(f"{'=' * 70}\n")

    # ===============================================================
    # STEP 1: VERIFY ORDER EXISTS AND STATUS
    # ===============================================================
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found"
        )

    # Check order status
    if order.status != OrderStatus.LC_APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order must be in LC_APPROVED status. Current: {order.status}",
        )

    print("✅ STEP 1: Order Verified")
    print(f"   Order ID: {order.id}")
    print(f"   Status: {order.status.value}")
    print(f"   Customer: {order.user.email}")
    print(f"   Vehicle: {order.vehicle.make} {order.vehicle.model}")

    # ===============================================================
    # STEP 2: CHECK IF ALREADY ASSIGNED
    # ===============================================================
    existing_shipment = (
        db.query(ShipmentDetails).filter(ShipmentDetails.order_id == order_id).first()
    )

    if existing_shipment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order already has an exporter assigned: {existing_shipment.exporter_id}",
        )

    print("\n✅ STEP 2: No Existing Assignment")

    # ===============================================================
    # STEP 3: VERIFY EXPORTER USER
    # ===============================================================
    exporter = db.query(User).filter(User.id == assignment.exporter_id).first()

    if not exporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exporter {assignment.exporter_id} not found",
        )

    if exporter.role != "EXPORTER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {exporter.email} is not an exporter. Role: {exporter.role}",
        )

    print("\n✅ STEP 3: Exporter Verified")
    print(f"   Exporter ID: {exporter.id}")
    print(f"   Exporter Email: {exporter.email}")
    print(f"   Exporter Role: {exporter.role}")

    # ===============================================================
    # STEP 4: CREATE SHIPMENT DETAILS (CD-70.3)
    # ===============================================================
    shipment = ShipmentDetails(order_id=order.id, exporter_id=exporter.id)

    db.add(shipment)
    db.flush()  # Get shipment.id without committing

    print("\n✅ STEP 4: Shipment Details Created")
    print(f"   Shipment ID: {shipment.id}")

    # ===============================================================
    # STEP 5: UPDATE ORDER STATUS (CD-70.2)
    # ===============================================================
    old_status = order.status
    order.status = OrderStatus.ASSIGNED_TO_EXPORTER

    print("\n✅ STEP 5: Order Status Updated")
    print(f"   Old Status: {old_status.value}")
    print(f"   New Status: {order.status.value}")

    # ===============================================================
    # STEP 6: CREATE STATUS HISTORY ENTRY
    # ===============================================================
    history = OrderStatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status=OrderStatus.ASSIGNED_TO_EXPORTER,
        changed_by=current_user.id,
        notes=f"Assigned to exporter: {exporter.email}",
    )

    db.add(history)

    print("\n✅ STEP 6: Status History Created")

    # Commit all changes
    db.commit()
    db.refresh(shipment)

    print(f"\n{'=' * 70}")
    print("🎉 EXPORTER ASSIGNMENT COMPLETED")
    print(f"   Order: {order.id}")
    print(f"   Exporter: {exporter.email}")
    print(f"   Status: {order.status.value}")
    print(f"{'=' * 70}\n")

    # ===============================================================
    # STEP 7: SEND EMAIL TO EXPORTER (CD-70.4)
    # ===============================================================
    # TODO: Implement email notification
    # await send_exporter_assignment_email(
    #     to=exporter.email,
    #     order_id=order.id,
    #     vehicle=f"{order.vehicle.make} {order.vehicle.model}",
    #     customer=order.user.name
    # )

    print(f"📧 TODO: Send email to {exporter.email}")

    return shipment


# ===================================================================
# ENDPOINT: GET ALL SHIPMENTS (FOR ADMIN)
# ===================================================================


@router.get("/all")
async def get_all_shipments(
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """
    Get all shipments (admin view).

    **Permissions**: Admin only

    **Returns:**
    - List of all shipments
    - Grouped by status
    """

    all_shipments = db.query(ShipmentDetails).all()

    # Group by status
    awaiting_details = []
    awaiting_approval = []
    approved = []

    for shipment in all_shipments:
        if not shipment.vessel_name:
            awaiting_details.append(shipment)
        elif shipment.status == ShipmentStatus.AWAITING_ADMIN_APPROVAL:
            awaiting_approval.append(shipment)
        elif shipment.status == ShipmentStatus.CONFIRMED_SHIPPED:
            approved.append(shipment)
        else:
            awaiting_details.append(shipment)

    return {
        "total": len(all_shipments),
        "awaiting_details": len(awaiting_details),
        "awaiting_approval": len(awaiting_approval),
        "approved": len(approved),
        "shipments": all_shipments,
    }


# ===================================================================
# ENDPOINT: GET SHIPMENT DETAILS
# ===================================================================


@router.get("/{shipment_id}", response_model=ShippingDetailsResponse)
async def get_shipment_details(
    shipment_id: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """
    Get detailed shipment information.

    **Permissions**: Admin only
    """

    shipment = db.query(ShipmentDetails).filter(ShipmentDetails.id == shipment_id).first()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment {shipment_id} not found"
        )

    return shipment
