document.addEventListener('DOMContentLoaded', function () {
    // --------------------------------------------------------
    // 1. 선택자 설정 (base.html의 ID와 일치해야 함)
    // --------------------------------------------------------
    const chatToggle = document.getElementById('chatToggle');
    const chatSidebar = document.getElementById('chatSidebar');
    const closeChat = document.getElementById('closeChat');

    // [중요] 방금 base.html에 추가한 ID
    const roomListContainer = document.getElementById('chatRoomList');

    const chatMessagesArea = document.getElementById('chatMessages');
    const msgInput = document.querySelector('#chatSidebar textarea');
    const sendBtn = document.querySelector('#chatSidebar button .fa-paper-plane')?.parentElement;

    // Socket.IO 연결
    const socket = io();
    let currentSessionId = null;

    // --------------------------------------------------------
    // 2. 소켓 로직
    // --------------------------------------------------------
    socket.on('connect', () => {
        console.log("✅ [Admin] 소켓 연결됨");
        if (currentSessionId) {
            socket.emit('join', { room_id: currentSessionId, user_type: 'admin' });
        }
    });

    socket.on('new_message', (data) => {
        // 새 메시지가 오면 목록 갱신
        fetchRooms();

        // 현재 보고 있는 방이면 메시지 추가
        if (currentSessionId === data.room_id) {
            renderSingleMessage({
                sender_type: data.sender_type || data.role,
                message: data.message || data.text,
                timestamp: data.timestamp,
                user_name: data.user_name
            });
        }
    });

    // --------------------------------------------------------
    // 3. UI 이벤트 (사이드바 토글)
    // --------------------------------------------------------
    if (chatToggle) {
        chatToggle.addEventListener('click', () => {
            if (chatSidebar) {
                chatSidebar.classList.toggle('translate-x-full');
                if (!chatSidebar.classList.contains('translate-x-full')) {
                    fetchRooms(); // 열릴 때 DB에서 목록 가져오기
                }
            }
        });
    }

    if (closeChat && chatSidebar) {
        closeChat.addEventListener('click', () => {
            chatSidebar.classList.add('translate-x-full');
        });
    }

    // --------------------------------------------------------
    // 4. 데이터 로직 (API 호출 -> 화면 그리기)
    // --------------------------------------------------------

    // (1) 방 목록 가져오기
    async function fetchRooms() {
        if (!roomListContainer) return;

        try {
            // [API 호출] 실제 DB 데이터를 가져옴
            const res = await axios.get('/api/admin/rooms');
            const rooms = res.data;
            renderRooms(rooms);
        } catch (err) {
            console.error('방 목록 로드 실패:', err);
            roomListContainer.innerHTML = '<div class="p-4 text-center text-gray-400 text-xs">데이터 로드 실패</div>';
        }
    }

    // (2) 방 목록 그리기 (HTML 생성)
    function renderRooms(rooms) {
        roomListContainer.innerHTML = ''; // 기존 목록 초기화

        if (!rooms || rooms.length === 0) {
            roomListContainer.innerHTML = '<div class="p-4 text-center text-gray-400 text-xs">진행 중인 상담이 없습니다.</div>';
            return;
        }

        rooms.forEach(room => {
            const el = document.createElement('div');
            const isActive = room.session_id === currentSessionId;

            // base.html의 디자인 클래스 적용
            el.className = `chat-room-item p-3 rounded-xl hover:bg-gray-50 cursor-pointer transition-all border-l-4 flex gap-3 group ${isActive ? 'bg-indigo-50/60 border-indigo-500' : 'border-transparent'}`;

            // 날짜/시간 처리
            let timeStr = '';
            if (room.created_at) {
                timeStr = new Date(room.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
            }

            // 이니셜 추출
            const displayName = room.user_name || '익명';
            const initial = displayName.charAt(0);
            const badgeColor = room.user_type === 'VIP' ? 'bg-orange-100 text-orange-600' : 'bg-indigo-100 text-indigo-600';

            // HTML 조립
            el.innerHTML = `
                <div class="relative">
                    <div class="w-10 h-10 rounded-full ${badgeColor} flex items-center justify-center font-bold text-sm shadow-sm">${initial}</div>
                    ${room.status === 'OPEN' ? '<span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-white rounded-full"></span>' : ''}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-center mb-0.5">
                        <span class="font-bold text-gray-800 text-sm room-name truncate">${displayName}</span>
                        <span class="text-[10px] text-gray-400 font-medium">${timeStr}</span>
                    </div>
                    <p class="text-xs text-gray-500 truncate group-hover:text-gray-700">
                        ${room.last_message || '대화 내역을 확인하세요.'}
                        <span class="text-[10px] text-gray-400">(${room.session_id})</span>
                    </p>
                </div>
            `;

            // 클릭 시 입장
            el.addEventListener('click', () => {
                enterChatRoom(room.session_id, displayName);
            });

            roomListContainer.appendChild(el);
        });
    }

    // (3) 채팅방 입장
    async function enterChatRoom(sessionId, userName) {
        currentSessionId = sessionId;

        // 헤더 업데이트
        const headerUser = document.getElementById('currentChatUser');
        const headerStatus = document.getElementById('currentChatStatus');
        if (headerUser) headerUser.textContent = userName;
        if (headerStatus) headerStatus.textContent = `Session: ${sessionId}`;

        // 채팅창 비우기
        chatMessagesArea.innerHTML = '';

        // 소켓 Join
        socket.emit('join', { room_id: sessionId, user_type: 'admin' });

        // 과거 내역 불러오기
        try {
            const res = await axios.get(`/api/admin/history/${sessionId}`);
            const messages = res.data;

            if (messages.length === 0) {
                chatMessagesArea.innerHTML = `
                    <div class="h-full flex flex-col items-center justify-center text-gray-400 gap-4 opacity-50">
                        <i class="fas fa-history text-4xl"></i>
                        <p class="text-sm">대화 기록이 없습니다.</p>
                    </div>`;
            } else {
                messages.forEach(msg => {
                    renderSingleMessage({
                        sender_type: msg.role,
                        message: msg.text,
                        timestamp: msg.timestamp,
                        user_name: msg.user_name
                    });
                });
            }
        } catch (err) {
            console.error('내역 로드 실패:', err);
        }

        // 목록 스타일 갱신 (선택된 방 하이라이트)
        fetchRooms();
    }

    // (4) 메시지 전송
    function sendAdminMessage() {
        if (!msgInput || !currentSessionId) return;
        const message = msgInput.value.trim();
        if (!message) return;

        socket.emit('send_message', {
            room_id: currentSessionId,
            sender_type: 'admin',
            message: message,
            user_name: '상담원'
        });
        msgInput.value = '';
    }

    // --------------------------------------------------------
    // 5. 메시지 렌더링 (말풍선 그리기)
    // --------------------------------------------------------
    function renderSingleMessage(data) {
        // Placeholder 제거
        if (chatMessagesArea.querySelector('.fa-comments') || chatMessagesArea.querySelector('.fa-history')) {
            chatMessagesArea.innerHTML = '';
        }

        const isMe = data.sender_type === 'admin';
        const isAI = data.sender_type === 'ai' || data.sender_type === 'bot';
        const isCustomer = !isMe && !isAI;

        const msgWrapper = document.createElement('div');
        msgWrapper.className = `flex w-full ${isMe ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in-up`;

        const timeStr = data.timestamp
            ? new Date(data.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });

        // 라벨 및 아이콘 설정
        let topLabel = '', iconHtml = '', bubbleClass = '';

        if (isMe) {
            iconHtml = `<div class="w-8 h-8 rounded-full bg-gray-200 flex-shrink-0 flex items-center justify-center text-gray-600 text-xs shadow-sm"><i class="fas fa-headset"></i></div>`;
            bubbleClass = 'bg-gray-100 p-3 rounded-2xl rounded-tr-none shadow-sm text-sm text-gray-700 leading-relaxed text-right';
        } else if (isAI) {
            topLabel = `<span class="text-[10px] text-indigo-500 mb-1 ml-1 block font-bold">Travel AI</span>`;
            iconHtml = `<div class="w-8 h-8 rounded-full bg-indigo-100 flex-shrink-0 flex items-center justify-center text-indigo-600 text-xs shadow-sm"><i class="fas fa-robot"></i></div>`;
            bubbleClass = 'bg-indigo-50 border border-indigo-100 p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-gray-800 leading-relaxed';
        } else {
            topLabel = `<span class="text-[10px] text-gray-500 mb-1 ml-1 block">${data.user_name || '고객'}</span>`;
            iconHtml = `<div class="w-8 h-8 rounded-full bg-blue-100 flex-shrink-0 flex items-center justify-center text-blue-600 text-xs shadow-sm"><i class="fas fa-user"></i></div>`;
            bubbleClass = 'bg-white border border-gray-200 p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-gray-800 leading-relaxed';
        }

        msgWrapper.innerHTML = `
            <div class="flex flex-col ${isMe ? 'items-end' : ''} max-w-[85%]">
                ${topLabel}
                <div class="flex gap-3 ${isMe ? 'flex-row-reverse' : ''}">
                    ${iconHtml}
                    <div class="flex flex-col gap-1 ${isMe ? 'items-end' : ''}">
                        <div class="${bubbleClass}">${data.message.replace(/\n/g, '<br>')}</div>
                        <span class="text-[10px] text-gray-400 mx-1">${timeStr}</span>
                    </div>
                </div>
            </div>`;

        chatMessagesArea.appendChild(msgWrapper);
        chatMessagesArea.scrollTop = chatMessagesArea.scrollHeight;
    }

    // 이벤트 리스너
    if (sendBtn) sendBtn.addEventListener('click', sendAdminMessage);
    if (msgInput) {
        msgInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAdminMessage();
            }
        });
    }

    // 초기 실행
    fetchRooms();

    // [NEW] 상담원 호출 알림 수신
    socket.on('admin_alert', (data) => {
        console.log("🚨 상담원 호출:", data);
        showAdminToast(data.message, data.room_id);

        // 목록 갱신 (빨간불 들어오게 하려면 추후 CSS 작업 필요)
        fetchRooms();
    });

    // 토스트 메시지 UI (화면 우측 상단에 뜸)
    function showAdminToast(msg, roomId) {
        let toast = document.getElementById('adminToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'adminToast';
            toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 transition-opacity duration-300 hidden';
            document.body.appendChild(toast);
        }

        toast.innerHTML = `<div class="font-bold mb-1"><i class="fas fa-bell"></i> 긴급 알림</div><div class="text-sm">${msg}</div>`;
        toast.classList.remove('hidden');

        setTimeout(() => { toast.classList.add('hidden'); }, 5000);
    }
});