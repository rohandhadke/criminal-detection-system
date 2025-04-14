from flask import Blueprint, render_template, request, redirect, session, flash, jsonify, send_file
from pymongo import MongoClient
import numpy as np
import os
from datetime import datetime
import random
from functools import wraps 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
from face_recognition.face_matcher import recognize_face_from_webcam

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
            return jsonify({
                "success": False,
                "blocked": True,
                "message": "Your account is blocked due to criminal match."
            })

        # Step 1: Use webcam to capture and match
        criminal_name = recognize_face_from_webcam()
        if criminal_name:
            # Step 2: If matched, block the account
            db.atm_users.update_one(
                {"card_number": card_number},
                {"$set": {"account_status": "blocked"}}
            )
            aadhaar_number = user.get("aadhaar")
            if aadhaar_number:
                print(aadhaar_number)
                db.criminals.update_one(
                    {"aadhaar_number": aadhaar_number},
                    {"$set": {"bank_status": "blocked"}}
                )
            else:
                print("not getting adhar number")
                
            return jsonify({
                "success": False,
                "blocked": True,
                "message": f"Your account is blocked because your face matched a criminal profile ({criminal_name}). Please contact the police station."
            })

        # Step 3: Allow login
        session["card_number"] = card_number
        return jsonify({"success": True, "blocked": False})
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




# ATM Transactions



# MongoDB Collections
users_col = db.atm_users
transactions_col = db.atm_transactions


# Route: Deposit Money
@atm.route("/deposit", methods=["POST"])
@login_required
def deposit_money():
    data = request.get_json()
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"message": "Invalid deposit amount."})

    users_col.update_one(
        {"card_number": session["card_number"]},
        {"$inc": {"balance": amount}}
    )

    transactions_col.insert_one({
        "card_number": session["card_number"],
        "type": "Deposit",
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({"message": f"₹{amount} deposited successfully!"})


# Route: Withdraw Money
@atm.route("/withdraw", methods=["POST"])
@login_required
def withdraw_money():
    data = request.get_json()
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"message": "Invalid withdraw amount."})

    user = users_col.find_one({"card_number": session["card_number"]})
    if user["balance"] < amount:
        return jsonify({"message": "Insufficient balance!"})

    users_col.update_one(
        {"card_number": session["card_number"]},
        {"$inc": {"balance": -amount}}
    )

    transactions_col.insert_one({
        "card_number": session["card_number"],
        "type": "Withdraw",
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({"message": f"₹{amount} withdrawn successfully!"})


# Route: Check Balance
@atm.route("/check_balance", methods=["POST"])
@login_required
def check_balance():
    user = users_col.find_one({"card_number": session["card_number"]})
    return jsonify({"balance": user["balance"]})


# Route: Change PIN
@atm.route("/change_pin", methods=["POST"])
@login_required
def change_pin():
    data = request.get_json()
    old_pin = data.get("old_pin")
    new_pin = data.get("new_pin")

    user = users_col.find_one({"card_number": session["card_number"]})
    if user["pin"] != old_pin:
        return jsonify({"message": "Old PIN is incorrect."})

    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"message": "New PIN must be a 4-digit number."})

    users_col.update_one(
        {"card_number": session["card_number"]},
        {"$set": {"pin": new_pin}}
    )

    return jsonify({"message": "PIN changed successfully!"})


# Route: Mini Statement (last 5 transactions)
@atm.route("/mini_statement", methods=["POST"])
@login_required
def mini_statement():
    transactions = transactions_col.find(
        {"card_number": session["card_number"]}
    ).sort("date", -1).limit(5)

    tx_list = []
    for tx in transactions:
        tx_list.append({
            "type": tx["type"],
            "amount": tx["amount"],
            "date": tx["date"]
        })

    return jsonify({"transactions": tx_list})


@atm.route("/blocked", methods=["GET"])
def show_account_blocked():
    return render_template("atm-simulation/atm_blocked.html")