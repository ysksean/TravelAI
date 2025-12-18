from flask import request
from flask_socketio import emit, join_room
from datetime import datetime

# [1] DB 및 모델 임포트 (schema 경로 사용)
from models import db
from schema.chat_schema import ChatRoom, ChatLog
from schema.land_schema import LandChatRoom, LandChatLog
from schema.customer_schema import Customer, Reservation

# [2] 서비스 임포트
from services.chat_service import save_message  # 고객용 저장 함수
from services.kafka_service import send_to_kafka  # 고객용 카프카 전송
from services.ai_service import get_ai_response  # AI 챗봇


def register_socket_events(socketio):
    # --------------------------------------------------------------
    # 1. 공통: 방 입장 (Join)
    # --------------------------------------------------------------
    @socketio.on('join')
    def handle_join(data):
        room_id = data.get('room_id')
        user_type = data.get('user_type')
        join_room(room_id)
        print(f"🚪 [Join] {user_type} entered room: {room_id}")

    # --------------------------------------------------------------
    # 2. 고객(Customer) 채팅 -> Kafka 사용
    # --------------------------------------------------------------
    @socketio.on('send_message')
    def handle_send_message(data):
        room_id = data['room_id']
        msg = data['message']
        sender_type = data['sender_type']  # 'customer' or 'admin'
        user_name = data.get('user_name', '익명')

        print(f"📩 [Customer Msg] {sender_type}: {msg}")

        # (1) DB 저장
        save_message(room_id, sender_type, msg, user_name)

        # (2) Kafka로 전송 (Scale-out 대응)
        kafka_payload = {
            'room_id': room_id,
            'sender_type': sender_type,
            'message': msg,
            'user_name': user_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        send_to_kafka(kafka_payload)

        # (3) AI 자동응답 (고객이 말했을 때만)
        if sender_type == 'customer':
            # 예약 확정 키워드 등 특수 로직은 여기서 처리하거나
            # 복잡하면 별도 서비스로 분리 가능
            if "예약 확정" in msg:
                # 간단한 하드코딩 응답 예시 (Step 5에서 고도화 예정)
                ai_reply = "예약 확정을 원하시면 담당자가 결제창을 보내드립니다."
                save_message(room_id, 'ai', ai_reply, 'Travel AI')

                # AI 메시지도 Kafka로 보냄
                ai_payload = kafka_payload.copy()
                ai_payload['sender_type'] = 'ai'
                ai_payload['message'] = ai_reply
                ai_payload['user_name'] = 'Travel AI'
                send_to_kafka(ai_payload)
            else:
                # 일반 AI 답변
                ai_reply = get_ai_response(msg)
                save_message(room_id, 'ai', ai_reply, 'Travel AI')

                ai_payload = kafka_payload.copy()
                ai_payload['sender_type'] = 'ai'
                ai_payload['message'] = ai_reply
                ai_payload['user_name'] = 'Travel AI'
                send_to_kafka(ai_payload)

    # --------------------------------------------------------------
    # 3. 랜드사(Land) 채팅 -> Kafka 미사용 (Direct Socket)
    # --------------------------------------------------------------
    @socketio.on('send_land_message')
    def handle_land_message(data):
        """
        랜드사 <-> 관리자 1:1 대화
        카프카를 거치지 않고 바로 DB 저장 및 브로드캐스트
        """
        room_id = data['room_id']
        msg = data.get('message', '')
        sender_type = data['sender_type']  # 'land' or 'admin'
        msg_type = data.get('type', 'text')  # 'text', 'file', 'json'
        file_path = data.get('file_path', None)

        print(f"🏢 [Land Msg] {sender_type}: {msg} ({msg_type})")

        # (1) DB 저장 (LandChatLog)
        try:
            new_log = LandChatLog(
                session_id=room_id,
                role=sender_type,
                message_type=msg_type,
                text=msg,
                file_path=file_path
            )
            db.session.add(new_log)

            # 방 정보 업데이트 (마지막 메시지 시간)
            room = LandChatRoom.query.filter_by(session_id=room_id).first()
            if room:
                display_msg = "(파일)" if msg_type != 'text' else msg
                room.last_message = display_msg
                room.last_active = datetime.now()

            db.session.commit()
        except Exception as e:
            print(f"❌ 랜드사 메시지 저장 실패: {e}")
            db.session.rollback()
            return

        # (2) 즉시 전송 (Direct Emit)
        # Kafka를 안 쓰므로 여기서 바로 같은 방에 있는 사람들에게 쏨
        emit('new_message', {
            'room_id': room_id,
            'sender_type': sender_type,
            'message': msg,
            'type': msg_type,
            'file_path': file_path,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=room_id)

        # (3) 관리자에게 알림 (선택사항)
        if sender_type == 'land':
            emit('admin_alert', {'message': f"새 랜드사 메시지: {msg[:10]}..."}, broadcast=True)