import json
import os
import uuid
import torch
import soundfile as sf

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sevabots.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -----------------------------
# DB Model
# -----------------------------
class ChatSession(db.Model):
    session_id = db.Column(db.String(50), primary_key=True)
    state = db.Column(db.String(50), default="init")

class UserProfile(db.Model):
    phone = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.String(10))
    address = db.Column(db.String(200))
    pin = db.Column(db.String(20))

class Scheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    benefits = db.Column(db.Text)
    state = db.Column(db.String(100))
    organization = db.Column(db.String(100))
    type = db.Column(db.String(100))
    category = db.Column(db.String(100))
    target = db.Column(db.String(100))
    income = db.Column(db.String(100))
    link = db.Column(db.String(500))
    steps = db.Column(db.Text)
    documents = db.Column(db.Text)
    
    def to_dict(self):
        return {
            "name": self.name,
            "benefits": self.benefits,
            "state": self.state,
            "organization": self.organization,
            "type": self.type,
            "category": self.category,
            "target": self.target,
            "income": self.income,
            "link": self.link,
            "steps": json.loads(self.steps) if self.steps else [],
            "documents": json.loads(self.documents) if self.documents else []
        }

class UserApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20))
    scheme_name = db.Column(db.String(255))
    status = db.Column(db.String(50), default="Applied")

