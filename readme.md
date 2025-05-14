# Chatbot
### Basic AI chatbot web app using ollama, flask, and a simple custom html/css/js front end
 
<pre>
<b>ollama    -->   flask app   -->   front end</b>
<i>runs models</i>     <i>serves the</i>         <i>chatbot interface</i>
                <i>front end and
                communicates with Ollama
                API</i>
</pre>

Usage:
 - ollama should be already running but make sure: `ollama --version `
 - run app.py: `python3 app.py`
 - web app should be running on: `localhost:5000`


<br></br>
---
#### Dev:

cmd curl command to prompt ollama api:
>```bash
>curl http://localhost:11434/api/generate -d "{  \"model\": \"gemma:2b\",  \"prompt\": \"Hello there\"}" -H "Content-Type: application/json"
```
