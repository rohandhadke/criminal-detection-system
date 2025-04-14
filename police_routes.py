from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app, Response, jsonify, send_file
from flask_bcrypt import Bcrypt
from database import db
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import pandas as pd
from io import BytesIO
from face_recognition.train_from_photos import train

bcrypt = Bcrypt()

police = Blueprint("police", __name__)


UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@police.route('/login', methods=['GET', 'POST'])
def police_login():
    if request.method == 'POST':
        badge_number = request.form.get('badge_number')
        password = request.form.get('password')

        print(badge_number)

        # Find police officer by email
        officer = db['police'].find_one({"badge_number": badge_number})

        if officer and bcrypt.check_password_hash(officer['password'], password):
            session['police_id'] = str(officer['_id'])  # Store officer ID in session
            session['police_name'] = officer['full_name']
            session['police_department'] = officer['department']

            flash("Login successful!", "success")
            return redirect(url_for('police.police_dashboard'))
        else:
            flash("Invalid email or password!", "danger")

    return render_template('police_login.html')

@police.route('/police/logout')
def logout():
    session.pop('police_id', None)
    session.pop('police_name', None)
    session.pop('police_department', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('police.police_login'))

@police.route('/dashboard')
def police_dashboard():
    if 'police_id' not in session:
        flash("Please login to access this page!", "danger")
        return redirect(url_for('police.police_login'))
    
    # Fetch the logged-in police officer's details
    police_officer = db['police'].find_one({"_id": ObjectId(session['police_id'])})
    criminal_data = list(db.criminals.find())

    if not police_officer:
        flash("Police officer not found!", "danger")
        return redirect(url_for('police.police_login'))
    
    for criminal in criminal_data:
        if 'photo' in criminal:
            criminal['photo'] = str(criminal['photo'])  # Convert ObjectId to string
    
    total_criminals = db.criminals.count_documents({})
    wanted_criminals = db.criminals.count_documents({"status": "Wanted"})
    arrested_criminals = db.criminals.count_documents({"status": "Arrested"})
    suspect_criminals = db.criminals.count_documents({"status": "Suspect"})

    return render_template('police_dashboard.html', 
        police=police_officer, criminals = criminal_data,        
        total_criminals=total_criminals,
        wanted_criminals=wanted_criminals,
        suspect_criminals = suspect_criminals,
        arrested_criminals=arrested_criminals)


@police.route('/add_criminal', methods=['POST'])
def add_criminal():
    if 'police_id' not in session:
        flash("You must be logged in as a police officer to add a criminal.", "danger")
        return redirect(url_for('police.police_login'))

    # Get form data
    name = request.form.get('name')
    alias = request.form.get('alias')
    dob = request.form.get('dob')
    age = request.form.get('age')
    gender = request.form.get('gender')
    aadhaar = request.form.get('aadhaar')
    crime_type = request.form.get('crime_type')
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state')
    status = request.form.get('status')
    description = request.form.get('description')

    # Handle file upload
    if 'photo' not in request.files:
        return "No photo uploaded", 400

    photo = request.files['photo']

    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        unique_filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        photo_path = os.path.join('static', 'photos', unique_filename)

        # Save file to static/photos directory
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        photo.save(photo_path)

        normalized_path = photo_path.replace('\\', '/')

        normalized_path = photo_path.replace('\\', '/')

        police_id = session['police_id']
        police_officer = db.police.find_one({'_id': ObjectId(police_id)})
        badge_number = police_officer['badge_number'] if police_officer and 'badge_number' in police_officer else 'Unknown'

        registered_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save all data including photo path, badge, and timestamp
        criminal_data = {
            "name": name,
            "alias": alias,
            "dob": dob,
            "age": age,
            "gender": gender,
            "aadhaar": aadhaar,
            "crime_type": crime_type,
            "address": address,
            "city": city,
            "state": state,
            "status": status,
            "description": description,
            "photo_path": normalized_path,
            "registered_by": badge_number,
            "registered_on": registered_on,
            "bank_status": "active"
        }

        db.criminals.insert_one(criminal_data)
        train()
        flash("Criminal added successfully", "success")
        return redirect(url_for('police.police_dashboard'))



@police.route('/photo/<photo_id>')
def get_photo(photo_id):
    try:
        criminal = db.criminals.find_one({'_id': ObjectId(photo_id)})
        if criminal and 'photo_path' in criminal:
            photo_path = criminal['photo_path']
            if os.path.exists(photo_path):
                return send_file(photo_path, mimetype='image/jpeg')
            else:
                return 'Image file not found', 404
        else:
            return 'Criminal not found or photo path missing', 404
    except Exception as e:
        return f"Error: {str(e)}", 500

