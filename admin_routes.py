from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import db
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from bson import ObjectId
from flask import abort
from functools import wraps

admin = Blueprint('admin', __name__)
bcrypt = Bcrypt()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.json  # Get JSON data from AJAX request
        email = data.get('email')
        password = data.get('password')

        # Find admin in database
        admin = db.admins.find_one({"username": email})
        if admin and bcrypt.check_password_hash(admin['password'], password):
            session['admin_id'] = str(admin['_id'])  # Start session
            return jsonify({"success": True, "redirect": url_for('admin.admin_dashboard')})
        
        return jsonify({"success": False, "message": "Invalid Credentials"})

    return render_template('admin_login.html')

# ADMIN DASHBOARD
@admin.route('/admin/dashboard')
@login_required
def admin_dashboard():
    police_officers = list(db.police.find())
    return render_template('admin_dashboard.html', police_officers=police_officers)

# ADD POLICE OFFICER
@admin.route('/admin/add_police', methods=['POST'])
@login_required
def add_police():
    full_name = request.form.get('name')
    email = request.form.get('email')
    department = request.form.get('department')
    badge_number = request.form.get('badge_number')
    police_station_branch = request.form.get('police_station_branch')
    password = request.form.get('password')

    # print(full_name, email, department, badge_number, police_station_branch, password)

    if not (full_name and email and department and badge_number and police_station_branch and password):
        flash("All fields are required!", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password)

    # Insert into MongoDB
    db['police'].insert_one({
        "full_name": full_name,
        "email": email,
        "department": department,
        "badge_number": badge_number,
        "police_station_branch": police_station_branch,
        "password": hashed_password
    })

    flash("Police Officer Added Successfully!", "success")
    return redirect(url_for('admin.admin_dashboard'))  # Redirect to admin dashboard

# EDIT POLICE OFFICER
@admin.route('/update_officer/<officer_id>', methods=['POST'])
@login_required
def update_officer(officer_id):
    officer = db.police.find_one({"_id": ObjectId(officer_id)})
    if not officer:
        flash('Officer not found', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    update_data = {
        "full_name": request.form.get('full_name'),
        "badge_number": request.form.get('badge_number'),
        "rank": request.form.get('rank'),
        "department": request.form.get('department'),
        "email": request.form.get('email'),
        "phone": request.form.get('phone'),
        "join_date": request.form.get('join_date'),
        "years_of_service": request.form.get('years_of_service'),
        "specialization": request.form.get('specialization'),
        "station": request.form.get('station')
    }
    # Remove empty fields
    update_data = {k: v for k, v in update_data.items() if v is not None}

    db.police.update_one({"_id": ObjectId(officer_id)}, {"$set": update_data})
    flash('Officer updated successfully!', 'success')
    return redirect(url_for('admin.officer_profile_by_admin', officer_id=officer_id))

# DELETE POLICE OFFICER
@admin.route('/admin/delete_police/<police_id>', methods=['GET'])
@login_required
def delete_police(police_id):
    try:
        # Convert string ID to ObjectId
        police_id = ObjectId(police_id)
        result = db.police.delete_one({"_id": police_id})
        
        if result.deleted_count > 0:
            flash('Police Officer Deleted Successfully', 'success')
        else:
            flash('Police Officer not found', 'danger')
    except Exception as e:
        flash('Error deleting police officer', 'danger')
    
    return redirect(url_for('admin.admin_dashboard'))

# ADMIN LOGOUT
@admin.route('/logout')
@login_required
def logout():
    session.clear()  # Clears all session data
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))

@admin.route('/officer_profile_by_admin/<officer_id>', methods=['GET', 'POST'])
@login_required
def officer_profile_by_admin(officer_id):
    # Fetch officer from DB using officer_id
    officer = get_officer_by_id(officer_id)  # Replace with your actual DB call
    criminals = get_criminals_added_by_officer(officer_id)  # Optional, if you want to show this

    if request.method == 'POST':
        # Update officer info from form data
        officer.full_name = request.form['full_name']
        officer.badge_number = request.form['badge_number']
        officer.rank = request.form['rank']
        officer.department = request.form['department']
        officer.email = request.form['email']
        officer.phone = request.form['phone']
        officer.join_date = request.form['join_date']
        officer.years_of_service = request.form['years_of_service']
        officer.specialization = request.form['specialization']
        officer.station = request.form['station']
        # Save officer to DB
        save_officer(officer)  # Replace with your actual DB save logic
        return redirect(url_for('admin.officer_profile_by_admin', officer_id=officer_id))

    return render_template(
        'officer_profile_by_admin.html',
        officer=officer,
        criminals=criminals
    )

