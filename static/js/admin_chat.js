const socket = io();
let currentRoomId = null;
let currentTab = 'customer';
let uploadFileObj = null;

document.addEventListener('DOMContentLoaded', () => {
    // [NEW] 1. UI 이벤트(버튼 클릭 등) 초기화 함수 실행
    initChatUI();

    // 2. 방 목록 불러오기
    fetchRooms();

    socket.on('connect', () => {
        console.log("✅ 관리자 소켓 연결됨");
    });

    socket.on('new_message', (data) => {
        if (data.room_id === currentRoomId) {
            renderMessage(data);
            scrollToBottom();
        }

        const isCustomerMsg = data.sender_type === 'customer' || (data.sender_type === 'ai' && currentTab === 'customer');
        const isLandMsg = data.sender_type === 'land';

        if ((currentTab === 'customer' && isCustomerMsg) || (currentTab === 'land' && isLandMsg)) {
            fetchRooms();
        }
    });

    socket.on('admin_alert', (data) => {
        showToast(`🚨 ${data.message}`);
        if(currentTab === 'customer') fetchRooms();
    });
});

// =========================================================
// [NEW] UI 제어 (사이드바 열기/닫기 로직 추가)
// =========================================================
function initChatUI() {
    const chatToggle = document.getElementById('chatToggle');   // 보라색 버튼
    const chatSidebar = document.getElementById('chatSidebar'); // 사이드바 패널
    const closeChat = document.getElementById('closeChat');     // 닫기(X) 버튼

    // 1. 보라색 버튼 클릭 시 -> 사이드바 열기
    if (chatToggle && chatSidebar) {
        chatToggle.addEventListener('click', () => {
            // translate-x-full 클래스를 제거하면 화면 안으로 슬라이드되어 들어옴
            chatSidebar.classList.remove('translate-x-full');

            // (선택사항) 빨간 알림 뱃지 숨기기
            const badge = chatToggle.querySelector('span.absolute');
            if(badge) badge.style.display = 'none';
        });
    }

    // 2. 닫기 버튼 클릭 시 -> 사이드바 숨기기
    if (closeChat && chatSidebar) {
        closeChat.addEventListener('click', () => {
            // translate-x-full 클래스를 추가하면 화면 밖으로 나감
            chatSidebar.classList.add('translate-x-full');
        });
    }
}

// ... (이하 기존 로직 동일) ...

function switchTab(tab) {
    if (currentTab === tab) return;
    currentTab = tab;
    currentRoomId = null;

    const btnCustomer = document.getElementById('tab-customer');
    const btnLand = document.getElementById('tab-land');

    if (tab === 'customer') {
        btnCustomer.classList.add('text-indigo-600', 'border-b-2', 'border-indigo-600');
        btnCustomer.classList.remove('text-gray-400');
        btnLand.classList.remove('text-indigo-600', 'border-b-2', 'border-indigo-600');
        btnLand.classList.add('text-gray-400');
    } else {
        btnLand.classList.add('text-indigo-600', 'border-b-2', 'border-indigo-600');
        btnLand.classList.remove('text-gray-400');
        btnCustomer.classList.remove('text-indigo-600', 'border-b-2', 'border-indigo-600');
        btnCustomer.classList.add('text-gray-400');
    }

    fetchRooms();

    document.getElementById('currentChatUser').innerText = "대화 상대를 선택하세요";
    document.getElementById('currentChatStatus').innerText = "ID: -";
    document.getElementById('chatMessages').innerHTML = `
        <div class="h-full flex flex-col items-center justify-center text-gray-400 gap-2 opacity-60">
            <i class="far fa-comments text-3xl"></i>
            <p class="text-xs">상담 내역이 여기에 표시됩니다.</p>
        </div>
    `;
}

async function fetchRooms() {
    const listContainer = document.getElementById('chatRoomList');
    try {
        const url = currentTab === 'customer' ? '/admin/rooms' : '/admin/land-rooms';

        const res = await axios.get(url);
        const rooms = res.data;

        listContainer.innerHTML = '';

        if (!rooms || rooms.length === 0) {
            listContainer.innerHTML = '<div class="p-4 text-center text-gray-400 text-xs">대화 방이 없습니다.</div>';
            return;
        }

        rooms.forEach(room => {
            const id = room.session_id;
            const name = currentTab === 'customer' ? (room.user_name || '익명') : (room.operator_name || '랜드사');
            const lastMsg = room.last_message || '대화 내용 없음';
            const time = room.last_active || '';
            const status = room.status || 'OPEN';

            const iconClass = currentTab === 'customer' ? 'fa-user' : 'fa-building';
            const iconBg = currentTab === 'customer' ? 'bg-indigo-100 text-indigo-500' : 'bg-green-100 text-green-500';
            const isActive = (id === currentRoomId) ? 'bg-indigo-50 border-indigo-200' : 'border-transparent hover:bg-gray-50';

            const html = `
                <div onclick="enterRoom('${id}', '${name}')"
                     class="flex items-center gap-3 p-3 cursor-pointer border-b transition-colors ${isActive}">
                    <div class="w-10 h-10 rounded-full ${iconBg} flex items-center justify-center shrink-0">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-start mb-1">
                            <h4 class="font-bold text-sm text-gray-800 truncate">${name}</h4>
                            <span class="text-[10px] text-gray-400">${time.substring(5, 16) || ''}</span>
                        </div>
                        <p class="text-xs text-gray-500 truncate">${lastMsg}</p>
                    </div>
                </div>
            `;
            listContainer.insertAdjacentHTML('beforeend', html);
        });

    } catch (err) {
        console.error("방 목록 로드 실패:", err);
        listContainer.innerHTML = '<div class="p-4 text-center text-red-400 text-xs">목록 로드 실패</div>';
    }
}

