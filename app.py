from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import datetime
import random
from dotenv import load_dotenv
from functools import wraps
import time
import re

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

def rate_limit(limit_seconds=5):
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
    paragraphs = text.split("\n")
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if re.match(r"^\d+\.", para):
            para = "\n" + para
        elif para.startswith(("•", "-")):
            para = "\n• " + para[1:].strip()
            
        if ": " in para and "http" not in para:
            parts = para.split(": ")
            para = f"{parts[0]}: \n{: .join(parts[1:])}"
            
        formatted_paragraphs.append(para)
    
    return "\n\n".join(formatted_paragraphs)

def is_beginner_plant_query(question):
    beginner_keywords = [
        "beginner", "first time", "easy", "low maintenance",
        "starter", "simple", "newbie", "new to plants",
        "starting out", "best for beginners"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in beginner_keywords)

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
        "\n\nFollow us on Instagram <a href='https://www.instagram.com/stemmaplants' target='_blank'>@stemmaplants</a> for plant care tips and new arrivals! 🌿",
        "\n\nCheck out our <a href='https://www.facebook.com/people/Stemma-Plant-Co/61569391287243/' target='_blank'>Facebook page</a> for updates and plant care tips! 🪴",
        "\n\nStay connected! Find us on <a href='https://www.instagram.com/stemmaplants' target='_blank'>Instagram @stemmaplants</a> and <a href='https://www.facebook.com/people/Stemma-Plant-Co/61569391287243/' target='_blank'>Facebook</a> for daily plant inspiration! 🌱"
    ]
    return random.choice(prompts)

@app.route("/ask_stemmy", methods=["POST"])
@rate_limit(5)
def ask_stemmy():
    user_input = request.json.get("question", "").strip()
    
    if not user_input:
        return jsonify({"error": "Please ask a question! 🌱"}), 400
    
    if not is_plant_related(user_input):
        return jsonify({
            "response": "I'm a plant specialist, so I can only help with questions about plants, gardening, and plant care! 🌱 Feel free to ask me anything about those topics!"
        })
    
    try:
        is_beginner_query = is_beginner_plant_query(user_input)
        
        system_prompt = """You are Stemmy 🌱, the specialist chatbot for Stemma Plant Co. Core information:

1. Our Current Plant Selection:
- Hoyas: Green, Compacta, Variegated varieties
- Pothos: Marble Queen, Golden, Emerald varieties
- Philodendrons: Brasil, Sun Red
- Other: Boston Fern, Polka Dot Plant (Hypoestes), Peperomia Cupid, Scindapsus Silver Ann

2. Plant Categories:
- Hanging Plants: Pothos Marble Queen HB, Pothos Golden HB
- Easy Care: Pothos varieties, Philodendron Brasil
- Statement Plants: Hoya varieties, Boston Fern
- Unique Finds: Scindapsus Silver Ann, Peperomia Cupid

3. Response Style:
- Keep responses concise and friendly
- Use plant-relevant emojis
- Format lists clearly
- Include direct links to our website
- Maximum 150 words

4. Key Guidelines:
- Only recommend plants from our current inventory
- Direct customers to https://www.stemmaplants.com/plants to browse selection
- Highlight our specialties: Hoyas, Pothos, and Philodendrons
- For specific plant questions, give care tips and link to our shop

Example beginner response:
"For new plant parents, I'd recommend our Pothos varieties - they're beautiful and adaptable! We have stunning Marble Queen and Golden Pothos in hanging baskets, perfect for beginners. The Philodendron Brasil is also an excellent choice. Browse our selection at stemmaplants.com/plants 🪴"

Example general response:
"We have a lovely selection of indoor plants! Our Hoyas are particularly special, and we carry several varieties. Check out our current collection at stemmaplants.com/plants 🌿"

When discussing prices: Direct customers to the website for current pricing."""

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
        formatted_answer = format_response(answer)
        
        if random.random() < 0.3:
            formatted_answer += get_random_social_prompt()
        
        return jsonify({"response": formatted_answer})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "response": "Having trouble connecting right now! Try reaching out on <a href='https://www.instagram.com/stemmaplants' target='_blank'>Instagram @stemmaplants</a> or visit our <a href='https://www.stemmaplants.com/contact-us' target='_blank'>contact page</a>! 🌿"
        }), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
