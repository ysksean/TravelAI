# routes/customer_routes.py
from flask import Blueprint, render_template, request, redirect, jsonify, session, url_for, flash
from sqlalchemy import desc
from werkzeug.security import check_password_hash

# [수정] SessionLocal 제거 -> models.db 사용 (통일성 유지)
from models import db

# [수정] 스키마 임포트 경로 확인
from schema.schema import ProductTable
from schema.customer_schema import Customer, Reservation
from schema.chat_schema import ChatRoom, ChatLog

# AI 서비스 모듈
from services.rag_service import search_best_products
from services.ai_service import generate_answer  # get_ai_response 필요 시 추가
from services.chat_service import save_message  # 소켓 연동용

# Blueprint 설정
bp = Blueprint('customer', __name__, template_folder='../templates/customer', static_folder='../static/customer')

# Mock Data (메인 페이지용)
mock_data = {
    "hero_slides": [],
    "products_a": [],
    "products_b": [],
    "promo": {
        "title": "특별한 여행, 특별한 가격",
        "bg_image": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80",
        "keywords": ["특가", "패키지", "자유여행"],
        "card": {
            "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "title": "보라카이 3박 5일",
            "desc": "화이트 비치에서 즐기는 꿈같은 휴가",
            "discount": "20%",
            "original_price": "890,000",
            "price": "712,000"
        }
    },
    "icons": [
        {"label": "골프여행", "icon": "fa-solid fa-golf-ball-tee"},
        {"label": "허니문", "icon": "fa-solid fa-heart"},
        {"label": "휴양지", "icon": "fa-solid fa-umbrella-beach"},
        {"label": "동남아 여행", "icon": "fa-brands fa-youtube"},
        {"label": "패키지", "icon": "fa-solid fa-suitcase"},
        {"label": "크루즈", "icon": "fa-solid fa-ship"},
        {"label": "해외숙소", "icon": "fa-solid fa-hotel"},
        {"label": "항공예약", "icon": "fa-solid fa-plane"},
        {"label": "여행의 발견", "icon": "fa-brands fa-instagram"},
        {"label": "여행 LIVE", "icon": "fa-solid fa-life-ring"}
    ]
}


@bp.route('/')
def index():
    """고객용 메인 페이지"""
    try:
        # [수정] db.session 사용 (Flask-SQLAlchemy)
        products = ProductTable.query.filter(
            ProductTable.status == 'published'
        ).order_by(desc(ProductTable.created_at)).limit(20).all()

        products_data = []
        for product in products:
            min_price = product.price_adult
            image_url = "https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"

            if product.images and isinstance(product.images, list) and len(product.images) > 0:
                image_url = product.images[0]
            elif product.details and isinstance(product.details, dict) and 'images' in product.details:
                if isinstance(product.details['images'], list) and product.details['images']:
                    image_url = product.details['images'][0]

            product_dict = {
                'id': product.id,
                'title': product.product_name,
                'price': f"{int(min_price):,}" if min_price else "문의",
                'image': image_url,
                'tags': [f"#{product.country}", f"#{product.city}"] if product.country else [],
                'country': product.country,
                'city': product.city
            }
            products_data.append(product_dict)

        data = mock_data.copy()
        if products_data:
            data['products_a'] = products_data[:4]
            data['products_b'] = products_data[4:8] if len(products_data) > 4 else products_data[4:]

        return render_template('index.html', data=data)
    except Exception as e:
        print(f"⚠️  Error loading products: {e}")
        return render_template('index.html', data=mock_data)


@bp.route('/products/<int:product_id>')
def product_detail(product_id):
    """상품 상세 페이지"""
    try:
        # [수정] db.session 사용
        product = ProductTable.query.filter(ProductTable.id == product_id).first()

        if not product or product.status != 'published':
            return render_template('includes/404.html', message="상품을 찾을 수 없습니다."), 404

        prices = []
        if product.start_date and product.price_adult:
            prices.append({
                'departure_date': product.start_date,
                'price_adult': product.price_adult,
                'status': 'available'
            })

        return render_template('includes/product_detail.html', product=product, prices=prices)
    except Exception as e:
        print(f"⚠️  Error loading product detail: {e}")
        return render_template('includes/404.html', message="오류가 발생했습니다."), 500


@bp.route('/chat', methods=['POST'])
def chat():
    """(REST API) 고객용 챗봇 - 필요 시 사용"""
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'reply': '메시지를 입력해주세요.'}), 400

    try:
        # RAG + AI 응답
        retrieved_products = search_best_products(user_message, top_k=3)
        ai_reply = generate_answer(user_message, retrieved_products)
        return jsonify({'reply': ai_reply})

    except Exception as e:
        print(f"❌ [Customer Chat Error] {e}")
        return jsonify({'reply': '죄송합니다. 잠시 후 다시 시도해주세요.'}), 500


@bp.route('/history/<session_id>')
def get_my_history(session_id):
    """
    [수정] 내 채팅 기록 가져오기
    이전 코드: ChatLog(session_id) -> 객체 생성 오류
    수정 코드: ChatLog.query.filter... -> DB 조회 정상
    """
    try:
        logs = ChatLog.query.filter_by(session_id=session_id) \
            .order_by(ChatLog.created_at.asc()).all()
        # to_dict() 메서드는 ChatLog 모델에 정의되어 있어야 함 (Step 1에서 추가함)
        return jsonify([l.to_dict() for l in logs])
    except Exception as e:
        print(f"History Error: {e}")
        return jsonify([])


# [NEW] Step 5: 결제 처리 API 추가
@bp.route('/pay', methods=['POST'])
def process_payment():
    """결제 버튼 클릭 시 처리"""
    data = request.get_json()
    reservation_id = data.get('reservation_id')

    if not reservation_id:
        return jsonify({'success': False, 'message': '잘못된 요청입니다.'}), 400

    try:
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'message': '예약 정보를 찾을 수 없습니다.'}), 404

        # 상태 변경
        reservation.booking_status = '결제완료'
        db.session.commit()

        # 채팅방 알림은 소켓(events.py) 혹은 클라이언트 측 처리에 맡김
        # 여기서는 성공 여부만 리턴

        # (선택) 여기서도 AI 메시지를 DB에 미리 넣어둘 수 있음
        success_msg = "✅ 결제가 정상적으로 완료되었습니다.<br>설레는 여행 되시길 바랍니다! ^^"
        if reservation.customer:
            save_message(reservation.customer.user_id, 'ai', success_msg, 'Travel AI')

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        print(f"Payment Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        customer = Customer.query.filter_by(user_id=user_id).first()

        if customer and check_password_hash(customer.password_hash, password):
            session['user_id'] = customer.user_id
            session['user_name'] = customer.name
            session['role'] = 'customer'
            return redirect(url_for('customer.index'))
        else:
            flash('아이디 또는 비밀번호가 일치하지 않습니다.')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('customer.index'))