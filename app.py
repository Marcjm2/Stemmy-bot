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

def format_response(text):
    # Split into paragraphs
    paragraphs = text.split("\n")
    formatted_paragraphs = []
    
    for para in paragraphs:
        # Add spacing for lists
        if para.strip().startswith(("1.", "2.", "3.", "4.", "•", "-")):
            para = "\n" + para
        # Add line break after colons that aren't part of URLs
        if ":" in para and "http" not in para:
            parts = para.split(":")
            para = parts[0] + ":\n" + ":".join(parts[1:])
        formatted_paragraphs.append(para.strip())
    
    # Join with proper spacing
    return "\n\n".join(p for p in formatted_paragraphs if p)

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

def get_random_social_prompt():
    prompts = [
        "\n\nP.S. Follow us on Instagram @stemmaplants for plant care tips and new arrivals! 🌿",
        "\n\nCheck out our Facebook page for updates and plant care tips: facebook.com/people/Stemma-Plant-Co/61569391287243/ 🪴",
        "\n\nStay connected! Find us on Instagram @stemmaplants and Facebook for daily plant inspiration! 🌱",
        "\n\nWant to see more plants? Follow our journey on Instagram @stemmaplants! 🪴"
    ]
    return random.choice(prompts)

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
        system_prompt = """You are Stemmy 🌱, the specialist chatbot for Stemma Plant Co. You help customers with plant care and shopping at our store. Important details:

1. Our Website:
- All our available plants are at https://www.stemmaplants.com/plants
- Direct customers here for current inventory
- Mention they can browse our selection online

2. Response Guidelines:
- Format lists with clear numbering and line breaks
- Keep paragraphs short and easy to read
- Use plant-specific emojis
- Include care details when discussing plants
- Maximum 150 words per response

3. When answering questions:
- Always mention our website for purchases
- Suggest checking our current inventory online
- Be enthusiastic about plants
- Format plant names in a clear way
- Include basic care tips when relevant

Example format for recommendations:
"Here are some great options:

1. Snake Plant 🪴: Easy care, low light
2. Pothos 🌿: Perfect for beginners
3. ZZ Plant 🌱: Very low maintenance

You can find all these and more at stemmaplants.com/plants!"

If asked about buying: Always direct to https://www.stemmaplants.com/plants for current inventory."""

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
        
        # Format response and randomly add social media prompt
        formatted_answer = format_response(answer)
        if random.random() < 0.3:  # 30% chance to add social media prompt
            formatted_answer += get_random_social_prompt()
        
        return jsonify({"response": formatted_answer})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "🌱 Oops! Something went wrong. Please try again!"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
