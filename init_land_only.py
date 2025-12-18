import random
from app import app
from models import db
# 새로 만든 랜드사 스키마만 임포트
from schema.land_schema import LandOperator, LandChatRoom, LandChatLog
from werkzeug.security import generate_password_hash


def init_land_db():
    with app.app_context():
        print("🏗️  랜드사 관련 테이블 생성 중...")

        # 1. 없는 테이블만 생성 (기존 Customer, Product 등은 건드리지 않음)
        db.create_all()
        print("✅ 테이블 스키마 확인 완료.")

        # 2. 랜드사 더미 데이터 확인 및 생성
        print("🏢  랜드사 더미 데이터 확인 중...")

        lands = [
            ("land_vn", "베트남 투어", "다낭/나트랑"),
            ("land_jp", "재팬 고고", "오사카/도쿄"),
            ("land_th", "타이 랜드", "방콕/파타야"),
            ("land_eu", "유로 프렌즈", "파리/로마"),
            ("land_us", "아메리카 드림", "하와이/괌")
        ]

        added_count = 0
        for lid, lname, lregion in lands:
            # 이미 존재하는지 확인 (중복 생성 방지)
            existing = LandOperator.query.filter_by(user_id=lid).first()

            if not existing:
                land_op = LandOperator(
                    user_id=lid,
                    password_hash=generate_password_hash("1234"),
                    name=lname,
                    region=lregion,
                    contact=f"070-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
                )
                db.session.add(land_op)
                added_count += 1
                print(f"   + 추가됨: {lname} ({lid})")
            else:
                print(f"   - 이미 존재함: {lname}")

        if added_count > 0:
            db.session.commit()
            print(f"✅  총 {added_count}개의 랜드사 계정이 새로 생성되었습니다.")
        else:
            print("✅  새로 추가된 계정이 없습니다.")

        print("👉  테스트 계정: land_vn / 1234")


if __name__ == "__main__":
    init_land_db()