async function enterRoom(roomId, name) {
    currentRoomId = roomId;

    document.getElementById('currentChatUser').innerText = name;
    document.getElementById('currentChatStatus').innerText = `ID: ${roomId}`;

    fetchRooms();

    const msgBox = document.getElementById('chatMessages');
    msgBox.innerHTML = '<div class="h-full flex items-center justify-center"><i class="fas fa-spinner fa-spin text-gray-400"></i></div>';

    try {
        const url = currentTab === 'customer'
            ? `/admin/history/${roomId}`
            : `/admin/land-history/${roomId}`;

        const res = await axios.get(url);
        const logs = res.data;

        msgBox.innerHTML = '';

        if (logs.length === 0) {
            msgBox.innerHTML = '<div class="p-4 text-center text-gray-300 text-xs">대화 내역이 없습니다.</div>';
        } else {
            logs.forEach(log => renderMessage(log));
            scrollToBottom();
        }

    } catch (err) {
        console.error(err);
        msgBox.innerHTML = '<div class="p-4 text-center text-red-400 text-xs">내역 로드 실패</div>';
    }
}

function renderMessage(log) {
    const msgBox = document.getElementById('chatMessages');
    const role = log.role; // 'admin', 'customer', 'land', 'ai'

    // [핵심 수정] 관리자가 보낸 메시지인지 판단
    // role이 'admin'이면 무조건 관리자 메시지임
    const isAdmin = (role === 'admin');

    let bubbleClass = '';
    let alignClass = '';
    let senderName = '';

    if (isAdmin) {
        // 관리자가 보낸 경우 (오른쪽 정렬)
        alignClass = 'justify-end';
        bubbleClass = 'bg-indigo-600 text-white rounded-tr-none';
        senderName = '상담원'; // 또는 '관리자'
    } else {
        // 상대방이 보낸 경우 (왼쪽 정렬)
        alignClass = 'justify-start';
        bubbleClass = 'bg-white border border-gray-200 text-gray-800 rounded-tl-none';

        // 상대방 이름 결정 로직
        if (role === 'ai') {
            senderName = 'Travel AI';
            bubbleClass = 'bg-gray-100 text-slate-600 border border-gray-100';
        }
        else if (role === 'land') {
            // [중요] 랜드사 채팅일 때 상대방 이름
            // log.operator_name이 있으면 쓰고, 없으면 '랜드사'
            senderName = log.operator_name || '랜드사';
        }
        else {
            // 고객 채팅일 때 상대방 이름
            senderName = log.user_name || '고객';
        }
    }

    // 메시지 내용 처리 (파일/텍스트)
    let content = log.text || log.message || '';

    // 파일/JSON 처리 로직
    if (log.file_path || log.type === 'file' || log.type === 'json' || (log.message_type && log.message_type !== 'text')) {
        const filePath = log.file_path || '#';
        // message_type이 json이거나 파일명이 .json으로 끝날 때
        const isJson = (log.message_type === 'json') || (log.type === 'json') || (filePath.endsWith('.json'));

        if (isJson) {
            content = `
                <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-green-100 text-green-600 rounded flex items-center justify-center"><i class="fas fa-file-invoice"></i></div>
                    <div>
                        <p class="font-bold text-xs underline mb-0.5">견적서 도착</p>
                        <a href="${filePath}" target="_blank" class="text-xs hover:text-indigo-200 break-all">${content}</a>
                    </div>
                </div>
            `;
        } else {
             content = `
                <div class="flex items-center gap-2">
                     <div class="w-8 h-8 bg-blue-100 text-blue-600 rounded flex items-center justify-center"><i class="fas fa-paperclip"></i></div>
                    <a href="${filePath}" target="_blank" class="text-xs hover:underline break-all">첨부파일 다운로드</a>
                </div>
            `;
        }
    } else {
        // 일반 텍스트는 줄바꿈 처리
        if (content) content = content.replace(/\n/g, '<br>');
    }

    // HTML 생성 및 추가
    const html = `
        <div class="flex ${alignClass} animate-fade-in-up mb-4">
            <div class="flex flex-col max-w-[75%]">
                <span class="text-[10px] text-gray-400 mb-1 ${isAdmin ? 'text-right' : 'text-left'}">${senderName}</span>
                <div class="px-4 py-2.5 rounded-lg shadow-sm text-sm ${bubbleClass} leading-relaxed">
                    ${content}
                </div>
                <span class="text-[9px] text-gray-300 mt-1 ${isAdmin ? 'text-right' : 'text-left'}">
                    ${log.timestamp || new Date().toLocaleTimeString()}
                </span>
            </div>
        </div>
    `;
    msgBox.insertAdjacentHTML('beforeend', html);
}

