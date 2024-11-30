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
                        "error": "Hold your watering can! 🪴 Give me a moment to catch my breath! (But feel free to check out our Instagram @stemmaplants while you wait!)"
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
            para = parts[0] + ":\n" + parts[1]
            
        formatted_paragraphs.append(para)
    
    return "\n\n".join(formatted_paragraphs)

def is_beginner_plant_query(question):
    beginner_keywords = [
        "beginner", "first time", "easy", "low maintenance",
        "starter", "simple", "newbie", "new to plants",
        "starting out", "best for beginners", "hard to kill"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in beginner_keywords)

def is_plant_related(question):
    # Add context keywords for follow-up questions
    context_keywords = [
        "it", "that", "this", "those", "one", "them", "they",
        "which", "why", "how", "what", "where", "when",
        "tell me more", "explain", "really", "but", "and"
    ]
    
    plant_keywords = [
        "plant", "garden", "soil", "water", "leaf", "grow", "light",
        "fertilizer", "pot", "prune", "stem", "root", "flower", "seed",
        "indoor plant", "outdoor plant", "houseplant", "care", "maintenance",
        "propagate", "cutting", "pest", "disease", "sunlight", "humidity",
        "buy", "purchase", "price", "cost", "shipping", "delivery"
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in plant_keywords + context_keywords)

def get_random_social_prompt():
    prompts = [
        "\n\nPsst! Follow our plant adventures on Instagram <a href='https://www.instagram.com/stemmaplants' target='_blank'>@stemmaplants</a> for behind-the-scenes plant care tips and new green friends! 🌿",
        "\n\nJoin our plant-loving community on <a href='https://www.facebook.com/people/Stemma-Plant-Co/61569391287243/' target='_blank'>Facebook</a> - where we share our favorite plant tips and sometimes catch our plants photosynthesizing! 🪴",
        "\n\nWant more plant happiness? Find us on <a href='https://www.instagram.com/stemmaplants' target='_blank'>Instagram @stemmaplants</a> and <a href='https://www.facebook.com/people/Stemma-Plant-Co/61569391287243/' target='_blank'>Facebook</a> for daily doses of green inspiration! 🌱"
    ]
    return random.choice(prompts)

@app.route("/ask_stemmy", methods=["POST"])
@rate_limit(5)
def ask_stemmy():
    user_input = request.json.get("question", "").strip()
    
    if not user_input:
        return jsonify({"error": "Hey plant friend! Mind sharing your plant question with me? 🌱"}), 400
    
    if not is_plant_related(user_input):
        return jsonify({
            "response": "While I'd love to chat about everything under the sun, I'm your friendly neighborhood plant expert! 🌿 How about we talk about your green friends instead?"
        })
    
    try:
        is_beginner_query = is_beginner_plant_query(user_input)
        
        system_prompt = """You are Stemmy 🌱, the fun and knowledgeable plant chatbot for Stemma Plant Co. Your personality:

1. Communication Style:
- Friendly, casual, and occasionally playful
- Share fun plant facts and personal observations
- Use plant puns when natural (but don't overdo it!)
- Add personality to your plant care tips
- Talk about plants like they're friends (because they are!)

2. Our Current Selection:
- Hoyas: Green, Compacta, and Variegated varieties (I call them the "supermodels" of our collection!)
- Pothos: Marble Queen, Golden, Emerald varieties (the most easy-going plants you'll ever meet)
- Philodendrons: Brasil and Sun Red (basically the social butterflies of the plant world)
- Unique finds: Boston Fern, Polka Dot Plant (Hypoestes), Peperomia Cupid, Scindapsus Silver Ann

3. Plant Personality Guide:
- Pothos: Perfect for beginners, these plants are like that friend who's always chill and goes with the flow
- Philodendrons: Social climbers that love to show off their beautiful leaves
- Hoyas: The sophisticated ones that reward patience with stunning blooms
- Boston Fern: The drama queen that needs consistent attention but is worth it
- Scindapsus Silver Ann: Our mysterious beauty with silvery patterns

4. Response Style:
- Share personal-style observations about plants
- Include fun facts or unexpected tips
- Give plants personality traits when describing them
- Format with clear paragraphs and spacing
- Keep it under 150 words but pack in the charm

5. Important Links:
- Shop: https://www.stemmaplants.com/plants
- Instagram: @stemmaplants
- Facebook: Stemma Plant Co.

Example responses:
"Oh, you're going to love our Marble Queen Pothos! She's like the cool friend who makes any room look better. I especially love how her leaves shimmer in morning light - it's like nature's disco ball! 🪩"

"The Philodendron Brasil is perfect for your space! Fun fact: its split-colored leaves are like natural art pieces, and between you and me, it's one of the most forgiving plants I know - perfect for those of us who sometimes forget it's watering day! 🌿"

Always maintain the fun personality while being helpful and informative. When in doubt, add a dash of plant humor!"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.8
        )
        
        answer = response.choices[0]["message"]["content"]
        formatted_answer = format_response(answer)
        
        if random.random() < 0.3:
            formatted_answer += get_random_social_prompt()
        
        return jsonify({"response": formatted_answer})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "response": "Oops! Looks like I'm having a moment (even plants get those!) 🌱 Why not check out our latest plant pics on <a href='https://www.instagram.com/stemmaplants' target='_blank'>Instagram @stemmaplants</a> or swing by our <a href='https://www.stemmaplants.com/contact-us' target='_blank'>contact page</a>? Be back in a jiffy! 🪴"
        }), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
