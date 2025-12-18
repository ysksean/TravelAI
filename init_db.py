import random
from app import app
from schema.chat_schema import ChatRoom, ChatLog
# [중요] 지울 테이블의 모델들을 임포트
from schema.customer_schema import Customer, Reservation

from werkzeug.security import generate_password_hash
import uuid


def init_database():
    with app.app_context():
        # 1. 특정 테이블만 순서대로 삭제 (자식 테이블 -> 부모 테이블 순서)
        # Products 테이블은 건드리지 않음!
        print("🗑️  채팅 및 고객 데이터 초기화 중...")

        try:
            # 외래키 의존성 때문에 삭제 순서가 중요합니다.
            ChatLog.__table__.drop(db.engine)  # 1. 채팅 로그 삭제
            ChatRoom.__table__.drop(db.engine)  # 2. 채팅방 삭제
            Reservation.__table__.drop(db.engine)  # 3. 예약 내역 삭제
            Customer.__table__.drop(db.engine)  # 4. 고객 정보 삭제
            print("✅ 기존 채팅/고객 테이블 삭제 완료")
        except Exception as e:
            print(f"⚠️ 테이블 삭제 중 경고(첫 실행 시 무시 가능): {e}")

        # 2. 테이블 다시 생성 (삭제된 것만 재생성됨)
        print("✨  테이블 스키마 업데이트 중...")
        db.create_all()

        # 3. 더미 고객 데이터 생성 (20명)
        print("📝  더미 고객 데이터 생성 중...")

        names = ["김철수", "이영희", "박민수", "정수진", "최동훈", "강지영", "윤서준", "장미란", "임재범", "한소희",
                 "오지호", "신민아", "송중기", "전지현", "황정민", "김혜수", "박서준", "아이유", "유재석", "강호동"]

        customers = []
        for i, name in enumerate(names):
            user_id = f"user{i + 1:02d}"  # user01, user02 ...
            pw = "1234"

            customer = Customer(
                user_id=user_id,
                password_hash=generate_password_hash(pw),
                salt="dummy_salt",
                name=name,
                phone=f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                email=f"{user_id}@example.com",
                gender=random.choice(['M', 'F']),
                user_type='VIP' if i < 5 else 'General',
                internal_uid=str(uuid.uuid4())
            )
            customers.append(customer)

        db.session.add_all(customers)
        db.session.commit()
        print(f"✅  총 {len(customers)}명의 고객 데이터가 생성되었습니다.")
        print("👉  테스트 계정: user01 / 1234")


if __name__ == "__main__":
    init_database()