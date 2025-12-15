from models import db, ChatRoom, ChatLog
from services.kafka_service import send_to_kafka


def save_and_publish_message(session_id, role, text, user_name='익명', user_type='일반'):
    """
    메시지를 저장하고 Kafka로 발행하는 핵심 로직
    """
    try:
        # 1. 채팅방(ChatRoom) 존재 여부 확인 및 생성
        room = ChatRoom.query.get(session_id)

        if not room:
            # 방이 없으면 새로 생성 (최초 접속 시)
            room = ChatRoom(
                session_id=session_id,
                user_name=user_name,
                user_type=user_type,
                status='OPEN'
            )
            db.session.add(room)
            print(f">>> [DB] 새 채팅방 생성: {session_id} ({user_name})")

        # 2. 메시지(ChatLog) 저장
        new_log = ChatLog(
            session_id=session_id,
            role=role,  # role (sender 대신 role 사용)
            text=text,  # text (message 대신 text 사용)
            user_name=user_name,  # 시점 기록용
            user_type=user_type
        )
        db.session.add(new_log)
        db.session.commit()

        # 3. Kafka 전송 (실시간 소켓용)
        # 소켓 클라이언트가 이해할 수 있는 포맷으로 변환
        payload = {
            'room_id': session_id,
            'sender_type': role,
            'message': text,
            'user_name': user_name,
            'timestamp': new_log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        send_to_kafka(payload)

        return True

    except Exception as e:
        print(f"⚠️ [Service Error] 메시지 저장 실패: {e}")
        db.session.rollback()
        return False


def get_room_list():
    """관리자용: 채팅방 목록 조회 (최근 생성순)"""
    rooms = ChatRoom.query.order_by(ChatRoom.created_at.desc()).all()
    return [r.to_dict() for r in rooms]


def get_chat_logs(session_id):
    """관리자용: 특정 방의 대화 내역 조회"""
    logs = ChatLog.query.filter_by(session_id=session_id) \
        .order_by(ChatLog.created_at.asc()).all()
    return [l.to_dict() for l in logs]