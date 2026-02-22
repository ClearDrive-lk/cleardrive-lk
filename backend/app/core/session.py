"""
Session metadata extraction and management.

This module provides utilities for:
- Parsing user agent strings to extract device information
- Getting geographic location from IP addresses (optional)
- Extracting complete session metadata
- Detecting suspicious session activity
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests  # type: ignore
from user_agents import parse as parse_user_agent

logger = logging.getLogger(__name__)


def parse_device_info(user_agent: str) -> Dict[str, str]:
    """
    Parse user agent string to extract device information.

    Uses the user-agents library to parse browser strings and
    extract structured device information.

    Args:
        user_agent: User agent string from HTTP request

    Returns:
        Dictionary containing:
        {
            "device_type": "Mobile" | "Tablet" | "PC" | "Bot" | "Unknown",
            "device_name": "iPhone 14 Pro" | "Samsung Galaxy S23" | "Desktop",
            "browser": "Chrome 120.0" | "Safari 17.2",
            "os": "iOS 17.2" | "Android 14" | "Windows 11"
        }

    Examples:
        # Mobile
        >>> parse_device_info("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0...")
        {
            "device_type": "Mobile",
            "device_name": "Apple iPhone",
            "browser": "Safari 17.2",
            "os": "iOS 17.0"
        }

        # Desktop
        >>> parse_device_info("Mozilla/5.0 (Windows NT 10.0; Win64; x64)...")
        {
            "device_type": "PC",
            "device_name": "Unknown Device",
            "browser": "Chrome 120.0",
            "os": "Windows 10"
        }
    """
    # Parse user agent
    ua = parse_user_agent(user_agent)

    # Determine device type
    device_type = "Unknown"
    if ua.is_mobile:
        device_type = "Mobile"
    elif ua.is_tablet:
        device_type = "Tablet"
    elif ua.is_pc:
        device_type = "PC"
    elif ua.is_bot:
        device_type = "Bot"

    # Get device name
    device_name = "Unknown Device"
    if ua.device.brand and ua.device.model:
        device_name = f"{ua.device.brand} {ua.device.model}"
    elif ua.device.family and ua.device.family != "Other":
        device_name = ua.device.family

    # Get browser and version
    browser = f"{ua.browser.family} {ua.browser.version_string}"

    # Get OS and version
    os = f"{ua.os.family} {ua.os.version_string}"

    return {
        "device_type": device_type,
        "device_name": device_name,
        "browser": browser,
        "os": os,
    }


async def get_location_from_ip(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Get geographic location from IP address using GeoIP service.

    Uses ipapi.co free tier (1000 requests/day).
    Can be disabled via GEOIP_ENABLED=false in config.

    Args:
        ip_address: IPv4 or IPv6 address

    Returns:
        Dictionary containing location data, or None if:
        - GeoIP is disabled
        - IP is localhost
        - API request fails

        {
            "country": "United States",
            "country_code": "US",
            "region": "California",
            "city": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }

    Examples:
        >>> await get_location_from_ip("8.8.8.8")
        {"country": "United States", "city": "Mountain View", ...}

        >>> await get_location_from_ip("127.0.0.1")
        {"country": "Local", "city": "Localhost", ...}

    Privacy Note:
        Location tracking is OPTIONAL and can be disabled.
        User consent should be obtained per GDPR requirements.
    """
    from app.core.config import settings

    # Skip if GeoIP disabled
    if not settings.GEOIP_ENABLED:
        logger.debug("GeoIP disabled, skipping location lookup")
        return None

    # Handle localhost
    if ip_address in ["127.0.0.1", "localhost", "::1"]:
        return {
            "country": "Local",
            "country_code": "LC",
            "region": "Local",
            "city": "Localhost",
            "latitude": 0.0,
            "longitude": 0.0,
        }

    try:
        # Use ipapi.co (free tier: 1000 requests/day)
        # Alternative: ip-api.com (45 requests/minute free)
        url = f"https://ipapi.co/{ip_address}/json/"

        response = requests.get(url, timeout=2)

        if response.status_code == 200:
            data = response.json()

            # Check for error response
            if "error" in data:
                logger.warning(f"GeoIP API error: {data.get('reason')}")
                return None

            return {
                "country": data.get("country_name"),
                "country_code": data.get("country_code"),
                "region": data.get("region"),
                "city": data.get("city"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            }
        else:
            logger.warning(f"GeoIP API request failed: {response.status_code}")
            return None

    except requests.Timeout:
        logger.warning("GeoIP API timeout")
        return None

    except Exception as e:
        logger.warning(f"Failed to get location for IP {ip_address}: {str(e)}")
        return None


async def extract_session_metadata(
    ip_address: str, user_agent: str, include_location: bool = True
) -> Dict[str, Any]:
    """
    Extract complete session metadata from HTTP request.

    Combines IP address, user agent parsing, and optional
    GeoIP lookup to create comprehensive session metadata.

    Args:
        ip_address: Client IP from request.client.host
        user_agent: User agent from request.headers["user-agent"]
        include_location: Whether to fetch GeoIP data (default True)

    Returns:
        Complete session metadata dictionary:
        {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "device_type": "Mobile",
            "device_name": "iPhone 14 Pro",
            "browser": "Safari 17.2",
            "os": "iOS 17.2",
            "location": {
                "country": "Sri Lanka",
                "city": "Colombo",
                "latitude": 6.9271,
                "longitude": 79.8612
            },
            "created_at": "2026-02-03T10:00:00Z",
            "last_active": "2026-02-03T10:00:00Z"
        }

    Example:
        >>> metadata = extract_session_metadata(
        ...     ip_address=request.client.host,
        ...     user_agent=request.headers.get("user-agent"),
        ...     include_location=True
        ... )
    """
    # Base metadata
    metadata: Dict[str, Any] = {
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": datetime.utcnow().isoformat(),
        "last_active": datetime.utcnow().isoformat(),
    }

    # Add device information
    device_info = parse_device_info(user_agent)
    metadata.update(device_info)

    # Add location (optional, requires async)
    if include_location:
        try:
            location = await get_location_from_ip(ip_address)
            if location:
                metadata["location"] = location
        except Exception as e:
            logger.warning(f"Failed to add location to metadata: {e}")

    return metadata


def detect_suspicious_activity(
    user_id: str, new_session_metadata: Dict, existing_sessions: List[Dict]
) -> Dict[str, Any]:
    """
    Detect suspicious session activity patterns.

    Analyzes new session against existing sessions to identify:
    - Impossible travel (different countries within 1 hour)
    - New device types not previously used
    - Unusual login times (optional)
    - Rapid session creation (optional)

    Args:
        user_id: User ID for logging
        new_session_metadata: Metadata for newly created session
        existing_sessions: List of user's existing sessions

    Returns:
        {
            "is_suspicious": True | False,
            "reasons": ["impossible_travel", "new_device_type"],
            "details": {
                "impossible_travel": {
                    "from_country": "United States",
                    "to_country": "Sri Lanka",
                    "time_diff_hours": 0.5
                },
                "new_device_type": "Tablet"
            }
        }

    Example:
        >>> suspicious = detect_suspicious_activity(
        ...     user_id="user-123",
        ...     new_session_metadata=metadata,
        ...     existing_sessions=sessions
        ... )
        >>> if suspicious["is_suspicious"]:
        ...     # Send alert email
        ...     send_security_alert(user_id, suspicious)
    """
    result: Dict[str, Any] = {"is_suspicious": False, "reasons": [], "details": {}}

    # Skip if no existing sessions
    if not existing_sessions:
        return result

    # Get location from new session
    new_location = new_session_metadata.get("location")
    if not new_location:
        # Can't detect travel without location
        return result

    new_country_code = new_location.get("country_code")
    if not new_country_code:
        return result

    # Check for impossible travel
    for session in existing_sessions:
        session_location = session.get("location")
        if not session_location:
            continue

        session_country_code = session_location.get("country_code")
        if not session_country_code:
            continue

        # Check if different country
        if session_country_code != new_country_code:
            # Calculate time difference
            try:
                session_time = datetime.fromisoformat(session.get("last_active", ""))
                new_time = datetime.fromisoformat(new_session_metadata.get("created_at", ""))

                time_diff = new_time - session_time
                time_diff_hours = time_diff.total_seconds() / 3600

                # If logged in from different country within 1 hour
                # → Physically impossible
                if 0 < time_diff_hours < 1:
                    result["is_suspicious"] = True
                    result["reasons"].append("impossible_travel")
                    result["details"]["impossible_travel"] = {
                        "from_country": session_location.get("country"),
                        "to_country": new_location.get("country"),
                        "time_diff_hours": round(time_diff_hours, 2),
                        "from_city": session_location.get("city"),
                        "to_city": new_location.get("city"),
                    }

                    logger.warning(
                        f"Impossible travel detected for user {user_id}: "
                        f"{session_location.get('country')} → "
                        f"{new_location.get('country')} in "
                        f"{time_diff_hours:.2f} hours",
                        extra={
                            "user_id": user_id,
                            "security_event": "impossible_travel",
                            "details": result["details"]["impossible_travel"],
                        },
                    )

            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse timestamps: {e}")
                continue

    # Check for new device type
    existing_device_types = {
        s.get("device_type") for s in existing_sessions if s.get("device_type")
    }

    new_device_type = new_session_metadata.get("device_type")

    if new_device_type and new_device_type not in existing_device_types:
        result["reasons"].append("new_device_type")
        result["details"]["new_device_type"] = new_device_type

        logger.info(
            f"New device type detected for user {user_id}: {new_device_type}",
            extra={
                "user_id": user_id,
                "security_event": "new_device_type",
                "device_type": new_device_type,
            },
        )

    return result
