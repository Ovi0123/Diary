from passlib.hash import bcrypt
from db.db_connection import connect_to_database

# client = MongoClient('mongodb://localhost:27017/')
# db = client['mydatabase']
# users_collection = db['users']

db = connect_to_database()
users_collection = db['users']

def register_user(username, email, password, sex):
        if users_collection.find_one({'email': email}):
            return False, "Email already exists. Please choose another email."
        if users_collection.find_one({'username': username}):
            return False, "Username already exists. Please choose another username."
        if not len(password) >= 4 and len(password) <= 20:
            return False, "Password must be alphanumeric and have a length of 4 to 20 characters."
        hashed_password = bcrypt.hash(password)
        user_id = users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password, 'sex': sex}).inserted_id
        return True, user_id
    