async function sendAdminMessage() {
    if (!currentRoomId) {
        showToast("대화 상대를 먼저 선택해주세요.");
        return;
    }

    if (uploadFileObj) {
        await uploadAndSendFile();
        return;
    }

    const input = document.getElementById('adminChatInput');
    const msg = input.value.trim();
    if (!msg) return;

    const eventName = currentTab === 'customer' ? 'send_message' : 'send_land_message';

    socket.emit(eventName, {
        room_id: currentRoomId,
        sender_type: 'admin',
        message: msg,
        user_name: '상담원'
    });

    input.value = '';
}

function handleFileSelect(input) {
    if (input.files && input.files[0]) {
        uploadFileObj = input.files[0];
        document.getElementById('fileName').innerText = uploadFileObj.name;
        document.getElementById('filePreview').classList.remove('hidden');
    }
}

function clearFile() {
    uploadFileObj = null;
    document.getElementById('adminFileInput').value = '';
    document.getElementById('filePreview').classList.add('hidden');
}

async function uploadAndSendFile() {
    const formData = new FormData();
    formData.append('file', uploadFileObj);

    try {
        const res = await axios.post('/admin/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (res.data.success) {
            const eventName = currentTab === 'customer' ? 'send_message' : 'send_land_message';

            socket.emit(eventName, {
                room_id: currentRoomId,
                sender_type: 'admin',
                message: uploadFileObj.name,
                type: 'file',
                file_path: res.data.filepath
            });
            clearFile();
        } else {
            alert('업로드 실패');
        }
    } catch (err) {
        console.error(err);
        alert('업로드 중 오류 발생');
    }
}

function handleEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendAdminMessage();
    }
}

function scrollToBottom() {
    const msgBox = document.getElementById('chatMessages');
    msgBox.scrollTop = msgBox.scrollHeight;
}

function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = "fixed top-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow-lg z-50 text-sm animate-fade-in-up";
    toast.innerHTML = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
// [NEW] 인보이스 생성 및 전송 함수
async function createAndSendInvoice() {
    if (!currentRoomId) {
        showToast("대화 상대를 먼저 선택해주세요.");
        return;
    }

    // 1. 랜드사에서 받은 최신 견적 데이터 준비 (예시 데이터)
    // 실제로는 현재 보고 있는 채팅방의 컨텍스트나, 관리자가 입력한 폼 데이터를 가져와야 합니다.
    // 여기서는 질문주신 JSON 데이터를 그대로 예시로 사용합니다.
    const invoiceData = {
        "product_name": "중국 심천 미션힐 리조트 4박 5일 명품 골프 투어",
        "start_date": "2025-12-07",
        "end_date": "2025-12-11",
        "nights": 4,
        "days": 5,
        "price_adult": 1890000,
        "head_counts": 6, // 6명으로 변경됨
        "total_price": 11340000,
        "details": JSON.stringify({
            "inclusions": ["왕복 항공료", "미션힐 리조트 4박", "조식/석식", "그린피/캐디피/카트비"],
            "exclusions": ["캐디팁", "중식", "비자", "개인경비"]
        })
    };

    try {
        showToast("⏳ 인보이스 생성 중...");

        // 2. 서버에 엑셀 생성 요청
        const res = await axios.post('/admin/generate-invoice', invoiceData);

        if (res.data.success) {
            // 3. 생성된 엑셀 파일을 채팅방으로 전송
            const socketData = {
                room_id: currentRoomId,
                sender_type: 'admin',
                message: '인보이스가 발행되었습니다.',
                type: 'file', // 혹은 'invoice' 타입 정의 가능
                file_path: res.data.filepath,
                user_name: '상담원'
            };

            // 소켓 전송 (고객용/랜드사용 구분)
            const eventName = currentTab === 'customer' ? 'send_message' : 'send_land_message';
            socket.emit(eventName, socketData);

            showToast("✅ 인보이스 발송 완료!");
            // (선택) 내 채팅창에도 바로 표시하려면 fetchRooms() 호출
        } else {
            alert("인보이스 생성 실패: " + res.data.error);
        }
    } catch (err) {
        console.error(err);
        alert("서버 통신 오류");
    }
}