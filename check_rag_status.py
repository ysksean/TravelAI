# check_rag_status.py
import faiss
import pickle
import os

INDEX_FILE = 'travel_products.index'
META_FILE = 'travel_metadata.pkl'


def check():
    print(f"{'=' * 30}")
    print("🔎 벡터 DB 상태 점검")
    print(f"{'=' * 30}")

    if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
        print("❌ 실패: 벡터 DB 파일이 없습니다. (API로 상품을 먼저 등록하세요)")
        return

    # 1. FAISS 인덱스 로드
    index = faiss.read_index(INDEX_FILE)
    print(f"✅ 벡터 인덱스 로드 성공!")
    print(f"📊 저장된 데이터(상품) 개수: {index.ntotal}개")

    # 2. 메타데이터 로드
    with open(META_FILE, "rb") as f:
        data = pickle.load(f)
        print(f"✅ 메타데이터 로드 성공! (총 {len(data)}건)")

    # 3. 가장 최근 데이터 내용 확인
    if len(data) > 0:
        last_item = data[-1]
        print("\n📝 [가장 최근 저장된 상품 정보]")
        print(f"   - 상품명: {last_item['product_name']}")
        print(f"   - 가격: {last_item['price']}")
        print(f"   - AI 학습용 요약 내용(Markdown) 일부:\n")
        print(f"{'-' * 20}")
        print(last_item['markdown_content'][:200])  # 200자만 미리보기
        print(f"{'-' * 20}")
        print("\n>>> 학습된 내용이 정상적으로 보입니다.")
    else:
        print("\n⚠️ 저장된 데이터가 없습니다.")


if __name__ == "__main__":
    check()