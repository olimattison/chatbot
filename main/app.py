"""
chatbot/main/app.py

This is the folder for the non Docker setup. i.e. Ollama is already installed and running
on the host machine. In this case, app.py can be directly run from this folder, no docker needed. 

"""

from flask import Flask, request, jsonify, render_template
import requests
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("prompt", "")

    payload = {
        "model": "gemma3:1b-it-qat",
        "prompt": user_input,
        "stream": True
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True)
        response.raise_for_status()

        reply = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                reply += data.get("response", "")

        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"response": f"Error contacting Ollama: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

