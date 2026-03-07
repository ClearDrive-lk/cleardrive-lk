"""
CD-41.7 load test for payment idempotency.

Usage:
    python scripts/load_test_payment_idempotency.py \
      --api-url http://localhost:8000 \
      --token <jwt> \
      --order-id <uuid> \
      --requests 100 \
      --workers 25
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import uuid
from collections import Counter
from typing import Any

import httpx


def _call_initiate(api_url: str, token: str, order_id: str, timeout: float) -> tuple[int, dict[str, Any]]:
    idem_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Idempotency-Key": idem_key,
    }
    payload = {"order_id": order_id}

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{api_url}/api/v1/payments/initiate", headers=headers, json=payload)
        body: dict[str, Any]
        try:
            body = response.json() if response.text else {}
        except Exception:
            body = {"raw": response.text[:200]}
        return response.status_code, body
    except Exception as exc:
        return 0, {"error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Load test payment idempotency flow.")
    parser.add_argument("--api-url", required=True, help="API base URL, e.g. http://localhost:8000")
    parser.add_argument("--token", required=True, help="Bearer access token")
    parser.add_argument("--order-id", required=True, help="Order UUID")
    parser.add_argument("--requests", type=int, default=100, help="Total initiate requests")
    parser.add_argument("--workers", type=int, default=25, help="Thread pool size")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout seconds")
    args = parser.parse_args()

    results: list[tuple[int, dict[str, Any]]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                _call_initiate,
                args.api_url.rstrip("/"),
                args.token,
                args.order_id,
                args.timeout,
            )
            for _ in range(args.requests)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    status_counts = Counter(status for status, _ in results)
    payment_ids = {
        body.get("payment_id")
        for _, body in results
        if isinstance(body, dict) and body.get("payment_id") is not None
    }

    summary = {
        "total_requests": args.requests,
        "workers": args.workers,
        "status_counts": dict(status_counts),
        "unique_payment_ids_returned": len(payment_ids),
        "payment_ids": sorted(str(pid) for pid in payment_ids),
        "sample_errors": [body for status, body in results if status == 0][:5],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
