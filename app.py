from flask import Flask, jsonify, render_template ,request ,redirect ,url_for ,send_file
# from dotenv import load_dotenv
from pymongo import MongoClient
import os
from datetime import datetime
import requests
import re
import time
import json
app = Flask(__name__)
# load_dotenv()
CHANGE_STREAM_DB = "mongodb+srv://dineshraut121998:NTAl4PbusozWrS2M@mydatabase.gpeeo.mongodb.net/?retryWrites=true&w=majority&appName=myDatabase"

client = MongoClient(CHANGE_STREAM_DB)
db = client.mentza
# Global user data storage
user_data = {"intro": "", "answers": [], "analyses": [], "generated_questions": [], "language": "en"}
###################################### define functions ###############################################
#################################################  process streaming   #################################################
def process_streaming_response(response):
        """
        Process streaming response from Ollama API
        """
        full_response = ""
        for line in response.iter_lines():
            if line:
                json_response = json.loads(line)
                if 'message' in json_response:
                    content = json_response['message'].get('content', '')
                    full_response += content
        return full_response
################################################ question generator #################################################
def extract_questions(text):
    return re.findall(r'\d+\.\s(.*?)(?=\n\d+\.|\Z)', text)

# # function to get question 
# def questions_generator(userid,job_role, language, no_of_questions=5):
#     url = "http://139.59.42.156:11434/api/chat"
#     no_of_questions = no_of_questions
#     job_role = job_role
#     language = language
#     prompt = f"generate {no_of_questions} question where job role is {job_role} (response in {language} and only include the questions in list , with no extra information)"
#     payload = {
#         "model": "llama3:latest",
#         "messages": [{"role": "user", "content": prompt}]
#     }
#     if db.interview_questions.find_one({"job_role":job_role}) is not None:
#         questions_list = db.interview_questions.find_one({"job_role":job_role})["response"]
#         return questions_list
#     else:
#         response = requests.post(url, json=payload, stream=True)
#         questions = process_streaming_response(response)
#         questions_list = extract_questions(questions)
#         document = {
#                 "prompt": prompt,
#                 "user_id": userid,
#                 "response": questions_list,
#                 "job_role": job_role,
#                 "language": language,
#                 "timestamp": datetime.utcnow()
#             }
#         id=db.interview_questions.insert_one(document)
#     return questions_list
def questions_generator(userid,job_role, language, count=5):
    url = "http://139.59.42.156:11434/api/generate"  # API URL
    headers = {"Content-Type": "application/json"}

    # Define language prompts
    language_prompt = {
        "en": f"Generate {count} interview questions for a {job_role} in JSON format. "
              f"Return a JSON array of objects, each containing only a 'question' key.",
        "mr": f"{job_role} साठी {count} मुलाखतीचे प्रश्न JSON स्वरूपात तयार करा. "
              f"फक्त 'question' असलेली JSON यादी परत करा.",
        "hi": f"{job_role} के लिए {count} साक्षात्कार प्रश्न JSON प्रारूप में तैयार करें। "
              f"केवल 'question' कुंजी वाली एक JSON सूची लौटाएं।"
    }

    prompt = language_prompt.get(language, language_prompt["en"])  # Default to English if not found

    data = {
        "model": "gemma:2b",
        "prompt": prompt,
        "stream": False
    }
    if db.interview_questions.find_one({"job_role":job_role}) is not None:
        questions_list = db.interview_questions.find_one({"job_role":job_role})["response"]
        return questions_list
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            response_data = response.json()

            # Extract response text
            response_text = response_data.get("response", "").strip()
            # print(response_text)
            text= response_text.replace("```json","").replace("```","").replace(",",".").replace("{","").replace("}",",").replace("\"question\"","").replace(":","").replace("\n","").split(",")
            # print(text)
            document = {
                            "prompt": prompt,
                            "response": text,
                            "job_role": job_role,
                            "language": language,
                            "timestamp": datetime.utcnow()
                    }
            db.interview_questions.insert_one(document)
            return text
            
        except Exception as e:
            print("Error processing API response:", e)
            return []
    else:
        print("API call failed:", response.status_code, response.text)
        return []

################################################ question generator #################################################

# print(questions_generator("1", "Software Engineer", "English", 5))


################################################ evaluate answer #################################################

# # function to evaluate the answer 
def evaluate_answer(userid ,question, answer):
    if db.interview_progress.find_one({"user_id":userid}) is not None:
        try:
            latest = db.interview_progress.find_one({ "user_id": userid }, sort=[("timestamp", -1)])
            if latest is not None:
                response = latest["progress"]  # Get the existing progress list
                response.append({"question": question, "answer": answer})  # Append new entry
                db.interview_progress.update_one(
                    {"user_id": userid},
                    {"$set": {"progress": response}}
                )
                return {"message": "success"}
        except Exception as e:
            print(e)
            return {"message": "error".format(e)}
    
    else:
        try :
            db.interview_progress.insert_one({"user_id":userid,"progress":[{"question":question,"answer":answer}],"timestamp":datetime.utcnow()})
            return {"message": "success"}
        except Exception as e:
            print(e)
            return {"message": "error".format(e)}

################################################ evaluate answer #################################################

# print(evaluate_answer("2","Can you describe a challenging software development project you've worked on and how you overcame the obstacles you faced?","I worked on developing a mock interview app using AI, where the main challenges were ensuring the AI could generate role-specific questions and accurately assess user responses. Overcoming these obstacles involved leveraging OpenAI's language models for question generation and response validation, along with thorough testing to fine-tune the scoring and feedback mechanisms. Collaboration with my team and iterative refinement ensured a successful outcome."))


