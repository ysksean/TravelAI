# flask_web/seed_db_100.py
import sys
import os
import json
import random
from datetime import datetime, timedelta

# 프로젝트 루트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from services.db_connect import SessionLocal
    from schema.schema import ProductTable
    # RAG 서비스 임포트
    from services.rag_service import add_product_to_vector_db
except ImportError:
    sys.path.append(os.path.dirname(current_dir))
    from services.db_connect import SessionLocal
    from schema.schema import ProductTable
    from services.rag_service import add_product_to_vector_db

# --- [확장된] 데이터 소스 (전 세계 주요 관광지) ---
DATA_SOURCE = {
    "일본": {
        "cities": ["도쿄", "오사카", "후쿠오카", "오키나와", "삿포로", "교토"],
        "hotels": {
            "도쿄": ["도쿄 프린스 호텔", "게이오 플라자", "신주쿠 워싱턴", "안다즈 도쿄"],
            "오사카": ["호텔 뉴 오타니", "리가 로얄 호텔", "콘래드 오사카", "스위소텔 난카이"],
            "후쿠오카": ["힐튼 씨호크", "호텔 닛코", "그랜드 하얏트", "미야코 호텔"],
            "오키나와": ["하얏트 리젠시 세라가키", "힐튼 차탄", "할레쿨라니 오키나와"],
            "삿포로": ["삿포로 그랜드", "JR 타워 닛코", "머큐어 삿포로"],
            "교토": ["포시즌스 교토", "리츠칼튼 교토", "교토 100년 료칸"]
        },
        "golf_courses": {
            "도쿄": ["와카스 골프 링크스", "도쿄 요미우리 C.C"],
            "오사카": ["이바라키 춘추 C.C", "오사카 골프 클럽"],
            "후쿠오카": ["센추리 골프 클럽", "코가 골프 클럽"],
            "오키나와": ["PGM 골프 리조트", "카누차 베이 C.C"],
            "삿포로": ["홋카이도 클래식 C.C", "니도무 클래식"],
            "교토": ["세타 골프 코스"]
        }
    },
    "베트남": {
        "cities": ["다낭", "나트랑", "푸꾸옥", "하노이", "호치민", "달랏"],
        "hotels": {
            "다낭": ["하얏트 리젠시", "빈펄 럭셔리", "인터컨티넨탈", "퓨전 마이아"],
            "나트랑": ["아미아나 리조트", "식스센스 닌반베이", "빈펄 리조트"],
            "푸꾸옥": ["JW 메리어트", "빈펄 디스커버리", "뉴월드 리조트"],
            "하노이": ["소피텔 레전드", "롯데 호텔 하노이", "인터컨티넨탈 랜드마크"],
            "호치민": ["파크 하얏트 사이공", "르 메르디앙", "쉐라톤 사이공"],
            "달랏": ["달랏 팰리스", "아나 만다라 빌라", "테라코타 리조트"]
        },
        "golf_courses": {
            "다낭": ["다낭 C.C", "몽고메리 링크스", "바나힐 G.C"],
            "나트랑": ["빈펄 골프 나트랑", "KN 골프 링크스"],
            "푸꾸옥": ["빈펄 골프 푸꾸옥"],
            "하노이": ["킹스 아일랜드", "스카이 레이크"],
            "호치민": ["탄손냑 G.C", "트윈 도브스"],
            "달랏": ["달랏 팰리스 G.C", "삼 뚜옌 람 G.C"]
        }
    },
    "태국": {
        "cities": ["방콕", "파타야", "치앙마이", "푸켓", "코사무이"],
        "hotels": {
            "방콕": ["만다린 오리엔탈", "시암 켐핀스키", "반얀트리", "페닌슐라"],
            "파타야": ["힐튼 파타야", "두짓 타니", "케이프 다라"],
            "치앙마이": ["포시즌스 리조트", "샹그릴라", "라야 헤리티지"],
            "푸켓": ["반얀트리 푸켓", "아만푸리", "트리스라"],
            "코사무이": ["W 코사무이", "콘래드 코사무이", "식스센스 사무이"]
        },
        "golf_courses": {
            "방콕": ["알파인 G.C", "타이 C.C", "나와타니"],
            "파타야": ["시암 C.C", "람차방 인터내셔널"],
            "치앙마이": ["하이랜드 G.C", "알파인 리조트"],
            "푸켓": ["블루 캐년 C.C", "레드 마운틴"],
            "코사무이": ["산티บุรี 사무이 C.C"]
        }
    },
    "유럽": {
        "cities": ["파리", "로마", "인터라켄", "바르셀로나", "런던", "프라하"],
        "hotels": {
            "파리": ["리츠 파리", "풀만 타워 에펠", "하얏트 리젠시 에투알"],
            "로마": ["세인트 레지스 로마", "호텔 아르테미데", "카발리에리 월도프"],
            "인터라켄": ["빅토리아 융프라우", "호텔 인터라켄", "린드너 그랜드"],
            "바르셀로나": ["W 바르셀로나", "아츠 호텔", "마제스틱 호텔"],
            "런던": ["더 사보이", "더 리츠 런던", "샹그릴라 더 샤드"],
            "프라하": ["포시즌스 프라하", "힐튼 프라하", "그랜드 호텔 보헤미아"]
        },
        "golf_courses": {
            "파리": ["르 골프 내셔널"],
            "로마": ["마르코 시모네 G.C"],
            "인터라켄": ["인터라켄 운터젠 G.C"],
            "바르셀로나": ["PGA 카탈루냐"],
            "런던": ["웬트워스 클럽"],
            "프라하": ["알바트로스 골프 리조트"]
        }
    },
    "미주/대양주": {
        "cities": ["하와이", "괌", "사이판", "시드니", "뉴욕"],
        "hotels": {
            "하와이": ["쉐라톤 와이키키", "할레쿨라니", "힐튼 하와이안 빌리지"],
            "괌": ["두짓타니 괌", "츠바키 타워", "PIC 괌"],
            "사이판": ["켄싱턴 호텔", "월드 리조트", "하얏트 리젠시"],
            "시드니": ["샹그릴라 시드니", "파크 하얏트", "포시즌스"],
            "뉴욕": ["더 플라자", "롯데 뉴욕 팰리스", "세인트 레지스"]
        },
        "golf_courses": {
            "하와이": ["코올리나 G.C", "터틀베이 리조트"],
            "괌": ["망길라오 G.C", "레오팔레스"],
            "사이판": ["라오라오 베이"],
            "시드니": ["로얄 시드니 G.C"],
            "뉴욕": ["베스페이지 블랙"]
        }
    },
    "중화권": {
        "cities": ["타이베이", "가오슝", "홍콩", "마카오"],
        "hotels": {
            "타이베이": ["만다린 오리엔탈", "W 타이베이", "그랜드 하얏트"],
            "가오슝": ["그랜드 하이라이", "실크스 클럽"],
            "홍콩": ["페닌슐라 홍콩", "리츠칼튼 홍콩", "포시즌스"],
            "마카오": ["베네시안 마카오", "갤럭시 호텔", "윈 팰리스"]
        },
        "golf_courses": {
            "타이베이": ["미라마 G.C"],
            "가오슝": ["신이 G.C"],
            "홍콩": ["홍콩 골프 클럽"],
            "마카오": ["마카오 골프 앤 컨트리 클럽"]
        }
    }
}

