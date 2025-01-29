from flask import Flask, jsonify, render_template ,request
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import requests
from functions import *
app = Flask(__name__)
load_dotenv()
change_stream_db = os.getenv('CHANGE_STREAM_DB')
client = MongoClient(change_stream_db)
db = client.mentza
@app.route("/")
def home():
    
    return render_template("index.html")  # Ensure `index.html` exists in a `templates/` folder

@app.route('/login', methods=['GET', 'POST']) # login route
def login():
    if request.method == 'POST':
        #get the credintials from the user
        username= request.form.get('username')
        password= request.form.get('password')
        credintails= db.users.find_one({"username": username})
        print(username , password)
        print(credintails)
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        elif None != credintails and username == credintails.get('username') and password == credintails.get('password'): # check with database
            return render_template('home.html',username=username)
        else : 
            return jsonify({'error': 'Invalid username or password'}), 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST']) # signup route
def signup():
    if request.method == 'POST':
        #get the credintials from the user
        username= request.form.get('username') # should be email
        password= request.form.get('password') 
        email= request.form.get('email')
        # university= request.json.get('university')
        # degree= request.json.get('degree')
        # stream= request.json.get('stream')
        # dob= request.json.get('dob')

        print(username , password , email ) #, university, dob, degree, stream
        if not username or not password or not email: # or university or dob or degree or stream
            return jsonify({'error': 'Username and password are required'}), 400
        elif db.users.find_one({'email': email}) or db.users.find_one({'username': username}): # already exist
            return jsonify({'error': 'Username already exists'}), 402
        else: 
            # store in database 
            data = {
                "user_id": generate_userid(),
                "username": username,
                "password": password,
                "email": email,
                # "c_password": c_pass,
                # "dob": dob,
                # "degree": degree,
                # "stream": stream,
                # "university": university
            }
            print(data)
            # mongodb
            response = db.users.insert_one(data)
            if response.inserted_id:
                return render_template('login_new.html')
            else:
                return jsonify({'error': 'Signup failed'}), 403
    return render_template('signup.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=12345)