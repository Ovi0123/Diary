from passlib.hash import bcrypt
from pymongo.errors import ServerSelectionTimeoutError
from db.db_connection import connect_to_database

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
        return False, "Database connection issue."