################################################  report generation  #################################################

def get_report(userid):
    url = "http://139.59.42.156:11434/api/chat"
    
    # get session data from mongodb
    if db.interview_progress.find_one({"user_id":userid}) is not None:
        latest = db.interview_progress.find_one({ "user_id": userid }, sort=[("timestamp", -1)])
        if latest is not None:
            session_data = latest["progress"]  # Get the existing progress list
            # print(session_data)
            if session_data is not None:
                print("session data fetched successfully")
            data=db.parameters.find_one({"job_role":"IT Sector"})
            # print(data["parameters"])
            if data is not None:
                print("parameters fetched successfully")
            parameters=data["parameters"]
            # send session data to ollama api with prompt
            prompt = f"Generate a performance report for a mock interview based on the following session data:\n\n{session_data}\n\nInclude strengths, areas for improvement, and tips to enhance performance. And also give some YouTube suggestions related to weakness (JSON response {parameters},youtubelinks,some other source links )"
            payload = {
                    "model": "llama3:latest",
                    "messages": [{"role": "user", "content": prompt}]
                }
            start_time = time.time()
            response = requests.post(url, json=payload, stream=True)
            report = process_streaming_response(response)
            end_time = time.time()
            print(f"Time taken to generate report: {end_time - start_time} seconds")
            # print(report)
            
            # store in mongodb
            document = {
                "user_id": userid,
                "report": report,
                "timestamp": datetime.utcnow()
            }
            db.reports.insert_one(document)
            # delete data when the interview is complete
            # db.interview_progress.delete_one({"user_id": userid})
            return report
        else:
            return "No data found"
        
    else:
        return "No data found"

################################################  report generation  #################################################

# print(get_report("1"))

###################################### define functions ###############################################

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
        # print(username , password)
        # print(credintails)
        if not username or not password:
            return render_template('login.html'), 400
        elif None != credintails and username == credintails.get('username') and password == credintails.get('password'): # check with database
            return render_template('home.html',username=username,name=credintails.get('name'))
        else : 
            return render_template('login.html'), 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST']) # signup route
def signup():
    if request.method == 'POST':
        #get the credintials from the user
        username= request.form.get('username') # should be email
        password= request.form.get('password') 
        email= request.form.get('email')
        name= request.form.get('name')

        # print(username , password , email ) #, university, dob, degree, stream
        if not username or not password or not email: # or university or dob or degree or stream
            return render_template('signup.html'), 400
        elif db.users.find_one({'email': email}) or db.users.find_one({'username': username}): # already exist
            return render_template('signup.html'), 402
        else: 
            # store in database 
            data = {
                "username": username,
                "password": password,
                "email": email,
                "name": name,
                "timestamp": datetime.utcnow()
            }
            # print(data)
            # mongodb
            response = db.users.insert_one(data)
            if response.inserted_id:
                return render_template('login.html')
            else:
                return jsonify({'error': 'Signup failed'}), 403
    return render_template('signup.html')


@app.route('/profile', methods=['GET','POST']) # get profile from database
def profile():
    if request.method == 'GET':
        return render_template('profile.html')
    username = request.json.get('username') # get id of user  
    user_profile= db.users.find_one({"username": username}) # find user profile by user id 
    # print(user_profile)
    return jsonify({"username": user_profile.get('username'), "name": user_profile.get('name'), "email": user_profile.get('email')}), 200

@app.route("/role",methods=["POST"])
def role():
    return render_template("job_role.html")

@app.route("/job-role", methods=["POST"])
def job_role():
    try:
        if request.method == "POST":
            job_role = request.form.get("job_role", "").strip()
            language = request.form.get("language", "en").strip()  # Get language selection from form
            userid = request.form.get("username", "").strip()
            questions = questions_generator(userid,job_role, language, count=5)
            if questions:
                user_data["job_role"] = job_role
                user_data["language"] = language
                user_data["username"] = userid
                user_data["generated_questions"] = questions
                return redirect(url_for("questions"))
    except Exception as e:
        return render_template("job_role.html")
    

@app.route("/questions", methods=["GET","POST"])
def questions():
    if request.method == "GET":
        # print(user_data)
        question= user_data["generated_questions"].pop(0)
        return render_template("questions.html",username=user_data["username"], job_role=user_data["job_role"], language=user_data["language"], questions=question)
    elif request.method == "POST":
        data = request.get_json()
        userid= data["user_id"]
        user_response= data["user_response"]
        question= data["question"]
        evaluate_answer(userid ,question, user_response)
        if user_data["generated_questions"] and len(user_data["generated_questions"]) > 0:
            question= user_data["generated_questions"].pop(0)
            return jsonify({"question": question}), 200
        else:
            return jsonify({"question": "interview completed please click on end button to get report"}), 200
        
@app.route("/fetch-reports", methods=["POST"])
def fetch_reports():
    userid = request.form.get("username", "").strip()
    report = db.reports.find({"user_id": userid})
    if report is None:
        report = []
    return render_template("s.html",username=userid, report=report)
@app.route("/report", methods=["GET","POST"])
def report():
    if request.method == "GET":
        return render_template("report.html")
    elif request.method == "POST":
        userid = request.form.get("username", "").strip()
        try:
                report = get_report(userid)
        except:
                report ="Sorry for inconvenience, your report is not generated try it may seems like you have not answere questions properly !!"
        return render_template("report.html",username=user_data["username"], report=report)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
