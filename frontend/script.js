// Self-invoking function to avoid polluting the global scope
(function() {
    const API_BASE_URL = "http://localhost:8000";

    // Find the script tag and get the businessId from the 'data-business-id' attribute
    const scriptTag = document.currentScript;
    const businessId = scriptTag.dataset.businessId;

    if (!businessId) {
        console.error("Chatbot Error: 'data-business-id' is missing from the script tag.");
        return;
    }

    // Wait for the DOM to be ready
    document.addEventListener("DOMContentLoaded", function() {
        // Fetch the configuration from our new backend endpoint
        fetch(`${API_BASE_URL}/config/${businessId}`)
            .then(response => response.json())
            .then(config => {
                // Once we have the config, build the chatbot UI
                buildChatbotUI(config);
            })
            .catch(error => console.error("Failed to load chatbot configuration:", error));
    });

    function buildChatbotUI(config) {
        // Inject the CSS for brand color
        const style = document.createElement('style');
        style.innerHTML = `
            :root { --brand-color: ${config.brand_color}; }
            #chat-bubble, #chat-header, #send-btn { background-color: var(--brand-color); }
            .user-message { background-color: var(--brand-color); }
            #chat-input:focus { border-color: var(--brand-color); }
        `;
        document.head.appendChild(style);

        const container = document.getElementById('chatbot-container');
        if (!container) return;
        
        container.innerHTML = `
            <div id="chat-bubble">...</div>
            <div id="chat-window">
                <div id="chat-header"><span>${config.agent_name}</span>...</div>
                <div id="chat-messages"></div>
                ...
            </div>
        `;
        // (The rest of your HTML structure and event listeners from the previous script.js goes here)
        // Make sure the `addMessage` function displays the `config.welcome_message` first!
    }

    // (Your sendMessage, addMessage, and other helper functions go here)
    // The sendMessage function will already have the businessId from the outer scope.

})();