from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
import uuid

from models.database import get_db
from models.payment import PaymentRecord, Platform, User, PlatformCredential
from services.commission import CommissionService
from api.auth import get_current_user

router = APIRouter()
commission_service = CommissionService()

def to_dict(row):
    """Convert SQLAlchemy row to dict"""
    if row is None:
        return None
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}

# ===== Routes =====

@router.get("/payments")
async def get_payments(
    request: Request,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PaymentRecord).where(PaymentRecord.user_id == current_user.id)

    if platform:
        query = query.where(PaymentRecord.platform == platform)
    if start_date:
        query = query.where(PaymentRecord.order_date >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        query = query.where(PaymentRecord.order_date <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * limit
    query = query.order_by(PaymentRecord.order_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "data": [to_dict(r) for r in records],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": max(1, (total + limit - 1) // limit),
        },
    }

@router.get("/summary")
async def get_summary(
    start_date: str,
    end_date: str,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = await commission_service.get_summary(
        db, current_user.id,
        datetime.fromisoformat(start_date.replace("Z", "+00:00")),
        datetime.fromisoformat(end_date.replace("Z", "+00:00")),
        platform,
    )
    return summary

@router.get("/alerts")
async def get_alerts(
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PaymentRecord).where(PaymentRecord.user_id == current_user.id)

    if platform:
        query = query.where(PaymentRecord.platform == platform)
    if start_date:
        query = query.where(PaymentRecord.order_date >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        query = query.where(PaymentRecord.order_date <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))

    query = query.order_by(PaymentRecord.order_date.desc()).limit(1000)
    result = await db.execute(query)
    records = result.scalars().all()

    alerts = await commission_service.analyze_records(records)
    return alerts

@router.get("/overcharged")
async def get_overcharged(
    start_date: str,
    end_date: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await commission_service.get_total_overcharged(
        db, current_user.id,
        datetime.fromisoformat(start_date.replace("Z", "+00:00")),
        datetime.fromisoformat(end_date.replace("Z", "+00:00")),
    )
    return result

@router.post("/sync/{platform}")
async def sync_platform(
    platform: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    from services.connector import sync_from_api
    result = await sync_from_api(
        db, current_user.id, platform,
        body.get("start_date"),
        body.get("end_date"),
    )
    return result

@router.post("/credentials")
async def save_credentials(
    platform: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json()
    result = await db.execute(
        select(PlatformCredential).where(
            PlatformCredential.user_id == current_user.id,
            PlatformCredential.platform == platform,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.credentials = body
        existing.is_active = True
    else:
        new_cred = PlatformCredential(
            user_id=current_user.id,
            platform=platform,
            credentials=body,
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
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in creds
    ]

@router.post("/rates")
async def add_custom_rate(
    platform: str,
    category: str,
    rate: float,
    effective_from: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime as dt
    effective = dt.fromisoformat(effective_from.replace("Z", "+00:00")) if effective_from else None
    await commission_service.add_custom_rate(db, platform, category, rate, effective)
    return {"success": True}
