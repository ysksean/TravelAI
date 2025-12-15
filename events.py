from flask import request
from flask_socketio import join_room
from services.chat_service import save_and_publish_message


def register_socket_events(socketio):
    @socketio.on('join')
    def handle_join(data):
        # session_id가 곧 room_id 역할을 합니다.
        room = data.get('room_id')
        join_room(room)
        print(f">>> [Socket] 입장: {room}")

    @socketio.on('send_message')
    def handle_send_message(data):
        # 1. 데이터 추출
        session_id = data.get('room_id')
        role = data.get('sender_type')  # customer, admin, ai 등
        text = data.get('message')

        # 추가 정보 (없으면 기본값)
        user_name = data.get('user_name', '고객')
        user_type = data.get('user_type', '일반')

        if not session_id or not text:
            return

        # 2. 서비스 호출 (DB 저장 + Kafka)
        save_and_publish_message(session_id, role, text, user_name, user_type)