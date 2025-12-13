# flask_web/seed_db.py
import sys
import os
import json
import random
from datetime import datetime, timedelta

# 프로젝트 루트 경로 설정 (flask_web 폴더 안에서 실행된다고 가정)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from services.db_connect import SessionLocal
    from schema.schema import ProductTable
except ImportError:
    # 상위 경로에서 모듈을 찾을 수 있도록 추가 설정
    sys.path.append(os.path.dirname(current_dir))
    from services.db_connect import SessionLocal
    from schema.schema import ProductTable

# --- 데이터 소스 (국가별 도시 및 리얼한 호텔/골프장) ---
DATA_SOURCE = {
    "일본": {
        "cities": ["도쿄", "오사카", "후쿠오카", "오키나와", "삿포로"],
        "hotels": {
            "도쿄": ["도쿄 프린스 호텔", "게이오 플라자 호텔", "신주쿠 워싱턴 호텔", "호텔 그레이서리 신주쿠"],
            "오사카": ["호텔 뉴 오타니 오사카", "리가 로얄 호텔", "오사카 메리어트 미야코", "스위소텔 난카이"],
            "후쿠오카": ["힐튼 후쿠오카 씨호크", "호텔 닛코 후쿠오카", "그랜드 하얏트 후쿠오카"],
            "오키나와": ["하얏트 리젠시 세라가키", "힐튼 오키나와 차탄", "류큐 호텔 & 리조트"],
            "삿포로": ["삿포로 그랜드 호텔", "JR 타워 호텔 닛코", "머큐어 삿포로"]
        },
        "golf_courses": {
            "도쿄": ["와카스 골프 링크스", "도쿄 요미우리 C.C", "사야마 골프 클럽"],
            "오사카": ["이바라키 춘추 골프 클럽", "오사카 골프 클럽", "한나 골프 클럽"],
            "후쿠오카": ["후쿠오카 센추리 골프 클럽", "키야 골프 클럽", "코가 골프 클럽"],
            "오키나와": ["PGM 골프 리조트 오키나와", "팜 힐스 골프 리조트", "카누차 골프 코스"],
            "삿포로": ["홋카이도 클래식 골프 클럽", "삿포로 국제 C.C", "해피 밸리 골프 클럽"]
        }
    },
    "베트남": {
        "cities": ["다낭", "나트랑", "하노이", "호치민", "푸꾸옥"],
        "hotels": {
            "다낭": ["하얏트 리젠시 다낭", "빈펄 럭셔리 다낭", "퓨전 마이아 리조트", "인터컨티넨탈 다낭"],
            "나트랑": ["아미아나 리조트", "빈펄 리조트 나트랑", "식스센스 닌반베이"],
            "하노이": ["소피텔 레전드 메트로폴", "롯데 호텔 하노이", "JW 메리어트 하노이"],
            "호치민": ["파크 하얏트 사이공", "카라벨 사이공", "르 메르디앙 사이공"],
            "푸꾸옥": ["JW 메리어트 푸꾸옥", "빈펄 리조트 & 스파", "인터컨티넨탈 푸꾸옥"]
        },
        "golf_courses": {
            "다낭": ["다낭 C.C", "몽고메리 링크스", "바나힐 골프 클럽", "호이아나 쇼어스"],
            "나트랑": ["빈펄 골프 나트랑", "다이아몬드 베이 골프", "KN 골프 링크스"],
            "하노이": ["킹스 아일랜드 골프", "반트리 골프 클럽", "스카이 레이크 리조트"],
            "호치민": ["탄손냑 골프 코스", "롱탄 골프 클럽", "트윈 도브스 골프"],
            "푸꾸옥": ["빈펄 골프 푸꾸옥"]
        }
    },
    "태국": {
        "cities": ["방콕", "파타야", "치앙마이", "푸켓"],
        "hotels": {
            "방콕": ["만다린 오리엔탈 방콕", "시암 켐핀스키", "반얀트리 방콕", "샹그릴라 방콕"],
            "파타야": ["힐튼 파타야", "두짓 타니 파타야", "케이프 다라 리조트"],
            "치앙마이": ["포시즌스 리조트 치앙마이", "샹그릴라 치앙마이", "아난타라 치앙마이"],
            "푸켓": ["반얀트리 푸켓", "아만푸리", "JW 메리어트 푸켓"]
        },
        "golf_courses": {
            "방콕": ["알파인 골프 클럽", "타이 C.C", "니칸티 골프 클럽"],
            "파타야": ["시암 C.C", "램차방 인터내셔널", "치찬 골프 리조트"],
            "치앙마이": ["알파인 골프 리조트", "하이랜드 골프 앤 스파", "서밋 그린 밸리"],
            "푸켓": ["블루 캐년 C.C", "레드 마운틴 골프 클럽", "라구나 골프 푸켓"]
        }
    },
    "필리핀": {
        "cities": ["마닐라", "클락", "세부", "보라카이"],
        "hotels": {
            "마닐라": ["오카다 마닐라", "소피텔 필리핀 플라자", "콘래드 마닐라"],
            "클락": ["스위소텔 클락", "메리어트 클락", "미도리 클락 호텔"],
            "세부": ["샹그릴라 막탄", "크림슨 리조트", "제이파크 아일랜드"],
            "보라카이": ["헤난 크리스탈 샌즈", "디스커버리 쇼어", "샹그릴라 보라카이"]
        },
        "golf_courses": {
            "마닐라": ["마닐라 사우스우즈", "오차드 골프 클럽", "셔우드 힐스"],
            "클락": ["미모사 골프 코스", "썬밸리 C.C", "루이시타 골프 클럽"],
            "세부": ["세부 C.C", "알타 비스타", "클럽 필리피노"],
            "보라카이": ["페어웨이 앤 블루워터"]
        }
    }
}

