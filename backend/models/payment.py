import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from models.database import Base

class Platform(str, enum.Enum):
    zomato = "zomato"
    swiggy = "swiggy"
    blinkit = "blinkit"
    instamart = "instamart"

class DataSource(str, enum.Enum):
    api = "api"
    scrape = "scrape"
    manual = "manual"
    pdf = "pdf"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    credentials = relationship("PlatformCredential", back_populates="user")
    payments = relationship("PaymentRecord", back_populates="user")

class PlatformCredential(Base):
    __tablename__ = "platform_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    credentials = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="credentials")

class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    order_id = Column(String(255), nullable=False)
    order_date = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(DateTime, nullable=True)

    # Item details
    item_description = Column(Text, nullable=True)
    item_quantity = Column(Integer, default=1)
    item_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Commission details
    expected_commission_rate = Column(Float, nullable=False)
    actual_commission_charged = Column(Float, nullable=False)
    commission_difference = Column(Float, nullable=False)

    # Fee breakdown
    platform_fee = Column(Float, default=0)
    delivery_fee = Column(Float, default=0)
    gst_on_fees = Column(Float, default=0)
    tds = Column(Float, default=0)
    other_deductions = Column(Float, default=0)

    # Settlement
    gross_amount = Column(Float, nullable=False)
    total_deductions = Column(Float, nullable=False)
    net_settlement = Column(Float, nullable=False)

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(20), nullable=False, default="manual")
    raw = Column(JSON, nullable=True)

    user = relationship("User", back_populates="payments")

    __table_args__ = (
        {"unique_together": ("user_id", "platform", "order_id")},
    )

class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    records_found = Column(Integer, default=0)
    records_new = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
