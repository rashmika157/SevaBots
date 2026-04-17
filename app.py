import json
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sevabots.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ChatSession(db.Model):
    session_id = db.Column(db.String(50), primary_key=True)
    state = db.Column(db.String(50), default="init")

with app.app_context():
    db.create_all()

# Temporary variable to store user data
user_data = []

@app.route("/api/schemes", methods=["GET", "OPTIONS"])
def get_schemes():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET")
        return response
        
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'schemes.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            schemes = json.load(f)
        resp = jsonify(schemes)
        resp.headers.add("Access-Control-Allow-Origin", "*")
        return resp, 200
    except Exception as e:
        resp = jsonify({"error": str(e)})
        resp.headers.add("Access-Control-Allow-Origin", "*")
        return resp, 500

@app.route("/api/match", methods=["POST", "OPTIONS"])
def match_schemes():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    data = request.get_json() or {}
    occupation = data.get("occupation", "")
    user_answers = data.get("userAnswers", {})

    income = "Any"
    need = "Not sure"
    
    if occupation == "Agriculture Sector":
        need = user_answers.get("What kind of support do you need?", "Not sure")
        income = user_answers.get("What is your annual family income?", "Any")
    elif occupation == "Medical Sector":
        need = user_answers.get("What is your primary healthcare requirement?", "Not Applicable")
        income = user_answers.get("What is your annual family income?", "Any")
    elif occupation == "Education Sector":
        need = user_answers.get("Are you seeking support for tuition or hostel fees?", "Not Applicable")
        income = user_answers.get("What is your annual family income?", "Any")
    elif occupation == "Others":
        need = user_answers.get("What is your primary objective?", "Not Applicable")
        income = user_answers.get("What is your annual family income?", "Any")

    try:
        file_path = os.path.join(os.path.dirname(__file__), 'schemes.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
            
        matching_schemes = []
        for scheme in all_schemes:
            if scheme.get('target') == 'General':
                continue
                
            match_occupation = (scheme.get('target') == occupation)
            match_need = (scheme.get('category') == need)
            match_income = (scheme.get('income') == "Any" or scheme.get('income') == income)
            
            if match_occupation and match_need and match_income:
                matching_schemes.append(scheme)

        resp = jsonify(matching_schemes)
        resp.headers.add("Access-Control-Allow-Origin", "*")
        return resp, 200
        
    except Exception as e:
        resp = jsonify({"error": str(e)})
        resp.headers.add("Access-Control-Allow-Origin", "*")
        return resp, 500

@app.route("/get-data", methods=["GET"])
def get_user_data():
    return jsonify(user_data), 200

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    data = request.get_json() or {}
    user_input = data.get("message", "").lower().strip()
    session_id = data.get("session_id", "default")
    
    chat_session = ChatSession.query.get(session_id)
    if not chat_session:
        chat_session = ChatSession(session_id=session_id, state="init")
        db.session.add(chat_session)
        db.session.commit()
        
    state = chat_session.state
    response = ""
    
    # Enhanced state machine tracking user responses contextually via SQLite Database
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
        elif "business" in user_input or "loan" in user_input or "start" in user_input:
            response = "You may be eligible for general loan schemes. What is your approximate annual income?"
            chat_session.state = "loan_income"
        else:
            response = "I can help you find schemes across Agriculture, Medical, Education, and Business. Could you tell me exactly what kind of support you need?"
            
    elif state == "farmer_size":
        if "small" in user_input:
            response = "Small farmers have multiple benefits. Do you own your agricultural land?"
            chat_session.state = "farmer_land"
        else:
            response = "Understood. Some equipment subsidies are available. Do you require financial support or crop insurance primarily?"
            chat_session.state = "farmer_need"
            
    elif state == "farmer_land":
        response = "Thank you. Based on your profile as a small farmer with land, the 'Financial Assistance for Marginal Farmers' scheme seems perfect. Shall I show you the details?"
        chat_session.state = "init" # End of flow
        
    elif state == "farmer_need":
        response = "Great. Based on your response, 'Pradhan Mantri Fasal Bima Yojana' could be a match. You can find this in our 'Personalized Schemes' section!"
        chat_session.state = "init"
        
    elif state == "medical_need":
         response = "Regardless of the exact treatment, the 'Ayushman Bharat PMJAY' covers a wide range of up to 5 Lakhs. Are you currently below the 1 Lakh income bracket?"
         chat_session.state = "medical_income"
         
    elif state == "medical_income":
         response = "Thank you for confirming. You are heavily likely to be eligible. I recommend completing the full Personalized Flow from the menu to secure it!"
         chat_session.state = "init"
         
    elif state == "education_need":
         response = "Understood. Is your family's annual income below 2.5 Lakhs?"
         chat_session.state = "education_income"
         
    elif state == "education_income":
         response = "Thank you. Both 'Pre-Matric Scholarship' and 'Post-Matric Hostel Allowance' might apply. Please check the Explore Schemes page for more info."
         chat_session.state = "init"
         
    elif state == "loan_income":
         response = "Got it. Consider exploring the 'MUDRA Yojana' for massive business subsidies! You can start a new query with me below at any time."
         chat_session.state = "init"

    db.session.commit()

    resp = jsonify({
        "reply": response
    })
    resp.headers.add("Access-Control-Allow-Origin", "*")
    return resp, 200

if __name__ == "__main__":
    app.run(port=5000)
