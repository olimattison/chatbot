// Session management
let currentSessionId = null;

function initializeSessionManager(initialSessionId) {
    currentSessionId = initialSessionId;
}

function createNewSession() {
    // Clear current session
    currentSessionId = null;
    
    // Clear messages
    document.getElementById('messagesContainer').innerHTML = `
        <div class="welcome-message">
            <i class="fas fa-comments"></i>
            <h3>New Chat Started!</h3>
            <p>Start a conversation by typing a message below.</p>
        </div>
    `;
    
    // Update active session in sidebar
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Hide error if any
    if (typeof hideError === 'function') {
        hideError();
    }
    
    // Update sidebar to show "New Chat" as active
    const newChatBtn = document.querySelector('.new-session-btn');
    if (newChatBtn) {
        newChatBtn.classList.add('active');
    }
}

function loadSession(sessionId) {
    currentSessionId = sessionId;
    
    // Update active session in sidebar
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.sessionId == sessionId) {
            item.classList.add('active');
        }
    });
    
    // Load session messages
    fetch(`/api/session/${sessionId}/messages`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayMessages(data.messages);
            } else {
                if (typeof showError === 'function') {
                    showError('Failed to load session messages');
                }
            }
        })
        .catch(error => {
            if (typeof showError === 'function') {
                showError('Error loading session: ' + error.message);
            }
        });
}

function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-comments"></i>
                <h3>Session Loaded</h3>
                <p>This session has no messages yet. Start a conversation!</p>
            </div>
        `;
        return;
    }
    
    messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <div class="message-avatar">
                        ${message.role === 'user' ? 'U' : 'AI'}
                    </div>
                    <span>${message.role === 'user' ? 'You' : 'AI Assistant'}</span>
                </div>
                <div class="message-text">${marked.parse(message.content)}</div>
            </div>
        `;
        container.appendChild(messageDiv);
    });
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Modify the original sendMessage function to include session management
function modifySendMessage() {
    // Store the original sendMessage function
    const originalSendMessage = window.sendMessage;
    
    // Create a new sendMessage function that includes session management
    window.sendMessage = async function() {
        const input = document.getElementById("userInput");
        const text = input.value.trim();
        const selectedModel = document.getElementById("modelSelect").value;

        if (!text || window.isTyping) return;

        // Clear input and add user message
        input.value = "";
        if (typeof autoResizeTextarea === 'function') {
            autoResizeTextarea(input);
        }
        if (typeof updateSendButton === 'function') {
            updateSendButton();
        }
        
        // Use the original addMessage function if available
        if (typeof addMessage === 'function') {
            addMessage("You", text, "user");
        } else {
            addMessageToUI('user', text);
        }
        
        if (typeof removeWelcomeMessage === 'function') {
            removeWelcomeMessage();
        }
        
        // Show typing indicator
        if (typeof showTypingIndicator === 'function') {
            showTypingIndicator(true);
        }
        if (typeof setLoadingState === 'function') {
            setLoadingState(true);
        }

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: text,
                    model: selectedModel,
                    session_id: currentSessionId
                })
            });

            const data = await response.json();
            
            if (data.error) {
                if (typeof showError === 'function') {
                    showError("❌ " + data.error);
                }
            } else {
                // Store session ID for future messages
                if (data.session_id) {
                    currentSessionId = data.session_id;
                }
                
                // Use the original typeBotMessage function if available
                if (typeof typeBotMessage === 'function') {
                    typeBotMessage(data.response);
                } else {
                    addMessageToUI('bot', data.response);
                }
                
                // Update sidebar without page reload
                if (data.session_id) {
                    // Update the current session in sidebar if it exists
                    const currentSessionItem = document.querySelector(`[data-session-id="${data.session_id}"]`);
                    if (currentSessionItem) {
                        // Update the session item to show it's active
                        document.querySelectorAll('.session-item').forEach(item => {
                            item.classList.remove('active');
                        });
                        currentSessionItem.classList.add('active');
                    } else {
                        // This is a new session, add it to the sidebar
                        addNewSessionToSidebar(data.session_id, text);
                    }
                }
            }
        } catch (err) {
            if (typeof showError === 'function') {
                showError("❌ Network error: " + err.message);
            }
        } finally {
            if (typeof showTypingIndicator === 'function') {
                showTypingIndicator(false);
            }
            if (typeof setLoadingState === 'function') {
                setLoadingState(false);
            }
            if (typeof focusInput === 'function') {
                focusInput();
            }
        }
    };
}

function addMessageToUI(role, content) {
    const container = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <div class="message-avatar">
                    ${role === 'user' ? 'U' : 'AI'}
                </div>
                <span>${role === 'user' ? 'You' : 'AI Assistant'}</span>
            </div>
            <div class="message-text">${marked.parse(content)}</div>
        </div>
    `;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function addNewSessionToSidebar(sessionId, firstMessage) {
    const sidebarContent = document.querySelector('.sidebar-content');
    if (!sidebarContent) return;
    
    // Remove active class from all sessions
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Create new session item
    const sessionItem = document.createElement('div');
    sessionItem.className = 'session-item active';
    sessionItem.setAttribute('data-session-id', sessionId);
    sessionItem.onclick = () => loadSession(sessionId);
    
    // Generate a simple title from the first message
    const title = firstMessage.length > 30 ? firstMessage.substring(0, 30) + '...' : firstMessage;
    
    // Get current date
    const now = new Date();
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    let dateStr;
    if (now.toDateString() === today.toDateString()) {
        dateStr = 'Today';
    } else if (now.toDateString() === yesterday.toDateString()) {
        dateStr = 'Yesterday';
    } else {
        dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    
    sessionItem.innerHTML = `
        <div class="session-title">
            ${title}
        </div>
        <div class="session-meta">
            <span>${dateStr}</span>
            <span>1 message</span>
        </div>
    `;
    
    // Insert the new session at the top of the sidebar (after the New Chat button)
    const newChatBtn = document.querySelector('.new-session-btn');
    if (newChatBtn && newChatBtn.nextSibling) {
        sidebarContent.insertBefore(sessionItem, newChatBtn.nextSibling);
    } else {
        sidebarContent.appendChild(sessionItem);
    }
    
    // Update current session ID
    currentSessionId = sessionId;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for the original script to load
    setTimeout(() => {
        modifySendMessage();
    }, 100);
}); 