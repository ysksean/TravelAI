from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON
from services.db_connect import Base


# ==========================================
# 1. Pydantic Models (JSON 검증용)
# ==========================================

class ProductMeta(BaseModel):
    status: str = "draft"
    version: str = "1.0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    source_files: Optional[List[str]] = []


class ProductInfo(BaseModel):
    product_name: str
    category: Optional[str] = "overseas"
    product_type: Optional[str] = "golf"
    country: Optional[str] = None
    city: Optional[str] = None
    departure_point: Optional[str] = None
    thumbnail_url: Optional[str] = None
    images: Optional[List[str]] = []


class ScheduleInfo(BaseModel):
    # [수정] JSON 입력은 문자열이므로 str로 변경하여 파싱 에러 방지
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    nights: int = 0
    days: int = 0


class PricingInfo(BaseModel):
    currency: str = "KRW"
    price_adult: int = 0
    price_child: int = 0
    price_infant: int = 0
    price_net: int = 0


class DetailInfo(BaseModel):
    flight_summary: Optional[str] = None
    inclusions: Optional[List[str]] = []
    exclusions: Optional[List[str]] = []
    special_notes: Optional[List[str]] = []
    content_html: Optional[str] = None
    others: Optional[str] = None


class ResourceHotel(BaseModel):
    name: str
    grade: Optional[str] = None
    description: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    meta_info: Optional[Dict] = {}


class ResourceGolf(BaseModel):
    name: str
    hole_info: Optional[str] = None
    address: Optional[str] = None
    operation_info: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    meta_info: Optional[Dict] = {}


class ResourcesInfo(BaseModel):
    hotels: Optional[List[ResourceHotel]] = []
    golf_courses: Optional[List[ResourceGolf]] = []


class Activity(BaseModel):
    time: Optional[str] = None
    type: Optional[str] = "other"
    title: str
    description: Optional[str] = None
    transport: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None


class ItineraryDay(BaseModel):
    day: int
    # [수정] JSON 입력은 문자열이므로 str로 변경
    date: Optional[str] = None
    activities: Optional[List[Activity]] = []
    meals: Optional[Dict[str, str]] = {}


class ProductMasterJSON(BaseModel):
    meta: ProductMeta
    info: ProductInfo
    schedule: ScheduleInfo
    pricing: PricingInfo
    details: DetailInfo
    resources: ResourcesInfo
    itinerary: List[ItineraryDay]


# ==========================================
# 2. SQLAlchemy Models (DB 테이블)
# ==========================================

class ProductTable(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    status = Column(String(50), default='draft')
    product_name = Column(String(255), nullable=False)
    category = Column(String(50))
    product_type = Column(String(50))
    country = Column(String(50))
    city = Column(String(50))
    departure_point = Column(String(50))

    # 일정 (DB에는 Date 타입 유지 -> SQLAlchemy가 문자열을 날짜로 자동 변환 시도함)
    start_date = Column(Date)
    end_date = Column(Date)
    nights = Column(Integer)
    days = Column(Integer)

    # 가격
    price_adult = Column(Integer)
    price_net = Column(Integer)
    currency = Column(String(10), default='KRW')

    # JSON 데이터
    images = Column(JSON)
    details = Column(JSON)
    resources = Column(JSON)
    itinerary = Column(JSON)
    source_files = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.product_name}')>"