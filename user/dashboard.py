from bson.objectid import ObjectId
from pymongo import DESCENDING  # Import DESCENDING for sorting
from db.db_connection import connect_to_database
import pandas as pd
from cryptography.fernet import Fernet

def load_key():
    return open("secret.key", "rb").read()

key = load_key()
f = Fernet(key)

def encrypt_data(data):
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data):
    try:
        decrypted_data = f.decrypt(encrypted_data).decode()
        return decrypted_data
    except Exception as e:
        print(f"Error decrypting data: {e}")
        raise

db = connect_to_database()
users_collection = db['users']
thoughts_collection = db['user_thoughts']

def get_user_data(user_id):
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_data is None:
            return {}  
        if user_data.get('profile_picture'):
            user_data['profile_picture'] = str(user_data['profile_picture'])
        if user_data.get('background_image'):
            user_data['background_image'] = str(user_data['background_image'])
        return user_data
   
def update_user_details(user_id, new_data):
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': new_data})
    
def get_user_thoughts(user_id):
        user_thoughts_collection = db[f'user_{user_id}_thoughts']  # Get user-specific collection
        user_thoughts = user_thoughts_collection.find()
        return list(user_thoughts)
   
def get_user_thoughts_sorted(user_id):
    user_thoughts_collection = db[f'user_{user_id}_thoughts'] 
    user_thoughts = list(user_thoughts_collection.find({'user_id': user_id}).sort('datetime', -1))
    
    for thought in user_thoughts:
        thought['thought'] = decrypt_data(thought['thought'])
    
    return user_thoughts
    


def save_user_thought(user_id, thought , datetime_obj):
    encrypted_thought = encrypt_data(thought)
    thought_data = {
        'user_id': user_id,
        'thought': encrypted_thought,
        'datetime': datetime_obj
    }
    user_thoughts_collection = db[f'user_{user_id}_thoughts']  
    user_thoughts_collection.insert_one(thought_data)

def update_user_thought(user_id, thought_id, new_thought):
    user_thoughts_collection = db[f'user_{user_id}_thoughts']  
    user_thoughts_collection.update_one({'_id': ObjectId(thought_id)}, {'$set': {'thought': new_thought}})

def convert_thoughts_to_excel(thoughts, username):
    df = pd.DataFrame(thoughts)
    df.drop(columns=['_id', 'user_id'], inplace=True, errors='ignore')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values(by='datetime', ascending=False)
    excel_filename = f"{username}_thoughts.xlsx"
    df.to_excel(excel_filename, index=False)
    
    return excel_filename
