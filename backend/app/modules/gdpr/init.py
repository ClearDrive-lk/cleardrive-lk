# backend/app/modules/gdpr/__init__.py

from .models import GDPRDeletion, GDPRRequest

__all__ = ["GDPRRequest", "GDPRDeletion"]
