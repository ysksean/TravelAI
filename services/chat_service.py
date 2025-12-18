from models import db
from datetime import datetime
from schema.chat_schema import ChatRoom, ChatLog
from schema.customer_schema import Customer

def save_message(session_id, role, text, user_name='익명', message_type='text', file_path=None):
    """
    소켓 메시지 저장 (DB 컬럼에 맞춰 수정됨)
    """
    try:
        # 1. 채팅방 확인 및 생성
        room = ChatRoom.query.filter_by(session_id=session_id).first()

        if not room:
            customer = Customer.query.filter_by(user_id=session_id).first()
            if customer:
                final_name = customer.name
                final_type = customer.user_type
            else:
                final_name = user_name
                final_type = 'General'

            room = ChatRoom(
                session_id=session_id,
                user_name=final_name,
                user_type=final_type,
                status='OPEN',
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            db.session.add(room)
            db.session.commit()

        # [수정] DB에 message_type 컬럼이 없으므로, 파일인 경우 text에 표시
        final_text = text
        if file_path:
            final_text = f"(파일: {text}) {file_path}"
        elif message_type == 'json':
            final_text = f"(견적서) {text}"

        # 2. 메시지 로그 저장 (없는 컬럼 제외)
        new_log = ChatLog(
            session_id=session_id,
            role=role,
            text=final_text,         # 변형된 텍스트 저장
            user_name=user_name,
            user_type='General',     # 기본값
            created_at=datetime.now()
        )
        db.session.add(new_log)

        # 3. 방 상태 업데이트
        room.last_active = datetime.now()
        room.last_message = final_text[:50]  # 미리보기

        db.session.commit()
        return True

    except Exception as e:
        print(f"⚠️ [ChatService] 메시지 저장 실패: {e}")
        db.session.rollback()
        return False