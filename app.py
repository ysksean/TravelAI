import os
import threading
from flask import Flask, redirect, url_for, render_template, jsonify
from flask_socketio import SocketIO

# [1] 모델 및 DB 관련 임포트
from models import db
from services.db_connect import DB_USER, DB_PASS_RAW, DB_HOST, DB_NAME

# [2] 스키마 임포트 (create_all 및 쿼리용) - 경로 수정됨
from schema.chat_schema import ChatRoom, ChatLog
from schema.customer_schema import Customer, Reservation
from schema.land_schema import LandChatRoom, LandChatLog
from schema.schema import ProductTable

# [3] 라우트(Blueprints) 임포트
# admin_routes 하나로 통합되었으므로 하나만 가져옵니다.
from routes.admin_routes import bp as admin_bp
from routes.customer_routes import bp as customer_bp
from routes.product_routes import product_bp
from routes.land_routes import bp as land_bp

# [4] 소켓 & 카프카 임포트
from events import register_socket_events
from services.kafka_service import kafka_consumer_worker

app = Flask(__name__)

# ==========================================
# 1. Config 설정
# ==========================================
app.secret_key = os.urandom(24)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASS_RAW}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==========================================
# 2. 초기화
# ==========================================
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ==========================================
# 3. 블루프린트 등록
# ==========================================
# 통합된 관리자 라우트 (채팅 API + ERP 페이지 포함)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(product_bp)
app.register_blueprint(land_bp) # 랜드사 라우트

# ==========================================
# 4. 소켓 이벤트 및 Kafka 설정
# ==========================================
register_socket_events(socketio)

def start_kafka_thread():
    """Kafka Consumer를 백그라운드 스레드로 실행"""
    t = threading.Thread(target=kafka_consumer_worker, args=(socketio,))
    t.daemon = True
    t.start()

# ==========================================
# 5. 에러 핸들러 및 기타 라우트
# ==========================================
@app.errorhandler(404)
def page_not_found(e):
    return "404 Not Found", 404

@app.route('/')
def root():
    return redirect(url_for('customer.index'))

# [API] 고객용 채팅 내역 조회
@app.route('/api/chat/history/<session_id>')
def get_customer_chat_history(session_id):
    """
    고객이 자신의 방 ID(session_id)로 과거 대화 내역을 요청함
    """
    try:
        # [수정] get_chat_logs 함수 대신 모델 직접 쿼리 (Import 오류 방지)
        logs = ChatLog.query.filter_by(session_id=session_id)\
                .order_by(ChatLog.created_at.asc()).all()
        return jsonify([l.to_dict() for l in logs])
    except Exception as e:
        print(f"❌ History Error: {e}")
        return jsonify([]), 500

# ==========================================
# 6. 서버 실행
# ==========================================
if __name__ == '__main__':
    with app.app_context():
        # 정의된 모든 테이블 생성 (schema 폴더 내 모델들)
        db.create_all()
        print("✅ DB Tables checked/created.")

        # Kafka Consumer 백그라운드 실행
        socketio.start_background_task(kafka_consumer_worker, socketio)

    print("\n" + "=" * 50)
    print("🚀 Chat & ERP Server Starting...")
    print("=" * 50)
    print("📍 Admin:         http://localhost:7878/admin")
    print("📍 Customer:      http://localhost:7878/customer")
    print("📍 Chat Socket:   ws://localhost:7878")
    print("=" * 50 + "\n")

    socketio.run(app, host='0.0.0.0', port=7878, debug=True, allow_unsafe_werkzeug=True)