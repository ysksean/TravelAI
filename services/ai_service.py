# flask_web/services/ai_service.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

# API 키 설정 (직접 입력하거나 환경변수 사용)
# os.environ["GOOGLE_API_KEY"] = "여기에_키를_입력하세요"
# 또는 아래처럼 직접 할당
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# (디버깅용) 키 로드 확인
if not GOOGLE_API_KEY:
    print("⚠️ 경고: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")
else:
    # 보안상 키 전체를 출력하지 않고 앞부분만 확인
    print(f"✅ Gemini API Key 로드 완료: {GOOGLE_API_KEY[:5]}...")

genai.configure(api_key=GOOGLE_API_KEY)

def generate_answer(user_query, retrieved_products):
    """
    검색된 상품 정보(Context)를 바탕으로 Gemini가 답변을 생성합니다.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # 1. 참고할 정보(Context) 구성
        if not retrieved_products:
            context_text = "관련된 상품 정보가 없습니다."
        else:
            context_text = ""
            for i, prod in enumerate(retrieved_products, 1):
                context_text += f"\n[상품 {i}]\n{prod['content']}\n"

        # 2. 프롬프트 엔지니어링 (페르소나 부여)

        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        now = datetime.now()
        today_str = now.strftime("%Y년 %m월 %d일")
        weekday_str = weekdays[now.weekday()]  # 0=월요일, 6=일요일
        system_prompt = f"""
        
당신은 전문 여행 상담사 'Travel AI'입니다. 
**"오늘은 {today_str} ({weekday_str}요일)입니다.**
아래 [참고 정보]에 있는 여행 상품 내용만을 바탕으로 고객의 질문에 친절하고 전문적으로 답변하세요.

[규칙]
1. [참고 정보]에 없는 내용은 지어내지 말고, "죄송하지만 해당 정보는 확인되지 않습니다"라고 말하세요.
2. 가격은 한국 원화(KRW) 기준으로 명확히 안내하세요.
3. 상품의 장점과 특징을 자연스럽게 어필하세요.
4. 마지막에는 항상 "더 궁금한 점이 있으시면 언제든 말씀해주세요!"로 끝맺으세요.

[참고 정보]
{context_text}

[고객 질문]
{user_query}
"""

        # 3. LLM 호출
        response = model.generate_content(system_prompt)
        return response.text

    except Exception as e:
        print(f"❌ [AI Error] {e}")
        return "죄송합니다. AI 서비스에 일시적인 문제가 발생했습니다."