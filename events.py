from flask import request
from flask_socketio import join_room, emit
from services.chat_service import save_message
from services.ai_service import process_user_message
from services.kafka_service import send_to_kafka
from models import db, ChatRoom, ChatLog
from datetime import datetime
import time


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
        save_message(session_id, role, text, user_name, user_type)

    @socketio.on('send_message')
    def handle_send_message(data):
        room = data['room_id']
        user_msg = data['message']
        sender_type = data['sender_type']
        user_name = data.get('user_name', '익명')

        # 1. 기본 저장 및 전송
        save_message(room, sender_type, user_msg)
        emit('new_message', {
            'room_id': room, 'sender_type': sender_type, 'message': user_msg,
            'user_name': user_name, 'timestamp': time.time() * 1000
        }, room=room)

        # 2. 고객 메시지일 경우 AI 처리
        if sender_type == 'customer':

            # AI 의도 분류 수행
            ai_response, category = process_user_message(user_msg)

            # [분기점] 불만(Complaint)인 경우
            if category == 'Complaint':
                print(f"🚨 [System] 상담원 호출 요청! ({user_msg})")

                # A. AI 답변 전송 ("상담원 연결해드릴게요")
                save_message(room, 'ai', ai_response)
                emit('new_message', {
                    'room_id': room, 'sender_type': 'ai', 'message': ai_response,
                    'user_name': 'Travel AI', 'timestamp': time.time() * 1000
                }, room=room)

                # B. [핵심] 관리자에게만 'admin_alert' 이벤트 전송
                emit('admin_alert', {
                    'room_id': room,
                    'message': f"고객({user_name})님이 상담원을 요청했습니다!",
                    'user_msg': user_msg
                }, broadcast=True)  # 모든 관리자에게 알림

                # C. Kafka 전송 (시스템 로그용)
                send_to_kafka('chat_topic', {'room_id': room, 'role': 'alert', 'message': user_msg})

            else:
                # 그 외 일반 대화
                save_message(room, 'ai', ai_response)
                emit('new_message', {
                    'room_id': room, 'sender_type': 'ai', 'message': ai_response,
                    'user_name': 'Travel AI', 'timestamp': time.time() * 1000
                }, room=room)