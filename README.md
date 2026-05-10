# MockMaster

MockMaster is an AI-powered career preparation platform that helps users:

- Analyse resumes
- Get role recommendations
- Fetch real job openings
- Practice AI-powered mock interviews
- Receive voice-based interview feedback

Built using FastAPI, Python, JavaScript, and AI APIs.

---

# Features

## Resume Analysis
- Extracts:
  - Skills
  - Experience
  - Resume summary
  - Suggested roles

## AI Mock Interviews
- AI-generated interview questions
- Technical + behavioural interviews
- Context-aware follow-up questions
- Final interview evaluation

## Voice & Delivery Analysis
Analyses:
- Confidence
- Clarity
- Speaking pace
- Hesitations
- Tone & pitch variation

Uses:
- MediaRecorder API
- Web Speech API
- librosa
- ffmpeg

---

# Tech Stack

## Backend
- FastAPI
- Python
- OpenAI API

## Frontend
- HTML
- CSS
- Vanilla JavaScript

## Audio Processing
- librosa
- ffmpeg
- Web Audio API

---

# Project Structure

```text
backend/
│
├── main.py
├── services/
│   ├── audio_analyser.py
│   ├── job_aggregator.py
│   ├── job_sources.py
│
static/
templates/

requirements.txt
run_app.bat
run_app.sh
````

---

# Setup

## Clone Repository

```bash
git clone <your_repo_url>
cd mockmaster
```

---

# Environment Variables

Fill the .env.example in the backend/agents folder with your gemini API key:

```env
GEMINI_API=your_openai_api_key
```

---

# Run the App

## Windows
```powershell
run_app.bat
```

## Mac/Linux

```bash
chmod +x run_app.sh
./run_app.sh
```

The scripts automatically:

* Create virtual environment
* Install requirements
* Start the FastAPI server

---

# Start Server Manually

```bash
uvicorn backend.main:app --reload --port 8000
```

Runs at:

```text
http://127.0.0.1:8000
```

---

# Main API Endpoints

```http
POST /api/jobs
POST /api/interview/start
POST /api/interview/answer
POST /api/interview/feedback
POST /api/interview/analyse-audio
```

---

# Browser Support

Recommended:

* Chrome
* Edge

Required for:

* SpeechRecognition API
* MediaRecorder API

---

# Future Improvements

* Webcam posture analysis
* Emotion detection
* PDF interview reports
* Multi-language support
* ATS score prediction