def seed_schemes():
    if Scheme.query.count() == 0:
        try:
            file_path = os.path.join(os.path.dirname(__file__), 'schemes.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_schemes = json.load(f)
                    for s in all_schemes:
                        scheme = Scheme(
                            name=s.get('name'),
                            benefits=s.get('benefits'),
                            state=s.get('state'),
                            organization=s.get('organization'),
                            type=s.get('type'),
                            category=s.get('category'),
                            target=s.get('target'),
                            income=s.get('income'),
                            link=s.get('link'),
                            steps=json.dumps(s.get('steps', [])),
                            documents=json.dumps(s.get('documents', []))
                        )
                        db.session.add(scheme)
                    db.session.commit()
                    print("✅ schemes.json successfully seeded to SQLite Database")
        except Exception as e:
            print(f"Seed Error: {e}")

with app.app_context():
    db.create_all()
    seed_schemes()

# -----------------------------
# STT + TTS MODELS (Lazy Loaded)
# -----------------------------
_stt_pipeline = None
_tts_model = None
_tts_tokenizer = None

def get_stt():
    global _stt_pipeline
    if _stt_pipeline is None:
        from transformers import pipeline
        print("Lazy-loading STT model (Whisper)...")
        _stt_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-small")
    return _stt_pipeline

def get_tts_components():
    global _tts_model, _tts_tokenizer
    if _tts_model is None or _tts_tokenizer is None:
        from transformers import VitsModel, AutoTokenizer
        print("Lazy-loading TTS model (MMS)...")
        _tts_model = VitsModel.from_pretrained("facebook/mms-tts-kan")
        _tts_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-kan")
    return _tts_model, _tts_tokenizer

def generate_tts(text):
    model, tokenizer = get_tts_components()
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform

    os.makedirs("audio", exist_ok=True)
    filename = f"audio_{uuid.uuid4().hex}.wav"
    filepath = os.path.join("audio", filename)

    sf.write(filepath, output.squeeze().cpu().numpy(), 16000)
    return filename

# -----------------------------
# Static
# -----------------------------
@app.route("/")
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route("/<path:path>")
def serve_static(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory('.', path)

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("audio", filename)

# -----------------------------
# Schemes API
# -----------------------------
@app.route("/api/schemes", methods=["GET"])
def get_schemes():
    try:
        schemes = [s.to_dict() for s in Scheme.query.all()]
        resp = jsonify(schemes)
        resp.headers.add("Access-Control-Allow-Origin", "*")
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# User Profile API
# -----------------------------
@app.route("/api/user/save", methods=["POST"])
def save_user_profile():
    data = request.get_json() or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    
    try:
        user = db.session.get(UserProfile, phone)
        if not user:
            user = UserProfile(phone=phone)
            db.session.add(user)
            
        user.name = data.get("name", user.name)
        user.age = data.get("age", user.age)
        user.address = data.get("address", user.address)
        user.pin = data.get("pin", user.pin)
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/schemes_add", methods=["POST"])
def add_user_scheme():
    data = request.get_json() or {}
    phone = data.get("phone")
    scheme_name = data.get("scheme_name")
    
    if not phone or not scheme_name:
        return jsonify({"error": "Missing data"}), 400
        
    try:
        existing = UserApplication.query.filter_by(phone=phone, scheme_name=scheme_name).first()
        if not existing:
            app_req = UserApplication(phone=phone, scheme_name=scheme_name)
            db.session.add(app_req)
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/schemes_get", methods=["GET"])
def get_user_schemes():
    phone = request.args.get("phone")
    if not phone:
        return jsonify([])
        
    try:
        apps = UserApplication.query.filter_by(phone=phone).all()
        results = []
        for a in apps:
            scheme = Scheme.query.filter_by(name=a.scheme_name).first()
            if scheme:
                s_dict = scheme.to_dict()
                s_dict["status"] = a.status
                results.append(s_dict)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Match API
# -----------------------------
@app.route("/api/match", methods=["POST"])
def match_schemes():
    data = request.get_json() or {}
    occupation = data.get("occupation", "")
    user_answers = data.get("userAnswers", {})

    try:
        all_schemes = Scheme.query.all()
        results = []
        
        # Determine strict category requirement dynamically based on occupation rules
        required_category = "Not Applicable"
        income_bracket = "Any"
        
        if occupation == "Agriculture Sector":
            required_category = user_answers.get("What kind of support do you need?", "Not Applicable")
            income_bracket = user_answers.get("What is your annual family income?", "Any")
        elif occupation == "Medical Sector":
            required_category = user_answers.get("What is your primary healthcare requirement?", "Not Applicable")
            income_bracket = user_answers.get("What is your annual family income?", "Any")
        elif occupation == "Education Sector":
            required_category = user_answers.get("Are you seeking support for tuition or hostel fees?", "Not Applicable")
            income_bracket = user_answers.get("What is your annual family income?", "Any")
        elif occupation == "Others":
            required_category = user_answers.get("What is your primary objective?", "Not Applicable")
            income_bracket = user_answers.get("What is your annual family income?", "Any")

        for scheme_model in all_schemes:
            scheme = scheme_model.to_dict()
            if scheme.get('target') == 'General':
                continue
                
            # Primary filter: Must match occupation sector exactly 
            if scheme.get('target') != occupation:
                continue
                
            # Secondary filter: Must map to their primary category need
            if required_category != "Not Applicable" and required_category != "Not sure":
                if scheme.get('category') != required_category:
                    continue
                    
            # Tertiary filter: Check income brackets roughly
            if scheme.get('income') != "Any" and income_bracket != "Any":
                if scheme.get('income') != income_bracket:
                    continue
                    
            results.append(scheme)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# CHAT (UNCHANGED LOGIC)
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_input = data.get("message", "").lower().strip()
    session_id = data.get("session_id", "default")

    try:
        chat_session = db.session.get(ChatSession, session_id)
        if not chat_session:
            chat_session = ChatSession(session_id=session_id, state="init")
            db.session.add(chat_session)
            db.session.commit()

        state = chat_session.state
        response = ""

        if state == "init":
            if "farmer" in user_input or "agriculture" in user_input:
                response = "I can help with agricultural schemes. Are you a small or large farmer?"
                chat_session.state = "farmer_size"
            elif "medical" in user_input or "health" in user_input:
                response = "I can help with medical schemes. Are you looking for hospitalization coverage or maternity care?"
                chat_session.state = "medical_need"
            elif "education" in user_input or "student" in user_input:
                response = "I see you are interested in educational schemes. Are you primarily seeking help with tuition fees or hostel fees?"
                chat_session.state = "education_need"
            else:
                response = "Please tell me your requirement."

        elif state == "farmer_size":
            response = "Do you own your agricultural land?"
            chat_session.state = "farmer_land"

        elif state == "farmer_land":
            response = "You may qualify for financial assistance schemes for farmers."
            chat_session.state = "init"

        db.session.commit()

        return jsonify({"reply": response})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# -----------------------------
# 🎤 VOICE API (MAIN)
# -----------------------------
@app.route("/voice", methods=["POST"])
def voice():
    try:
        if "input_audio" not in request.files:
            return jsonify({"error": "No audio"}), 400

        file = request.files["input_audio"]

        # Save audio
        temp_file = f"temp_{uuid.uuid4().hex}.wav"
        file.save(temp_file)

        # 1️⃣ STT
        stt_processor = get_stt()
        result = stt_processor(temp_file)
        user_text = result["text"]

        # 2️⃣ PASS TO CHAT ENGINE
        chat_response = chat_internal(user_text)

        # 3️⃣ TTS
        audio_file = generate_tts(chat_response)

        return jsonify({
            "transcribed_text": user_text,
            "response_text": chat_response,
            "audio_url": f"/audio/{audio_file}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# INTERNAL CHAT HELPER
# -----------------------------
def chat_internal(user_text):
    text = user_text.lower()

    if "farmer" in text or "agriculture" in text or "ರೈತ" in user_text:
        return "ನೀವು ರೈತರಿಗೆ ಸಂಬಂಧಿಸಿದ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರಾಗಿರಬಹುದು."

    elif "student" in text or "ವಿದ್ಯಾರ್ಥಿ" in user_text:
        return "ನೀವು ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಸಂಬಂಧಿಸಿದ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರಾಗಿರಬಹುದು."

    elif "health" in text or "medical" in text or "ಆರೋಗ್ಯ" in user_text:
        return "ನೀವು ಆರೋಗ್ಯ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರಾಗಿರಬಹುದು."

    else:
        return "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಅಗತ್ಯವನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಹೇಳಿ."

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(port=5000)