# app/models/__init__.py
import app.modules  # 👈 force model registration
from app.core.database import SessionLocal, engine, Base


# Auth
from app.modules.auth.models import User

# Orders
from app.modules.orders.models import Order

# Payments
from app.modules.payments.models import Payment

# KYC
from app.modules.kyc.models import KYCDocument

# Vehicles
from app.modules.vehicles.models import Vehicle

# Shipping
from app.modules.shipping.models import ShipmentDetails

# Security
from app.modules.security.models import FileIntegrity

# GDPR
from app.modules.gdpr.models import GDPRRequest

# VEHICLES
from app.modules.vehicles.models import Vehicle
