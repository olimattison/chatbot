// Global variables
let currentModel = 'llama3'; // Fallback default
let isTyping = false;

// Initialize the application
document.addEventListener("DOMContentLoaded", () => {
  initializeApp();
  setupEventListeners();
});

// Initialize the app
async function initializeApp() {
  await fetchModels();
  setupTextareaAutoResize();
  focusInput();
}

// Setup event listeners
function setupEventListeners() {
  const modelSelect = document.getElementById("modelSelect");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");

  // Model selection
  modelSelect.addEventListener("change", (e) => {
    currentModel = e.target.value;
    console.log("Switched to model:", currentModel);
  });

  // Input events
  userInput.addEventListener("input", () => {
    autoResizeTextarea(userInput);
    updateSendButton();
  });

  // Focus management
  userInput.addEventListener("focus", () => {
    userInput.parentElement.style.borderColor = "var(--primary)";
  });

  userInput.addEventListener("blur", () => {
    userInput.parentElement.style.borderColor = "var(--border)";
  });
}

// Load models from Ollama and populate dropdown
async function fetchModels() {
  const select = document.getElementById("modelSelect");
  select.innerHTML = `<option disabled selected>Loading models...</option>`;

  try {
    const res = await fetch("http://localhost:11434/api/tags");
    if (!res.ok) throw new Error(`Failed to fetch models: ${res.statusText}`);

    const data = await res.json();
    if (!data.models || data.models.length === 0) {
      throw new Error("No models found. Load models into Ollama first.");
    }

    select.innerHTML = "";
    data.models.forEach(model => {
      const option = document.createElement("option");
      option.value = model.name;
      option.textContent = model.name;
      if (model.name === currentModel) option.selected = true;
      select.appendChild(option);
    });

    // Update current model to first available
    if (data.models.length > 0) {
      currentModel = data.models[0].name;
    }
  } catch (err) {
    console.error("Error fetching models from Ollama:", err);
    select.innerHTML = "";
    const option = document.createElement("option");
    option.disabled = true;
    option.selected = true;
    option.textContent = "⚠️ Unable to load models";
    select.appendChild(option);
    showError("Unable to load models. Please ensure Ollama is running.");
  }
}

// Send message function
async function sendMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  const selectedModel = document.getElementById("modelSelect").value;

  if (!text || isTyping) return;

  // Clear input and add user message
  input.value = "";
  autoResizeTextarea(input);
  updateSendButton();
  
  addMessage("You", text, "user");
  removeWelcomeMessage();
  
  // Show typing indicator
  showTypingIndicator(true);
  setLoadingState(true);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: text,
        model: selectedModel,
        session_id: window.currentSessionId || null
      })
    });

    const data = await response.json();
    
    if (data.error) {
      showError("❌ " + data.error);
    } else {
      // Store session ID for future messages
      if (data.session_id) {
        window.currentSessionId = data.session_id;
      }
      typeBotMessage(data.response);
    }
  } catch (err) {
    showError("❌ Network error: " + err.message);
  } finally {
    showTypingIndicator(false);
    setLoadingState(false);
    focusInput();
  }
}

// Add a message to the chat
function addMessage(sender, text, type) {
  const messagesContainer = document.getElementById("messagesContainer");
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;
  
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
  messageDiv.innerHTML = `
    <div class="message-content">
      <div class="message-header">
        <div class="message-avatar">
          ${type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>'}
        </div>
        <span>${sender}</span>
        <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">${timestamp}</span>
      </div>
      <div class="message-text">
        ${marked.parse(text)}
      </div>
    </div>
  `;
  
  messagesContainer.appendChild(messageDiv);
  scrollToBottom();
}

// Type bot message with animation
function typeBotMessage(fullText) {
  const messagesContainer = document.getElementById("messagesContainer");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message bot";
  
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
  messageDiv.innerHTML = `
    <div class="message-content">
      <div class="message-header">
        <div class="message-avatar">
          <i class="fas fa-robot"></i>
        </div>
        <span>AI Assistant</span>
        <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">${timestamp}</span>
      </div>
      <div class="message-text" id="typing-text"></div>
    </div>
  `;
  
  messagesContainer.appendChild(messageDiv);
  const textElement = messageDiv.querySelector("#typing-text");
  
  let i = 0;
  const typingSpeed = 15; // milliseconds per character
  
  function type() {
    if (i <= fullText.length) {
      textElement.innerHTML = marked.parse(fullText.slice(0, i));
      scrollToBottom();
      i++;
      setTimeout(type, typingSpeed);
    }
  }
  
  type();
}

// Show/hide typing indicator
function showTypingIndicator(show) {
  const indicator = document.getElementById("typingIndicator");
  indicator.style.display = show ? "flex" : "none";
  if (show) scrollToBottom();
}

// Set loading state
function setLoadingState(loading) {
  isTyping = loading;
  const sendButton = document.getElementById("sendButton");
  const userInput = document.getElementById("userInput");
  
  if (loading) {
    sendButton.disabled = true;
    userInput.disabled = true;
    sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  } else {
    sendButton.disabled = false;
    userInput.disabled = false;
    sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
  }
}

// Auto-resize textarea
function setupTextareaAutoResize() {
  const textarea = document.getElementById("userInput");
  autoResizeTextarea(textarea);
}

function autoResizeTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

// Update send button state
function updateSendButton() {
  const input = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const hasText = input.value.trim().length > 0;
  
  sendButton.disabled = !hasText || isTyping;
  sendButton.style.opacity = hasText && !isTyping ? "1" : "0.6";
}

// Handle keyboard shortcuts
function handleKeyDown(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

// Show error message
function showError(message) {
  const errorContainer = document.getElementById("errorContainer");
  const errorMessage = document.getElementById("errorMessage");
  
  errorMessage.textContent = message;
  errorContainer.style.display = "flex";
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    hideError();
  }, 5000);
}

// Hide error message
function hideError() {
  const errorContainer = document.getElementById("errorContainer");
  errorContainer.style.display = "none";
}

// Remove welcome message
function removeWelcomeMessage() {
  const welcomeMessage = document.querySelector(".welcome-message");
  if (welcomeMessage) {
    welcomeMessage.remove();
  }
}

// Scroll to bottom of messages
function scrollToBottom() {
  const messagesContainer = document.getElementById("messagesContainer");
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Focus on input
function focusInput() {
  const userInput = document.getElementById("userInput");
  userInput.focus();
}

// Export functions for global access
window.sendMessage = sendMessage;
window.handleKeyDown = handleKeyDown;
window.hideError = hideError;

