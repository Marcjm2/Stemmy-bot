from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import datetime
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Fetch API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("⚠️ OPENAI_API_KEY is not set. Please set it in your environment.")

def generate_dynamic_personality():
    personalities = [
        "You are Stemmy 🌱, a cheerful plant enthusiast who loves helping people grow happy, healthy plants.",
        "You are Stemmy 🌱, a witty and playful plant assistant who occasionally adds fun plant facts to your responses.",
        "You are Stemmy 🌱, a calm and wise plant expert who explains things in a relaxing and reassuring way.",
        "You are Stemmy 🌱, an energetic plant coach who motivates users to take great care of their plants."
    ]
    return random.choice(personalities)

def greet_user():
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        return "Good morning! ☀️ Let's talk about plants!"
    elif current_hour < 18:
        return "Good afternoon! 🌼 What plant questions can I help with?"
    else:
        return "Good evening! 🌙 Ready to chat about your leafy friends!"

@app.route("/ask_stemmy", methods=["POST"])
def ask_stemmy():
    print("Request received at /ask_stemmy")
    user_input = request.json.get("question")
    if not user_input:
        print("No question provided.")
        return jsonify({"error": "No question provided. Please include a 'question' key in the JSON payload."}), 400
    
    print(f"User question: {user_input}")
    
    try:
        dynamic_personality = generate_dynamic_personality()
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": dynamic_personality},
                {"role": "user", "content": user_input}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        answer = response.choices[0]['message']['content']
        print(f"Stemmy response: {answer}")
        
        return jsonify({"response": answer})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"🌱 An unexpected error occurred: {str(e)}"}), 500

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Flask is working!"})

if __name__ == "__main__":
    print(greet_user())
    print("Hi, I'm Stemmy 🌱! How can I help you today?")
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
