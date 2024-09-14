from flask import Flask, request, render_template, redirect, url_for, session , make_response , send_file , flash
import os
from db.db_connection import connect_to_database
from werkzeug.utils import secure_filename
import gridfs
from io import BytesIO
# import base64
from cryptography.fernet import Fernet
import bcrypt
import datetime
from bson import ObjectId
from functools import wraps
from user.login import login_user   
from user.register import register_user
from user.dashboard import get_user_data, save_user_thought, update_user_details , get_user_thoughts_sorted , convert_thoughts_to_excel , encrypt_data


app = Flask(__name__)
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.secret_key = b'oBe6cN2foAllfHQL1I0FrLGMJqZRe470lxCJz3TH-oE='
#app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

def load_key():
    return open("secret.key", "rb").read()

# Configure Jinja environment to include the 'max' function
app.jinja_env.globals.update(max=max)


db = connect_to_database()
fs = gridfs.GridFS(db)
users_collection = db['users']
thoughts_collection = db['user_thoughts']
fs_files_collection = db['fs.files']
fs_chunks_collection = db['fs.chunks']


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('home_page'))
        return func(*args, **kwargs)
    return decorated_function

def not_authenticated(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            # return redirect(url_for('dashboard', message='You cannot register while logged in. Please log out and try again.'))
            session['message'] = 'You cannot register while logged in. Please log out and try again.'
            return redirect(url_for('dashboard'))
        return func(*args, **kwargs)
    return decorated_function

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        return redirect(request.url)
        # return 'No file part'
    
    
    file = request.files['profile_picture']
    user_id = session['user_id']
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    # Delete existing profile image from GridFS (if exists)

    if user_data and 'profile_picture' in user_data:
        # Get the file ID of the existing profile image
        existing_profile_picture_id = user_data['profile_picture']
        fs.delete(existing_profile_picture_id)
        
        # Delete the file from the fs.files collection
        fs_files_collection.delete_one({'_id': existing_profile_picture_id})
        
        # Delete associated chunks from the fs.chunks collection
        fs_chunks_collection.delete_many({'files_id': existing_profile_picture_id})
    # print(file)  # Add this line to print the file object
    # Delete existing profile picture from GridFS (if exists)
    # if users_collection['profile_picture']:
    #     # Get the file ID of the existing profile picture
    #     existing_profile_picture_id = users_collection['profile_picture']
    #     # Delete the file from the fs.files collection
    #     fs_files_collection.delete_one({'_id': existing_profile_picture_id})
    #     # Delete associated chunks from the fs.chunks collection
    #     fs_chunks_collection.delete_many({'files_id': existing_profile_picture_id})
    if file:
        filename = secure_filename(file.filename)
        # Save the uploaded file to your MongoDB GridFS
        file_id = fs.put(file, filename=filename)

        user_id = session['user_id']
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'profile_picture': file_id}})
        return redirect(url_for('dashboard'))
        # Update the user's profile picture field in the database
        # user_id = session.get('user_id')
        # if user_id:
            # users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'profile_picture': file_id}})
            # return redirect(url_for('dashboard'))
    return 'No file selected'
    
@app.route('/upload_background_image', methods=['POST'])
def upload_background_image():
    if 'background_image' not in request.files:
        return redirect(request.url)

    
    file = request.files['background_image']

    user_id = session['user_id']
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})

    # Delete existing background image from GridFS (if exists)
    if user_data and 'background_image' in user_data:
        # Get the file ID of the existing background image
        existing_background_image_id = user_data['background_image']
        fs.delete(existing_background_image_id)
        
        # Delete the file from the fs.files collection
        fs_files_collection.delete_one({'_id': existing_background_image_id})
        
        # Delete associated chunks from the fs.chunks collection
        fs_chunks_collection.delete_many({'files_id': existing_background_image_id})

    if file:
        filename = secure_filename(file.filename)
        file_id = fs.put(file, filename=filename)
        user_id = session['user_id']
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'background_image': file_id}})
        return redirect(url_for('dashboard'))
    return redirect(url_for('dashboard'))
    
@app.route('/image/<filename>')
def get_image(filename):
    file_id = ObjectId(filename)
    file = fs.get(file_id)
    return send_file(BytesIO(file.read()), mimetype='image/jpeg')
   


