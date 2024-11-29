from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import datetime
import random
from dotenv import load_dotenv
from functools import wraps
import time

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

def rate_limit(limit_seconds=30):
    request_history = {}
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            requester_id = request.remote_addr
            current_time = time.time()
            
            if requester_id in request_history:
                last_request_time = request_history[requester_id]
                if current_time - last_request_time < limit_seconds:
                    return jsonify({
                        "error": "Please wait a moment before asking another question! 🌱",
                        "retry_after": int(limit_seconds - (current_time - last_request_time))
                    }), 429
            
            request_history[requester_id] = current_time
            return f(*args, **kwargs)
        return wrapped
    return decorator

def is_plant_related(question):
    plant_keywords = [
        "plant", "garden", "soil", "water", "leaf", "grow", "light",
        "fertilizer", "pot", "prune", "stem", "root", "flower", "seed",
        "indoor plant", "outdoor plant", "houseplant", "care", "maintenance",
        "propagate", "cutting", "pest", "disease", "sunlight", "humidity",
        "buy", "purchase", "price", "cost", "shipping", "delivery"
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in plant_keywords)

@app.route("/ask_stemmy", methods=["POST"])
@rate_limit(30)
def ask_stemmy():
    user_input = request.json.get("question", "").strip()
    
    if not user_input:
        return jsonify({"error": "Please ask a question! 🌱"}), 400
    
    if not is_plant_related(user_input):
        return jsonify({
            "response": "I'm a plant specialist, so I can only help with questions about plants, gardening, and plant care! 🌱 Feel free to ask me anything about those topics!"
        })
    
    try:
        system_prompt = """You are Stemmy 🌱, the specialist chatbot for Stemma Plant Co. You ONLY help customers with:
        - Plant care and maintenance advice
        - Plant selection recommendations
        - General gardening guidance
        
        Key guidelines:
        - ONLY answer questions about plants and plant care
        - If someone asks about buying plants, direct them to browse our selection at stemmaplants.com
        - For specific plants, you can mention they're available on our website and guide them to check the site
        - Keep responses friendly and organized with bullet points where appropriate
        - Add relevant plant emojis for engagement
        - Keep responses under 150 words
        - Format lists and key points with line breaks
        - If asked about non-plant topics, politely redirect to plant-related discussions
        
        Example redirect: "As a plant specialist, I focus on helping with plant-related questions! 🌱 Is there anything about plants or gardening you'd like to know?"
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        answer = response.choices[0]["message"]["content"]
        
        # Format response with proper spacing
        formatted_answer = answer.replace("•", "\n•").replace(":", ":\n")
        
        return jsonify({"response": formatted_answer})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "🌱 Oops! Something went wrong. Please try again!"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
