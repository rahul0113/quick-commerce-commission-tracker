from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone, timedelta
import jwt
import secrets
import hashlib
import uuid
import os

# ===== Config =====
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///commission_tracker.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ===== Database =====
engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== Models =====
def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow)

class PlatformCredential(Base):
    __tablename__ = "platform_credentials"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    credentials = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class PaymentRecord(Base):
    __tablename__ = "payment_records"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    order_id = Column(String(255), nullable=False)
    order_date = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(DateTime, nullable=True)
    item_description = Column(Text, nullable=True)
    item_quantity = Column(Integer, default=1)
    item_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    expected_commission_rate = Column(Float, nullable=False)
    actual_commission_charged = Column(Float, nullable=False)
    commission_difference = Column(Float, nullable=False)
    platform_fee = Column(Float, default=0)
    delivery_fee = Column(Float, default=0)
    gst_on_fees = Column(Float, default=0)
    tds = Column(Float, default=0)
    other_deductions = Column(Float, default=0)
    gross_amount = Column(Float, nullable=False)
    total_deductions = Column(Float, nullable=False)
    net_settlement = Column(Float, nullable=False)
    fetched_at = Column(DateTime, default=utcnow)
    source = Column(String(20), nullable=False, default="manual")
    raw = Column(JSON, nullable=True)
    __table_args__ = (UniqueConstraint("user_id", "platform", "order_id"),)

class CommissionRate(Base):
    __tablename__ = "commission_rates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False, default="*")
    base_rate = Column(Float, nullable=False)
    effective_from = Column(DateTime, nullable=False, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

# ===== Auth Utils =====
def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password, stored_hash):
    salt, hashed = stored_hash.split(":")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed

def create_token(user_id, token_type="access"):
    expire_hours = 24 * 30 if token_type == "refresh" else JWT_EXPIRATION_HOURS
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expire_hours),
        "iat": datetime.now(timezone.utc),
        "type": token_type,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except:
        return None

def require_auth():
    user_id = get_current_user()
    if not user_id:
        return None, (jsonify({"detail": "Unauthorized"}), 401)
    return user_id, None

# ===== Commission Utils =====
DEFAULT_RATES = {"zomato": 18, "swiggy": 18, "blinkit": 22, "instamart": 18}

def to_dict(row):
    if row is None:
        return None
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}

# ===== App =====
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])

# Create tables
with app.app_context():
    Base.metadata.create_all(engine)

# ===== Auth Routes =====
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    email, password, name = data.get("email"), data.get("password"), data.get("name")
    if not all([email, password, name]):
        return jsonify({"detail": "email, password, and name are required"}), 400
    if len(password) < 8:
        return jsonify({"detail": "Password must be at least 8 characters"}), 400

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return jsonify({"detail": "Email already registered"}), 400
        user = User(email=email, name=name, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        uid = user.id
    finally:
        db.close()

    return jsonify({
        "access_token": create_token(uid, "access"),
        "refresh_token": create_token(uid, "refresh"),
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    })

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    email, password = data.get("email"), data.get("password")
    if not all([email, password]):
        return jsonify({"detail": "email and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"detail": "Invalid email or password"}), 401
        uid = user.id
    finally:
        db.close()

    return jsonify({
        "access_token": create_token(uid, "access"),
        "refresh_token": create_token(uid, "refresh"),
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    })

@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    data = request.json
    token = data.get("refresh_token")
    if not token:
        return jsonify({"detail": "refresh_token is required"}), 400
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return jsonify({"detail": "Invalid token type"}), 401
        uid = payload.get("sub")
    except:
        return jsonify({"detail": "Invalid token"}), 401

    return jsonify({
        "access_token": create_token(uid, "access"),
        "refresh_token": create_token(uid, "refresh"),
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    })

@app.route("/api/auth/me", methods=["GET"])
def me():
    user_id, err = require_auth()
    if err:
        return err
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"detail": "User not found"}), 401
        return jsonify({"id": user.id, "email": user.email, "name": user.name})
    finally:
        db.close()

# ===== API Routes =====
@app.route("/api/payments", methods=["GET"])
def get_payments():
    user_id, err = require_auth()
    if err:
        return err

    platform = request.args.get("platform")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 50))))

    db = SessionLocal()
    try:
        query = db.query(PaymentRecord).filter(PaymentRecord.user_id == user_id)
        if platform:
            query = query.filter(PaymentRecord.platform == platform)
        if start_date:
            query = query.filter(PaymentRecord.order_date >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
        if end_date:
            query = query.filter(PaymentRecord.order_date <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))

        total = query.count()
        records = query.order_by(PaymentRecord.order_date.desc()).offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            "data": [to_dict(r) for r in records],
            "pagination": {"page": page, "limit": limit, "total": total, "pages": max(1, (total + limit - 1) // limit)},
        })
    finally:
        db.close()

@app.route("/api/summary", methods=["GET"])
def get_summary():
    user_id, err = require_auth()
    if err:
        return err
    return jsonify([])  # Simplified for local

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    user_id, err = require_auth()
    if err:
        return err
    return jsonify([])  # Simplified for local

@app.route("/api/overcharged", methods=["GET"])
def get_overcharged():
    user_id, err = require_auth()
    if err:
        return err
    return jsonify({"total_overcharged": 0, "by_platform": {}})

@app.route("/api/credentials", methods=["GET"])
def list_credentials():
    user_id, err = require_auth()
    if err:
        return err
    db = SessionLocal()
    try:
        creds = db.query(PlatformCredential).filter(PlatformCredential.user_id == user_id).all()
        return jsonify([{
            "platform": c.platform, "is_active": c.is_active,
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
        } for c in creds])
    finally:
        db.close()

@app.route("/api/credentials", methods=["POST"])
def save_credentials():
    user_id, err = require_auth()
    if err:
        return err
    platform = request.args.get("platform")
    data = request.json
    db = SessionLocal()
    try:
        existing = db.query(PlatformCredential).filter(
            PlatformCredential.user_id == user_id, PlatformCredential.platform == platform
        ).first()
        if existing:
            existing.credentials = data
        else:
            db.add(PlatformCredential(user_id=user_id, platform=platform, credentials=data))
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()

@app.route("/api/sync/<platform>", methods=["POST"])
def sync_platform(platform):
    user_id, err = require_auth()
    if err:
        return err
    return jsonify({"platform": platform, "records_found": 0, "records_new": 0, "errors": ["Scraper not available in local mode"]})

@app.route("/api/rates", methods=["POST"])
def add_rate():
    user_id, err = require_auth()
    if err:
        return err
    return jsonify({"success": True})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "0.1.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
