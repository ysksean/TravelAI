document.addEventListener('DOMContentLoaded', function () {
    const chatToggle = document.getElementById('chatToggle');
    const chatSidebar = document.getElementById('chatSidebar');
    const closeChat = document.getElementById('closeChat');
    const chatMessagesArea = document.getElementById('chatMessages');

    // Toggle Sidebar
    if (chatToggle && chatSidebar) {
        chatToggle.addEventListener('click', () => {
            chatSidebar.classList.toggle('translate-x-full');
            if (!chatSidebar.classList.contains('translate-x-full')) {
                // Fetch immediately when opened
                fetchChatHistory();
            }
        });
    }

    // Close Sidebar
    if (closeChat && chatSidebar) {
        closeChat.addEventListener('click', () => {
            chatSidebar.classList.add('translate-x-full');
        });
    }

    // --- SESSION-BASED CHAT LOGIC ---
    let currentSessionId = null;

    // 1. Fetch & Render Rooms (Sidebar)
    async function fetchRooms() {
        const listContainer = document.querySelector('.chat-room-item')?.parentElement;
        // Need to find the container. Usually it's the one with .overflow-y-auto inside the sidebar.
        // Let's assume the structure is preserved.
        // Best to select the container directly if possible.
        // 채팅 수정내용
        let container = document.querySelector('#chatSidebar .overflow-y-auto.custom-scrollbar .space-y-1');
        if (!container && listContainer) container = listContainer; // Fallback
        if (!container) return; // Cannot find list container

        try {
            const res = await fetch('/api/chat/rooms');
            if (res.ok) {
                const rooms = await res.json();
                renderRooms(rooms, container);
            }
        } catch (err) {
            console.error('Failed to fetch rooms:', err);
        }
    }

    function renderRooms(rooms, container) {
        container.innerHTML = ''; // Clear existing

        if (rooms.length === 0) {
            container.innerHTML = '<div class="p-4 text-center text-gray-400 text-xs">상담 내역이 없습니다.</div>';
            return;
        }

        rooms.forEach(room => {
            const el = document.createElement('div');
            el.className = 'chat-room-item p-3 rounded-xl hover:bg-gray-50 cursor-pointer transition-all border-l-4 border-transparent flex gap-3 group';
            // Highlight if selected
            if (room.session_id === currentSessionId) {
                el.classList.remove('border-transparent');
                el.classList.add('bg-indigo-50/60', 'border-indigo-500');
            }

            // Name & Time
            const displayName = room.user_name || 'Anonymous';
            let timeStr = '';
            if (room.last_active) {
                const date = new Date(room.last_active);
                // Simple formatting
                timeStr = date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
            }
            const initial = displayName.charAt(0);
            const badgeColor = room.user_type === 'member' ? 'bg-green-100 text-green-600' : 'bg-indigo-100 text-indigo-600';

            el.innerHTML = `
                <div class="relative">
                    <div class="w-10 h-10 rounded-full ${badgeColor} flex items-center justify-center font-bold text-sm shadow-sm">${initial}</div>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-center mb-0.5">
                        <span class="font-bold text-gray-800 text-sm room-name truncate">${displayName}</span>
                        <span class="text-[10px] text-gray-400 font-medium">${timeStr}</span>
                    </div>
                    <p class="text-xs text-gray-500 truncate group-hover:text-gray-700">
                        <span class="bg-gray-100 px-1 rounded text-[10px] mr-1">${room.user_type}</span>
                        ${room.session_id.substring(0, 8)}...
                    </p>
                </div>
            `;

            el.addEventListener('click', () => {
                currentSessionId = room.session_id;
                // Update UI selection immediately
                document.querySelectorAll('.chat-room-item').forEach(i => {
                    i.classList.remove('bg-indigo-50/60', 'border-indigo-500');
                    i.classList.add('border-transparent');
                });
                el.classList.remove('border-transparent');
                el.classList.add('bg-indigo-50/60', 'border-indigo-500');

                // Update Header Info
                const headerUser = document.getElementById('currentChatUser');
                if (headerUser) headerUser.textContent = displayName;

                // Load Chat
                fetchChatHistory();
            });

            container.appendChild(el);
        });
    }

    // 2. Fetch History (Specific Session)
    async function fetchChatHistory() {
        if (!chatMessagesArea) return;

        if (!currentSessionId) {
            chatMessagesArea.innerHTML = `
                <div class="h-full flex flex-col items-center justify-center text-gray-400 gap-4 opacity-50">
                    <i class="fas fa-comments text-4xl"></i>
                    <p class="text-sm">상담 목록에서 대화를 선택해주세요.</p>
                </div>`; // <-- 이 메시지가 기본 화면이 됩니다.
            return;
        }

        try {
            const res = await fetch(`/api/chat/history?session_id=${currentSessionId}`);
            if (res.ok) {
                const messages = await res.json();
                renderMessages(messages);
            }
        } catch (err) {
            console.error('Failed to fetch chat history:', err);
        }
    }

    // 3. Render Messages (Same Logic)
    function renderMessages(messages) {
        chatMessagesArea.innerHTML = ''; // Clear existing

        if (messages.length === 0) {
            chatMessagesArea.innerHTML = `
                <div class="h-full flex flex-col items-center justify-center text-gray-400 gap-4 opacity-50">
                    <i class="fas fa-history text-4xl"></i>
                    <p class="text-sm">대화 기록이 없습니다.</p>
                </div>`;
            return;
        }

        messages.forEach(msg => {
            const isUser = msg.sender === 'user';
            const msgWrapper = document.createElement('div');
            msgWrapper.className = `flex w-full ${isUser ? 'justify-start' : 'justify-end'} mb-4 animate-fade-in-up`;

            let timeStr = '';
            if (msg.created_at) {
                const date = new Date(msg.created_at);
                timeStr = date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
            }

            let topLabel = '';
            // Only show detailed label for user, keep simple for bot
            if (isUser) {
                topLabel = `<span class="text-[10px] text-gray-500 mb-1 ml-1 block">${msg.user_name}</span>`;
            } else {
                topLabel = `<span class="text-[10px] text-gray-500 mb-1 mr-1 block text-right">AI Agent</span>`;
            }

            const innerHTML = isUser ? `
                <div class="flex flex-col max-w-[85%]">
                    ${topLabel}
                    <div class="flex gap-3">
                        <div class="w-8 h-8 rounded-full bg-blue-100 flex-shrink-0 flex items-center justify-center text-blue-600 text-xs shadow-sm">
                            <i class="fas fa-user"></i>
                        </div>
                        <div class="flex flex-col gap-1">
                            <div class="bg-indigo-50 border border-indigo-100 p-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-gray-800 leading-relaxed">
                                ${msg.message}
                            </div>
                            <span class="text-[10px] text-gray-400 ml-1">${timeStr}</span>
                        </div>
                    </div>
                </div>
            ` : `
                 <div class="flex flex-col items-end max-w-[85%]">
                    ${topLabel}
                    <div class="flex gap-3 flex-row-reverse">
                         <div class="w-8 h-8 rounded-full bg-gray-200 flex-shrink-0 flex items-center justify-center text-gray-600 text-xs shadow-sm">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="flex flex-col gap-1 items-end">
                            <div class="bg-gray-100 p-3 rounded-2xl rounded-tr-none shadow-sm text-sm text-gray-700 leading-relaxed text-right">
                                ${msg.message}
                            </div>
                            <span class="text-[10px] text-gray-400 mr-1 flex items-center gap-1">
                                ${timeStr} <i class="fas fa-check text-gray-400 text-[8px]"></i>
                            </span>
                        </div>
                    </div>
                </div>
            `;

            msgWrapper.innerHTML = innerHTML;
            chatMessagesArea.appendChild(msgWrapper);
        });
        chatMessagesArea.scrollTop = chatMessagesArea.scrollHeight;
    }

    // Init: Fetch Rooms initially
    fetchRooms();
    // Poll rooms less frequently
    setInterval(fetchRooms, 10000);

    // Poll current chat if active
    setInterval(() => {
        if (currentSessionId) fetchChatHistory();
    }, 3000);
});