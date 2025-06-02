let currentModel = 'llama3'; // Fallback default

// Load models from Ollama and populate dropdown
async function fetchModels() {
  const select = document.getElementById("modelSelect");
  select.innerHTML = `<option>Loading...</option>`;

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
  } catch (err) {
    console.error("Error fetching models from Ollama:", err);
    select.innerHTML = "";
    const option = document.createElement("option");
    option.disabled = true;
    option.selected = true;
    option.textContent = "⚠️ Unable to load models";
    select.appendChild(option);

  }
}

// On load: get model list and attach listener
document.addEventListener("DOMContentLoaded", () => {
  fetchModels();

  const select = document.getElementById("modelSelect");
  select.addEventListener("change", (e) => {
    currentModel = e.target.value;
    console.log("Switched to model:", currentModel);
  });
});

function sendMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  const selectedModel = document.getElementById("modelSelect").value;

  if (!text) return;

  addMessage("You", text, "user");
  input.value = "";

  showTyping(true);
  
  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
    prompt: text,
    model: selectedModel
    })
  })
    .then(res => res.json())
   .then(data => {
    showTyping(false);
    if (data.error) {
        showError("❌ " + data.error);
    } else {
        typeBotMessage(data.response);
    }
    })
    .catch(err => {
    showTyping(false);
    showError("❌ Error: " + err.message);
    });

}

function addMessage(sender, text, cls) {
  const messages = document.getElementById("messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = cls;
  msgDiv.innerHTML = `<strong>${sender}:</strong><br>${marked.parse(text)}`;
  messages.appendChild(msgDiv);
  messages.scrollTop = messages.scrollHeight;
}

function showTyping(show) {
  document.getElementById("typing").style.display = show ? "block" : "none";
}

function typeBotMessage(fullText) {
  const messages = document.getElementById("messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = "bot";
  msgDiv.innerHTML = "<strong>Bot:</strong><br>";
  const contentSpan = document.createElement("div");
  msgDiv.appendChild(contentSpan);
  messages.appendChild(msgDiv);

  let i = 0;
  function type() {
    contentSpan.innerHTML = marked.parse(fullText.slice(0, i));
    messages.scrollTop = messages.scrollHeight;
    if (i <= fullText.length) {
      i++;
      setTimeout(type, 15); // Typing speed
    }
  }
  type();
}

function showError(message) {
  const box = document.getElementById("errorBox");
  const msg = document.getElementById("errorMessage");
  msg.textContent = message;
  box.style.display = "block";
}

function hideError() {
  document.getElementById("errorBox").style.display = "none";
}

