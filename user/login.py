from passlib.hash import bcrypt
from pymongo.errors import ServerSelectionTimeoutError
from flask import redirect, url_for, flash
from db.db_connection import connect_to_database

# client = MongoClient('mongodb://localhost:27017/')
# db = client['mydatabase']
# users_collection = db['users']

db = connect_to_database()
users_collection = db['users']

# Now you can use the users_collection to perform database operations


def login_user(username_or_email, password, sex):
    try:
        user = users_collection.find_one({'$or': [{'username': username_or_email}, {'email': username_or_email}]})
        if user and bcrypt.verify(password, user['password']):
            if user['sex'] != sex:
                return False, "Invalid gender selection."
            return True, user['_id']
        else:
            return False, "Incorrect username/email or password."
    except ServerSelectionTimeoutError:
        flash("Some Disturbance occurred, just try after some time", "error")
        return redirect(url_for('home_page'))
