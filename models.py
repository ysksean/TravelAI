from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ChatRoom(db.Model):
    """
    [1. chat_rooms 테이블] 채팅방 메타 정보
    """
    __tablename__ = 'chat_rooms'

    # 컬럼 정의
    session_id = db.Column(db.String(255), primary_key=True)  # 채팅방 고유 ID (PK)
    user_name = db.Column(db.String(100), nullable=False)  # 고객 이름
    user_type = db.Column(db.String(10), default='일반')  # 고객 유형 (VIP, 일반 등)
    status = db.Column(db.String(20), nullable=False, default='OPEN')  # OPEN, CLOSED, PENDING 등

    # [중요] 에러 해결을 위해 추가된 컬럼들
    last_message = db.Column(db.Text, nullable=True)  # 목록에서 보여줄 마지막 메시지
    last_active = db.Column(db.DateTime, default=datetime.now)  # 정렬 기준 (최신순)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Relationship (ChatLog와 1:N 관계 설정)
    logs = db.relationship('ChatLog', backref='room', lazy=True)

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'user_name': self.user_name,
            'user_type': self.user_type,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class ChatLog(db.Model):
    """
    [2. chat_logs 테이블] 개별 메시지 기록
    """
    __tablename__ = 'chat_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # PK
    session_id = db.Column(db.String(255), db.ForeignKey('chat_rooms.session_id'), nullable=False)  # FK

    role = db.Column(db.String(10), nullable=False)  # 발화 주체 (고객, 봇, 여행사 등)
    text = db.Column(db.Text, nullable=False)  # 메시지 내용

    # (선택) 시점 기록용 중복 컬럼 (이미지 요청사항 반영)
    user_name = db.Column(db.String(100), nullable=True)
    user_type = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'text': self.text,
            'user_name': self.user_name,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }