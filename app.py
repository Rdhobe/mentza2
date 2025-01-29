from flask import Flask, jsonify, render_template ,request ,redirect ,url_for ,send_file
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
# Global user data storage
user_data = {"intro": "", "answers": [], "analyses": [], "generated_questions": [], "language": "en"}

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

@app.route('/home') # main page 
def home():
    return render_template('jobrole.html')

@app.route('/report') # report route
def report():
    report = {
        "technical_proficiency": generate_parameter_analysis(user_data, "technical proficiency", 8),  # Example rating of 8
        "communication": generate_parameter_analysis(user_data, "communication", 7),  # Example rating of 7
        "decision_making": generate_parameter_analysis(user_data, "decision making", 6),  # Example rating of 6
        "confidence": generate_parameter_analysis(user_data, "confidence", 9),  # Example rating of 9
        "areas_to_improve": generate_parameter_analysis(user_data, "areas to improve", 5),  # Example rating of 5
    }
    return render_template('report.html',analysis_report =report )

@app.route('/profile', methods=['GET','POST']) # get profile from database
def profile():
    if request.method == 'GET':
        return render_template('profile.html')
    username = request.json.get('username') # get id of user  
    user_profile= db.users.find_one({"username": username}) # find user profile by user id 
    print(user_profile)
    return jsonify({"username": user_profile.get('username'), "name": user_profile.get('name'), "email": user_profile.get('email')}), 200


@app.route('/role', methods=['GET', 'POST'])
def role():
    if request.method == "POST":
        user_intro = request.form.get("user_intro", "").strip()
        user_data["intro"] = user_intro

        with open("user_data.txt", "w", encoding="utf-8") as file:
            file.write(f"वापरकर्ता परिचय: {user_intro}\n")

        return redirect(url_for("job_role"))

    return render_template("home.html")


@app.route("/job-role", methods=["GET","POST"])
def job_role():
    if request.method == "POST":
        job_role = request.form.get("job_role", "").strip()
        language = request.form.get("language", "en").strip()  # Get language selection from form
        user_data["job_role"] = job_role
        user_data["language"] = language

        questions = generate_interview_questions(job_role, language)

        if questions:
            user_data["generated_questions"] = questions
            with open("user_data.txt", "a", encoding="utf-8") as file:
                file.write(f"Generated Questions in {language}:\n{questions}\n")
            return redirect(url_for("questions", question_no=1))
        else:
            return "Failed to generate questions. Please try again."

    return render_template("job_role.html")

@app.route("/questions/<int:question_no>", methods=["GET", "POST"])
def questions(question_no):
    questions = user_data.get("generated_questions", [])
    language = user_data.get("language", "en")

    if not questions:
        return "No questions were generated. Please restart the process and ensure the job role is provided."

    if question_no > len(questions):
        return render_template("report.html", analyses=user_data["analyses"])

    current_question = questions[question_no - 1]

    # Speak the current question in the selected language
    speak_text(current_question, language, f"question{question_no}.mp3")

    if request.method == "POST":
        # Capture the user's spoken answer
        user_input = listen_to_voice()  # Get the voice input from user in selected language

        # If the user didn't speak an answer, we can get it from the form (fallback)
        if not user_input:
            user_input = request.form.get("user_answer", "").strip()

        # Analyze the correctness of the answer (not based on actual content, just correctness)
        feedback = generate_dynamic_feedback(current_question, user_input)

        # Save the answer and feedback
        user_data["answers"].append(user_input)
        user_data["analyses"].append(feedback)

        with open("user_data.txt", "a", encoding="utf-8") as file:
            file.write(f"Question {question_no}: {current_question}\nAnswer: {user_input}\nFeedback: {feedback}\n\n")

        # Speak the feedback in the selected language
        # speak_text(feedback, language, f"feedback{question_no}.mp3")

        # Proceed to the next question automatically after feedback
        if question_no < len(questions):
            return redirect(url_for("questions", question_no=question_no + 1))
        else:
            return redirect(url_for("download_report"))

    return render_template("questions.html", question_no=question_no, question=current_question, language=language)

@app.route("/download_report", methods=["GET"])
def download_report():
    # Generate a summary of answer analysis
    summary = generate_summary(user_data["analyses"])

    # Generate the analysis report based on parameters
    analysis_report = {
        "technical_proficiency": generate_parameter_analysis(user_data, "technical proficiency", 8),  # Example rating of 8
        "communication": generate_parameter_analysis(user_data, "communication", 7),  # Example rating of 7
        "decision_making": generate_parameter_analysis(user_data, "decision making", 6),  # Example rating of 6
        "confidence": generate_parameter_analysis(user_data, "confidence", 9),  # Example rating of 9
        "areas_to_improve": generate_parameter_analysis(user_data, "areas to improve", 5),  # Example rating of 5
    }

    return render_template("report.html", summary=summary, analysis_report=analysis_report)


@app.route("/download", methods=["GET"])
def download_reports():
    filepath = "user_data.txt"
    return send_file(filepath, as_attachment=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=12345)