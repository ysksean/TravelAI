# flask_web/routes/land_routes.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from models import db
# [중요] LandOperator 모델 추가
from schema.land_schema import LandOperator, LandChatRoom, LandChatLog
import uuid
import os
import time
from datetime import datetime

bp = Blueprint('land', __name__, url_prefix='/land')

# 파일 업로드 경로 설정
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# 1. 랜드사 로그인 (DB 연동)
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        # 1. LandOperator 테이블에서 ID 조회 (예: 'land_vn')
        operator = LandOperator.query.filter_by(user_id=user_id).first()

        # 2. 계정이 존재하고 비밀번호가 맞는지 확인
        if operator and check_password_hash(operator.password_hash, password):

            # [핵심 로직] operator의 고유 ID(PK)로 채팅방 찾기
            # DB의 land_chat_rooms 테이블에서 operator_id가 1인 방을 찾습니다.
            room = LandChatRoom.query.filter_by(operator_id=str(operator.id)).first()

            # 방이 없으면 최초 생성 (예외 처리)
            if not room:
                print(f"🆕 [{operator.name}]님의 채팅방이 없어 새로 생성합니다.")
                new_session_id = f"land_{operator.user_id}_{uuid.uuid4().hex[:8]}"
                room = LandChatRoom(
                    session_id=new_session_id,
                    operator_id=str(operator.id),  # DB의 PK(1, 2...)를 저장
                    operator_name=operator.name,
                    status='OPEN'
                )
                db.session.add(room)
                db.session.commit()

            # 3. 세션에 필수 정보 저장 (로그인 유지용)
            session['land_session_id'] = room.session_id  # 채팅방 소켓 연결용 ID
            session['land_db_id'] = operator.id  # 랜드사 PK ID (1)
            session['land_user_id'] = operator.user_id  # 랜드사 로그인 ID (land_vn)
            session['land_name'] = operator.name  # 랜드사 이름 (베트남 투어)

            print(f"✅ 로그인 성공: {operator.name} (Room: {room.session_id})")
            return redirect(url_for('land.chat'))

        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')

    return render_template('land/login.html')


# 2. 랜드사 로그아웃
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('land.login'))


# 3. 랜드사 채팅방
@bp.route('/chat')
def chat():
    # 로그인 세션 체크
    if 'land_session_id' not in session:
        return redirect(url_for('land.login'))

    room_id = session['land_session_id']  # 'land_land_vn_...'
    operator_name = session.get('land_name', '랜드사')

    # 1. 방 정보 조회 (DB)
    room = LandChatRoom.query.filter_by(session_id=room_id).first()

    # (안전장치) 세션은 있는데 DB에서 방이 삭제된 경우 복구
    if not room:
        room = LandChatRoom(
            session_id=room_id,
            operator_id=str(session.get('land_db_id', 0)),
            operator_name=operator_name,
            status='OPEN'
        )
        db.session.add(room)
        db.session.commit()

    # 2. 대화 기록 조회 (DB)
    logs = LandChatLog.query.filter_by(session_id=room_id) \
        .order_by(LandChatLog.created_at.asc()).all()

    # 템플릿 렌더링
    return render_template('land/chat.html', room=room, logs=logs, room_id=room_id, operator_name=operator_name)


# ==========================================
# 4. 견적서 업로드 API
# ==========================================
@bp.route('/upload-quote', methods=['POST'])
def upload_quote():
    # 권한 체크
    if 'land_session_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        room_id = session['land_session_id']
        operator_name = session.get('land_name', '랜드사')
        operator_db_id = str(session.get('land_db_id', 0))

        # 방 확인 (없으면 생성)
        room = LandChatRoom.query.filter_by(session_id=room_id).first()
        if not room:
            room = LandChatRoom(
                session_id=room_id,
                operator_id=operator_db_id,
                operator_name=operator_name,
                status='OPEN'
            )
            db.session.add(room)
            db.session.commit()

        # 파일 저장
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # 메시지 타입 및 요약
        msg_type = 'json' if filename.lower().endswith('.json') else 'file'
        quote_summary = f"파일 전송: {file.filename}"

        # DB에 로그 저장
        new_log = LandChatLog(
            session_id=room_id,
            role='land',
            message_type=msg_type,
            text=quote_summary,
            file_path=f"/static/uploads/{filename}"
        )
        db.session.add(new_log)

        # 방 상태 업데이트
        room.last_message = quote_summary
        room.last_active = db.func.now()
        db.session.commit()

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'success': True,
            'message': quote_summary,
            'filepath': f"/static/uploads/{filename}",
            'created_at': now_str,  # <--- 이 부분이 핵심! (JS가 이걸 기다림)
            'role': 'land'  # (선택) 보낸 사람 역할 명시
        })

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500