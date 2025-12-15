# routes/admin_routes.py
from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, desc, text
from services.db_connect import SessionLocal

# [수정] models 모듈 제거 및 schema.py 연결
from schema.schema import ProductTable
# from models import Product, ProductPrice, ProductItinerary, ChatLog  <-- 삭제됨
from services.chat_service import get_room_list, get_chat_logs

import os
import json
import time
import traceback
from datetime import datetime
import google.generativeai as genai

# RAG Engine (Import if available)

from services.rag_service import add_product_to_vector_db
# [핵심] 서비스 모듈 임포트
from services.rag_service import search_best_products
from services.ai_service import generate_answer


bp = Blueprint('admin', __name__)

# Initialize UniversalTravelAI (Mock)


# Constants
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'ai_models')


# --- Page Routes ---

@bp.route('/')
def index():
    return render_template('admin/index.html', active_page='dashboard')


@bp.route('/products')
def product_list():
    # [참고] 추후 DB 연동 시 ProductTable.query.all() 등으로 변경 가능
    products = [
        {'id': 'P001', 'name': '도쿄 3박 4일 패키지', 'status': '판매중', 'period': '3박 4일', 'manager': '김관리', 'region': '일본'},
        {'id': 'P002', 'name': '오사카 유니버설 스튜디오', 'status': '대기', 'period': '2박 3일', 'manager': '이매니저', 'region': '일본'},
        {'id': 'P003', 'name': '다낭 호캉스 특가', 'status': '판매중', 'period': '3박 5일', 'manager': '박팀장', 'region': '베트남'},
        {'id': 'P004', 'name': '제주도 힐링 여행', 'status': '종료', 'period': '2박 3일', 'manager': '최대리', 'region': '한국'},
    ]
    return render_template('admin/product_list.html', active_page='products', products=products)


@bp.route('/products/new')
def product_create():
    # [수정] 템플릿 경로 확인 (templates 폴더 바로 아래에 있다면 'product_create.html')
    return render_template('admin/product_create.html', active_page='products')


@bp.route('/products/<id>')
def product_detail(id):
    product = {'id': id, 'name': '도쿄 3박 4일 패키지', 'status': '판매중', 'period': '3박 4일', 'manager': '김관리', 'region': '일본',
               'price': '1,200,000'}
    return render_template('admin/product_detail.html', active_page='products', product=product)


@bp.route('/reservations')
def reservation_list():
    reservations = [
        {'id': 'RES-2025-001', 'customer': '홍길동', 'phone': '010-1234-5678', 'product': '미야코지마 골프 3박 4일',
         'date': '2025-10-10', 'pax': 2, 'status': '예약확정'},
        {'id': 'RES-2025-002', 'customer': '김철수', 'phone': '010-2345-6789', 'product': '도쿄 3일 패키지',
         'date': '2025-10-15', 'pax': 4, 'status': '대기'},
        {'id': 'RES-2025-003', 'customer': '이영희', 'phone': '010-3456-7890', 'product': '오사카 4일 패키지',
         'date': '2025-10-20', 'pax': 2, 'status': '예약확정'},
        {'id': 'RES-2025-004', 'customer': '박민수', 'phone': '010-4567-8901', 'product': '제주도 3박 4일',
         'date': '2025-10-25', 'pax': 3, 'status': '취소'},
        {'id': 'RES-2025-005', 'customer': '정수진', 'phone': '010-5678-9012', 'product': '부산 2박 3일', 'date': '2025-11-01',
         'pax': 2, 'status': '대기'},
    ]
    return render_template('admin/reservation_list.html', active_page='reservations', reservations=reservations)


@bp.route('/reservations/<id>')
def reservation_detail(id):
    reservation = {'id': id, 'customer': '홍길동', 'phone': '010-1234-5678', 'product': '미야코지마 골프', 'date': '2025-10-10',
                   'pax': 2, 'status': '예약확정', 'amount': '2,500,000'}
    return render_template('admin/reservation_detail.html', active_page='reservations', reservation=reservation)


@bp.route('/quotations')
def quotation_list():
    quotations = [
        {'id': 'Q-2025-001', 'customer': '홍길동', 'product': '미야코지마 골프 3박 4일', 'amount': '2,500,000',
         'date': '2025-01-15', 'status': '대기'},
        {'id': 'Q-2025-002', 'customer': '김철수', 'product': '도쿄 3일 패키지', 'amount': '1,800,000', 'date': '2025-01-16',
         'status': '확정'},
        {'id': 'Q-2025-003', 'customer': '이영희', 'product': '오사카 4일 패키지', 'amount': '2,200,000', 'date': '2025-01-17',
         'status': '대기'},
        {'id': 'Q-2025-004', 'customer': '박민수', 'product': '제주도 3박 4일', 'amount': '1,500,000', 'date': '2025-01-18',
         'status': '취소'},
        {'id': 'Q-2025-005', 'customer': '정수진', 'product': '부산 2박 3일', 'amount': '800,000', 'date': '2025-01-19',
         'status': '확정'},
    ]
    return render_template('admin/quotation_list.html', active_page='quotations', quotations=quotations)


@bp.route('/quotations/new')
def quotation_create():
    return render_template('admin/quotation_create.html', active_page='quotations')


@bp.route('/quotations/<id>')
def quotation_detail(id):
    quotation = {'id': id, 'customer': '홍길동', 'product': '미야코지마 골프', 'amount': '2,500,000', 'date': '2025-01-15',
                 'status': '대기'}
    return render_template('admin/quotation_detail.html', active_page='quotations', quotation=quotation)


@bp.route('/payments')
def payment_page():
    return render_template('admin/payment.html', active_page='payments')


@bp.route('/finance')
def finance_page():
    return render_template('admin/finance.html', active_page='finance')


@bp.route('/flights')
def flight_list():
    flights = [
        {'id': 'KE001', 'airline': '대한항공', 'route': 'ICN → NRT', 'departure': '2025-10-10 09:00',
         'arrival': '2025-10-10 12:00', 'pax': 2, 'status': '예약완료'},
        {'id': 'OZ201', 'airline': '아시아나항공', 'route': 'ICN → KIX', 'departure': '2025-10-15 14:00',
         'arrival': '2025-10-15 16:30', 'pax': 4, 'status': '발권대기'},
        {'id': '7C123', 'airline': '제주항공', 'route': 'ICN → CJU', 'departure': '2025-10-20 08:00',
         'arrival': '2025-10-20 09:30', 'pax': 2, 'status': '예약완료'},
        {'id': 'LJ501', 'airline': '진에어', 'route': 'ICN → PUS', 'departure': '2025-10-25 10:00',
         'arrival': '2025-10-25 11:00', 'pax': 3, 'status': '발권완료'},
        {'id': 'TW301', 'airline': '티웨이항공', 'route': 'ICN → FUK', 'departure': '2025-11-01 13:00',
         'arrival': '2025-11-01 15:00', 'pax': 2, 'status': '예약완료'},
    ]
    return render_template('admin/flight_list.html', active_page='flights', flights=flights)


@bp.route('/hotels')
def hotel_list():
    hotels = [
        {'name': '미야코지마 리조트', 'region': '오키나와, 일본', 'rating': 5, 'rooms': 120, 'manager': '김호텔'},
        {'name': '도쿄 그랜드 호텔', 'region': '도쿄, 일본', 'rating': 4, 'rooms': 200, 'manager': '이호텔'},
        {'name': '오사카 베이 호텔', 'region': '오사카, 일본', 'rating': 4, 'rooms': 150, 'manager': '박호텔'},
        {'name': '제주 신라호텔', 'region': '제주도, 한국', 'rating': 5, 'rooms': 300, 'manager': '정호텔'},
        {'name': '부산 파라다이스 호텔', 'region': '부산, 한국', 'rating': 5, 'rooms': 250, 'manager': '최호텔'},
    ]
    return render_template('admin/hotel_list.html', active_page='hotels', hotels=hotels)


@bp.route('/attractions')
def attraction_list():
    attractions = [
        {'name': '도쿄 타워', 'region': '도쿄, 일본', 'type': '랜드마크', 'time': '2시간'},
        {'name': '오사카 성', 'region': '오사카, 일본', 'type': '역사', 'time': '1.5시간'},
        {'name': '제주 한라산', 'region': '제주도, 한국', 'type': '자연', 'time': '4시간'},
        {'name': '부산 해운대', 'region': '부산, 한국', 'type': '해변', 'time': '3시간'},
        {'name': '교토 기요미즈데라', 'region': '교토, 일본', 'type': '사원', 'time': '2시간'},
    ]
    return render_template('admin/attraction_list.html', active_page='attractions', attractions=attractions)


@bp.route('/partners')
def partner_list():
    partners = [
        {'id': 1, 'name': '일본여행사', 'region': '도쿄, 일본', 'type': '랜드오퍼레이터', 'contact': '김파트너', 'phone': '010-1111-2222',
         'email': 'kim@japan-travel.com', 'status': 'active'},
        {'id': 2, 'name': '제주여행사', 'region': '제주도, 한국', 'type': '로컬여행사', 'contact': '이파트너', 'phone': '010-2222-3333',
         'email': 'lee@jeju-travel.com', 'status': 'active'},
        {'id': 3, 'name': '부산여행사', 'region': '부산, 한국', 'type': '로컬여행사', 'contact': '박파트너', 'phone': '010-3333-4444',
         'email': 'park@busan-travel.com', 'status': 'active'},
        {'id': 4, 'name': '오키나와여행사', 'region': '오키나와, 일본', 'type': '랜드오퍼레이터', 'contact': '정파트너',
         'phone': '010-4444-5555', 'email': 'jung@okinawa-travel.com', 'status': 'active'},
        {'id': 5, 'name': '도쿄여행사', 'region': '도쿄, 일본', 'type': '랜드오퍼레이터', 'contact': '최파트너', 'phone': '010-5555-6666',
         'email': 'choi@tokyo-travel.com', 'status': 'inactive'},
    ]
    return render_template('admin/partner_list.html', active_page='partners', partners=partners)


@bp.route('/partners/new')
def partner_create():
    return render_template('admin/partner_create.html', active_page='partners')


@bp.route('/customers')
def customer_list():
    customers = [
        {'id': 'C-001', 'name': '홍길동', 'email': 'hong@example.com', 'phone': '010-1234-5678', 'trips': 3,
         'lastTrip': '2025-10-10', 'grade': 'VIP', 'status': 'active'},
        {'id': 'C-002', 'name': '김철수', 'email': 'kim@example.com', 'phone': '010-2345-6789', 'trips': 2,
         'lastTrip': '2025-10-15', 'grade': 'Gold', 'status': 'active'},
        {'id': 'C-003', 'name': '이영희', 'email': 'lee@example.com', 'phone': '010-3456-7890', 'trips': 1,
         'lastTrip': '2025-10-20', 'grade': '일반', 'status': 'active'},
        {'id': 'C-004', 'name': '박민수', 'email': 'park@example.com', 'phone': '010-4567-8901', 'trips': 0,
         'lastTrip': '-', 'grade': '일반', 'status': 'inactive'},
        {'id': 'C-005', 'name': '정수진', 'email': 'jung@example.com', 'phone': '010-5678-9012', 'trips': 1,
         'lastTrip': '2025-11-01', 'grade': '일반', 'status': 'active'},
    ]
    return render_template('admin/customer_list.html', active_page='customers', customers=customers)


@bp.route('/settings')
def settings_page():
    return render_template('admin/settings.html', active_page='settings')

# 채팅
admin_bp = Blueprint('chat_admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/rooms')
def route_get_rooms():
    """최종 호출 주소: /api/admin/rooms"""
    rooms = get_room_list()
    return jsonify(rooms)

@admin_bp.route('/history/<session_id>')
def route_get_history(session_id):
    """최종 호출 주소: /api/admin/history/<session_id>"""
    logs = get_chat_logs(session_id)
    return jsonify(logs)


@bp.route('/api/chat', methods=['POST'])
def chat():
    """
    관리자용 챗봇 테스트 API
    (DB 로그 저장은 스키마 수정 전까지 보류하고, RAG 답변 기능만 활성화)
    """
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'reply': '메시지를 입력해주세요.'}), 400

    try:
        # 1. RAG 검색
        retrieved_products = search_best_products(user_message, top_k=3)

        # 2. AI 답변 생성
        ai_reply = generate_answer(user_message, retrieved_products)

        # [참고] 관리자 모드이므로 검색된 근거(소스)도 같이 보여주면 좋음 (선택사항)
        sources = [p['product_name'] for p in retrieved_products]

        return jsonify({
            'reply': ai_reply,
            'sources': sources
        })

    except Exception as e:
        print(f"❌ [Admin Chat Error] {e}")
        return jsonify({'reply': '에러가 발생했습니다.'}), 500

