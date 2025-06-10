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
    return redirect(url_for('home'))

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
    criminals = list(db.criminals.find())
    
    # Format dates and handle missing values
    for criminal in criminals:
        if 'registered_on' in criminal:
            if isinstance(criminal['registered_on'], str):
                # If it's already a string, use it as is
                continue
            else:
                # If it's a datetime object, format it
                criminal['registered_on'] = criminal['registered_on'].strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('criminal_record.html', criminals=criminals)

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

@police.route('/api/criminals/<criminal_id>', methods=['GET'])
def get_criminal(criminal_id):
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        criminal = db.criminals.find_one({"_id": ObjectId(criminal_id)})
        if not criminal:
            return jsonify({
                'success': False,
                'message': 'Criminal not found'
            }), 404

        # Convert ObjectId to string for JSON serialization
        criminal['_id'] = str(criminal['_id'])
        
        return jsonify({
            'success': True,
            'data': criminal
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/api/criminals/<criminal_id>/update/<section>', methods=['POST'])
def update_criminal_section(criminal_id, section):
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        criminal_id = ObjectId(criminal_id)
        
        # Define update fields for each section
        update_fields = {
            'personal': {
                'name': data.get('name'),
                'gender': data.get('gender'),
                'nationality': data.get('nationality'),
                'dob': data.get('dob'),
                'age': data.get('age'),
                'aadhaar': data.get('aadhaar')
            },
            'physical': {
                'height': data.get('height'),
                'weight': data.get('weight'),
                'hair_color': data.get('hair_color'),
                'eye_color': data.get('eye_color'),
                'distinguishing_marks': data.get('distinguishing_marks')
            },
            'contact': {
                'permanent_address': data.get('permanent_address'),
                'last_known_address': data.get('last_known_address'),
                'phone_numbers': data.get('phone_numbers', []),
                'email_addresses': data.get('email_addresses', [])
            },
            'criminal': {
                'status': data.get('status'),
                'bank_status': data.get('bank_status'),
                'primary_crime_type': data.get('primary_crime_type'),
                'fir_number': data.get('fir_number'),
                'modus_operandi': data.get('modus_operandi'),
                'case_status': data.get('case_status'),
                'last_arrest_date': data.get('last_arrest_date')
            },
            'timeline': {
                'timeline': data.get('timeline', [])
            }
        }

        if section not in update_fields:
            return jsonify({
                'success': False,
                'message': 'Invalid section'
            }), 400

        # Remove None values from the update data
        update_data = {k: v for k, v in update_fields[section].items() if v is not None}

        if not update_data:
            return jsonify({
                'success': False,
                'message': 'No valid data to update'
            }), 400

        # Update the criminal record
        result = db.criminals.update_one(
            {'_id': criminal_id},
            {'$set': update_data}
        )

        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'message': 'No changes were made'
            }), 400

        # Log the update
        update_log = {
            'criminal_id': criminal_id,
            'police_id': ObjectId(session['police_id']),
            'section': section,
            'updated_fields': list(update_data.keys()),
            'timestamp': datetime.now()
        }
        db.update_logs.insert_one(update_log)

        return jsonify({
            'success': True,
            'message': f'{section.capitalize()} information updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/api/criminals/<criminal_id>/update/timeline', methods=['POST'])
def update_criminal_timeline(criminal_id):
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        data = request.get_json()
        criminal_id = ObjectId(criminal_id)
        
        # Validate timeline data
        timeline = data.get('timeline', [])
        if not isinstance(timeline, list):
            return jsonify({
                'success': False,
                'message': 'Timeline must be a list of events'
            }), 400

        # Update the criminal record
        result = db.criminals.update_one(
            {'_id': criminal_id},
            {'$set': {'timeline': timeline}}
        )

        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'message': 'No changes were made'
            }), 400

        # Log the update
        update_log = {
            'criminal_id': criminal_id,
            'police_id': ObjectId(session['police_id']),
            'section': 'timeline',
            'updated_fields': ['timeline'],
            'timestamp': datetime.now()
        }
        db.update_logs.insert_one(update_log)

        return jsonify({
            'success': True,
            'message': 'Timeline updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/api/criminals/<criminal_id>/update/associates', methods=['POST'])
def update_criminal_associates(criminal_id):
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        data = request.get_json()
        criminal_id = ObjectId(criminal_id)
        
        # Validate associates data
        associates = data.get('associates', [])
        if not isinstance(associates, list):
            return jsonify({
                'success': False,
                'message': 'Associates must be a list'
            }), 400

        # Update the criminal record
        result = db.criminals.update_one(
            {'_id': criminal_id},
            {'$set': {'associates': associates}}
        )

        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'message': 'No changes were made'
            }), 400

        # Log the update
        update_log = {
            'criminal_id': criminal_id,
            'police_id': ObjectId(session['police_id']),
            'section': 'associates',
            'updated_fields': ['associates'],
            'timestamp': datetime.now()
        }
        db.update_logs.insert_one(update_log)

        return jsonify({
            'success': True,
            'message': 'Associates updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/api/criminals/<criminal_id>/update/evidence', methods=['POST'])
def update_criminal_evidence(criminal_id):
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        data = request.get_json()
        criminal_id = ObjectId(criminal_id)
        
        # Validate evidence data
        evidence = data.get('evidence', [])
        if not isinstance(evidence, list):
            return jsonify({
                'success': False,
                'message': 'Evidence must be a list'
            }), 400

        # Update the criminal record
        result = db.criminals.update_one(
            {'_id': criminal_id},
            {'$set': {'evidence': evidence}}
        )

        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'message': 'No changes were made'
            }), 400

        # Log the update
        update_log = {
            'criminal_id': criminal_id,
            'police_id': ObjectId(session['police_id']),
            'section': 'evidence',
            'updated_fields': ['evidence'],
            'timestamp': datetime.now()
        }
        db.update_logs.insert_one(update_log)

        return jsonify({
            'success': True,
            'message': 'Evidence updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/api/criminals/<criminal_id>/update/case', methods=['POST'])
def update_criminal_case(criminal_id):
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        data = request.get_json()
        criminal_id = ObjectId(criminal_id)
        
        # Validate case data
        if not isinstance(data, dict):
            return jsonify({
                'success': False,
                'message': 'Invalid data format'
            }), 400

        # Prepare update data
        update_data = {
            'case_number': data.get('case_number'),
            'case_status': data.get('case_status'),
            'case_description': data.get('case_description'),
            'fir_number': data.get('fir_number'),
            'case_filed_date': data.get('case_filed_date'),
            'investigating_officers': data.get('investigating_officers', []),
            'police_actions': data.get('police_actions', []),
            'evidence': data.get('evidence', [])
        }

        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Update the criminal record
        result = db.criminals.update_one(
            {'_id': criminal_id},
            {'$set': update_data}
        )

        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'message': 'No changes were made'
            }), 400

        # Log the update
        update_log = {
            'criminal_id': criminal_id,
            'police_id': ObjectId(session['police_id']),
            'section': 'case',
            'updated_fields': list(update_data.keys()),
            'timestamp': datetime.now()
        }
        db.update_logs.insert_one(update_log)

        return jsonify({
            'success': True,
            'message': 'Case details updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/api/police/officers', methods=['GET'])
def get_available_officers():
    if 'police_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    try:
        # Fetch all active police officers
        officers = list(db.police.find(
            {'status': 'active'},
            {
                'full_name': 1,
                'badge_number': 1,
                'department': 1,
                'rank': 1,
                '_id': 0  # Exclude _id from response
            }
        ))
        
        return jsonify({
            'success': True,
            'officers': officers
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@police.route('/officer/profile/<badge_number>')
def officer_profile(badge_number):
    # Fetch officer information
    officer = db['police'].find_one({'badge_number': badge_number})
    if not officer:
        flash('Officer not found', 'error')
        return redirect(url_for('police.police_dashboard'))
    
    # Convert ObjectId to string
    officer['_id'] = str(officer['_id'])
    
    # Calculate statistics
    stats = {
        'cases_handled': db.criminals.count_documents({'registered_by': badge_number}),
        'arrests_made': db.criminals.count_documents({'status': 'Arrested', 'arrested_by': badge_number}),
        'criminals_added': db.criminals.count_documents({'registered_by': badge_number})
    }
    officer['stats'] = stats
    
    # Fetch recent activity
    recent_activity = list(db.officer_activity.find(
        {'badge_number': badge_number}
    ).sort('date', -1).limit(5))
    
    # Convert dates to strings
    for activity in recent_activity:
        activity['date'] = activity['date'].strftime('%Y-%m-%d %H:%M:%S')
    
    officer['recent_activity'] = recent_activity
    
    # Fetch criminals added by this officer
    criminals = list(db.criminals.find({'registered_by': badge_number}).sort('registered_on', -1))
    
    # Convert ObjectId to string and format dates
    for criminal in criminals:
        criminal['_id'] = str(criminal['_id'])
        if 'registered_on' in criminal:
            if isinstance(criminal['registered_on'], str):
                continue
            else:
                criminal['registered_on'] = criminal['registered_on'].strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('police_profile.html', officer=officer, criminals=criminals)