@police.route("/edit_criminal/<criminal_id>", methods=["GET", "POST"])
def edit_criminal(criminal_id):
    criminal = db.criminals.find_one({"_id": ObjectId(criminal_id)})

    if request.method == "POST":
        name = request.form["name"]
        crime_type = request.form["crime_type"]
        penalty = request.form["penalty"]
        punishment_duration = request.form["punishment_duration"]
        
        criminals_collection.update_one(
            {"_id": ObjectId(criminal_id)},
            {"$set": {
                "name": name,
                "crime_type": crime_type,
                "penalty": penalty,
                "punishment_duration": punishment_duration
            }}
        )
        
        flash("Criminal record updated!", "success")
        return redirect(url_for("police.dashboard"))

    return render_template("edit_criminal.html", criminal=criminal)


@police.route('/criminals/all')
def criminal_record():
    # Fetch all criminal records from MongoDB
    criminals = db.criminals.find()
    criminal_list = []

    for criminal in criminals:
        criminal['_id'] = str(criminal['_id'])  # Convert ObjectId to string
        criminal_list.append(criminal)
    
    # print(criminal_list)

    return render_template('criminal_record.html', criminals=criminal_list)

@police.route('/criminal/profile/<criminal_id>')
def criminal_profile(criminal_id):
    try:
        # Fetch criminal details from MongoDB
        criminal = db.criminals.find_one({"_id": ObjectId(criminal_id)})
        if not criminal:
            return "Criminal not found", 404

        aadhaar = criminal.get('aadhaar')
        if not aadhaar:
            return "Aadhaar not found in criminal record", 400

        # Get all ATM users with the same Aadhaar
        atm_users = list(db.atm_users.find({"aadhaar": aadhaar}))

        card_numbers = [user.get('card_number') for user in atm_users if user.get('card_number')]
        atm_transactions = []

        if card_numbers:
            # Fetch transactions for all the card numbers
            atm_transactions = list(
                db.atm_transactions.find({"card_number": {"$in": card_numbers}}).sort("date", -1)
            )

        return render_template(
            'criminal_file.html',
            criminal=criminal,
            atm_users=atm_users,
            atm_transactions=atm_transactions
        )

    except Exception as e:
        return f"Error: {str(e)}", 500

@police.route('/block_accounts/<criminal_id>', methods=['POST'])
def block_accounts(criminal_id):
    try:
        # Fetch the criminal's Aadhaar
        criminal = db.criminals.find_one({"_id": ObjectId(criminal_id)})
        if not criminal or not criminal.get('aadhaar'):
            return jsonify({"message": "Criminal or Aadhaar not found"}), 404

        aadhaar = criminal['aadhaar']

        # Update all ATM user accounts to 'blocked'
        result = db.atm_users.update_many(
            {"aadhaar": aadhaar},
            {"$set": {"account_status": "blocked"}}
        )

        # Also update bank_status in the criminal document
        db.criminals.update_one(
            {"_id": ObjectId(criminal_id)},
            {"$set": {"bank_status": "blocked"}}
        )

        return jsonify({"message": f"{result.modified_count} account(s) blocked successfully."})

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@police.route('/unblock_accounts/<criminal_id>', methods=['POST'])
def unblock_accounts(criminal_id):
    try:
        # Fetch the criminal's Aadhaar
        criminal = db.criminals.find_one({"_id": ObjectId(criminal_id)})
        if not criminal or not criminal.get('aadhaar'):
            return jsonify({"message": "Criminal or Aadhaar not found"}), 404

        aadhaar = criminal['aadhaar']

        # Update all ATM user accounts to 'active'
        result = db.atm_users.update_many(
            {"aadhaar": aadhaar},
            {"$set": {"account_status": "active"}}
        )

        # Also update bank_status in the criminal document
        db.criminals.update_one(
            {"_id": ObjectId(criminal_id)},
            {"$set": {"bank_status": "active"}}
        )

        return jsonify({"message": f"{result.modified_count} account(s) unblocked successfully."})

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500



@police.route('/export_criminal_records')
def export_criminal_records():
    criminals = list(db.criminals.find({}))
    
    # Convert ObjectId to string
    for criminal in criminals:
        criminal['_id'] = str(criminal['_id'])

    # Create a DataFrame
    df = pd.DataFrame(criminals)

    # Optional: drop internal or binary fields you don't want in the export
    if 'photo' in df.columns:
        df.drop(columns=['photo'], inplace=True)
    if 'photo_path' not in df.columns:
        df['photo_path'] = ''  # if path is needed
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='CriminalRecords', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        download_name="Criminal_Records.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
