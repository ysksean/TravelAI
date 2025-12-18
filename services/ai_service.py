import google.generativeai as genai
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# [중요] RAG 서비스 가져오기
try:
    from services.rag_service import search_best_products
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from services.rag_service import search_best_products

# .env 로드
load_dotenv()

# API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("⚠️ 경고: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

session_storage = {}


# ==========================================
# [NEW] 요청사항 분석기 (없음 vs 있음 판단)
# ==========================================
def analyze_request_intent(user_text):
    """
    사용자의 입력이 '요청사항 없음'인지 '구체적인 요청'인지 분류
    Return: 'NONE' (없음) or 'EXIST' (있음)
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        당신은 여행 예약 상담 봇입니다. 
        고객에게 "추가 요청사항이 있으신가요?"라고 물어본 후, 고객의 답변을 분석해야 합니다.

        [고객 답변]
        "{user_text}"

        [판단 기준]
        - 부정적 표현 (없다, 없음, 괜찮아, 아니오, 패스, 딱히 없어, 그대로 진행해) -> 'NONE'
        - 긍정적 표현 (휠체어, 오션뷰, 조식 포함, 싸게 해줘, 일정 변경, 네 있어요) -> 'EXIST'

        [출력 포맷]
        오직 JSON만 출력: {{"intent": "NONE" 또는 "EXIST"}}
        """
        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean_text)
        return result.get('intent', 'EXIST')
    except:
        return 'EXIST'  # 에러 발생 시 안전하게 요청이 있다고 가정


# ==========================================
# 공통 슬롯 필링 엔진 (LLM)
# ==========================================
def run_slot_filling(user_text, required_fields_desc, task_name, session_id):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        current_context = session_storage.get(session_id, {})

        # 시스템 제어 변수(task, booking_step)는 프롬프트에서 제외하여 혼란 방지
        filtered_context = {k: v for k, v in current_context.items() if k not in ['task', 'booking_step']}
        context_str = ", ".join([f"{k}:{v}" for k, v in filtered_context.items()])

        prompt = f"""
        당신은 꼼꼼하고 친절한 '여행 상담 전문 플래너'입니다.
        현재 고객의 '{task_name}' 요청을 처리하기 위해 정보를 확인하고 있습니다.

        [목표]
        대화를 통해 아래 [필수 정보]를 모두 수집해야 합니다.

        [필수 정보 목록]
        {required_fields_desc}

        [현재까지 수집된 정보 (기억)]
        {context_str if context_str else "(아직 없음)"}

        [고객의 현재 말]
        "{user_text}"

        [지시사항]
        1. [현재까지 수집된 정보]와 [고객의 현재 말]을 합쳐서 정보를 갱신하세요.
        2. **Case A (정보 부족):** 필수 정보가 하나라도 부족하다면, 부족한 정보만 콕 집어서 친절하게 되물어보는 답변(reply)을 작성하세요.
        3. **Case B (정보 완료):** 모든 필수 정보가 모였다면, "완벽합니다! 말씀하신 [요약 내용]으로 확인했습니다."라는 확정 답변(reply)을 작성하세요.
        4. **출력 형식:** 반드시 아래 JSON 포맷으로만 출력하세요.

        [출력 포맷 - JSON Only]
        {{
            "status": "ing" (정보 부족 시) 또는 "complete" (모두 완료 시),
            "extracted_data": {{ "항목명": "값", "항목명2": "값" }},
            "reply": "고객에게 할 답변 텍스트"
        }}
        """

        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean_text)

        if result.get('extracted_data'):
            updated_data = {**current_context, **result['extracted_data']}
            session_storage[session_id] = updated_data
            # 디버깅용 로그
            # print(f"💾 [Memory] 세션({session_id}) 갱신: {session_storage[session_id]}")

        return result

    except Exception as e:
        print(f"❌ [Slot Filling Error] {e}")
        return {
            "status": "ing",
            "reply": "죄송합니다. 정보를 정확히 이해하지 못했습니다. 다시 말씀해 주시겠어요?",
            "extracted_data": {}
        }