IMAGES = [
    "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?auto=format&fit=crop&q=80&w=800",  # 골프
    "https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?auto=format&fit=crop&q=80&w=800",  # 리조트
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=800",  # 호텔 로비
    "https://images.unsplash.com/photo-1523580494863-6f3031224c94?auto=format&fit=crop&q=80&w=800",  # 야경
    "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&q=80&w=800",  # 관광지
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&q=80&w=800",  # 유럽 풍경
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&q=80&w=800"  # 해변
]


def get_random_date():
    """오늘부터 6개월 이내의 랜덤한 날짜 반환"""
    start_date = datetime.now() + timedelta(days=random.randint(7, 180))
    return start_date


def create_product_json(index):
    # 1. 랜덤 국가 및 도시 선택
    country = random.choice(list(DATA_SOURCE.keys()))
    city = random.choice(DATA_SOURCE[country]["cities"])

    # 2. 일정 기간 랜덤 설정
    # 유럽/미주는 장거리라 일정이 긴 편
    if country in ["유럽", "미주/대양주"]:
        nights = random.choice([5, 6, 7, 8])
    else:
        nights = random.choice([2, 3, 4])
    days = nights + 1
    duration_str = f"{nights}박 {days}일"

    # 3. 날짜 설정
    start_dt = get_random_date()
    end_dt = start_dt + timedelta(days=days - 1)

    # 4. 리소스 선택
    hotel_name = random.choice(DATA_SOURCE[country]["hotels"].get(city, [f"{city} 시티 호텔"]))
    golf_list = DATA_SOURCE[country]["golf_courses"].get(city, [])

    # 골프 패키지 확률 (동남아/일본은 높게, 그 외는 낮게)
    golf_prob = 0.7 if country in ["일본", "베트남", "태국", "필리핀"] else 0.2
    is_golf_package = len(golf_list) > 0 and random.random() < golf_prob

    # 상품명 생성
    product_name = f"[{country}] {city} {hotel_name} {duration_str}"
    if is_golf_package:
        product_name += " 명품 골프 투어"
        product_type = "golf"
    elif country == "유럽":
        product_name += " 낭만 가득 유럽 여행"
        product_type = "tour"
    elif city in ["하와이", "괌", "푸켓", "몰디브", "발리"]:
        product_name += " 허니문 & 커플 여행"
        product_type = "tour"
    else:
        product_name += " 힐링 휴양 패키지"
        product_type = "tour"

    # 가격 책정 (국가별 물가 반영)
    if country == "유럽" or country == "미주/대양주":
        price = random.randint(200, 500) * 10000
    elif country == "일본":
        price = random.randint(80, 200) * 10000
    else:
        price = random.randint(50, 150) * 10000

    # 5. JSON 생성
    product_data = {
        "meta": {
            "status": "published" if random.random() > 0.1 else "draft",
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source_files": [f"quotation_v2_{index:03d}.pdf"]
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
            "price_child": int(price * 0.9),
            "price_infant": int(price * 0.1),
            "price_net": int(price * 0.8)
        },
        "details": {
            "flight_summary": f"국적기/외항사 인천-{city} 왕복",
            "inclusions": ["왕복 항공권", "전 일정 숙박", "차량 및 가이드", "여행자 보험"],
            "exclusions": ["개인 경비", "매너팁", "일부 식사"],
            "special_notes": ["여권 유효기간 6개월 이상 필수"],
            "content_html": f"<p>{city}의 매력을 듬뿍 느낄 수 있는 최고의 여행입니다.</p>"
        },
        "resources": {
            "hotels": [{
                "name": hotel_name,
                "grade": "5성급",
                "description": "럭셔리한 휴식을 제공하는 특급 호텔",
                "check_in": "15:00",
                "check_out": "11:00",
                "website": "www.example.com",
                "image_url": random.choice(IMAGES)
            }],
            "golf_courses": []
        },
        "itinerary": []
    }

    if is_golf_package:
        selected_golfs = random.sample(golf_list, min(len(golf_list), nights))
        for g_name in selected_golfs:
            product_data["resources"]["golf_courses"].append({
                "name": g_name,
                "hole_info": "18홀 / 72파",
                "description": "최상의 컨디션을 자랑하는 골프 코스",
                "image_url": random.choice(IMAGES)
            })

    # 일정 생성
    for day in range(1, days + 1):
        day_date = start_dt + timedelta(days=day - 1)
        day_plan = {
            "day": day,
            "date": day_date.strftime("%Y-%m-%d"),
            "activities": [],
            "meals": {"breakfast": "호텔식", "lunch": "자유식", "dinner": "현지식"}
        }

        if day == 1:
            day_plan["activities"].append(
                {"time": "10:00", "type": "flight", "title": "출국", "description": "설레는 여행 시작"})
            day_plan["activities"].append({"time": "15:00", "type": "hotel", "title": "체크인", "description": "호텔 휴식"})
        elif day == days:
            day_plan["activities"].append(
                {"time": "09:00", "type": "transport", "title": "공항 이동", "description": "귀국 준비"})
            day_plan["activities"].append({"time": "12:00", "type": "flight", "title": "귀국", "description": "인천 도착"})
        else:
            if is_golf_package and (day - 2) < len(product_data["resources"]["golf_courses"]):
                g_course = product_data["resources"]["golf_courses"][day - 2]
                day_plan["activities"].append(
                    {"time": "08:00", "type": "golf", "title": f"{g_course['name']} 라운딩", "description": "나이스 샷!"})
            else:
                day_plan["activities"].append(
                    {"time": "10:00", "type": "sightseeing", "title": "시티 투어", "description": f"{city}의 명소 탐방"})

        product_data["itinerary"].append(day_plan)

    return product_data