IMAGES = [
    "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?auto=format&fit=crop&q=80&w=800",  # 골프
    "https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?auto=format&fit=crop&q=80&w=800",  # 리조트
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=800",  # 호텔 로비
    "https://images.unsplash.com/photo-1523580494863-6f3031224c94?auto=format&fit=crop&q=80&w=800",  # 야경
    "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&q=80&w=800"  # 관광지
]


def get_random_date():
    """오늘부터 6개월 이내의 랜덤한 날짜 반환 (문자열)"""
    start_date = datetime.now() + timedelta(days=random.randint(7, 180))
    return start_date


def create_product_json(index):
    # 1. 랜덤 국가 및 도시 선택
    country = random.choice(list(DATA_SOURCE.keys()))
    city = random.choice(DATA_SOURCE[country]["cities"])

    # 2. 일정 기간 랜덤 설정 (2박3일 ~ 4박5일)
    nights = random.choice([2, 3, 4])
    days = nights + 1
    duration_str = f"{nights}박 {days}일"

    # 3. 날짜 설정
    start_dt = get_random_date()
    end_dt = start_dt + timedelta(days=days - 1)

    # 4. 리소스 선택 (호텔, 골프장)
    hotel_name = random.choice(DATA_SOURCE[country]["hotels"].get(city, [f"{city} 시티 호텔"]))
    # 골프장이 없는 도시(예: 보라카이 일부)는 관광 상품으로 전환하거나 기본값 사용
    golf_list = DATA_SOURCE[country]["golf_courses"].get(city, [])
    is_golf_package = len(golf_list) > 0 and random.random() > 0.2  # 80% 확률로 골프 패키지

    product_name = f"[{country}] {city} {hotel_name} {duration_str}"
    if is_golf_package:
        product_name += " 명품 골프 투어"
        product_type = "golf"
    else:
        product_name += " 힐링 휴양 패키지"
        product_type = "tour"

    price = random.randint(50, 300) * 10000  # 50만 ~ 300만

    # 5. JSON 구조 생성
    product_data = {
        "meta": {
            "status": "published" if random.random() > 0.3 else "draft",
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source_files": [f"quotation_{index:03d}.pdf"]
        },
        "info": {
            "product_name": product_name,
            "category": "overseas",
            "product_type": product_type,
            "country": country,
            "city": city,
            "departure_point": "ICN/GMP",
            "thumbnail_url": random.choice(IMAGES),
            "images": random.sample(IMAGES, 3)
        },
        "schedule": {
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "nights": nights,
            "days": days
        },
        "pricing": {
            "currency": "KRW",
            "price_adult": price,
            "price_child": int(price * 0.8),
            "price_infant": int(price * 0.1),
            "price_net": int(price * 0.7)
        },
        "details": {
            "flight_summary": f"대한항공/아시아나 인천-{city} 왕복",
            "inclusions": ["왕복 항공권", "전 일정 특급 호텔", "조식 및 석식", "여행자 보험"],
            "exclusions": ["개인 경비", "매너팁", "중식"],
            "special_notes": ["여권 유효기간 6개월 이상 필수"],
            "content_html": f"<p>{city}의 아름다운 풍경과 함께하는 럭셔리 여행입니다.</p>"
        },
        "resources": {
            "hotels": [
                {
                    "name": hotel_name,
                    "grade": "5성급",
                    "description": "최고급 시설과 서비스를 자랑하는 특급 호텔",
                    "check_in": "15:00",
                    "check_out": "11:00",
                    "website": "www.hotel-example.com",
                    "image_url": random.choice(IMAGES)
                }
            ],
            "golf_courses": []
        },
        "itinerary": []
    }

    # 골프장 리소스 추가
    if is_golf_package:
        # 일정에 따라 서로 다른 골프장 선택 (최대 3곳)
        selected_golfs = random.sample(golf_list, min(len(golf_list), nights))
        for g_name in selected_golfs:
            product_data["resources"]["golf_courses"].append({
                "name": g_name,
                "hole_info": "18홀 / 72파",
                "description": "국제 규격의 명문 코스",
                "image_url": random.choice(IMAGES)
            })

    # 상세 일정 생성
    for day in range(1, days + 1):
        day_date = start_dt + timedelta(days=day - 1)
        day_plan = {
            "day": day,
            "date": day_date.strftime("%Y-%m-%d"),
            "activities": [],
            "meals": {"breakfast": "호텔식", "lunch": "현지식", "dinner": "특식"}
        }

        if day == 1:
            day_plan["activities"].append({
                "time": "10:00", "type": "flight", "title": "인천 국제공항 출발", "description": "설레는 여행의 시작"
            })
            day_plan["activities"].append({
                "time": "14:00", "type": "transport", "title": f"{city} 공항 도착 및 이동", "description": "가이드 미팅 후 호텔로 이동"
            })
            day_plan["activities"].append({
                "time": "16:00", "type": "hotel", "title": "호텔 체크인 및 휴식", "description": "자유 시간"
            })
        elif day == days:
            day_plan["activities"].append({
                "time": "09:00", "type": "transport", "title": "호텔 체크아웃 및 공항 이동", "description": "아쉬운 작별"
            })
            day_plan["activities"].append({
                "time": "12:00", "type": "flight", "title": f"{city} 출발", "description": "인천으로 향발"
            })
        else:
            # 중간 일정 (2일차 ~ )
            if is_golf_package and (day - 2) < len(product_data["resources"]["golf_courses"]):
                golf_course = product_data["resources"]["golf_courses"][day - 2]
                day_plan["activities"].append({
                    "time": "08:00", "type": "golf", "title": f"{golf_course['name']} 18홀 라운딩",
                    "description": "쾌적한 라운딩을 즐기세요"
                })
                day_plan["activities"].append({
                    "time": "14:00", "type": "other", "title": "오후 자유 일정", "description": "스파 또는 쇼핑"
                })
            else:
                day_plan["activities"].append({
                    "time": "09:00", "type": "sightseeing", "title": f"{city} 시내 주요 명소 관광",
                    "description": "가이드와 함께하는 시티 투어"
                })

        product_data["itinerary"].append(day_plan)

    return product_data