# ==========================================
# 1. 의도 분류 (Router)
# ==========================================
def classify_intent(user_text):
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
# 2. 핸들러 (Handlers)
# ==========================================

def handle_greeting(user_text):
    return "안녕하세요! ✈️ 여행의 시작, 무엇을 도와드릴까요? (상품 추천 / 맞춤 견적 / 상담원 연결)"


def handle_complaint(user_text):
    return "불편을 드려 죄송합니다. 😥\n보다 정확한 해결을 위해 **상담원을 연결**해 드릴까요? ('네'라고 답변하시면 연결됩니다)"


# [수정됨] 예약 핸들러 (요청사항 분기 로직 강화)
def handle_booking(user_text, session_id):
    """
    [Booking]
    Step 1: 출발지, 인원 수집
    Step 2: 추가 요청사항 확인 (Lock 유지)
    Step 3: 인보이스 또는 견적 요청으로 분기 (Unlock)
    """
    # 1. 세션 초기화
    if session_id not in session_storage:
        session_storage[session_id] = {}

    # ★ 핵심: Booking 모드로 Lock 설정
    session_storage[session_id]['task'] = 'booking'

    # 현재 단계 확인
    current_step = session_storage[session_id].get('booking_step', 'collecting_info')

    # ------------------------------------------------------------------
    # [Step 2] 추가 요청사항 확인 단계 (필수 정보 수집 완료 후 진입)
    # ------------------------------------------------------------------
    if current_step == 'waiting_for_request':
        # 사용자의 대답("없음" 또는 "바다뷰 줘") 분석
        intent = analyze_request_intent(user_text)

        # 이제 예약 대화 종료 -> Lock 해제 및 상태 초기화
        session_storage[session_id]['task'] = None
        session_storage[session_id]['booking_step'] = None

        if intent == 'NONE':
            # Case 1: 요청사항 없음 -> 인보이스 발행
            return "네, 알겠습니다. 별도 요청사항이 없으시군요.\n\n확인된 정보로 **인보이스(예약 확정서)**를 바로 발행해 드리겠습니다! 잠시만 기다려주세요. 📄"
        else:
            # Case 2: 요청사항 있음 -> 랜드사 견적 요청
            session_storage[session_id]['customer_request'] = user_text  # 요청사항 저장
            return f"네, 확인했습니다.\n말씀하신 **'{user_text}'** 내용을 반영하여 랜드사에 정확한 견적을 요청하겠습니다.\n\n답변이 올 때까지 잠시만 기다려주세요! ⏳"

    # ------------------------------------------------------------------
    # [Step 1] 필수 정보(출발지, 인원) 수집 단계
    # ------------------------------------------------------------------
    required = "1. 출발지 (Departure)\n2. 인원 (Headcount)"
    result = run_slot_filling(user_text, required, "상품 예약 진행", session_id)

    if result['status'] == 'complete':
        # 필수 정보가 다 모였다면, 바로 끝내지 않고 'Step 2'로 상태 변경
        session_storage[session_id]['booking_step'] = 'waiting_for_request'

        # 정보 요약
        collected_data = session_storage[session_id]
        summary = f"출발지: {collected_data.get('출발지')}, 인원: {collected_data.get('인원')}"

        return f"정보 확인 감사합니다. ({summary})\n\n마지막으로, 숙소나 식사, 휠체어 등 **추가로 요청하실 특별한 사항**이 있으신가요?\n(딱히 없으시면 '없음'이라고 말씀해 주세요)"
    else:
        # 정보가 부족하면 계속 되묻기 (Lock 유지)
        return result['reply']