def seed_database():
    session = SessionLocal()
    products_to_insert = []

    print("🚀 Generating 100 DIVERSE product JSONs...")

    for i in range(1, 101):
        p_data = create_product_json(i)
        products_to_insert.append(p_data)

        # RAG 벡터 등록
        try:
            add_product_to_vector_db(p_data)
            print(f"   [{i}/100] ↳ [RAG] 등록: {p_data['info']['product_name']}")
        except Exception as e:
            print(f"   [{i}/100] ↳ ⚠️ [RAG Error] {e}")

        # DB 객체 변환
        new_product = ProductTable(
            status=p_data['meta']['status'],
            product_name=p_data['info']['product_name'],
            category=p_data['info']['category'],
            product_type=p_data['info']['product_type'],
            country=p_data['info']['country'],
            city=p_data['info']['city'],
            departure_point=p_data['info']['departure_point'],
            start_date=datetime.strptime(p_data['schedule']['start_date'], "%Y-%m-%d").date(),
            end_date=datetime.strptime(p_data['schedule']['end_date'], "%Y-%m-%d").date(),
            nights=p_data['schedule']['nights'],
            days=p_data['schedule']['days'],
            price_adult=p_data['pricing']['price_adult'],
            price_net=p_data['pricing']['price_net'],
            currency=p_data['pricing']['currency'],
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

        with open("dummy_products_list_100.json", "w", encoding="utf-8") as f:
            json.dump(products_to_insert, f, ensure_ascii=False, indent=2)
        print("📂 Saved 'dummy_products_list_100.json' for reference.")

    except Exception as e:
        session.rollback()
        print(f"❌ DB Insert Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()