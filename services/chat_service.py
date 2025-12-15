from models import db, ChatRoom, ChatLog
from datetime import datetime
from models import db, ChatRoom, ChatLog
from datetime import datetime


def save_message(session_id, role, text, user_name='익명'):
    """
    [통합 DB 저장 함수]
    채팅방이 없으면 만들고, 메시지를 저장합니다. (Kafka 전송 X)
    - session_id: 방 ID
    - role: 'customer', 'admin', 'ai'
    - text: 메시지 내용
    """
    try:
        # 1. 채팅방 확인
        room = ChatRoom.query.filter_by(session_id=session_id).first()

        # 2. 방이 없으면 생성
        if not room:
            room = ChatRoom(
                session_id=session_id,
                user_name=user_name,
                user_type='General',
                status='OPEN'
            )
            db.session.add(room)
            db.session.commit()  # ID 생성을 위해 커밋

        # 3. 메시지 로그 저장
        new_log = ChatLog(
            session_id=session_id,
            role=role,
            text=text,
            user_name=user_name,
            created_at=datetime.now()
        )
        db.session.add(new_log)

        # 4. 방 상태 업데이트 (최신 메시지 표시용)
        room.last_active = datetime.now()
        room.last_message = text[:100]  # 너무 길면 자름

        db.session.commit()
        return True

    except Exception as e:
        print(f"⚠️ [ChatService] 메시지 저장 실패: {e}")
        db.session.rollback()
        return False


def get_room_list():
    """관리자용: 채팅방 목록 조회 (최근 활동순)"""
    try:
        rooms = ChatRoom.query.order_by(ChatRoom.last_active.desc()).all()
        result = []
        for r in rooms:
            result.append({
                'session_id': r.session_id,
                'user_name': r.user_name,
                'user_type': r.user_type,
                'status': r.status,
                'last_message': r.last_message,
                'last_active': r.last_active.strftime('%Y-%m-%d %H:%M:%S') if r.last_active else None,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else None
            })
        return result
    except Exception as e:
        print(f"⚠️ [ChatService] 목록 조회 실패: {e}")
        return []


def get_chat_logs(session_id):
    """채팅방 대화 내역 조회 (오래된 순)"""
    try:
        logs = ChatLog.query.filter_by(session_id=session_id) \
            .order_by(ChatLog.created_at.asc()).all()

        result = []
        for l in logs:
            result.append({
                'id': l.id,
                'role': l.role,
                'text': l.text,
                'user_name': l.user_name,
                'timestamp': l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else None
            })
        return result
    except Exception as e:
        print(f"⚠️ [ChatService] 내역 조회 실패: {e}")
        return []