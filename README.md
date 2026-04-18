# SevaBot 

SevaBot is a full-stack web application designed to help citizens, farmers, and students easily discover, navigate, and apply for government schemes dynamically. It features a conversational AI system powered by NLP to intuitively match user symptoms, circumstances, or inputs with the correct benefits via cross-lingual accessibility.

## Key Features

- **Personalized Scheme Matching:** Intelligently matches users to exact schemes using dynamic database configurations algorithms.
- **Multilingual UI Support:** Deep native translation mapping in English, Hindi, and Kannada.
- **Fully-Fledged Voice AI:** Integrates with local speech-to-text (Whisper) and text-to-speech (MMS) models to talk directly with the citizen. 
- **User Dashboard & Persistence:** Seamless UI allowing users to easily parse data, "Save to Dashboard", and trace tracked benefits directly synced via their profiles.

## Technology Stack

- **Frontend:** Pure HTML5, Vanilla JavaScript, and Modular CSS (No frameworks needed). Highly optimized.
- **Backend:** Python +  Flask + SQLite 
- **Artificial Intelligence Pipeline:** HuggingFace `transformers` (`openai/whisper-small` for STT, `facebook/mms-tts-kan` for TTS)

## Running the Project Locally

### Prerequisites
Make sure you have Python installed (Version 3.8+ recommended).

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rashmika157/Sevabots.git
   cd Sevabots
   ```

2. **Install the required dependancies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the localized database and web server:**
   ```bash
   python app.py
   ```
   *Note: On the first run, the system will automatically parse and seed the `schemes.json` file securely into the internal SQLite db! It will also download the HF models on the first voice prompt.*

4. **Navigate to the web application:**
   Open your browser and visit: `http://127.0.0.1:5000`

## Deployment Instructions

The application is architecturally designed with relative URL endpoints (`/api/...`). This structurally implies you can host the repository seamlessly using a single unified pipeline! 

1. Push your code exactly as it is to a GitHub repository.
2. Connect the repository to a Python hosting cloud provider like **Render.com**, **Railway**, or **Heroku**.
3. Specify the runtime command as `gunicorn app:app` (ensure you add `gunicorn` to your requirements if hosted externally).
4. The service will naturally boot and serve up both your HTML interface and your backend routing logic underneath the same domain.

## Authors
Developed to streamline civic engagement and scheme distribution.