def get_officer_by_id(officer_id):
    try:
        officer = db.police.find_one({"_id": ObjectId(officer_id)})
        if not officer:
            abort(404, description="Officer not found")
        officer['_id'] = str(officer['_id'])  # For template compatibility

        # Calculate statistics (optional, as in police_routes.py)
        stats = {
            'cases_handled': db.criminals.count_documents({'registered_by': officer.get('badge_number')}),
            'arrests_made': db.criminals.count_documents({'status': 'Arrested', 'arrested_by': officer.get('badge_number')}),
            'criminals_added': db.criminals.count_documents({'registered_by': officer.get('badge_number')})
        }
        officer['stats'] = stats

        # Recent activity (optional)
        recent_activity = list(db.officer_activity.find(
            {'badge_number': officer.get('badge_number')}
        ).sort('date', -1).limit(5))
        for activity in recent_activity:
            if 'date' in activity and hasattr(activity['date'], 'strftime'):
                activity['date'] = activity['date'].strftime('%Y-%m-%d %H:%M:%S')
        officer['recent_activity'] = recent_activity

        return officer
    except Exception as e:
        print(f"Error fetching officer: {e}")
        abort(500, description="Internal Server Error")

def get_criminals_added_by_officer(officer_id):
    try:
        officer = db.police.find_one({"_id": ObjectId(officer_id)})
        if not officer:
            return []
        badge_number = officer.get('badge_number')
        criminals = list(db.criminals.find({'registered_by': badge_number}).sort('registered_on', -1))
        for criminal in criminals:
            criminal['_id'] = str(criminal['_id'])
            if 'registered_on' in criminal and hasattr(criminal['registered_on'], 'strftime'):
                criminal['registered_on'] = criminal['registered_on'].strftime('%Y-%m-%d %H:%M:%S')
        return criminals
    except Exception as e:
        print(f"Error fetching criminals: {e}")
        return []
    


@admin.route('/reports')
@login_required
def reports():
    # Get total officers count
    total_officers = db.police.count_documents({})
    
    # Get total criminals count
    total_criminals = db.criminals.count_documents({})
    
    # Get active and solved cases counts
    active_cases = db.criminals.count_documents({"status": "Arrested"})
    solved_cases = db.criminals.count_documents({"status": "wanted"})
    
    # Get department statistics
    department_stats = []
    departments = ["Patrol", "Traffic", "CID", "Narcotics"]
    
    for dept in departments:
        officers_count = db.police.count_documents({"department": dept})
        active_cases_count = db.criminals.count_documents({
            "assigned_department": dept,
            "status": "wanted"
        })
        
        department_stats.append({
            "name": dept,
            "officers": officers_count,
            "active_cases": active_cases_count
        })
    
    
    # Get recent criminal activities
    recent_activities = list(db.criminals.find(
        {},
        {"name": 1, "crime_type": 1, "registered_on": 1, "status": 1, "_id": 0}
    ).sort("date", -1).limit(5))
    
    # Add status colors for badges
    for activity in recent_activities:
        if activity["status"] == "active":
            activity["status_color"] = "danger"
        elif activity["status"] == "solved":
            activity["status_color"] = "success"
        else:
            activity["status_color"] = "warning"
    
    # Prepare data for charts
    department_labels = [dept["name"] for dept in department_stats]
    department_data = [dept["officers"] for dept in department_stats]
    
    # Get criminal types distribution
    criminal_types = db.criminals.aggregate([
        {"$group": {"_id": "$crime_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    
    criminal_type_labels = []
    criminal_type_data = []
    
    for type_doc in criminal_types:
        criminal_type_labels.append(type_doc["_id"])
        criminal_type_data.append(type_doc["count"])
    
    return render_template('reports.html',
                         total_officers=total_officers,
                         total_criminals=total_criminals,
                         active_cases=active_cases,
                         solved_cases=solved_cases,
                         department_stats=department_stats,
                         recent_activities=recent_activities,
                         department_labels=department_labels,
                         department_data=department_data,
                         criminal_type_labels=criminal_type_labels,
                         criminal_type_data=criminal_type_data) 