from datetime import datetime
from models import db

class ChatRoom(db.Model):
    """
    [1. chat_rooms 테이블] 채팅방 정보
    (이미지 기준 컬럼: session_id, user_name, user_type, status, last_message, last_active, created_at)
    """
    __tablename__ = 'chat_rooms'

    session_id = db.Column(db.String(255), primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), default='General')
    status = db.Column(db.String(20), nullable=False, default='OPEN')

    last_message = db.Column(db.Text, nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship
    logs = db.relationship('ChatLog', backref='room', lazy=True)

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'user_name': self.user_name,
            'user_type': self.user_type,
            'status': self.status,
            'last_message': self.last_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class ChatLog(db.Model):
    """
    [2. chat_logs 테이블] 메시지 기록
    (이미지 기준 컬럼: id, session_id, role, text, user_name, user_type, created_at)
    """
    __tablename__ = 'chat_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(255), db.ForeignKey('chat_rooms.session_id'), nullable=False)

    role = db.Column(db.String(10), nullable=False)  # customer, admin, ai
    text = db.Column(db.Text, nullable=False)        # 메시지 내용

    # [중요] 이미지에 있는 컬럼만 유지
    user_name = db.Column(db.String(100), nullable=True)
    user_type = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'text': self.text,
            'user_name': self.user_name,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }