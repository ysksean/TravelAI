import google.generativeai as genai
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# [중요] RAG 서비스 가져오기
# (단독 실행 시 경로 문제 방지를 위한 try-except)
try:
    from services.rag_service import search_best_products
except ImportError:
    # 테스트를 위해 상위 폴더 경로 추가
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from services.rag_service import search_best_products

# .env 로드
load_dotenv()

# API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("⚠️ 경고: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")
else:
    # genai 설정
    genai.configure(api_key=GOOGLE_API_KEY)


# ==========================================
# 1. 의도 분류 (Router)
# ==========================================
def classify_intent(user_text):
    """
    의도 분류 (Router) - 추천 거절 및 맞춤 요청 인식 강화
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        당신은 여행사 챗봇의 라우터입니다. 사용자 입력을 분석해 카테고리를 분류하세요.

        [카테고리]
        1. Greeting: 인사, 잡담
        2. Complaint: 불만, 상담원 연결, 환불
        3. Booking: 구체적인 상품에 대한 예약 의사 ("이거 예약할래", "저걸로 할게")
        4. Recommend: 상품 추천 요청 ("다낭 있어?", "골프 여행 추천해줘")
        5. Custom: 
           - 추천받은 상품 거절 ("이거 별로야", "다른 건 없어?", "아니 다낭으로 해줘")
           - 없는 상품에 대한 집요한 요청 ("무조건 다낭 가야해")
           - 맞춤 견적 요청 ("우리끼리만 가고 싶어", "일정 조율해줘")
        6. Irrelevant: 여행 무관 주제

        [사용자 입력]
        "{user_text}"

        [출력] 오직 JSON만: {{"category": "카테고리명"}}
        """

        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean_text)
        return result.get('category', 'Custom')

    except Exception as e:
        print(f"⚠️ [Intent Error] {e}")
        return "Custom"


# ==========================================
# 2. 핸들러 (Handlers) - 각 상황별 처리
# ==========================================

def handle_greeting(user_text):
    return "안녕하세요! ✈️ 여행의 시작, 무엇을 도와드릴까요? (상품 추천 / 맞춤 견적 / 상담원 연결)"


def handle_complaint(user_text):
    return "불편을 드려 죄송합니다. 😥\n보다 정확한 해결을 위해 **상담원을 연결**해 드릴까요? ('네'라고 답변하시면 연결됩니다)"


def handle_booking(user_text):
    # (추후 개발) 슬롯 필링 로직이 들어갈 자리
    return "예약을 원하시는군요! 원하시는 일정과 인원수를 말씀해 주시면 예약을 도와드리겠습니다."


def handle_custom(user_text):
    """
    [Custom] 맞춤 견적 파이프라인 (State Logic / Slot Filling)
    고객의 요구사항(목적지, 날짜, 인원)을 모두 파악해야 랜드사에 보낼 수 있음.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # 1. 정보 추출 및 누락 확인 프롬프트
        prompt = f"""
        당신은 '맞춤 견적 담당 여행 플래너'입니다.
        고객이 원하는 여행 견적을 내기 위해서는 **3가지 필수 정보**가 필요합니다.

        [필수 정보]
        1. 목적지 (Destination)
        2. 날짜/일정 (Date)
        3. 인원 (Headcount)

        [고객의 말]
        "{user_text}"

        [지시사항]
        위 [고객의 말]만 보고 필수 정보가 다 있는지 판단하세요.

        Case A: 필수 정보가 하나라도 부족하다면?
        - 부족한 정보를 친절하게 되물어보는 답변을 작성하세요.
        - 예: "다낭으로 가시는군요! 혹시 출발 예정일과 가시는 인원은 어떻게 되시나요?"

        Case B: 필수 정보가 모두 있다면?
        - "완벽합니다! 요청하신 [목적지, 날짜, 인원] 내용으로 현지 랜드사에 견적을 요청하겠습니다. 결과는 알림톡으로 보내드릴게요." 라는 확정 답변을 작성하세요.
        - JSON 형식으로 추출된 정보도 함께 명시할 필요는 없고, 자연스러운 대화문만 출력하세요.

        [출력] 자연스러운 한국어 답변
        """

        response = model.generate_content(prompt)

        # (심화) 여기서 실제 DB 저장을 하려면, LLM에게 JSON도 뱉으라고 해서 파싱해야 함.
        # 일단은 대화 흐름(State Logic) 완성에 집중.
        return response.text

    except Exception as e:
        print(f"❌ [Custom Error] {e}")
        return "맞춤 견적을 위해 여행지, 날짜, 인원을 말씀해 주세요."


def handle_recommend_process(user_text):
    """
    [핵심] RAG 검색 + LLM 답변 생성
    """
    print(f"🤖 [AI] 상품 추천 로직 시작: {user_text}")

    # 1. RAG 서비스 호출 (Threshold 로직 포함됨)
    # 결과가 없거나 유사도가 낮으면 빈 리스트([])가 반환됨
    search_results = search_best_products(user_text)

    # 2. [Fallback] 검색 결과가 없으면 -> Custom 핸들러로 전환
    if not search_results:
        print("🔀 [Router] RAG 결과 없음(유사도 낮음) -> Custom으로 전환")
        return handle_custom(user_text)

    # 3. LLM 답변 생성 (검색된 내용 바탕으로)
    return generate_answer(user_text, search_results)

def handle_irrelevant(user_text):
    return "죄송합니다. 😅 저는 **여행 전문 챗봇**이라 그 부분은 답변드리기 어렵습니다.\n여행 상품 추천이나 견적에 대해 물어봐 주세요!"


def generate_answer(user_query, retrieved_products):
    """
    검색된 상품 정보(Context)를 바탕으로 Gemini가 답변을 생성
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Context 구성
        context_text = ""
        for i, prod in enumerate(retrieved_products, 1):
            context_text += f"""
            [추천 상품 {i}]
            - 상품명: {prod['product_name']}
            - 가격: {prod['price']:,}원
            - 출발일: {prod['start_date']}
            - 내용 요약: {prod['content'][:200]}...
            """

        # 날짜 정보
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        now = datetime.now()
        today_str = now.strftime("%Y년 %m월 %d일")
        weekday_str = weekdays[now.weekday()]

        system_prompt = f"""
        당신은 전문 여행 상담사 'Travel AI'입니다. 
        오늘은 **{today_str} ({weekday_str}요일)**입니다.
        아래 [참고 정보]에 있는 여행 상품 내용만을 바탕으로 고객의 질문에 친절하고 전문적으로 답변하세요.

        [규칙]
        1. 반드시 [참고 정보]에 있는 상품만 추천하세요. 없는 내용은 지어내지 마세요.
        2. 고객이 원하는 조건(날짜, 지역)과 가장 비슷한 상품을 1순위로 권하세요.
        3. 각 상품의 번호, 이름, 가격, 출발일을 명확히 언급하세요.
        4. 마지막에는 "이 상품들 중 마음에 드는 것이 있으신가요?"로 끝맺으세요.

        [참고 정보]
        {context_text}

        [고객 질문]
        {user_query}
        """

        response = model.generate_content(system_prompt)
        return response.text

    except Exception as e:
        print(f"❌ [AI Error] 답변 생성 실패: {e}")
        return "죄송합니다. 답변을 생성하는 중 문제가 발생했습니다."


