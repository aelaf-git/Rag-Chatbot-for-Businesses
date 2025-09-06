// JAVASCRIPT for the Chatbot Widget

// Wait for the entire HTML document to be loaded and parsed before running our script.
document.addEventListener("DOMContentLoaded", function() {

    // --- CONFIGURATION ---
    const API_BASE_URL = "http://localhost:8000"; 
    
    // Hardcode the business ID for this test file.
    // **IMPORTANT**: Make sure you have registered a business and that its ID exists in your /data/ folder.
    const businessId = "770a8c4a-9632-495e-9a15-9d5d0f77e8fb"; // <-- Replace this with a real ID from your dashboard

    // Create the HTML structure of the widget
    const container = document.getElementById('chatbot-container');
    if (!container) {
        console.error("Chatbot Error: The div with id 'chatbot-container' was not found.");
        return;
    }
    container.innerHTML = `
        <div id="chat-bubble">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
        </div>
        <div id="chat-window">
            <div id="chat-header">
                <span>AI Assistant</span>
                <button id="close-btn">&times;</button>
            </div>
            <div id="chat-messages"></div>
            <div id="chat-input-container">
                <input type="text" id="chat-input" placeholder="Ask a question...">
                <button id="send-btn">Send</button>
            </div>
        </div>
    `;

    // Get references to the new DOM elements
    const chatBubble = document.getElementById('chat-bubble');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('close-btn');
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    
    function toggleChatWindow() {
        chatWindow.classList.toggle('open');
    }
    
    async function sendMessage() {
        const messagesContainer = document.getElementById('chat-messages');
        const question = chatInput.value.trim();

        if (!question) return;

        addMessage(question, 'user');
        chatInput.value = '';
        
        const typingIndicator = addMessage('Typing...', 'bot typing-indicator');
        
        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    businessId: businessId,
                }),
            });

            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const data = await response.json();
            typingIndicator.remove();
            addMessage(data.answer, 'bot');
        } catch (error) {
            console.error("Error fetching chat response:", error);
            typingIndicator.remove();
            addMessage("Sorry, I'm having trouble connecting. Please try again later.", 'bot');
        }
    }

    function addMessage(text, type) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return messageDiv;
    }
    
    // Add event listeners
    chatBubble.addEventListener('click', toggleChatWindow);
    closeBtn.addEventListener('click', toggleChatWindow);
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

}); // --- End of the DOMContentLoaded listener ---