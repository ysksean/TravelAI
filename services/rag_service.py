import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from datetime import datetime

# 설정
INDEX_FILE = 'travel_products.index'
META_FILE = 'travel_metadata.pkl'
MODEL_NAME = 'BAAI/bge-m3'

_model = None


def get_model():
    global _model
    if _model is None:
        print(">>> [RAG] 임베딩 모델 로딩 중... (BGE-M3)", flush=True)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def json_to_markdown(data):
    """JSON 데이터를 Markdown 포맷으로 변환 (Structure-Aware Chunking)"""
    info = data.get('info', {})
    schedule = data.get('schedule', {})
    pricing = data.get('pricing', {})
    details = data.get('details', {})
    itinerary_list = data.get('itinerary', [])

    # 1. 기본 정보 헤더
    md_text = f"# 상품명: {info.get('product_name', '제목 없음')}\n"
    md_text += f"- 국가/도시: {info.get('country', '')} / {info.get('city', '')}\n"

    # 여행 기간 및 날짜 정보
    start_date = schedule.get('start_date', '날짜미정')
    end_date = schedule.get('end_date', '')
    nights = schedule.get('nights', 0)
    days = schedule.get('days', 0)
    md_text += f"- 여행 기간: {start_date} ~ {end_date} ({nights}박 {days}일)\n\n"

    # 2. 가격 정보
    md_text += f"## 가격 정보\n- 성인: {pricing.get('price_adult', 0):,}원\n\n"

    # 3. 상세 조건
    md_text += "## 상세 조건\n"
    md_text += f"- 포함: {', '.join(details.get('inclusions', []))}\n"
    md_text += f"- 불포함: {', '.join(details.get('exclusions', []))}\n\n"

    # 4. 상세 일정
    md_text += "## 상세 일정\n"
    for day_item in itinerary_list:
        day_num = day_item.get('day')
        act_summary = " -> ".join([act.get('title') for act in day_item.get('activities', [])])
        md_text += f"- {day_num}일차: {act_summary}\n"

    return md_text


def add_product_to_vector_db(product_data: dict):
    """벡터 DB에 상품 추가"""
    try:
        markdown_text = json_to_markdown(product_data)

        # 메타데이터에 'start_date' 저장
        start_date = product_data.get('schedule', {}).get('start_date', '9999-12-31')

        new_metadata = {
            "product_name": product_data.get('info', {}).get('product_name'),
            "price": product_data.get('pricing', {}).get('price_adult'),
            "start_date": start_date,
            "markdown_content": markdown_text
        }

        model = get_model()
        embedding = model.encode([markdown_text])
        embedding = np.array(embedding).astype('float32')

        if os.path.exists(INDEX_FILE):
            index = faiss.read_index(INDEX_FILE)
            with open(META_FILE, "rb") as f:
                metadata_list = pickle.load(f)
        else:
            dimension = embedding.shape[1]
            index = faiss.IndexFlatL2(dimension)
            metadata_list = []

        index.add(embedding)
        metadata_list.append(new_metadata)

        faiss.write_index(index, INDEX_FILE)
        with open(META_FILE, "wb") as f:
            pickle.dump(metadata_list, f)

        print(f">>> [RAG] 벡터 DB 업데이트 완료: {new_metadata['product_name']} (날짜: {start_date})", flush=True)
        return True
    except Exception as e:
        print(f"⚠️ [RAG Error] 벡터 DB 저장 실패: {e}", flush=True)
        return False


def search_best_products(user_query: str, top_k: int = 3):
    """RAG 검색 함수 (Threshold, 날짜 정렬 포함)"""
    if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
        print("⚠️ [RAG] 인덱스 파일이 없습니다.")
        return []

    try:
        model = get_model()
        query_vector = model.encode([user_query])
        query_vector = np.array(query_vector).astype('float32')

        index = faiss.read_index(INDEX_FILE)

        # 후보군 검색
        candidate_k = min(20, index.ntotal)
        distances, indices = index.search(query_vector, candidate_k)

        # =========================================================
        # [NEW] 임계값(Threshold) 검사 로직
        # =========================================================
        # BGE-M3 모델 기준 L2 Distance
        # 0.0에 가까울수록 유사함. 
        # 테스트 결과에 따라 이 값(1.2)을 조절하세요.
        THRESHOLD = 1.2

        best_score = float(distances[0][0])  # 1위 결과의 거리 점수

        print(f"\n🔍 [RAG 점수 확인] 질문: '{user_query}' | 1위 거리(L2): {best_score:.4f}")

        if best_score > THRESHOLD:
            print(f"⛔ [RAG] 유사도 낮음 (기준 {THRESHOLD} 초과) -> 빈 리스트 반환 (Custom 전환용)")
            return []
        # =========================================================

        with open(META_FILE, "rb") as f:
            metadata_list = pickle.load(f)

        candidates = []
        for i in range(candidate_k):
            idx = indices[0][i]
            if idx < 0: continue

            item = metadata_list[idx]
            s_date = item.get('start_date', '9999-12-31')

            candidates.append({
                "product_name": item['product_name'],
                "price": item['price'],
                "content": item['markdown_content'],
                "score": float(distances[0][i]),
                "start_date": s_date
            })

        # 날짜 관련 질문 감지 및 정렬
        date_keywords = ["날짜", "언제", "가까운", "빠른", "곧", "일정", "오늘", "이번주", "이번달"]
        is_time_query = any(keyword in user_query for keyword in date_keywords)

        if is_time_query:
            print(f"🕒 [RAG] 시간 관련 질문 감지! -> 가까운 날짜순 정렬 시도")

            def date_sort_key(item):
                try:
                    d_obj = datetime.strptime(item['start_date'], "%Y-%m-%d")
                    # 이미 지난 날짜는 9999년으로 보내서 추천 우선순위에서 배제
                    if d_obj.date() < datetime.now().date():
                        return datetime(9999, 12, 31)
                    return d_obj
                except:
                    return datetime(9999, 12, 31)

            candidates.sort(key=date_sort_key)

        # 최종 top_k 자르기
        final_results = candidates[:top_k]

        # 결과 확인용 출력
        print("-" * 50)
        for i, res in enumerate(final_results):
            print(f"[{i + 1}] {res['product_name']}")
            print(f"    - 날짜: {res['start_date']}")
            print(f"    - 거리: {res['score']:.4f}")
        print("=" * 50 + "\n")

        return final_results

    except Exception as e:
        print(f"⚠️ [RAG Search Error] {e}")
        return []


# # 테스트 실행용
# if __name__ == "__main__":
#     search_best_products("다낭 3박 4일 골프 여행")
#     search_best_products("라면 끓이는 법 알려줘")