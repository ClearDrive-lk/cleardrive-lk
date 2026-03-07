# backend/app/modules/orders/state_machine.py

"""
Order state machine - defines valid state transitions and prerequisites.
Author: Tharin
Story: CD-31 - Order State Machine
"""

from typing import Dict, List, Optional, Callable
from app.modules.orders.models import OrderStatus, PaymentStatus


# ===================================================================
# VALID STATE TRANSITIONS (CD-31.2)
# ===================================================================

# Maps current state → list of allowed next states
VALID_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
    # From CREATED
    OrderStatus.CREATED: [
        OrderStatus.PAYMENT_CONFIRMED,
        OrderStatus.CANCELLED,
    ],
    
    # From PAYMENT_CONFIRMED
    OrderStatus.PAYMENT_CONFIRMED: [
        OrderStatus.ASSIGNED_TO_EXPORTER,
        OrderStatus.CANCELLED,
    ],
    
    # From ASSIGNED_TO_EXPORTER
    OrderStatus.ASSIGNED_TO_EXPORTER: [
        OrderStatus.AWAITING_SHIPMENT_CONFIRMATION,
        OrderStatus.CANCELLED,
    ],
    
    # From AWAITING_SHIPMENT_CONFIRMATION
    OrderStatus.AWAITING_SHIPMENT_CONFIRMATION: [
        OrderStatus.SHIPMENT_DOCS_UPLOADED,
        OrderStatus.CANCELLED,
    ],
    
    # From SHIPMENT_DOCS_UPLOADED
    OrderStatus.SHIPMENT_DOCS_UPLOADED: [
        OrderStatus.SHIPPED,
        OrderStatus.CANCELLED,
    ],
    
    # From SHIPPED
    OrderStatus.SHIPPED: [
        OrderStatus.IN_TRANSIT,
        OrderStatus.CANCELLED,  # Rare, but possible if ship issue
    ],
    
    # From IN_TRANSIT
    OrderStatus.IN_TRANSIT: [
        OrderStatus.ARRIVED_AT_PORT,
    ],
    
    # From ARRIVED_AT_PORT
    OrderStatus.ARRIVED_AT_PORT: [
        OrderStatus.CUSTOMS_CLEARANCE,
    ],
    
    # From CUSTOMS_CLEARANCE
    OrderStatus.CUSTOMS_CLEARANCE: [
        OrderStatus.DELIVERED,
    ],
    
    # From DELIVERED - Terminal state (no transitions)
    OrderStatus.DELIVERED: [],
    
    # From CANCELLED - Terminal state (no transitions)
    OrderStatus.CANCELLED: [],
}


# ===================================================================
# STATE PREREQUISITES (CD-31.4)
# ===================================================================

# Each state requires certain conditions to be met
# These are checked before allowing transition

def check_payment_confirmed_prerequisites(order) -> tuple[bool, str]:
    """Prerequisites for PAYMENT_CONFIRMED state."""
    # Check: Payment must be completed
    if order.payment_status != PaymentStatus.COMPLETED:
        return False, "Payment must be completed"
    return True, ""


def check_assigned_to_exporter_prerequisites(order, db) -> tuple[bool, str]:
    """Prerequisites for ASSIGNED_TO_EXPORTER state."""
    # Check: ShipmentDetails must exist with exporter assigned
    from app.modules.shipping.models import ShipmentDetails
    
    shipment = db.query(ShipmentDetails).filter(
        ShipmentDetails.order_id == order.id
    ).first()
    
    if not shipment:
        return False, "No shipment details found"
    
    if not shipment.assigned_exporter_id:
        return False, "No exporter assigned"
    
    return True, ""


def check_awaiting_shipment_prerequisites(order, db) -> tuple[bool, str]:
    """Prerequisites for AWAITING_SHIPMENT_CONFIRMATION state."""
    # Check: Exporter must have submitted vessel/port details
    from app.modules.shipping.models import ShipmentDetails
    
    shipment = db.query(ShipmentDetails).filter(
        ShipmentDetails.order_id == order.id
    ).first()
    
    if not shipment:
        return False, "No shipment details"
    
    if not shipment.vessel_name or not shipment.departure_port:
        return False, "Vessel and port details not submitted"
    
    return True, ""


