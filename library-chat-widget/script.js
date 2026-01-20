
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('lcw-toggle-btn');
    const closeBtn = document.getElementById('lcw-close-btn');
    const chatWindow = document.getElementById('lcw-chat-window');
    const sendBtn = document.getElementById('lcw-send-btn');
    const inputField = document.getElementById('lcw-input');
    const messagesContainer = document.getElementById('lcw-messages');

    if(!toggleBtn) return; // Exit if elements don't exist (e.g. wrong page)

    function toggleChat() {
        if (chatWindow.style.display === 'none') {
            chatWindow.style.display = 'flex';
            toggleBtn.style.display = 'none';
        } else {
            chatWindow.style.display = 'none';
            toggleBtn.style.display = 'flex';
        }
    }
    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    function parseMarkdown(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('lcw-message', sender);
        if (sender === 'bot') {
            div.innerHTML = parseMarkdown(text);
        } else {
            div.textContent = text;
        }
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        inputField.value = '';
        inputField.disabled = true;
        sendBtn.disabled = true;

        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('lcw-message', 'bot');
        loadingDiv.id = 'lcw-loading';
        loadingDiv.textContent = 'Thinking...';
        messagesContainer.appendChild(loadingDiv);

        try {
            const res = await fetch(lcwSettings.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });
            const data = await res.json();
            document.getElementById('lcw-loading').remove();
            
            if (data.answer) {
                addMessage(data.answer, 'bot');
            } else {
                addMessage("I'm sorry, I didn't get a response.", 'bot');
            }
        } catch (err) {
            console.error(err);
            document.getElementById('lcw-loading').remove();
            addMessage("Error connecting to server. Please try again later.", 'bot');
        } finally {
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
