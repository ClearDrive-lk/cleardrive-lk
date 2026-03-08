"""PayHere signature verification helpers (CD-42.2)."""

from __future__ import annotations

import hashlib
import os


class PayHereSignatureVerifier:
    """Verify PayHere webhook signatures."""

    def __init__(self) -> None:
        self.merchant_id = os.getenv("PAYHERE_MERCHANT_ID")
        self.merchant_secret = os.getenv("PAYHERE_MERCHANT_SECRET")
        if not self.merchant_secret:
            raise ValueError("PAYHERE_MERCHANT_SECRET not configured")

    @staticmethod
    def _md5_hash(text: str) -> str:
        return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest().upper()

    def calculate_signature(
        self,
        merchant_id: str,
        order_id: str,
        amount: str,
        currency: str,
        status_code: str,
    ) -> str:
        merchant_secret = self.merchant_secret or ""
        secret_hash = self._md5_hash(merchant_secret)
        payload = f"{merchant_id}{order_id}{amount}{currency}{status_code}{secret_hash}"
        return self._md5_hash(payload)

    def verify_signature(
        self, webhook_data: dict[str, str | None], provided_signature: str
    ) -> bool:
        merchant_id = str(webhook_data.get("merchant_id") or "")
        if self.merchant_id and merchant_id != self.merchant_id:
            return False

        expected_signature = self.calculate_signature(
            merchant_id=merchant_id,
            order_id=str(webhook_data.get("order_id") or ""),
            amount=str(webhook_data.get("payhere_amount") or ""),
            currency=str(webhook_data.get("payhere_currency") or ""),
            status_code=str(webhook_data.get("status_code") or ""),
        )
        return expected_signature.upper() == provided_signature.upper()


payhere_verifier = PayHereSignatureVerifier()
