from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

police = Blueprint("police", __name__)

@police.route("/add_criminal", methods=["GET", "POST"])
def add_criminal():
    if request.method == "POST":
        name = request.form["name"]
        crime_type = request.form["crime_type"]
        penalty = request.form["penalty"]
        punishment_duration = request.form["punishment_duration"]
        status = "active"

        criminals_collection.insert_one({
            "name": name,
            "crime_type": crime_type,
            "penalty": penalty,
            "punishment_duration": punishment_duration,
            "status": status
        })

        flash("Criminal added successfully!", "success")
        return redirect(url_for("police.dashboard"))

    return render_template("add_criminal.html")

@police.route("/edit_criminal/<criminal_id>", methods=["GET", "POST"])
def edit_criminal(criminal_id):
    criminal = criminals_collection.find_one({"_id": ObjectId(criminal_id)})

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

