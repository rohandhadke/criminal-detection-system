from pymongo import MongoClient
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["criminal-detection-system"]


# Collections
users_collection = db["users"]
criminals_collection = db["criminals"]

def create_default_admin():
    """Checks if an admin exists, if not, creates a default admin account."""
    existing_admin = db.admins.find_one({"username": "admin@cds.com"})
    if not existing_admin:
        hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')
        db.admins.insert_one({
            "name": "Super Admin",
            "username": "admin@cds.com",
            "password": hashed_password
        })
        print("Default Admin Created: Email -> admin@cds.com, Password -> admin")
    else:
        print("Admin already exists.")


create_default_admin()