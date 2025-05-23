const sendBtn = document.getElementById('sendBtn');
const promptInput = document.getElementById('promptInput');
const chatbox = document.getElementById('chatbox');

sendBtn.addEventListener('click', async () => {
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  chatbox.innerHTML += `<p><strong>You:</strong> ${prompt}</p>`;
  promptInput.value = '';

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });

    const data = await res.json();
    chatbox.innerHTML += `<p><strong>Bot:</strong> ${data.response}</p>`;
  } catch (err) {
    console.error(err);
    chatbox.innerHTML += `<p><strong>Error:</strong> Failed to contact server.</p>`;
  }
});

