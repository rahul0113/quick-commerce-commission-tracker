from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import uuid

from models.database import get_db
from models.payment import PaymentRecord, Platform, User, PlatformCredential
from services.commission import CommissionService
from api.auth import get_current_user

router = APIRouter()
commission_service = CommissionService()

# ===== Pydantic Models =====

class PaymentResponse(BaseModel):
    id: uuid.UUID
    platform: str
    order_id: str
    order_date: datetime
    settlement_date: Optional[datetime]
    item_description: Optional[str]
    item_quantity: int
    item_price: float
    total_price: float
    expected_commission_rate: float
    actual_commission_charged: float
    commission_difference: float
    platform_fee: float
    delivery_fee: float
    gst_on_fees: float
    tds: float
    other_deductions: float
    gross_amount: float
    total_deductions: float
    net_settlement: float
    fetched_at: datetime
    source: str

    class Config:
        from_attributes = True

class PaymentListResponse(BaseModel):
    data: List[PaymentResponse]
    pagination: dict

class SummaryResponse(BaseModel):
    platform: str
    period: str
    total_orders: int
    total_sales: float
    total_commission_charged: float
    total_commission_expected: float
    total_overcharged: float
    avg_commission_rate: float
    net_settled: float

class OverchargedResponse(BaseModel):
    total_overcharged: float
    by_platform: dict

class AlertResponse(BaseModel):
    platform: str
    order_id: str
    expected: float
    actual: float
    difference: float
    severity: str
    message: str

# ===== Routes =====

@router.get("/payments", response_model=PaymentListResponse)
async def get_payments(
    platform: Optional[Platform] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PaymentRecord).where(PaymentRecord.user_id == current_user.id)

    if platform:
        query = query.where(PaymentRecord.platform == platform)
    if start_date:
        query = query.where(PaymentRecord.order_date >= start_date)
    if end_date:
        query = query.where(PaymentRecord.order_date <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * limit
    query = query.order_by(PaymentRecord.order_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return PaymentListResponse(
        data=records,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "pages": max(1, (total + limit - 1) // limit),
        },
    )

@router.get("/summary", response_model=List[SummaryResponse])
async def get_summary(
    start_date: datetime,
    end_date: datetime,
    platform: Optional[Platform] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = await commission_service.get_summary(db, current_user.id, start_date, end_date, platform)
    return summary

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    platform: Optional[Platform] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PaymentRecord).where(PaymentRecord.user_id == current_user.id)

    if platform:
        query = query.where(PaymentRecord.platform == platform)
    if start_date:
        query = query.where(PaymentRecord.order_date >= start_date)
    if end_date:
        query = query.where(PaymentRecord.order_date <= end_date)

    query = query.order_by(PaymentRecord.order_date.desc()).limit(1000)
    result = await db.execute(query)
    records = result.scalars().all()

    alerts = await commission_service.analyze_records(records)
    return alerts

@router.get("/overcharged", response_model=OverchargedResponse)
async def get_overcharged(
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await commission_service.get_total_overcharged(db, current_user.id, start_date, end_date)
    return result

@router.post("/sync/{platform}")
async def sync_platform(
    platform: Platform,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from services.connector import sync_from_api
    result = await sync_from_api(db, current_user.id, platform, start_date, end_date)
    return result

@router.post("/credentials")
async def save_credentials(
    platform: Platform,
    credentials: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PlatformCredential).where(
            PlatformCredential.user_id == current_user.id,
            PlatformCredential.platform == platform,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.credentials = credentials
        existing.is_active = True
    else:
        new_cred = PlatformCredential(
            user_id=current_user.id,
            platform=platform,
            credentials=credentials,
        )
        db.add(new_cred)

    await db.commit()
    return {"success": True}

@router.get("/credentials")
async def list_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PlatformCredential).where(PlatformCredential.user_id == current_user.id)
    )
    creds = result.scalars().all()
    return [
        {
            "platform": c.platform,
            "is_active": c.is_active,
            "last_sync_at": c.last_sync_at,
            "created_at": c.created_at,
        }
        for c in creds
    ]

@router.post("/rates")
async def add_custom_rate(
    platform: Platform,
    category: str,
    rate: float,
    effective_from: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await commission_service.add_custom_rate(db, platform, category, rate, effective_from)
    return {"success": True}
