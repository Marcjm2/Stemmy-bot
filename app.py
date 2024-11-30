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

def clean_url(text):
    # Find URLs and ensure they don't have trailing punctuation
    url_pattern = r'\b(https?://[^\s]+[^\s.,!?])'
    cleaned_text = re.sub(url_pattern, r'\1', text)
    return cleaned_text

def format_response(text):
    # Clean URLs first
    text = clean_url(text)
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
            para = parts[0] + ":\n" + parts[1]
            
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
    # Add context keywords for follow-up questions
    context_keywords = [
        "it", "that", "this", "those", "one", "them", "they",
        "which", "why", "how", "what", "where", "when"
    ]
    
    plant_keywords = [
        "plant", "garden", "soil", "water", "leaf", "grow", "light",
        "fertilizer", "pot", "prune", "stem", "root", "flower", "seed",
        "indoor plant", "outdoor plant", "houseplant", "care", "maintenance",
        "propagate", "cutting", "pest", "disease", "sunlight", "humidity",
        "buy", "purchase", "price", "cost", "shipping", "delivery"
    ]
    
    question_lower = question.lower()
    # Consider both plant-specific keywords and context words for follow-ups
    return any(keyword in question_lower for keyword in plant_keywords + context_keywords)

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
            "response": "I'm your dedicated plant specialist, focusing exclusively on plant care and gardening! While that sounds fun, I can only help with plant-related questions. How about we talk about getting you a new leafy friend instead? 🌱"
        })
    
    try:
        is_beginner_query = is_beginner_plant_query(user_input)
        
        system_prompt = """You are Stemmy 🌱, the friendly but PLANT-FOCUSED chatbot for Stemma Plant Co. Core guidelines:

1. STRICT POLICY: Only discuss plants, plant care, and our inventory. Never provide advice about non-plant topics, even in a friendly way.

2. Our Current Plant Selection:
- Hoyas: Green, Compacta, Variegated varieties
- Pothos: Marble Queen, Golden, Emerald varieties
- Philodendrons: Brasil, Sun Red
- Other: Boston Fern, Polka Dot Plant (Hypoestes), Peperomia Cupid, Scindapsus Silver Ann

3. Communication Style:
- Be friendly but stay on topic (plants only!)
- Format responses with clear paragraphs
- Include our website link without trailing punctuation
- Keep responses under 150 words

4. URLs to Use:
- Store: https://www.stemmaplants.com/plants
- Instagram: https://www.instagram.com/stemmaplants
- Facebook: https://www.facebook.com/people/Stemma-Plant-Co/61569391287243

5. Key Points:
- Only recommend plants we currently stock
- Direct all purchase inquiries to our website
- Share plant care tips and features
- Use emojis relevant to plants

Remember: If a question is not about plants, firmly but politely redirect to plant topics. No exceptions, even for simple non-plant questions."""

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
