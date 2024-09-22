from flask import Flask, request, render_template, redirect, url_for, session , make_response , send_file , flash
import os
from db.db_connection import connect_to_database
from werkzeug.utils import secure_filename
import gridfs
from io import BytesIO
from cryptography.fernet import Fernet
import bcrypt
import datetime
from bson import ObjectId
from functools import wraps
from user.login import login_user   
from user.register import register_user
from user.dashboard import get_user_data, save_user_thought, update_user_details , get_user_thoughts_sorted , convert_thoughts_to_excel , encrypt_data


app = Flask(__name__)
app.secret_key = b'8CJWgCQw4u01NmPiPAP0lWJIMghAoBrwecQDP0LVsT0='

def load_key():
    return open("secret.key", "rb").read()


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
    
    
    file = request.files['profile_picture']
    user_id = session['user_id']
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})

    if user_data and 'profile_picture' in user_data:
        existing_profile_picture_id = user_data['profile_picture']
        fs.delete(existing_profile_picture_id)
        fs_files_collection.delete_one({'_id': existing_profile_picture_id})
        fs_chunks_collection.delete_many({'files_id': existing_profile_picture_id})
    if file:
        filename = secure_filename(file.filename)
        file_id = fs.put(file, filename=filename)

        user_id = session['user_id']
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'profile_picture': file_id}})
        return redirect(url_for('dashboard'))
    return 'No file selected'
    
@app.route('/upload_background_image', methods=['POST'])
def upload_background_image():
    if 'background_image' not in request.files:
        return redirect(request.url)

    
    file = request.files['background_image']

    user_id = session['user_id']
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})

    
    if user_data and 'background_image' in user_data:
        existing_background_image_id = user_data['background_image']
        fs.delete(existing_background_image_id)
        fs_files_collection.delete_one({'_id': existing_background_image_id})
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
   
    page = request.args.get('page', 1, type=int)  
    per_page = 2 
    user_id = session['user_id']
    user_data = get_user_data(user_id)
   
    if not user_data:
        flash('User not found', 'danger')
        return redirect(url_for('home_page'))
    background_image_url = url_for('get_image', filename=user_data.get('background_image')) if user_data.get('background_image') else None
    background = user_data.get('background', 'default')
    user_thoughts = get_user_thoughts_sorted(user_id)
    total_thoughts = len(user_thoughts)
    total_pages = (total_thoughts + per_page - 1) // per_page
    if page > total_pages:
        page = total_pages
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_thoughts = user_thoughts[start_index:end_index]

    # Prepare for pagination display
    page_range_start = max(2, page - 1)
    page_range_end = min(total_pages, page + 1)

    for thought in paginated_thoughts:
        thought['datetime'] = thought['datetime'].strftime('%Y-%m-%d %H:%M:%S')
    if not paginated_thoughts:
        return render_template('dashboard.html', user_data=user_data, thoughts=[], total_pages=total_pages, current_page=page, message=None, background=background, background_image_url=background_image_url, show_add_thought=True)
    message = session.pop('message', None) 
    return render_template('dashboard.html', user_data=user_data, thoughts=paginated_thoughts, total_pages=total_pages, current_page=page, message=message , background=background, background_image_url=background_image_url, page_range_start=page_range_start, page_range_end=page_range_end)

    



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
    sex = request.form.get('sex')  

    if not sex:
        return render_template('register.html', message="Please provide a gender.")

    success, message_or_user_id = register_user(username, email, password, sex)
    if success:
        session['user_id'] = str(message_or_user_id)
        session['username'] = str(username)
        return redirect(url_for('dashboard'))
    else:
        if message_or_user_id == "Database connection issue.":
            flash("Some Disturbance occurred, just try after some time", "error")
            return redirect(url_for('home_page'))
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
    sex = request.form.get('sex')  

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
        if message_or_user_id == "Database connection issue.":
            flash("Some Disturbance occurred, just try after some time", "error")
            return redirect(url_for('home_page'))
        else:
            return message_or_user_id + " Please <a href='/login/'>try again</a> or New user? Please Register <a href='/register'>here</a>"
    
        
@app.route('/update_details', methods=['POST'])
@login_required

def update_details():
    user_id = session['user_id']
    existing_user_data = get_user_data(user_id)
    new_data = {}
    if request.form['username'] and request.form['username'] != existing_user_data['username']:
        new_data['username'] = request.form['username']
    if request.form['email'] and request.form['email'] != existing_user_data['email']:
        new_data['email'] = request.form['email']
    if request.form['password']:
        new_password_hash = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        if new_password_hash != existing_user_data['password']:
            new_data['password'] = new_password_hash
    if new_data:
        update_user_details(user_id, new_data)
        session['message'] = 'Details updated successfully'
        if 'username' in new_data:
            session['username'] = new_data['username']
    else:
        session['message'] = 'No changes were made'
    return redirect(url_for('dashboard'))

@app.route('/save_thought', methods=['POST'])
@login_required
def save_thought():
    user_id = session['user_id']
    thought = request.form['thought']
    datetime_str = request.form['datetime']
    if not datetime_str:
        datetime_obj = datetime.datetime.now()
    else:
        datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
    
    save_user_thought(user_id, thought, datetime_obj)
    session['message'] = 'Thought saved successfully'
    return redirect(url_for('dashboard'))

@app.route('/update_thought/<thought_id>', methods=['POST'])
@login_required
def update_thought(thought_id):
    user_id = session['user_id']
    updated_thought = request.form['updated_thought']
    current_page = request.args.get('page', 1, type=int) 
    encrypted_updated_thought = encrypt_data(updated_thought)
    user_thoughts_collection = db[f'user_{user_id}_thoughts']
    existing_thought = user_thoughts_collection.find_one({'_id': ObjectId(thought_id), 'user_id': user_id})
    if existing_thought is not None:
        if encrypted_updated_thought != existing_thought.get('thought'):
            user_thoughts_collection.update_one({'_id': ObjectId(thought_id), 'user_id': user_id}, {'$set': {'thought': encrypted_updated_thought}})
            session['message'] = 'Thought updated successfully'
        else:
            session['message'] = 'No changes made to the thought'

    else:
        session['message'] = 'Thought with ID {} not found.'.format(thought_id)
    
    
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
    username = session['username'] 
    thoughts = get_user_thoughts_sorted(user_id)
    excel_filename = convert_thoughts_to_excel(thoughts, username)
    with open(excel_filename, "rb") as f:
        file_content = f.read()
    response = make_response(file_content)
    response.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(excel_filename)}"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return response
if __name__ == '__main__':
    app.run(host='0.0.0.0' , debug=True)
