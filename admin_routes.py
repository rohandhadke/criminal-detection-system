from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import db
from flask_bcrypt import Bcrypt

admin = Blueprint('admin', __name__)
bcrypt = Bcrypt()



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
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    police_officers = list(db.police.find())
    return render_template('admin_dashboard.html', police_officers=police_officers)

# ADD POLICE OFFICER
@admin.route('/admin/add_police', methods=['POST'])
def add_police():
    if 'admin_id' not in session:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('admin_login'))

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
@admin.route('/admin/edit_police', methods=['POST'])
def edit_police():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    police_id = request.form['police_id']
    full_name = request.form['full_name']
    email = request.form['email']
    department = request.form['department']
    badge_number = request.form['badge_number']
    police_station_branch = request.form['police_station_branch']

    db.police.update_one(
        {"_id": ObjectId(police_id)},
        {"$set": {
            "full_name": full_name,
            "email": email,
            "department": department,
            "badge_number": badge_number,
            "police_station_branch": police_station_branch
        }}
    )
    flash('Police Officer Updated Successfully', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# ADMIN LOGOUT
@admin.route('/logout')
def logout():
    session.clear()  # Clears all session data
    flash("Logged out successfully!", "success")
    return redirect(url_for('admin.admin_login'))
