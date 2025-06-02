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

from flask import request, jsonify
import requests
import json

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("prompt", "")
    model = request.json.get("model", "gemma3:4b-it-qat")  # Default fallback
    print(f"Received model: {model!r}")

    payload = {
        "model": model,
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
        print(jsonify({"error": f"Error contacting Ollama: {e}"}))
        return jsonify({
            "error": f"Error contacting Ollama"
        }), 500


if __name__ == '__main__':
    app.run(debug=True)

