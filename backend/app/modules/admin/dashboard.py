"""
Admin dashboard analytics endpoints.

CD-61: Admin Dashboard Analytics
Provides comprehensive metrics and visualizations for administrators.

Endpoints:
    GET /admin/dashboard/stats   - Overall platform statistics (KPIs)
    GET /admin/dashboard/users   - User analytics (registrations, roles, KYC)
    GET /admin/dashboard/orders  - Order metrics (status, volume, rates)
    GET /admin/dashboard/revenue - Revenue analytics (trends, payment methods)
    GET /admin/dashboard/system  - System health metrics (CPU, memory, Redis)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import psutil
from app.core.dependencies import get_current_active_user, get_db
from app.core.permissions import Permission, require_permission
from app.core.redis import redis_client
from app.models.kyc import KYCDocument, KYCStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Cache utility
# ─────────────────────────────────────────────────────────────────────────────


async def get_cached_or_compute(cache_key: str, ttl_seconds: int, compute_func, *args, **kwargs):
    """
    Retrieve data from Redis cache or compute and cache it.

    Args:
        cache_key:      Redis key to store/retrieve the value.
        ttl_seconds:    Cache TTL in seconds.
        compute_func:   Async callable that returns the data when cache misses.
        *args/**kwargs: Forwarded to compute_func.

    Returns:
        Cached dict or freshly computed data.
    """
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    data = await compute_func(*args, **kwargs)

    await redis_client.setex(cache_key, ttl_seconds, json.dumps(data, default=str))
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Shared sub-schemas
# ─────────────────────────────────────────────────────────────────────────────


class DailyCount(BaseModel):
    """A single (date, count) data point used across analytics endpoints."""

    date: str
    count: int


# ─────────────────────────────────────────────────────────────────────────────
# CD-61.1 – Overall Platform Statistics
# ─────────────────────────────────────────────────────────────────────────────


class DashboardStats(BaseModel):
    """High-level KPIs returned by GET /admin/dashboard/stats."""

    # User Metrics
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int

    # Order Metrics
    total_orders: int
    pending_orders: int
    in_progress_orders: int
    completed_orders: int
    cancelled_orders: int

    # Revenue Metrics
    total_revenue: float
    revenue_today: float
    revenue_this_week: float
    revenue_this_month: float
    avg_order_value: float

    # KYC Metrics
    kyc_pending: int
    kyc_approved: int
    kyc_rejected: int


@router.get("/stats", response_model=DashboardStats)
@require_permission(Permission.MANAGE_USERS)
async def get_dashboard_stats(
    _: User = Depends(require_permission(Permission.MANAGE_USERS)),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get overall platform statistics.

    Returns high-level KPIs for the admin dashboard:
    - User metrics  (total, active, new registrations by period)
    - Order metrics (total, by status)
    - Revenue metrics (total, recent, average order value)
    - KYC metrics   (pending, approved, rejected)

    Permissions: manage_users
    Cache: 5 minutes (Redis key ``dashboard:stats``)

    Returns:
        DashboardStats with all KPI fields populated.
    """
    # ── Try cache first (5-minute TTL) ──────────────────────────────────────
    CACHE_KEY = "dashboard:stats"
    CACHE_TTL = 300  # 5 minutes

    cached = await redis_client.get(CACHE_KEY)
    if cached:
        logger.info(
            f"Returning cached stats for admin {current_user.email}",
            extra={"admin_id": str(current_user.id)},
        )
        return DashboardStats(**json.loads(cached))

    # ── Time boundaries ──────────────────────────────────────────────────────
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # ── User Metrics ─────────────────────────────────────────────────────────
    total_users = db.query(func.count(User.id)).scalar()

    active_users = db.query(func.count(User.id)).filter(User.updated_at >= month_start).scalar()
    new_users_today = db.query(func.count(User.id)).filter(User.created_at >= today_start).scalar()
    new_users_this_week = (
        db.query(func.count(User.id)).filter(User.created_at >= week_start).scalar()
    )
    new_users_this_month = (
        db.query(func.count(User.id)).filter(User.created_at >= month_start).scalar()
    )

    # ── Order Metrics ────────────────────────────────────────────────────────
    total_orders = db.query(func.count(Order.id)).scalar()

    pending_orders = (
        db.query(func.count(Order.id)).filter(Order.status == OrderStatus.PENDING).scalar()
    )
    in_progress_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.status.in_(
                [
                    OrderStatus.PAYMENT_PENDING,
                    OrderStatus.VEHICLE_ORDERED,
                    OrderStatus.IN_TRANSIT,
                    OrderStatus.CUSTOMS_CLEARANCE,
                ]
            )
        )
        .scalar()
    )
    completed_orders = (
        db.query(func.count(Order.id)).filter(Order.status == OrderStatus.DELIVERED).scalar()
    )
    cancelled_orders = (
        db.query(func.count(Order.id)).filter(Order.status == OrderStatus.CANCELLED).scalar()
    )

    # ── Revenue Metrics ──────────────────────────────────────────────────────
    total_revenue = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.status == PaymentStatus.COMPLETED)
        .scalar()
        or 0.0
    )
    revenue_today = (
        db.query(func.sum(Payment.amount))
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= today_start,
            )
        )
        .scalar()
        or 0.0
    )
    revenue_this_week = (
        db.query(func.sum(Payment.amount))
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= week_start,
            )
        )
        .scalar()
        or 0.0
    )
    revenue_this_month = (
        db.query(func.sum(Payment.amount))
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= month_start,
            )
        )
        .scalar()
        or 0.0
    )
    avg_order_value = (total_revenue / completed_orders) if completed_orders > 0 else 0.0

    # ── KYC Metrics ──────────────────────────────────────────────────────────
    kyc_pending = (
        db.query(func.count(KYCDocument.id))
        .filter(KYCDocument.status == KYCStatus.PENDING)
        .scalar()
    )
    kyc_approved = (
        db.query(func.count(KYCDocument.id))
        .filter(KYCDocument.status == KYCStatus.APPROVED)
        .scalar()
    )
    kyc_rejected = (
        db.query(func.count(KYCDocument.id))
        .filter(KYCDocument.status == KYCStatus.REJECTED)
        .scalar()
    )

    # ── Build response & cache ────────────────────────────────────────────────
    stats = DashboardStats(
        total_users=total_users,
        active_users=active_users,
        new_users_today=new_users_today,
        new_users_this_week=new_users_this_week,
        new_users_this_month=new_users_this_month,
        total_orders=total_orders,
        pending_orders=pending_orders,
        in_progress_orders=in_progress_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_revenue=total_revenue,
        revenue_today=revenue_today,
        revenue_this_week=revenue_this_week,
        revenue_this_month=revenue_this_month,
        avg_order_value=avg_order_value,
        kyc_pending=kyc_pending,
        kyc_approved=kyc_approved,
        kyc_rejected=kyc_rejected,
    )

    await redis_client.setex(CACHE_KEY, CACHE_TTL, json.dumps(stats.dict()))

    logger.info(
        f"Admin {current_user.email} accessed dashboard stats",
        extra={"admin_id": str(current_user.id)},
    )

    return stats


# ─────────────────────────────────────────────────────────────────────────────
# CD-61.2 – User Analytics
# ─────────────────────────────────────────────────────────────────────────────


class UserAnalytics(BaseModel):
    """User growth trends and distribution returned by GET /admin/dashboard/users."""

    daily_registrations: List[DailyCount]
    role_distribution: Dict[str, int]
    kyc_status_distribution: Dict[str, int]
    active_users_trend: List[DailyCount]
    top_registration_days: List[DailyCount]


@router.get("/users", response_model=UserAnalytics)
@require_permission(Permission.MANAGE_USERS)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyse"),
    _: User = Depends(require_permission(Permission.MANAGE_USERS)),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get user analytics and trends.

    Returns:
    - Daily registrations over the selected period
    - Role distribution (CUSTOMER, ADMIN, EXPORTER, …)
    - KYC status distribution (including users with no KYC)
    - Active-users trend (by last-updated date)
    - Top 10 registration days

    Args:
        days: Look-back window in days (1–365, default 30).

    Permissions: manage_users
    Cache: 10 minutes (Redis key ``dashboard:users:{days}``)

    Returns:
        UserAnalytics object.
    """
    CACHE_KEY = f"dashboard:users:{days}"
    CACHE_TTL = 600  # 10 minutes

    cached = await redis_client.get(CACHE_KEY)
    if cached:
        logger.info(
            f"Returning cached user analytics for admin {current_user.email}",
            extra={"admin_id": str(current_user.id), "days": days},
        )
        return UserAnalytics(**json.loads(cached))

    start_date = datetime.utcnow() - timedelta(days=days)

    # ── Daily Registrations ──────────────────────────────────────────────────
    daily_reg_rows = (
        db.query(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )
    daily_registrations = [
        DailyCount(date=row.date.isoformat(), count=row.count) for row in daily_reg_rows
    ]

    # ── Role Distribution ────────────────────────────────────────────────────
    role_dist_rows = (
        db.query(User.role, func.count(User.id).label("count")).group_by(User.role).all()
    )
    role_distribution = {row.role.value: row.count for row in role_dist_rows}

    # ── KYC Status Distribution ──────────────────────────────────────────────
    kyc_dist_rows = (
        db.query(KYCDocument.status, func.count(KYCDocument.id).label("count"))
        .group_by(KYCDocument.status)
        .all()
    )
    kyc_status_distribution = {row.status.value: row.count for row in kyc_dist_rows}

    # Users without any KYC document
    users_without_kyc = (
        db.query(func.count(User.id)).filter(~User.id.in_(db.query(KYCDocument.user_id))).scalar()
    )
    kyc_status_distribution["NONE"] = users_without_kyc

    # ── Active Users Trend ───────────────────────────────────────────────────
    active_trend_rows = (
        db.query(
            func.date(User.updated_at).label("date"),
            func.count(User.id).label("count"),
        )
        .filter(User.updated_at >= start_date)
        .group_by(func.date(User.updated_at))
        .order_by(func.date(User.updated_at))
        .all()
    )
    active_users_trend = [
        DailyCount(date=row.date.isoformat(), count=row.count) for row in active_trend_rows
    ]

    # ── Top Registration Days ────────────────────────────────────────────────
    top_days_rows = (
        db.query(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.count(User.id).desc())
        .limit(10)
        .all()
    )
    top_registration_days = [
        DailyCount(date=row.date.isoformat(), count=row.count) for row in top_days_rows
    ]

    analytics = UserAnalytics(
        daily_registrations=daily_registrations,
        role_distribution=role_distribution,
        kyc_status_distribution=kyc_status_distribution,
        active_users_trend=active_users_trend,
        top_registration_days=top_registration_days,
    )

    await redis_client.setex(CACHE_KEY, CACHE_TTL, json.dumps(analytics.dict()))

    logger.info(
        f"Admin {current_user.email} accessed user analytics (last {days} days)",
        extra={"admin_id": str(current_user.id), "days": days},
    )

    return analytics


# ─────────────────────────────────────────────────────────────────────────────
# CD-61.3 – Order Analytics
# ─────────────────────────────────────────────────────────────────────────────


class OrderAnalytics(BaseModel):
    """Order metrics returned by GET /admin/dashboard/orders."""

    status_distribution: Dict[str, int]
    daily_orders: List[DailyCount]
    avg_processing_time_days: float
    completion_rate: float
    cancellation_rate: float
    orders_by_vehicle_type: Dict[str, int]


@router.get("/orders", response_model=OrderAnalytics)
@require_permission(Permission.MANAGE_USERS)
async def get_order_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyse"),
    _: User = Depends(require_permission(Permission.MANAGE_USERS)),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get order analytics and metrics.

    Returns:
    - Order status distribution over the selected period
    - Daily order volume
    - Average processing time (created → delivered)
    - Completion and cancellation rates
    - Orders by vehicle type (TODO: wire to real Vehicle model)

    Args:
        days: Look-back window in days (1–365, default 30).

    Permissions: manage_users
    Cache: 10 minutes (Redis key ``dashboard:orders:{days}``)

    Returns:
        OrderAnalytics object.
    """
    CACHE_KEY = f"dashboard:orders:{days}"
    CACHE_TTL = 600  # 10 minutes

    cached = await redis_client.get(CACHE_KEY)
    if cached:
        logger.info(
            f"Returning cached order analytics for admin {current_user.email}",
            extra={"admin_id": str(current_user.id), "days": days},
        )
        return OrderAnalytics(**json.loads(cached))

    start_date = datetime.utcnow() - timedelta(days=days)

    # ── Status Distribution ──────────────────────────────────────────────────
    status_rows = (
        db.query(Order.status, func.count(Order.id).label("count"))
        .filter(Order.created_at >= start_date)
        .group_by(Order.status)
        .all()
    )
    status_distribution = {row.status.value: row.count for row in status_rows}

    # ── Daily Orders ─────────────────────────────────────────────────────────
    daily_rows = (
        db.query(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("count"),
        )
        .filter(Order.created_at >= start_date)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    daily_orders = [DailyCount(date=row.date.isoformat(), count=row.count) for row in daily_rows]

    # ── Average Processing Time ──────────────────────────────────────────────
    completed = (
        db.query(Order)
        .filter(
            and_(
                Order.status == OrderStatus.DELIVERED,
                Order.created_at >= start_date,
                Order.updated_at.isnot(None),
            )
        )
        .all()
    )
    if completed:
        total_days = sum((o.updated_at - o.created_at).days for o in completed)
        avg_processing_time_days = total_days / len(completed)
    else:
        avg_processing_time_days = 0.0

    # ── Completion & Cancellation Rates ──────────────────────────────────────
    total_orders = db.query(func.count(Order.id)).filter(Order.created_at >= start_date).scalar()
    completed_count = (
        db.query(func.count(Order.id))
        .filter(and_(Order.status == OrderStatus.DELIVERED, Order.created_at >= start_date))
        .scalar()
    )
    cancelled_count = (
        db.query(func.count(Order.id))
        .filter(and_(Order.status == OrderStatus.CANCELLED, Order.created_at >= start_date))
        .scalar()
    )

    completion_rate = (completed_count / total_orders * 100) if total_orders > 0 else 0.0
    cancellation_rate = (cancelled_count / total_orders * 100) if total_orders > 0 else 0.0

    # ── Orders by Vehicle Type ────────────────────────────────────────────────
    # TODO: Replace placeholder with real Vehicle join
    orders_by_vehicle_type = {"Sedan": 50, "SUV": 30, "Truck": 15, "Van": 5}

    analytics = OrderAnalytics(
        status_distribution=status_distribution,
        daily_orders=daily_orders,
        avg_processing_time_days=round(avg_processing_time_days, 2),
        completion_rate=round(completion_rate, 2),
        cancellation_rate=round(cancellation_rate, 2),
        orders_by_vehicle_type=orders_by_vehicle_type,
    )

    await redis_client.setex(CACHE_KEY, CACHE_TTL, json.dumps(analytics.dict()))

    logger.info(
        f"Admin {current_user.email} accessed order analytics (last {days} days)",
        extra={"admin_id": str(current_user.id), "days": days},
    )

    return analytics


# ─────────────────────────────────────────────────────────────────────────────
# CD-61.4 – Revenue Analytics
# ─────────────────────────────────────────────────────────────────────────────


class RevenueDataPoint(BaseModel):
    """A single (date, amount) revenue data point."""

    date: str
    amount: float


class MonthlyRevenue(BaseModel):
    """Aggregated revenue for a calendar month."""

    month: str  # e.g. "2026-01"
    amount: float


class TopRevenueSource(BaseModel):
    """Revenue breakdown by source/category."""

    source: str
    amount: float
    percentage: float


class RevenueAnalytics(BaseModel):
    """Revenue metrics returned by GET /admin/dashboard/revenue."""

    daily_revenue: List[RevenueDataPoint]
    monthly_revenue: List[MonthlyRevenue]
    payment_method_breakdown: Dict[str, float]
    top_revenue_sources: List[TopRevenueSource]
    revenue_growth_rate: float


@router.get("/revenue", response_model=RevenueAnalytics)
@require_permission(Permission.MANAGE_USERS)
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyse"),
    _: User = Depends(require_permission(Permission.MANAGE_USERS)),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get revenue analytics and trends.

    Returns:
    - Daily revenue over the selected period
    - Last 12 months of monthly revenue
    - Payment-method breakdown (CARD, BANK, etc.)
    - Top revenue sources by vehicle type (TODO: real Vehicle join)
    - Period-over-period revenue growth rate

    Args:
        days: Look-back window in days (1–365, default 30).

    Permissions: manage_users
    Cache: 10 minutes (Redis key ``dashboard:revenue:{days}``)

    Returns:
        RevenueAnalytics object.
    """
    CACHE_KEY = f"dashboard:revenue:{days}"
    CACHE_TTL = 600  # 10 minutes

    cached = await redis_client.get(CACHE_KEY)
    if cached:
        logger.info(
            f"Returning cached revenue analytics for admin {current_user.email}",
            extra={"admin_id": str(current_user.id), "days": days},
        )
        return RevenueAnalytics(**json.loads(cached))

    start_date = datetime.utcnow() - timedelta(days=days)

    # ── Daily Revenue ────────────────────────────────────────────────────────
    daily_rev_rows = (
        db.query(
            func.date(Payment.created_at).label("date"),
            func.sum(Payment.amount).label("amount"),
        )
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= start_date,
            )
        )
        .group_by(func.date(Payment.created_at))
        .order_by(func.date(Payment.created_at))
        .all()
    )
    daily_revenue = [
        RevenueDataPoint(date=row.date.isoformat(), amount=float(row.amount))
        for row in daily_rev_rows
    ]

    # ── Monthly Revenue (last 12 months) ─────────────────────────────────────
    monthly_rev_rows = (
        db.query(
            func.date_trunc("month", Payment.created_at).label("month"),
            func.sum(Payment.amount).label("amount"),
        )
        .filter(Payment.status == PaymentStatus.COMPLETED)
        .group_by(func.date_trunc("month", Payment.created_at))
        .order_by(func.date_trunc("month", Payment.created_at))
        .limit(12)
        .all()
    )
    monthly_revenue = [
        MonthlyRevenue(month=row.month.strftime("%Y-%m"), amount=float(row.amount))
        for row in monthly_rev_rows
    ]

    # ── Payment Method Breakdown ─────────────────────────────────────────────
    method_rows = (
        db.query(Payment.payment_method, func.sum(Payment.amount).label("amount"))
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= start_date,
            )
        )
        .group_by(Payment.payment_method)
        .all()
    )
    payment_method_breakdown = {row.payment_method: float(row.amount) for row in method_rows}

    # ── Top Revenue Sources ───────────────────────────────────────────────────
    # TODO: Replace placeholder percentages with a real Vehicle-type join
    total_revenue = sum(payment_method_breakdown.values())
    top_revenue_sources = [
        TopRevenueSource(source="Sedan Imports", amount=total_revenue * 0.45, percentage=45.0),
        TopRevenueSource(source="SUV Imports", amount=total_revenue * 0.30, percentage=30.0),
        TopRevenueSource(source="Truck Imports", amount=total_revenue * 0.15, percentage=15.0),
        TopRevenueSource(source="Van Imports", amount=total_revenue * 0.10, percentage=10.0),
    ]

    # ── Revenue Growth Rate ───────────────────────────────────────────────────
    previous_start = start_date - timedelta(days=days)

    current_period_revenue = (
        db.query(func.sum(Payment.amount))
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= start_date,
            )
        )
        .scalar()
        or 0.0
    )
    previous_period_revenue = (
        db.query(func.sum(Payment.amount))
        .filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= previous_start,
                Payment.created_at < start_date,
            )
        )
        .scalar()
        or 0.0
    )

    if previous_period_revenue > 0:
        revenue_growth_rate = (
            (current_period_revenue - previous_period_revenue) / previous_period_revenue * 100
        )
    else:
        revenue_growth_rate = 0.0

    analytics = RevenueAnalytics(
        daily_revenue=daily_revenue,
        monthly_revenue=monthly_revenue,
        payment_method_breakdown=payment_method_breakdown,
        top_revenue_sources=top_revenue_sources,
        revenue_growth_rate=round(revenue_growth_rate, 2),
    )

    await redis_client.setex(CACHE_KEY, CACHE_TTL, json.dumps(analytics.dict()))

    logger.info(
        f"Admin {current_user.email} accessed revenue analytics (last {days} days)",
        extra={"admin_id": str(current_user.id), "days": days},
    )

    return analytics


# ─────────────────────────────────────────────────────────────────────────────
# CD-61.5 – System Health Metrics
# ─────────────────────────────────────────────────────────────────────────────


class SystemHealth(BaseModel):
    """System performance and resource metrics returned by GET /admin/dashboard/system."""

    # API Performance (TODO: wire to real APM/middleware)
    api_response_time_avg_ms: float
    api_response_time_p95_ms: float
    api_response_time_p99_ms: float
    error_rate_percent: float

    # System Resources
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float

    # Database
    active_database_connections: int
    max_database_connections: int

    # Redis
    redis_health: str
    active_sessions: int

    # Application
    uptime_hours: float


@router.get("/system", response_model=SystemHealth)
@require_permission(Permission.MANAGE_USERS)
async def get_system_health(
    _: User = Depends(require_permission(Permission.MANAGE_USERS)),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get system health and performance metrics.

    Returns:
    - API response times (average, p95, p99) – placeholder until APM middleware is wired
    - Error rate – placeholder until error-tracking middleware is wired
    - CPU, memory, and disk usage (live via psutil)
    - PostgreSQL connection pool status (live)
    - Redis health check and active session count (live)
    - Application uptime – placeholder until startup timestamp is stored

    Permissions: manage_users
    Cache: 1 minute (Redis key ``dashboard:system``)

    Returns:
        SystemHealth object.
    """
    CACHE_KEY = "dashboard:system"
    CACHE_TTL = 60  # 1 minute

    cached = await redis_client.get(CACHE_KEY)
    if cached:
        logger.info(
            f"Returning cached system health for admin {current_user.email}",
            extra={"admin_id": str(current_user.id)},
        )
        return SystemHealth(**json.loads(cached))

    # ── API Performance ───────────────────────────────────────────────────────
    # TODO: Replace with real values collected by a timing middleware / APM tool
    api_response_time_avg_ms = 250.0
    api_response_time_p95_ms = 500.0
    api_response_time_p99_ms = 1000.0
    error_rate_percent = 0.5

    # ── System Resources (live) ───────────────────────────────────────────────
    cpu_usage_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_usage_percent = memory.percent
    disk = psutil.disk_usage("/")
    disk_usage_percent = disk.percent

    # ── Database (live PostgreSQL query) ──────────────────────────────────────
    active_connections_result = db.execute(
        text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
    ).scalar()
    active_connections = int(active_connections_result or 0)
    max_connections_result = db.execute(text("SHOW max_connections")).scalar()
    max_connections = int(max_connections_result) if max_connections_result is not None else 0

    # ── Redis (live) ─────────────────────────────────────────────────────────
    try:
        await redis_client.ping()
        redis_health = "healthy"
    except Exception as exc:
        logger.error(f"Redis health check failed: {exc}")
        redis_health = "unhealthy"

    session_keys = await redis_client.keys("session:*")
    active_sessions = len(session_keys)

    # ── Uptime ────────────────────────────────────────────────────────────────
    # TODO: Store application start time at boot and compute real uptime
    uptime_hours = 72.5  # placeholder

    health = SystemHealth(
        api_response_time_avg_ms=api_response_time_avg_ms,
        api_response_time_p95_ms=api_response_time_p95_ms,
        api_response_time_p99_ms=api_response_time_p99_ms,
        error_rate_percent=error_rate_percent,
        cpu_usage_percent=round(cpu_usage_percent, 2),
        memory_usage_percent=round(memory_usage_percent, 2),
        disk_usage_percent=round(disk_usage_percent, 2),
        active_database_connections=active_connections,
        max_database_connections=max_connections,
        redis_health=redis_health,
        active_sessions=active_sessions,
        uptime_hours=uptime_hours,
    )

    await redis_client.setex(CACHE_KEY, CACHE_TTL, json.dumps(health.dict()))

    logger.info(
        f"Admin {current_user.email} accessed system health metrics",
        extra={"admin_id": str(current_user.id)},
    )

    return health
