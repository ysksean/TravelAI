import os
from flask import Flask, redirect, url_for, render_template, jsonify
from flask_socketio import SocketIO
import threading

# [1] 모델 및 DB 관련 임포트 (SQLAlchemy)
from models import db
from services.db_connect import DB_USER, DB_PASS_RAW, DB_HOST, DB_NAME

# [2] 라우트(Blueprints) 임포트
# 기존 라우트
from routes.admin_routes import bp as erp_admin_bp  # 기존 ERP 관리자 페이지
from routes.customer_routes import bp as customer_bp
from routes.product_routes import product_bp
# [NEW] 채팅 전용 관리자 API (아까 만든 routes/admin_route.py)
from routes.admin_routes import admin_bp as chat_api_bp

# [3] 소켓 & 카프카 임포트
from events import register_socket_events
from services.kafka_service import kafka_consumer_worker
from services.chat_service import get_chat_logs

app = Flask(__name__)

# ==========================================
# 1. Config 설정 (SQLAlchemy + Secret)
# ==========================================
app.secret_key = os.urandom(24)
app.config['JSON_AS_ASCII'] = False

# [중요] 기존 db_connect 변수를 활용해 SQLAlchemy 접속 주소 생성
# 형식: mysql+pymysql://USER:PASSWORD@HOST/DB_NAME
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASS_RAW}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==========================================
# 2. 초기화 (DB, SocketIO)
# ==========================================
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*") # CORS 허용

# ==========================================
# 3. 블루프린트 등록
# ==========================================
# 기존 ERP 라우트
app.register_blueprint(erp_admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(product_bp)

# [NEW] 채팅용 API 라우트 등록 (routes/admin_route.py)
# 이 파일 안에 '/admin' prefix가 이미 있다면 겹치지 않게 주의하거나 병합 필요
# 여기서는 API 구분을 위해 별도로 등록합니다.
app.register_blueprint(chat_api_bp)

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
# 5. 에러 핸들러 및 루트 리다이렉트
# ==========================================
@app.errorhandler(404)
def page_not_found(e):
    return "404 Not Found", 404

@app.route('/')
def root():
    return redirect(url_for('customer.index'))

# [테스트용] 관리자 채팅 페이지 라우트
@app.route('/admin/test')
def admin_test_page():
    return render_template('admin_test.html')

# [테스트용] 고객 채팅 페이지
@app.route('/customer/test')
def customer_test_page():
    return render_template('customer_test.html')

# 고객용 채팅 내역 조회 API
@app.route('/api/chat/history/<session_id>')
def get_customer_chat_history(session_id):
    """
    고객이 자신의 방 ID(session_id)로 과거 대화 내역을 요청함
    """
    try:
        # 서비스 함수 호출 (DB에서 조회)
        logs = get_chat_logs(session_id)
        return jsonify(logs)
    except Exception as e:
        print(f"❌ History Error: {e}")
        return jsonify([]), 500

# ==========================================
# 6. 서버 실행 (Entry Point)
# ==========================================
if __name__ == '__main__':
    with app.app_context():
        # [중요] models.py에 정의된 테이블(chat_rooms, chat_logs) 자동 생성
        # 기존 테이블이 있다면 무시됨
        db.create_all()
        print("✅ DB Tables checked/created.")

        # Kafka Consumer 시작
        socketio.start_background_task(kafka_consumer_worker, socketio)

    print("\n" + "=" * 50)
    print("🚀 Chat & ERP Server Starting...")
    print("=" * 50)
    print("📍 ERP Admin:     http://localhost:7878/admin")
    print("📍 Customer:      http://localhost:7878/customer")
    print("📍 Chat Socket:   ws://localhost:7878")
    print("=" * 50 + "\n")

    # [중요] app.run() 대신 socketio.run() 사용!
    socketio.run(app, host='0.0.0.0', port=7878, debug=True, allow_unsafe_werkzeug=True)