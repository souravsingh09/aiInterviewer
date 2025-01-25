# AI-Interviewer-Llama3
AI Interviewer Implementation Using LLama3 Model

# AI Interviewer Project
 
This project simulates an AI interviewer using the LLama3 model to interact with users. It leverages OpenAI-compatible APIs, Azure Speech Services for speech-to-text and text-to-speech functionalities, and a JavaScript frontend with a Python backend.
 
## Features
 
- **LLama3-based Interviewer**: Simulates an AI-powered interviewer that asks and responds to questions.
- **OpenAI-Compatible API**: Interacts with an OpenAI-compatible server for model execution and conversation management.
- **Speech-to-Text & Text-to-Speech**: Uses Azure Speech Service to convert user speech input to text and the AI's text response to speech (handled in the JavaScript frontend).
- **Modular Design**: Separate backend (Python) and frontend (JavaScript) codebase with clear API communication.
 
## Architecture
 
The project follows a client-server architecture:
 
- **Frontend**: Built with JavaScript, it handles user input, API calls, and displays responses. It also manages speech input/output via Azure Speech Services.
  
- **Backend**: Written in Python, the backend handles API calls to the OpenAI-compatible server, processes the model's responses, and interacts with the frontend.
 
- **Azure Speech Service**:
  - Converts speech input from the user into text (handled in the frontend).
  - Converts the AI's text-based responses into speech output (handled in the frontend).
 
## Requirements
 
### Backend (Python)
- Python 3.12.2+
- `openai` package (for API communication)
- `flask` or `fastapi` (for RESTful API setup)
 
### Frontend (JavaScript)
- Modern browser with JavaScript support
- Axios (for HTTP requests)
- Azure Speech SDK (for speech-to-text and text-to-speech integration)
 
### Azure
- Azure Speech Service account and API keys
 
## Setup
 
### Backend (Python)
 
1. Install python package:
```bash
pip install -r requirements.txt
```
2. Change the email ids:
   In file Utils_Scheduler_modified.py provide your email id in line 288 and 304.
   In file Utils_interviewer.py provide your email id in line 252.
 
3. Start the backend server:
 
```bash
python app.py
```

4. Access the wep page via url [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Important Points to consider

1. Always ensure that the LLM endpoint is correctly configured.
2. The prompts are configured correctly for the models selected. Changing the models may require changing the prompts.
3. Integrating the Bulk shortlisting of resumes will require changes in the CSS and HTML files.
   
# aiInterviewer
