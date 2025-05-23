# Chatbot
### Basic AI chatbot web app using ollama, flask, and a simple custom html/css/js front end
 
<pre>
<b>ollama    -->   flask app   -->   front end</b>
<i>runs models</i>     <i>serves the</i>         <i>chatbot interface</i>
                <i>front end and
                communicates with Ollama
                API</i>
</pre>


This project has two versions: Docker and non-Docker.

**for non-Docker:**
 - if needed create virtual env: `python3 -m venv venv`
   - & activate it: `source venv/bin/activate`
   - & install dependencies: `pip install -r requirements.txt`
 - start ollama manually then make sure it is running: `ollama --version`
 - navigate to main folder: `cd main`
 - run app.py: `python3 app.py`
 - web app should be running on: `localhost:5000`


### for docker
 - navigate to Docker folder: `cd Docker`
 - build image: `docker build -t ollama .`
 - run container: `docker run -p 11434:11434 --name ollama ollama`
 - web app should be running on `localhost:5000`
 - interact with container (optional): `docker exec -it ollama bash`
 


<br></br>
---
#### Dev:

cmd curl command to prompt ollama api:
>```bash
>curl http://localhost:11434/api/generate -d "{  \"model\": \"gemma:2b\",  \"prompt\": \"Hello there\"}" -H "Content-Type: application/json"
```
