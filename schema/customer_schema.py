# flask_web/schema/customer_schema.py
from models import db
from datetime import datetime
import uuid


# 1. 고객 테이블
class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    salt = db.Column(db.String(50), nullable=False)
    internal_uid = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4()))

    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)

    user_type = db.Column(db.String(20), default='General')  # 일반/VIP
    role = db.Column(db.String(20), default='customer')
    status = db.Column(db.String(20), default='active')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='customer', lazy=True)


# 2. 예약 테이블
class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)

    rep_name = db.Column(db.String(50), nullable=False)
    rep_phone = db.Column(db.String(20), nullable=False)
    departure_place = db.Column(db.String(50), nullable=True)
    headcount = db.Column(db.Integer, default=1)
    requests = db.Column(db.Text, nullable=True)

    booking_status = db.Column(db.String(20), default='pending')

    total_price = db.Column(db.Integer, default=0)
    deposit_price = db.Column(db.Integer, default=0)
    balance_price = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)