def seed_database():
    session = SessionLocal()
    products_to_insert = []

    print("🚀 Generating 20 unique product JSONs...")

    for i in range(1, 21):
        p_data = create_product_json(i)
        products_to_insert.append(p_data)

        # DB 객체 변환 (Flattening)
        new_product = ProductTable(
            status=p_data['meta']['status'],
            product_name=p_data['info']['product_name'],
            category=p_data['info']['category'],
            product_type=p_data['info']['product_type'],
            country=p_data['info']['country'],
            city=p_data['info']['city'],
            departure_point=p_data['info']['departure_point'],

            # DB Date 타입으로 변환
            start_date=datetime.strptime(p_data['schedule']['start_date'], "%Y-%m-%d").date(),
            end_date=datetime.strptime(p_data['schedule']['end_date'], "%Y-%m-%d").date(),
            nights=p_data['schedule']['nights'],
            days=p_data['schedule']['days'],

            price_adult=p_data['pricing']['price_adult'],
            price_net=p_data['pricing']['price_net'],
            currency=p_data['pricing']['currency'],

            # JSON 컬럼
            images=p_data['info']['images'],
            details=p_data['details'],
            resources=p_data['resources'],
            itinerary=p_data['itinerary'],
            source_files=p_data['meta']['source_files'],

            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(new_product)

    try:
        session.commit()
        print(f"✅ Successfully inserted {len(products_to_insert)} products into Database.")

        # JSON 파일 저장 (확인용)
        with open("dummy_products_list.json", "w", encoding="utf-8") as f:
            json.dump(products_to_insert, f, ensure_ascii=False, indent=2)
        print("📂 Saved 'dummy_products_list.json' for reference.")

    except Exception as e:
        session.rollback()
        print(f"❌ DB Insert Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()