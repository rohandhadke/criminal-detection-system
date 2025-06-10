from flask import Blueprint, request, redirect, url_for, flash, render_template
from database import users_collection
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

auth = Blueprint("auth", __name__)

@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        role = request.form["role"]  # "admin" or "police"

        # Check if email already exists
        if users_collection.find_one({"email": email}):
            flash("Email already exists!", "danger")
            return redirect(url_for("auth.signup"))

        # Insert into database
        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": password,
            "role": role
        })

        flash("Signup successful! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = users_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]

            flash("Login successful!", "success")
            return redirect(url_for("admin.dashboard") if user["role"] == "admin" else url_for("police.dashboard"))

        flash("Invalid credentials!", "danger")
    return render_template("login.html")