// 이 파일에 있는 내용은 전부 채팅 내용 저장하고 표시하는 데에 필요한 함수입니다!


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const sendButton = document.querySelector('.input-area button');
const messageInput = document.querySelector('.input-area input');
const chatroomId = window.location.pathname.split('/').filter(Boolean).pop(); // URL에서 채팅방 ID 가져오기

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

function sendMessage() {
    const content = messageInput.value.trim();
    if (content === '') {
        return;
    }

    fetch('/chat/send-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'chatroom_id': chatroomId,
            'content': content
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('네트워크 응답 오류');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            console.log('메시지 전송 성공');
            messageInput.value = ''; // 입력창 비우기

            const chatContainer = document.querySelector('.chat-container');
            const newMessageElement = createMessageElement(content, 'sent');
            chatContainer.appendChild(newMessageElement);
            chatContainer.scrollTop = chatContainer.scrollHeight; // 스크롤 맨 아래로 이동

        } else {
            console.error('메시지 전송 실패:', data.error);
            alert('메시지 전송 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('에러 발생:', error);
        alert('메시지 전송 중 오류가 발생했습니다.');
    });
}

function createMessageElement(content, type) {
    const messageBox = document.createElement('div');
    messageBox.classList.add('message-box', type);

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${type}-message`);

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');

    const p = document.createElement('p');
    p.textContent = content;

    const timestampSpan = document.createElement('span');
    timestampSpan.classList.add('message-timestamp');
    timestampSpan.textContent = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });

    messageContent.appendChild(p);
    messageContent.appendChild(timestampSpan);
    messageDiv.appendChild(messageContent);
    messageBox.appendChild(messageDiv);

    return messageBox;
}