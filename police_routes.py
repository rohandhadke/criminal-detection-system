from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from flask_bcrypt import Bcrypt
from database import db
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime
from io import BytesIO
import os
import gridfs

bcrypt = Bcrypt()

police = Blueprint("police", __name__)

fs = gridfs.GridFS(db)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

    return render_template('police_dashboard.html', police=police_officer, criminals = criminal_data)


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
        # Save photo in GridFS
        photo_id = fs.put(photo, filename=photo.filename)
    else:
        return "Invalid file type", 400


    # Store data in MongoDB
    criminal_data = {
        "name": name,
        "alias": alias,
        "dob": dob,
        "age": int(age),
        "gender": gender,
        "aadhaar": aadhaar,
        "crime_type": crime_type,
        "address": address,
        "city": city,
        "state": state,
        "status": status,
        "description": description,
        "photo": photo_id,
        "added_by": ObjectId(session['police_id']),
        "added_on": datetime.utcnow()
    }

    db['criminals'].insert_one(criminal_data)

    flash("Criminal record added successfully!", "success")
    return redirect(url_for('police.police_dashboard'))

@police.route('/photo/<photo_id>')
def get_photo(photo_id):
    try:
        file_data = fs.get(bson.ObjectId(photo_id))  # Retrieve file from GridFS
        return send_file(file_data, mimetype='image/jpeg')  # Change mimetype if needed
    except:
        return "File not found", 404

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

    return render_template('criminal_record.html', criminals=criminal_list)

@police.route('/criminal/profile/<criminal_id>')
def criminal_profile(criminal_id):
    try:
        # Fetch criminal details from MongoDB
        criminal = db.criminals.find_one({"_id": ObjectId(criminal_id)})
        
        if not criminal:
            return "Criminal not found", 404

        return render_template('criminal_file.html', criminal=criminal)
    
    except Exception as e:
        return str(e)