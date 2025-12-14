# routes/customer_routes.py
from flask import Blueprint, render_template, request, jsonify
from services.db_connect import SessionLocal
# [수정] models 모듈 제거 -> schema.py 사용
from schema.schema import ProductTable
from sqlalchemy import desc, or_, func
import os
import re

# [핵심] 우리가 만든 서비스 모듈 임포트
from services.rag_service import search_best_products
from services.ai_service import generate_answer

# Blueprint 설정
bp = Blueprint('customer', __name__, template_folder='../templates/customer', static_folder='../static/customer')

# RAG 엔진 임포트 (전역 변수로 사용하거나 함수 내에서 호출)
try:
    from services.rag_service import rag_engine
except ImportError:
    rag_engine = None

import google.generativeai as genai

# Note: GenAI config should be in app.py or a config block, but doing it here locally if needed or assuming initialized env.

# Mock Data (간소화하여 유지)
mock_data = {
    # ... (생략된 mock data 내용, 필요하면 복원하거나 DB 사용 권장)
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
    """
    고객용 메인 페이지 - /customer/
    """
    try:
        db = SessionLocal()
        try:
            # published 상태인 상품만 조회
            # [수정] Product -> ProductTable
            products = db.query(ProductTable).filter(
                ProductTable.status == 'published'
            ).order_by(desc(ProductTable.created_at)).limit(20).all()

            products_data = []
            for product in products:
                # [수정] 가격 로직 변경 (ProductTable에 직접 price_adult 존재)
                min_price = product.price_adult

                # [수정] 이미지 로직 변경 (details JSON 필드가 아닌 images 컬럼 사용)
                image_url = "https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"

                # 1. images 컬럼 확인 (JSON List)
                if product.images and isinstance(product.images, list) and len(product.images) > 0:
                    image_url = product.images[0]
                # 2. Fallback: details JSON 확인
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

            # 템플릿 경로: index.html (relative)
            return render_template('index.html', data=data)
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️  Error loading products: {e}")
        # import traceback; traceback.print_exc()
        return render_template('index.html', data=mock_data)


@bp.route('/products/<int:product_id>')
def product_detail(product_id):
    """
    상품 상세 페이지 - /customer/products/<id>
    """
    try:
        db = SessionLocal()
        try:
            # [수정] Product -> ProductTable
            product = db.query(ProductTable).filter(ProductTable.id == product_id).first()
            if not product or product.status != 'published':
                return render_template('includes/404.html', message="상품을 찾을 수 없습니다."), 404

            # [수정] 가격/출발일 정보 구성 (ProductPrice 테이블 없음 -> ProductTable 정보 활용)
            # 기존 템플릿이 prices 리스트를 순회한다고 가정하고, 단일 출발일 정보를 리스트로 만듦
            prices = []
            if product.start_date and product.price_adult:
                prices.append({
                    'departure_date': product.start_date,  # date 객체
                    'price_adult': product.price_adult,
                    'status': 'available'
                })

            return render_template('includes/product_detail.html', product=product, prices=prices)
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️  Error loading product detail: {e}")
        # Mock Product for fallback
        mock_product = type('obj', (object,), {
            'product_name': '보라카이 3박 5일 (Mock)',
            'country': '필리핀',
            'city': '보라카이',
            'nights': 3,
            'days': 5,
            'details': {'content_html': '이것은 DB 오류 시 보여지는 예시 상품입니다.',
                        'images': ['https://images.unsplash.com/photo-1540206351-d6465b3ac5c1']},
            'images': ['https://images.unsplash.com/photo-1540206351-d6465b3ac5c1']
        })
        mock_prices = []
        return render_template('includes/product_detail.html', product=mock_product, prices=mock_prices)


@bp.route('/chat', methods=['POST'])
def chat():
    """
    고객용 챗봇 API
    """
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'reply': '메시지를 입력해주세요.'}), 400

    try:
        # 1. RAG 검색 (우리가 만든 함수 호출)
        # top_k=3 : 가장 연관성 높은 상품 3개 검색
        retrieved_products = search_best_products(user_message, top_k=3)

        # 2. AI 답변 생성 (우리가 만든 함수 호출)
        # 검색된 상품 정보를 바탕으로 Gemini가 답변
        ai_reply = generate_answer(user_message, retrieved_products)

        return jsonify({'reply': ai_reply})

    except Exception as e:
        print(f"❌ [Customer Chat Error] {e}")
        return jsonify({'reply': '죄송합니다. 잠시 후 다시 시도해주세요.'}), 500