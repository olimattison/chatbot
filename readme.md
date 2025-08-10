# Chatbot
### Chatbot - AI chatbot web app using ollama, flask, and a modern html/css/js front end

### BETA 0.01:
 - Flask Login authentication
 - Database for persistence
 - Updated UI
 - Admin Dashboard


<pre>
<b>ollama    -->   flask app   -->   front end</b>
<i>runs models</i>     <i>serves the</i>         <i>chatbot interface</i>
                <i>front end and
                communicates with Ollama
                API</i>
</pre>



** Getting Started:**
 - if needed create virtual env: `python3 -m venv venv`
   - & activate it: `source venv/bin/activate`
   - & install dependencies: `pip install -r requirements.txt`
 - start ollama manually then make sure it is running: `ollama --version`
 - navigate to main folder: `cd main`
 - run app.py: `python3 app.py`
 - web app should be running on: `localhost:5000`



### Features
  - Functional chatbot interface built with Flask and Js powered by Ollama
  - Authentication with Flask Login
  - Saves chat history
  - Admin Dashboard to manage settings and users 



<br></br>
---

#### Dev:
todo:
 - dont touch the ui its perfect
 - UPDATE README with node module installation


installed moduules:
  - marked
  - bootstrap css

cmd curl command to prompt ollama api:
>```bash
>curl http://localhost:11434/api/generate -d "{  \"model\": \"gemma:4b-it-qat\",  \"prompt\": \"Hello there\"}" -H "Content-Type: application/json"
```



TODO --> BETA 0.02

- much work
- test thouroughly and find bugs


- logo maybe eventually