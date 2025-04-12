from flask import Blueprint, render_template, request, redirect, session, flash, jsonify, send_file
from pymongo import MongoClient
# import face_recognition
# import cv2
import numpy as np
import os
from datetime import datetime
import random
from functools import wraps 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

atm = Blueprint("atm", __name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["criminal-detection-system"]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "card_number" not in session:
            print("Please insert your card and login.")
            return redirect("/atm")
        return f(*args, **kwargs)
    return decorated_function


def generate_passbook_pdf(user_data, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(180, height - 50, "LSOYS BANK - Account Passbook")

    c.setFont("Helvetica", 12)
    y = height - 100

    for key, value in user_data.items():
        c.drawString(80, y, f"{key}: {value}")
        y -= 20

    c.drawString(80, y - 10, f"Issued Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.showPage()
    c.save()

# Route: ATM Home Page
@atm.route("/")
def atm_home():
    return render_template("atm-simulation/index.html")  # frontend page for simulation

# Route: Login with Card Number and PIN
@atm.route("/login", methods=["POST"])
def atm_login():
    data = request.get_json()
    card_number = data.get("card_number")
    pin = data.get("pin")

    user = db.atm_users.find_one({"card_number": card_number})
    if user and user["pin"] == pin:
        if user["account_status"] == "blocked":
            return jsonify({"success": False, "blocked": True})
        
        session["card_number"] = card_number
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "blocked": False})

def generate_card_number():
    while True:
        number = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        if not db.atm_users.find_one({"card_number": number}):
            return number  
        
# Route: Register New User
@atm.route("/create_account", methods=["GET"])
def show_create_account_form():
    return render_template("atm-simulation/create_account.html")

@atm.route("/create_account", methods=["POST"])
def create_account():
    data = request.get_json()

    required_fields = ["full_name", "dob", "mobile", "aadhaar", "account_type", "nationality", "balance", "pin"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields."}), 400

    pin = data["pin"]
    if len(pin) != 4 or not pin.isdigit():
        return jsonify({"message": "PIN must be a 4-digit number."}), 400

    card_number = generate_card_number()

    user_data = {
        "full_name": data["full_name"],
        "dob": data["dob"],
        "mobile": data["mobile"],
        "aadhaar": data["aadhaar"],
        "account_type": data["account_type"],
        "balance": data.get("balance", 0.0),
        "nationality": data["nationality"],
        "pin": pin,
        "created_at": datetime.now(),
        "card_number": card_number,
        "account_status": "active"
    }

    db.atm_users.insert_one(user_data)
        # Create PDF directory if it doesn't exist
    pdf_dir = os.path.join("static", "passbooks")
    os.makedirs(pdf_dir, exist_ok=True)

    # Generate PDF file
    pdf_filename = f"{pdf_dir}/passbook_{card_number}.pdf"
    generate_passbook_pdf(user_data, pdf_filename)

    return jsonify({
        "message": "Account created successfully!",
        "card_number": card_number,
        "passbook_url": f"/{pdf_filename}"  # You can open/download it from this URL
    }), 201

    # return jsonify({"message": "Account created successfully!", "card_number": card_number}), 201

# Route: Dashboard
@atm.route("/main_menu")
@login_required
def main_menu():
    card_number = session.get("card_number")
    if not card_number:
        return redirect("/atm")
    
    user = db.atm_users.find_one({"card_number": card_number})
    return render_template("atm-simulation/main_menu.html", user=user)

@atm.route("/logout", methods=["POST"])
@login_required
def atm_logout():
    session.clear()
    return jsonify({"success": True})

# Route: Face Detection API
# @atm.route("/face_check", methods=["POST"])
# def face_check():
#     file = request.files["photo"]
#     img_np = np.frombuffer(file.read(), np.uint8)
#     img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
#     unknown_encoding = face_recognition.face_encodings(img)

#     if not unknown_encoding:
#         return jsonify({"status": "error", "message": "Face not detected."})

#     criminals = db.criminals.find()
#     for crim in criminals:
#         known_encoding = np.array(crim["photo_encoding"])
#         results = face_recognition.compare_faces([known_encoding], unknown_encoding[0], tolerance=0.5)

#         if results[0]:
#             # Block user account
#             card_number = session.get("card_number")
#             db.users.update_one({"card_number": card_number}, {"$set": {"account_status": "blocked"}})
#             db.alerts.insert_one({
#                 "card_number": card_number,
#                 "full_name": crim["full_name"],
#                 "match_percentage": 99.0,
#                 "message": "Criminal face detected. Account blocked.",
#                 "alert_status": "unresolved"
#             })
#             return jsonify({"status": "blocked", "message": "Criminal face detected. Account blocked."})

#     return jsonify({"status": "ok", "message": "No criminal match found."})
