import os
import requests
import json
import openai
from gtts import gTTS
import pygame
import speech_recognition as sr
from pymongo import MongoClient
import re , random


# Path for generated audio files
AUDIO_PATH = os.path.abspath("static/audio")
if not os.path.exists(AUDIO_PATH):
    os.makedirs(AUDIO_PATH, exist_ok=True)

def generate_userid ():
    userid = random.randint(10**9, 10**10 - 1)
    # if db.users.find_one({"userid": userid}) is not None:
    #     return generate_userid()
    # else:
    #     return userid
    return userid

def speak_text(text, language, filename):
    try:
        # Ensure language is set properly for TTS
        tts = gTTS(text=text, lang=language)
        filepath = os.path.join(AUDIO_PATH, filename)
        tts.save(filepath)
        play_audio(filepath)
        return filepath
    except Exception as e:
        print(f"Error speaking text: {e}")
        return None


def play_audio(filepath):
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
    except Exception as e:
        print(f"Error playing audio: {e}")


def generate_interview_questions(job_role, language, count=7):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai.api_key}", "Content-Type": "application/json"}

    # Define the prompt based on the language
    language_prompt = {
        "en": f"Generate a list of {count} interview questions for a job role as a {{job_role}} in JSON format. Only include the questions, with no extra information.",
        "mr": f"{job_role} च्या नोकरीसाठी {count} मुलाखतीचे प्रश्न JSON स्वरूपात तयार करा. फक्त प्रश्न समाविष्ट करा, इतर कोणतीही माहिती नसावी.",
        "hi": f"{job_role} की नौकरी के लिए {count} साक्षात्कार प्रश्न JSON प्रारूप में तैयार करें। केवल प्रश्न शामिल करें, कोई अतिरिक्त जानकारी नहीं।"
    }

    if language not in language_prompt:
        print(f"Unsupported language '{language}', defaulting to English.")
        language = "en"

    prompt = language_prompt[language].format(job_role=job_role)

    # Define the request payload
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert interviewer. Respond strictly in JSON format."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    # Send the request to the OpenAI API
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        try:
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]

            # Remove the code block markers if present
            if content.startswith("```json"):
                content = content.strip("```json").strip("```").strip()

            # Parse the cleaned content as JSON
            questions = json.loads(content)
            print("API Response:", questions)

            if isinstance(questions, dict) and "interview_questions" in questions:
                return questions["interview_questions"]
            else:
                print("Unexpected format: Questions not in expected JSON structure.")
                return []
        except json.JSONDecodeError:
            print("Failed to decode JSON from API response. Cleaned content:", content)
            return []
        except Exception as e:
            print("Error processing API response:", e)
            return []
    else:
        print("API call failed:", response.status_code, response.text)
        return []



# Function to analyze response using OpenAI API
def analyze_response(question, answer):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai.api_key}", "Content-Type": "application/json"}

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": f"Question: {question}\nAnswer: {answer}\nAnalyze the answer and suggest improvements in Marathi."}],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"


def listen_to_voice(language="en"):
    recognizer = sr.Recognizer()

    # Language mapping for speech recognition
    language_codes = {
        "en": "en-US",    # English (US)
        "mr": "mr-IN",    # Marathi
        "hi": "hi-IN"     # Hindi
    }

    # Default to English if the language is not in the list
    speech_language = language_codes.get(language, "en-US")

    with sr.Microphone() as source:
        try:
            print(f"Listening for input in {speech_language}...")
            audio = recognizer.listen(source, timeout=20, phrase_time_limit=10)  # Increased timeout
            response_text = recognizer.recognize_google(audio, language=speech_language)
            return response_text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Error with the request: {e}")
            return None
        except sr.WaitTimeoutError:
            print("Timeout: No speech detected")
            return None


def analyze_correctness_of_answer(question, user_answer):
    # Simple logic for determining feedback based on general answer correctness
    # For now, we'll just check if the user mentioned a key concept in a general way

    # Example check for Python features
    if "easy to learn" in user_answer and "libraries" in user_answer:
        return "That’s a great response! Let’s move forward."
    else:
        return "Good try, but you could dive deeper into this topic. Let’s continue."


def generate_dynamic_feedback(question, answer):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai.api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Question: {question}
    Answer: {answer}
    Provide feedback based on the answer:
    - If the answer is correct, give positive feedback such as: "Great job!" or "Excellent response!"
    - If the answer is incorrect, provide encouraging feedback such as: "You’re close, but here’s an area to improve." or "Don’t worry, let’s move on."
    Do not ask questions in the feedback. Only provide the feedback as a statement.
    """

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": "You are an expert interviewer."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    else:
        print(f"Error generating feedback: {response.status_code}, {response.text}")
        return "I couldn't process your answer. Please try again."

def is_followup_query(user_input):
    query_keywords = ["what", "why", "how", "explain", "can you", "tell me", "meaning", "define"]
    return any(keyword in user_input.lower() for keyword in query_keywords)




def generate_summary(analyses):
    # Generate a brief summary based on analyses
    correct_answers = sum(1 for feedback in analyses if "great" in feedback.lower())
    improvement_needed = len(analyses) - correct_answers

    summary = (
        f"You answered {correct_answers} questions well. "
        f"You can improve in {improvement_needed} areas. "
        "Continue practicing to refine your skills!"
    )
    return summary


def generate_parameter_analysis(user_data, parameter, rating):
    # This function generates a report and rating based on the user's answers for a specific parameter
    analysis = ""
    if parameter == "technical proficiency":
        analysis = "You demonstrated solid technical knowledge in the questions. However, deeper understanding could enhance your expertise."
    elif parameter == "communication":
        analysis = "Your communication was clear, but more concise answers would make your responses stronger."
    elif parameter == "decision making":
        analysis = "Your decision-making skills were good, though refining them in complex scenarios will help."
    elif parameter == "confidence":
        analysis = "You displayed good confidence throughout the session, though there is room to project more confidence in difficult situations."
    elif parameter == "areas to improve":
        analysis = "You can work on improving your technical depth and communication precision."

    return {"report": analysis, "rating": rating}