# ==========================================
# 3. 메인 프로세스 (Controller)
# ==========================================
def process_user_message(user_text):
    # 1. 의도 분류
    category = classify_intent(user_text)
    print(f"🧐 [Intent] 분류 결과: {category}")

    # 2. 라우팅 (Switch)
    if category == 'Greeting':
        response = handle_greeting(user_text)
    elif category == 'Complaint':
        response = handle_complaint(user_text)
    elif category == 'Booking':
        response = handle_booking(user_text)
    elif category == 'Recommend':
        response = handle_recommend_process(user_text)
        # RAG 실패해서 내부적으로 Custom 메시지가 왔을 때의 처리는 handle_recommend_process 안에서 해결됨
    elif category == 'Irrelevant': # [NEW] 추가됨
        response = handle_irrelevant(user_text)
    else:
        # Custom 및 기타 -> 스마트 핸들러로 교체
        response = handle_custom(user_text)

    return response, category


# ==========================================
# 4. 테스트 코드 (직접 실행 시 동작)
# ==========================================
if __name__ == "__main__":
    print("\n🚀 [AI Service] 통합 테스트 시작\n")

    # 시나리오 1: 단순 인사
    print("--- Test 1: 인사 (Greeting) ---")
    res, cat = process_user_message("안녕 반가워")
    print(f"🤖 답변({cat}): {res}\n")

    # 시나리오 2: 정상 추천 (RAG가 잘 되어야 함)
    print("--- Test 2: 상품 추천 (Recommend) ---")
    res, cat = process_user_message("다낭 3박 4일 골프 여행 추천해줘")
    print(f"🤖 답변({cat}): {res}\n")

    # 시나리오 3: 엉뚱한 질문 -> Custom 전환 (Fallback) 또는 Irrelevant
    print("--- Test 3: 엉뚱한 질문 (Irrelevant/Custom Fallback) ---")
    res, cat = process_user_message("라면 맛있게 끓이는 법 알려줘")
    print(f"🤖 답변({cat}): {res}\n")

    # 시나리오 4: 상담원 연결
    print("--- Test 4: 불만/상담원 (Complaint) ---")
    res, cat = process_user_message("너무 답답해 상담원 연결해줘")
    print(f"🤖 답변({cat}): {res}\n")

    # [NEW] 시나리오 5: 맞춤 견적 진입 (추천 거절 or 정보 부족 -> 되묻기)
    # 기대 결과: "날짜와 인원은 어떻게 되시나요?" 라고 물어봐야 함
    print("--- Test 5: 맞춤 견적 진입 (Custom - 정보 부족) ---")
    res, cat = process_user_message("아니, 추천해준 거 말고 무조건 다낭으로 가고 싶어.")
    print(f"🤖 답변({cat}): {res}\n")

    # [NEW] 시나리오 6: 맞춤 견적 완료 (모든 정보 제공 -> 접수 확정)
    # 기대 결과: "견적 요청을 접수했습니다" 라고 확정해야 함
    print("--- Test 6: 맞춤 견적 완료 (Custom - 정보 충족) ---")
    res, cat = process_user_message("내년 1월 15일에 성인 4명 다낭으로 견적 내줘")
    print(f"🤖 답변({cat}): {res}\n")