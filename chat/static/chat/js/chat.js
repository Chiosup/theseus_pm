document.addEventListener('DOMContentLoaded', function() {
    const roomId = document.getElementById('chat-container').dataset.roomId;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const chatSocket = new WebSocket(
        wsProtocol + window.location.host + '/ws/chat/' + roomId + '/'
    );
    
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'chat_message') {
            addMessageToChat(data.message);
        }
    };
    
    function addMessageToChat(message) {
        const chatLog = document.getElementById('chat-log');
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>${message.sender.username}</strong>
                <small>${new Date(message.timestamp).toLocaleString()}</small>
            </div>
            <div class="message-content">${message.content}</div>
        `;
        chatLog.appendChild(messageElement);
        chatLog.scrollTop = chatLog.scrollHeight;
    }
    
    document.getElementById('chat-message-input').onkeyup = function(e) {
        if (e.key === 'Enter') {
            const messageInput = document.getElementById('chat-message-input');
            chatSocket.send(JSON.stringify({
                'type': 'chat_message',
                'message': messageInput.value
            }));
            messageInput.value = '';
        }
    };
    const messageForm = document.querySelector('.message-form');
    const messagesContainer = document.querySelector('.messages-container');
    
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            }).then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                }
            });
        });
    }
    
    // Автопрокрутка вниз при загрузке
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});