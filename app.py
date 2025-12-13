# app.py
from flask import Flask, redirect, url_for
from services.db_connect import engine
# [수정] models 모듈 제거 (존재하지 않음), 대신 schema에서 Base 가져오기
# from models import init_db
from schema.schema import Base
from routes.admin_routes import bp as admin_bp
from routes.customer_routes import bp as customer_bp
from routes.product_routes import product_bp
import os

app = Flask(__name__)

# Config (Optional)
app.secret_key = os.urandom(24)
app.config['JSON_AS_ASCII'] = False

# Register Blueprints
# admin은 /admin으로, customer는 /customer로 시작하도록 설정
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/customer')
# [추가] Product API 등록
app.register_blueprint(product_bp)


# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return "404 Not Found", 404


# Root Route -> Redirect to Customer or Admin?
@app.route('/')
def root():
    # Redirect to customer main by default
    return redirect(url_for('customer.index'))


def init_db():
    """
    DB 테이블 생성 함수
    schema.py에 정의된 모델들을 바탕으로 테이블을 생성합니다.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully.")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")


if __name__ == '__main__':
    # Initialize DB
    init_db()

    print("\n" + "=" * 50)
    print("🚀 Flask Application Starting...")
    print("=" * 50)
    print("📍 ERP (Admin): http://localhost:7878/admin")
    print("📍 Customer:    http://localhost:7878/customer")
    print("📍 Product API: http://localhost:7878/api/products (POST)")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=7878, debug=True)