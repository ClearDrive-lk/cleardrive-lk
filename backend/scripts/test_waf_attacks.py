#!/usr/bin/env python
"""
Basic Cloudflare WAF attack simulation script for CD-93.6.

This script does not configure Cloudflare. It verifies whether a deployed
environment appears to block common malicious request patterns.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def request(method: str, url: str, *, data: dict | None = None) -> tuple[int, str]:
    payload = None
    headers = {
        "User-Agent": "cleardrive-waf-test/1.0",
        "Accept": "application/json,text/plain,*/*",
    }
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read(512).decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read(512).decode("utf-8", errors="replace")
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)


def classify(status_code: int) -> str:
    if status_code in {401, 403, 406, 409, 429}:
        return "blocked_or_challenged"
    if 500 <= status_code <= 599:
        return "origin_error"
    if status_code == 0:
        return "network_error"
    return "passed"


def run_probe(name: str, method: str, url: str, *, data: dict | None = None) -> dict:
    status_code, body = request(method, url, data=data)
    return {
      "name": name,
      "method": method,
      "url": url,
      "status_code": status_code,
      "result": classify(status_code),
      "body_preview": body[:200],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Public HTTPS base URL behind Cloudflare")
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.5,
        help="Delay between requests to avoid collapsing all probes into one rate-limit event",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    probes = [
        (
            "baseline_homepage",
            "GET",
            f"{base_url}/",
            None,
        ),
        (
            "sqli_query_probe",
            "GET",
            f"{base_url}/api/v1/vehicles?search="
            + urllib.parse.quote("' OR 1=1 UNION SELECT password FROM users --"),
            None,
        ),
        (
            "xss_query_probe",
            "GET",
            f"{base_url}/api/v1/vehicles?search="
            + urllib.parse.quote("<script>alert('xss')</script>"),
            None,
        ),
        (
            "path_traversal_probe",
            "GET",
            f"{base_url}/../../etc/passwd",
            None,
        ),
        (
            "sqli_body_probe",
            "POST",
            f"{base_url}/api/v1/auth/request-otp",
            {"email": "test@example.com' OR '1'='1"},
        ),
    ]

    results = []
    print("=" * 72)
    print("CLOUDFLARE WAF ATTACK SIMULATION")
    print("=" * 72)
    print(f"Base URL: {base_url}")

    for name, method, url, data in probes:
        result = run_probe(name, method, url, data=data)
        results.append(result)
        print(
            f"[{result['result']}] {name} -> {result['status_code']} {method} {url}"
        )
        time.sleep(args.sleep_seconds)

    print("\nRate limit probe against /api/v1/auth/request-otp")
    rate_limit_hits = []
    for index in range(12):
        result = run_probe(
            f"rate_limit_probe_{index + 1}",
            "POST",
            f"{base_url}/api/v1/auth/request-otp",
            data={"email": f"probe{index}@example.com"},
        )
        rate_limit_hits.append(result)
        print(
            f"  {index + 1:02d}. {result['status_code']} -> {result['result']}"
        )
        time.sleep(0.2)

    blocked_count = sum(1 for item in results if item["result"] == "blocked_or_challenged")
    rate_limited = any(item["status_code"] == 429 for item in rate_limit_hits)

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Malicious probes blocked/challenged: {blocked_count}/{len(results) - 1}")
    print(f"Rate limiting observed: {'yes' if rate_limited else 'no'}")

    print("\nJSON:")
    print(
        json.dumps(
            {
                "base_url": base_url,
                "probe_results": results,
                "rate_limit_results": rate_limit_hits,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
