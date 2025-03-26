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
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin.admin_login'))

    name = request.form['name']
    email = request.form['email']
    password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

    db.police.insert_one({"name": name, "email": email, "password": password})
    flash('Police Officer Added Successfully', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# EDIT POLICE OFFICER
@admin.route('/admin/edit_police', methods=['POST'])
def edit_police():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin.admin_login'))

    police_id = request.form['police_id']
    name = request.form['name']
    email = request.form['email']

    db.police.update_one({"_id": police_id}, {"$set": {"name": name, "email": email}})
    flash('Police Officer Updated', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# DELETE POLICE OFFICER
@admin.route('/admin/delete_police/<police_id>')
def delete_police(police_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin.admin_login'))

    db.police.delete_one({"_id": police_id})
    flash('Police Officer Deleted', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# ADMIN LOGOUT
@admin.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.admin_login'))
