# flask_web/routes/product_routes.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from services.db_connect import SessionLocal
from schema.schema import ProductMasterJSON, ProductTable
import traceback
import json
import sys  # [추가] 로그 강제 출력을 위한 모듈
# RAG 서비스 함수 임포트
from services.rag_service import add_product_to_vector_db
product_bp = Blueprint('product_bp', __name__)


@product_bp.route('/api/products', methods=['POST'])
def create_product():
    """
    상품 JSON 데이터를 받아 DB에 저장하는 API
    """
    # [디버깅] API 호출 즉시 로그 출력 (flush=True로 버퍼링 방지)
    print("\n" + "=" * 50, file=sys.stdout)
    print("🔥 [API CALL] /api/products 요청이 서버에 도달했습니다!", file=sys.stdout, flush=True)

    session = SessionLocal()
    try:
        # 1. 요청 데이터 확인 (안전한 JSON 파싱)
        data = request.get_json(silent=True)
        if not data:
            print("❌ [API Error] JSON 데이터가 없거나 파싱할 수 없습니다.", file=sys.stdout, flush=True)
            return jsonify({"status": "error", "message": "No data provided or Invalid JSON"}), 400

        print(f"📩 [API Debug] Received Data Keys: {list(data.keys())}", file=sys.stdout, flush=True)

        # 2. Pydantic 검증 및 파싱
        try:
            validated_data = ProductMasterJSON(**data)

            # [디버깅] 파싱된 데이터 값 확인
            print(f"✅ [API Debug] Pydantic Validation Passed!", file=sys.stdout, flush=True)
            print(f"   - Name: {validated_data.info.product_name}", file=sys.stdout, flush=True)
            print(f"   - Price: {validated_data.pricing.price_adult}", file=sys.stdout, flush=True)

        except Exception as e:
            print(f"❌ [API Error] Validation Failed: {e}", file=sys.stdout, flush=True)
            return jsonify({"status": "error", "message": f"Validation Error: {str(e)}"}), 400

        # 3. Pydantic -> Dict 변환 헬퍼 (JSON 컬럼용)
        def to_dict(model_obj):
            if hasattr(model_obj, 'model_dump'):
                return model_obj.model_dump(mode='json')  # v2
            if hasattr(model_obj, 'dict'):
                return model_obj.dict()  # v1
            return model_obj

            # 4. DB 모델 매핑

        new_product = ProductTable(
            # 기본 정보 매핑
            status=validated_data.meta.status,
            product_name=validated_data.info.product_name,
            category=validated_data.info.category,
            product_type=validated_data.info.product_type,
            country=validated_data.info.country,
            city=validated_data.info.city,
            departure_point=validated_data.info.departure_point,

            # 일정 매핑
            start_date=validated_data.schedule.start_date,
            end_date=validated_data.schedule.end_date,
            nights=validated_data.schedule.nights,
            days=validated_data.schedule.days,

            # 가격 매핑
            price_adult=validated_data.pricing.price_adult,
            price_net=validated_data.pricing.price_net,
            currency=validated_data.pricing.currency,

            # JSON 컬럼 매핑 (딕셔너리 변환)
            images=validated_data.info.images if validated_data.info.images else [],
            details=to_dict(validated_data.details),
            resources=to_dict(validated_data.resources),
            itinerary=[to_dict(day) for day in validated_data.itinerary],
            source_files=validated_data.meta.source_files,

            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        print(f"🛠 [API Debug] DB Object Created. Saving...", file=sys.stdout, flush=True)

        # 5. DB 저장
        session.add(new_product)
        session.commit()
        session.refresh(new_product)

        print(f"🎉 [API Success] DB Inserted! ID: {new_product.id}", file=sys.stdout, flush=True)

        # ==========================================================
        # [추가 2] RAG 벡터 DB 업데이트 로직
        # ==========================================================
        print(f"🤖 [RAG] 벡터 DB 업데이트 시작...", file=sys.stdout, flush=True)
        try:
            # Pydantic 모델을 딕셔너리로 변환하여 서비스에 전달
            product_dict = validated_data.model_dump(mode='json') if hasattr(validated_data,
                                                                             'model_dump') else validated_data.dict()
            add_product_to_vector_db(product_dict)
        except Exception as rag_error:
            # RAG 실패가 DB 저장을 취소시키지 않도록 예외 처리만 하고 로그 남김
            print(f"⚠️ [RAG Error] 벡터 DB 업데이트 중 오류 발생 (DB 저장은 성공함): {rag_error}", file=sys.stdout, flush=True)

        print("=" * 50 + "\n", file=sys.stdout)

        return jsonify({
            "status": "success",
            "message": "Product saved successfully",
            "product_id": new_product.id
        }), 201

    except Exception as e:
        session.rollback()
        print(f"❌ [API Critical Error]: {e}", file=sys.stdout, flush=True)
        # 파이참 콘솔에 전체 에러 스택 트레이스 출력
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        session.close()