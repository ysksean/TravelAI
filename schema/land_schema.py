# flask_web/schema/land_schema.py
from datetime import datetime
from models import db
import uuid


# 1. 랜드사 계정 테이블
class LandOperator(db.Model):
    __tablename__ = 'land_operators'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)  # 로그인 ID (예: land01)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 업체명 (예: 하나투어 베트남지사)
    region = db.Column(db.String(50), nullable=True)  # 담당 지역 (예: 다낭)
    contact = db.Column(db.String(50), nullable=True)  # 연락처

    created_at = db.Column(db.DateTime, default=datetime.now)


# 2. 랜드사 채팅방 (관리자 <-> 랜드사 1:1)
class LandChatRoom(db.Model):
    __tablename__ = 'land_chat_rooms'

    session_id = db.Column(db.String(255), primary_key=True)  # 고유방 ID
    operator_id = db.Column(db.Integer, db.ForeignKey('land_operators.id'), nullable=False)  # 어떤 랜드사인지

    # 랜드사 이름/지역 (조회 편의성 위해 중복 저장 or 조인 사용)
    operator_name = db.Column(db.String(100))

    status = db.Column(db.String(20), default='OPEN')
    last_message = db.Column(db.Text, nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 1:N 관계
    logs = db.relationship('LandChatLog', backref='land_room', lazy=True)


# 3. 랜드사 채팅 기록
class LandChatLog(db.Model):
    __tablename__ = 'land_chat_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(255), db.ForeignKey('land_chat_rooms.session_id'), nullable=False)

    role = db.Column(db.String(20), nullable=False)  # 'admin', 'land'
    message_type = db.Column(db.String(20), default='text')  # 'text', 'file', 'json' (견적서)
    text = db.Column(db.Text, nullable=True)  # 텍스트 내용 or 파일명
    file_path = db.Column(db.String(255), nullable=True)  # 파일 업로드 시 경로

    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'type': self.message_type,
            'text': self.text,
            'file_path': self.file_path,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }