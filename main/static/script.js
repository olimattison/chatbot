function sendMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  addMessage("You", text, "user");
  input.value = "";

  showTyping(true);

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: text })
  })
    .then(res => res.json())
    .then(data => {
      showTyping(false);
      typeBotMessage(data.response);
    })
    .catch(err => {
      showTyping(false);
      addMessage("Bot", "Error: " + err.message, "bot");
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
      setTimeout(type, 15); // Adjust typing speed here
    }
  }
  type();
}