def check_docs_uploaded_prerequisites(order, db) -> tuple[bool, str]:
    """Prerequisites for SHIPMENT_DOCS_UPLOADED state."""
    # Check: All required documents must be uploaded
    from app.modules.shipping.models import ShipmentDetails, ShippingDocument, DocumentType
    
    shipment = db.query(ShipmentDetails).filter(
        ShipmentDetails.order_id == order.id
    ).first()
    
    if not shipment:
        return False, "No shipment details"
    
    # Get uploaded documents
    uploaded_docs = db.query(ShippingDocument).filter(
        ShippingDocument.shipment_id == shipment.id
    ).all()
    
    uploaded_types = {doc.document_type for doc in uploaded_docs}
    
    # Required documents
    required_types = {
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.PACKING_LIST,
    }
    
    missing_types = required_types - uploaded_types
    
    if missing_types:
        missing_names = [t.value for t in missing_types]
        return False, f"Missing documents: {', '.join(missing_names)}"
    
    return True, ""


def check_shipped_prerequisites(order, db) -> tuple[bool, str]:
    """Prerequisites for SHIPPED state."""
    # Check: Shipment must be approved by admin
    from app.modules.shipping.models import ShipmentDetails
    
    shipment = db.query(ShipmentDetails).filter(
        ShipmentDetails.order_id == order.id
    ).first()
    
    if not shipment:
        return False, "No shipment details"
    
    if not shipment.approved:
        return False, "Shipment not approved by admin"
    
    return True, ""


# Map: state → prerequisite check function
STATE_PREREQUISITES: Dict[OrderStatus, Optional[Callable]] = {
    OrderStatus.CREATED: None,
    OrderStatus.PAYMENT_CONFIRMED: check_payment_confirmed_prerequisites,
    OrderStatus.ASSIGNED_TO_EXPORTER: check_assigned_to_exporter_prerequisites,
    OrderStatus.AWAITING_SHIPMENT_CONFIRMATION: check_awaiting_shipment_prerequisites,
    OrderStatus.SHIPMENT_DOCS_UPLOADED: check_docs_uploaded_prerequisites,
    OrderStatus.SHIPPED: check_shipped_prerequisites,
    OrderStatus.IN_TRANSIT: None,
    OrderStatus.ARRIVED_AT_PORT: None,
    OrderStatus.CUSTOMS_CLEARANCE: None,
    OrderStatus.DELIVERED: None,
    OrderStatus.CANCELLED: None,
}


# ===================================================================
# STATE TRANSITION VALIDATION (CD-31.3)
# ===================================================================

def is_valid_transition(
    current_status: OrderStatus,
    new_status: OrderStatus
) -> bool:
    """
    Check if transition from current_status to new_status is valid.
    
    Args:
        current_status: Current order status
        new_status: Desired new status
        
    Returns:
        True if transition is allowed, False otherwise
    """
    
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    return new_status in allowed_transitions


def validate_state_transition(
    order,
    new_status: OrderStatus,
    db
) -> tuple[bool, str]:
    """
    Validate if order can transition to new status.
    
    Checks:
    1. Is the transition valid? (state machine rules)
    2. Are prerequisites met? (business logic)
    
    Args:
        order: Order object
        new_status: Desired new status
        db: Database session
        
    Returns:
        (is_valid, error_message)
        - (True, "") if valid
        - (False, "reason") if invalid
    """
    
    current_status = order.status
    
    # ===============================================================
    # CHECK 1: Is transition allowed by state machine?
    # ===============================================================
    if not is_valid_transition(current_status, new_status):
        allowed = VALID_TRANSITIONS.get(current_status, [])
        allowed_names = [s.value for s in allowed]
        
        return False, (
            f"Invalid transition: {current_status.value} → {new_status.value}. "
            f"Allowed transitions: {', '.join(allowed_names)}"
        )
    
    # ===============================================================
    # CHECK 2: Are prerequisites met?
    # ===============================================================
    prerequisite_check = STATE_PREREQUISITES.get(new_status)
    
    if prerequisite_check:
        # Call the prerequisite check function
        # Some functions need db, some don't
        import inspect
        sig = inspect.signature(prerequisite_check)
        
        if len(sig.parameters) == 1:
            # Function only needs order
            is_valid, error_msg = prerequisite_check(order)
        else:
            # Function needs order and db
            is_valid, error_msg = prerequisite_check(order, db)
        
        if not is_valid:
            return False, f"Prerequisites not met: {error_msg}"
    
    return True, ""


# ===================================================================
# HELPER: GET ALLOWED NEXT STATES
# ===================================================================

def get_allowed_next_states(current_status: OrderStatus) -> List[OrderStatus]:
    """Get list of allowed next states from current state."""
    return VALID_TRANSITIONS.get(current_status, [])