# [수정됨] 맞춤 견적 핸들러
def handle_custom(user_text, session_id):
    if session_id not in session_storage:
        session_storage[session_id] = {}

    session_storage[session_id]['task'] = 'custom'  # Lock

    required = """
    1. 출발지 (Departure Place)
    2. 인원 (Headcount)
    3. 희망 국가/도시 (Destination Country/City)
    4. 여행 기간 (Duration, 예: 3박 4일)
    5. 희망 출발일 (Start Date)
    """
    result = run_slot_filling(user_text, required, "맞춤 여행 견적", session_id)

    if result['status'] == 'complete':
        session_storage[session_id]['task'] = None  # Unlock
        return handle_additional_requests(user_text, session_storage[session_id])
    else:
        return result['reply']


def handle_recommend_process(user_text, session_id):
    print(f"🤖 [AI] 상품 추천 로직 시작: {user_text}")
    search_results = search_best_products(user_text)

    if not search_results:
        print("🔀 [Router] RAG 결과 없음 -> Custom(맞춤 견적)으로 전환")
        return handle_custom(user_text, session_id)

    answer = generate_answer(user_text, search_results)
    return answer + "\n\n(이 상품이 마음에 드시면 '예약할래'라고 말씀해 주세요!)"


def handle_irrelevant(user_text):
    return "죄송합니다. 😅 저는 **여행 전문 챗봇**이라 그 부분은 답변드리기 어렵습니다."


# (더 이상 booking에서 사용하지 않지만, custom 등에서 사용할 수 있어 유지)
def handle_additional_requests(user_text, collected_data):
    return "모든 정보가 확인되었습니다! 랜드사에 맞춤 견적을 요청하겠습니다."


def generate_answer(user_query, retrieved_products):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        context_text = ""
        for i, prod in enumerate(retrieved_products, 1):
            context_text += f"[추천 {i}] {prod['product_name']} / {prod['price']:,}원 / {prod['start_date']}\n"

        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        now = datetime.now()
        today_str = now.strftime("%Y년 %m월 %d일")
        weekday_str = weekdays[now.weekday()]

        system_prompt = f"""
        전문 여행 상담사 'Travel AI'입니다. 오늘은 {today_str} ({weekday_str})입니다.
        [참고 정보] {context_text}
        [질문] {user_query}
        [규칙] 없는 내용은 지어내지 말고, 참고 정보를 바탕으로 친절하게 답변하세요.
        """
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        print(f"❌ [AI Error] 답변 생성 실패: {e}")
        return "죄송합니다. 답변을 생성하는 중 문제가 발생했습니다."


# ==========================================
# 3. 메인 프로세스 (Controller) - Task Locking 적용
# ==========================================
def process_user_message(user_text, session_id="guest"):
    # 1. [Lock Check] 진행 중인 작업 확인
    current_session = session_storage.get(session_id, {})
    current_task = current_session.get('task')

    if current_task:
        print(f"🔒 [Lock] '{current_task}' 모드 유지 중... (step: {current_session.get('booking_step')})")

        if current_task == 'booking':
            # 예약 모드 Lock 상태면 의도 분류 없이 바로 핸들러로 이동
            return handle_booking(user_text, session_id), "Booking (Locked)"
        elif current_task == 'custom':
            return handle_custom(user_text, session_id), "Custom (Locked)"

    # 2. [Normal] 의도 분류
    category = classify_intent(user_text)
    print(f"🧐 [Intent] 분류 결과: {category}")

    if category == 'Greeting':
        return handle_greeting(user_text), category
    elif category == 'Complaint':
        return handle_complaint(user_text), category
    elif category == 'Booking':
        return handle_booking(user_text, session_id), category
    elif category == 'Recommend':
        return handle_recommend_process(user_text, session_id), category
    elif category == 'Irrelevant':
        return handle_irrelevant(user_text), category
    else:
        return handle_custom(user_text, session_id), category


def get_ai_response(user_text, session_id="guest"):
    response_text, _ = process_user_message(user_text, session_id)
    return response_text