@app.route('/dashboard')
@login_required
def dashboard():
   
    page = request.args.get('page', 1, type=int)  # Get the page number from query parameters, default to 1
    per_page = 2  # Number of thoughts per page
    user_id = session['user_id']
    user_data = get_user_data(user_id)
    # user_data = get_user_data(current_user.id)
    if not user_data:
        # Handle the case where the user is not found
        flash('User not found', 'danger')
        return redirect(url_for('home_page'))
    # background_image_url = url_for('get_image', filename=user_data['background_image']) if user_data['background_image'] else None
    background_image_url = url_for('get_image', filename=user_data.get('background_image')) if user_data.get('background_image') else None
    background = user_data.get('background', 'default')
    # # Get user thoughts
    # user_thoughts = get_user_thoughts(user_id)

    # Get user thoughts in reverse order
    user_thoughts = get_user_thoughts_sorted(user_id)
    # Get total number of thoughts for pagination
    #total_thoughts = thoughts_collection.count_documents({'user_id': user_id})
    # Sort thoughts by datetime in descending order
    # sorted_thoughts = sorted(user_thoughts, key=lambda x: datetime.strptime(x['datetime'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    total_thoughts = len(user_thoughts)

    # # Calculate total number of pages based on remaining thoughts after deletion
    # remaining_thoughts = total_thoughts - per_page * (page - 1)
    # remaining_pages = (remaining_thoughts + per_page - 1) // per_page

    # Calculate total number of pages based on total thoughts and thoughts per page
    total_pages = (total_thoughts + per_page - 1) // per_page
    
    # Adjust current page if it exceeds the remaining pages
    if page > total_pages:
        page = total_pages

    # Calculate start and end indices for current page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    # Slice thoughts for the current page
    paginated_thoughts = user_thoughts[start_index:end_index]

    #thoughts = get_user_thoughts(user_id)
    # thoughts_with_dates = []
    for thought in paginated_thoughts:
        # if 'datetime' in thought:  # Check if 'datetime' key exists
        thought['datetime'] = thought['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        # thoughts_with_dates.append(thought)

    # # Calculate total number of pages
    # total_pages = (total_thoughts + per_page - 1) // per_page
    # Check if thoughts list is empty
    if not paginated_thoughts:
        # If no thoughts, render the dashboard without paginated thoughts
        return render_template('dashboard.html', user_data=user_data, thoughts=[], total_pages=total_pages, current_page=page, message=None, background=background, background_image_url=background_image_url, show_add_thought=True)
    

    message = session.pop('message', None)  # Retrieve and remove the message from the session
    

    return render_template('dashboard.html', user_data=user_data, thoughts=paginated_thoughts, total_pages=total_pages, current_page=page, message=message , background=background, background_image_url=background_image_url)
    # message = request.args.get('message', None)
    # # message = session.pop('message', None)  # Get the message and remove it from session
    # message = session.get('message')
    # session.pop('message', None)  # Remove the message from the session
    # message = session.pop('message', None)  # Retrieve and remove the message from the session
    # if 'user_id' in session:
    #     user_id = session['user_id']
    #     user_data = get_user_data(user_id)
    #     thoughts = get_user_thoughts(user_id)
    #     thoughts_with_dates = []
    #     for thought in thoughts:
    #         if 'datetime' in thought:  # Check if 'datetime' key exists
    #             thought['datetime'] = thought['datetime'].strftime('%Y-%m-%d %H:%M:%S')
    #         thoughts_with_dates.append(thought)
    #     return render_template('dashboard.html', user_data=user_data, message=message, thoughts=thoughts_with_dates)
    

    



@app.route('/register/', methods=['GET'])
@not_authenticated
def register_page():
    return render_template('register.html')

@app.route('/register/', methods=['POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    # sex = request.form['sex']
    sex = request.form.get('sex')  # Use get method to handle missing key

    # Check if the sex field is empty
    if not sex:
        return render_template('register.html', message="Please provide a gender.")

    success, message_or_user_id = register_user(username, email, password, sex)
    if success:
        session['user_id'] = str(message_or_user_id)
        session['username'] = str(username)
        return redirect(url_for('dashboard'))
    else:
        return render_template('register.html', message=message_or_user_id)
   


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template("login.html")

    username_or_email = request.form['username_or_email']
    password = request.form['password']
    # sex = request.form['sex']
    sex = request.form.get('sex')  # Use request.form.get to safely get the 'sex' field

    if not sex:
        return "Please select your gender. <a href='/'>Go back to login</a>"

    valid_genders = ['Male', 'Female' , 'Other']

    if sex not in valid_genders:
        return "Invalid gender selection. <a href='/'>Go back to login</a>"
    
   
    success, message_or_user_id= login_user(username_or_email, password, sex)
    if success:
        user_data = get_user_data(message_or_user_id)
        if 'username' in user_data:
            session['user_id'] = str(message_or_user_id)
            session['username'] = user_data['username']  # Store the username in the session
            return redirect(url_for('dashboard'))
        else:
            return "User data does not contain username. Please try again."
    else:
        return message_or_user_id + " Please <a href='/login/'>try again</a> or New user? Please Register <a href='/register'>here</a>"
    
        
@app.route('/update_details', methods=['POST'])
@login_required

def update_details():
    user_id = session['user_id']
    existing_user_data = get_user_data(user_id)
    new_data = {}

    # Check if the username field is not empty and different from the existing value
    if request.form['username'] and request.form['username'] != existing_user_data['username']:
        new_data['username'] = request.form['username']

    # Check if the email field is not empty and different from the existing value
    if request.form['email'] and request.form['email'] != existing_user_data['email']:
        new_data['email'] = request.form['email']

    # Check if the password field is not empty and different from the existing value
    if request.form['password']:
        new_password_hash = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        if new_password_hash != existing_user_data['password']:
            new_data['password'] = new_password_hash

    # Add other fields as needed

    # Update user details if there are changes
    if new_data:
        update_user_details(user_id, new_data)
        session['message'] = 'Details updated successfully'
        if 'username' in new_data:
            session['username'] = new_data['username']
    else:
        session['message'] = 'No changes were made'
    
    #session['message'] = 'Details updated successfully'
    return redirect(url_for('dashboard'))

@app.route('/save_thought', methods=['POST'])
@login_required
def save_thought():
    user_id = session['user_id']
    thought = request.form['thought']
    datetime_str = request.form['datetime']
    
    # # Parse the datetime string to a datetime object
    # datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
    # save_user_thought(user_id, thought , datetime_obj)
    # #return redirect(url_for('dashboard', message='Thought saved successfully'))
    # Check if datetime_str is empty

    
    if not datetime_str:
        # If empty, use the current datetime
        datetime_obj = datetime.datetime.now()
    else:
        # Parse the datetime string to a datetime object
        datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
    
    save_user_thought(user_id, thought, datetime_obj)
    session['message'] = 'Thought saved successfully'
    return redirect(url_for('dashboard'))

@app.route('/update_thought/<thought_id>', methods=['POST'])
@login_required
def update_thought(thought_id):
    user_id = session['user_id']
    updated_thought = request.form['updated_thought']
    current_page = request.args.get('page', 1, type=int)  # Get the current page number

    # Encrypt the updated thought
    encrypted_updated_thought = encrypt_data(updated_thought)
    # Fetch the existing thought from the database
    user_thoughts_collection = db[f'user_{user_id}_thoughts']
    existing_thought = user_thoughts_collection.find_one({'_id': ObjectId(thought_id), 'user_id': user_id})
    
    # Check if the existing thought exists and is not None
    if existing_thought is not None:
    # Check if the updated thought is different from the existing one
        if encrypted_updated_thought != existing_thought.get('thought'):
            user_thoughts_collection.update_one({'_id': ObjectId(thought_id), 'user_id': user_id}, {'$set': {'thought': encrypted_updated_thought}})
            session['message'] = 'Thought updated successfully'
            # return redirect(url_for('dashboard', message='Thought updated successfully')) 
        else:
            # return redirect(url_for('dashboard', message='No changes made to the thought'))
            session['message'] = 'No changes made to the thought'

    else:
        # Handle the case when the thought doesn't exist
        # return redirect(url_for('dashboard', message='Thought with ID {} not found.'.format(thought_id)))
        session['message'] = 'Thought with ID {} not found.'.format(thought_id)
    
    #session['message'] = 'Thought updated successfully'
    return redirect(url_for('dashboard' , page=current_page))

@app.route('/delete_thought/<thought_id>', methods=['POST'])
@login_required
def delete_thought(thought_id):
    user_id = session['user_id']
    current_page = request.args.get('page', 1, type=int)  # Get the current page number
    user_thoughts_collection = db[f'user_{user_id}_thoughts']  # Get user-specific collection
    result = user_thoughts_collection.delete_one({'_id': ObjectId(thought_id)})
    if result.deleted_count == 1:
        session['message'] = 'Thought deleted successfully'
    else:
        session['message'] = 'Thought with ID {} not found.'.format(thought_id)
    return redirect(url_for('dashboard' , page=current_page))
  



@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home_page'))

@app.route('/export_thoughts', methods=['GET'])
@login_required
def export_thoughts():
    user_id = session['user_id']
    username = session['username']  # Retrieve the username from the session
    
    thoughts = get_user_thoughts_sorted(user_id)
    
    # Create the Excel file with the username in the filename
    excel_filename = convert_thoughts_to_excel(thoughts, username)
    
    # Read the file content
    with open(excel_filename, "rb") as f:
        file_content = f.read()
    
    # Prepare response with file data
    response = make_response(file_content)
    
    # Set appropriate headers for file download
    response.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(excel_filename)}"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return response

# def encrypt_thought(thought: str) -> str:
#     encrypted_thought = cipher_suite.encrypt(thought.encode())
#     return encrypted_thought.decode()

# def decrypt_thought(encrypted_thought: str) -> str:
#     decrypted_thought = cipher_suite.decrypt(encrypted_thought.encode())
#     return decrypted_thought.decode()


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0' , debug=True)
