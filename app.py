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

# Add plant data
plants = [
    {
        'name': 'Hoya Green',
        'price': 34.00,
        'size': '6-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Allow soil to dry between waterings',
        'description': 'A hardy and low-maintenance plant with waxy green leaves',
        'care': 'Water when the top inch of soil feels dry. Avoid overwatering',
        'stock': 'In stock'
    },
    {
        'name': 'Hoya Compacta',
        'price': 34.00,
        'size': '6-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Let the soil dry out slightly between waterings',
        'description': 'Also known as Hindu Rope, this unique Hoya features twisted, curling leaves',
        'care': 'Keep in a warm, humid spot. Mist occasionally to maintain humidity',
        'stock': 'In stock'
    },
    {
        'name': 'Boston Fern HB',
        'price': 39.00,
        'size': '10-inch hanging basket (Plastic Hanger)',
        'light': 'Bright, indirect to medium light',
        'water': 'Keep soil consistently moist but not soggy',
        'description': 'A lush, classic fern perfect for adding greenery to any space',
        'care': 'Mist regularly to maintain humidity. Avoid direct sunlight',
        'stock': 'In stock'
    },
    {
        'name': 'Pothos Marble Queen HB',
        'price': 36.00,
        'size': '8-inch hanging basket',
        'light': 'Low to medium, indirect light',
        'water': 'Allow the top inch of soil to dry out between waterings',
        'description': 'A striking plant with creamy white and green variegated leaves',
        'care': 'Thrives in low-maintenance conditions. Wipe leaves to remove dust',
        'stock': 'In stock'
    },
    {
        'name': 'Hypoestes (Polka Dot Plant) 3 Plant Bundle',
        'price': 24.00,
        'size': '4-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Keep soil evenly moist, but avoid waterlogging',
        'description': 'A cheerful bundle of Polka Dot Plants with speckled leaves in various colors',
        'care': 'Pinch off growth to encourage bushiness. Prefers humid environments',
        'stock': 'In stock'
    },
    {
        'name': 'Hoya Green Variegated',
        'price': 34.00,
        'size': '6-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Let soil dry slightly between waterings',
        'description': 'A variegated version of the classic Hoya with creamy accents on its leaves',
        'care': 'Provide good drainage and avoid standing water. Mist for humidity',
        'stock': 'In stock'
    },
    {
        'name': 'Peperomia Cupid',
        'price': 22.00,
        'size': '6-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Allow soil to dry out between waterings',
        'description': 'A compact plant with heart-shaped leaves edged in cream',
        'care': 'Avoid overwatering. Ideal for desktops or small spaces',
        'stock': 'In stock'
    },
    {
        'name': 'Philodendron Brasil',
        'price': 22.00,
        'size': '6-inch pot',
        'light': 'Medium to bright, indirect light',
        'water': 'Allow soil to dry partially between waterings',
        'description': 'A vibrant plant with striking yellow and green variegated leaves',
        'care': 'Easy to care for and great for beginners. Trim as needed',
        'stock': 'In stock'
    },
    {
        'name': 'Philodendron Sun Red',
        'price': 25.00,
        'size': '6-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Water when the top inch of soil feels dry',
        'description': 'A unique philodendron with rich red tones and a pop of color',
        'care': 'Wipe leaves occasionally to keep them clean and glossy',
        'stock': 'In stock'
    },
    {
        'name': 'Pothos Emerald',
        'price': 20.00,
        'size': '6-inch pot',
        'light': 'Low to medium, indirect light',
        'water': 'Let the soil dry out slightly between waterings',
        'description': 'A hardy Pothos variety with deep green leaves',
        'care': 'Very low-maintenance. Perfect for beginners or low-light spaces',
        'stock': 'In stock'
    },
    {
        'name': 'Scindapsus Silver Ann',
        'price': 29.00,
        'size': '6-inch pot',
        'light': 'Bright, indirect light',
        'water': 'Allow the top inch of soil to dry between waterings',
        'description': 'A beautiful trailing plant with silvery, velvety leaves',
        'care': 'Provide good drainage and rotate periodically for even growth',
        'stock': 'In stock'
    },
    {
        'name': 'Pothos Golden HB',
        'price': 36.00,
        'size': '8-inch hanging basket',
        'light': 'Low to medium, indirect light',
        'water': 'Allow the top inch of soil to dry out between waterings',
        'description': 'A classic golden Pothos with striking yellow-green variegated leaves',
        'care': 'Thrives in a variety of conditions. Easy to propagate',
        'stock': 'In stock'
    }
]

# Store information formatting
STORE_INFO = """
🚚 Local Delivery: Available in Myrtle Beach and surrounding areas! Pop in your zip code at checkout to check if you're in our delivery zone
💚 Free delivery on orders over $75
📦 National Shipping: $10 flat ground shipping (Free over $75)
🎁 Looking for a gift? Grab a gift card at https://www.stemmaplants.com/plants/p/gift-card
📸 Instagram: https://www.instagram.com/stemmaplants
📞 Contact: https://www.stemmaplants.com/contact-us"""

def clean_url(text):
    """Enhanced URL cleaning to prevent trailing punctuation and format issues"""
    url_pattern = r'(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+(?:\/[^\s.,!?]*)?)'
    
    def replace_url(match):
        url = match.group(0)
        if not url.startswith('http'):
            url = 'https://' + url
        url = url.rstrip('.,!?')
        return url

    return re.sub(url_pattern, replace_url, text)

def get_plant_details(query):
    """Enhanced plant information retrieval with better price formatting"""
    query = query.lower()
    relevant_info = []
    matching_plants = []
    
    # First, try exact matches
    for plant in plants:
        if query in plant['name'].lower():
            matching_plants.append(plant)
    
    # If no exact matches, look for partial matches
    if not matching_plants:
        for plant in plants:
            if any(word in plant['name'].lower() for word in query.split()):
                matching_plants.append(plant)
    
    # Format the matches
    for plant in matching_plants:
        price_str = f"${plant['price']:.2f}"
        plant_info = f"🪴 {plant['name']}: {price_str} - {plant['description']} ({plant['size']})"
        relevant_info.append(plant_info)
        relevant_info.append(f"💚 Care: {plant['care']}")
        relevant_info.append(f"☀️ Light: {plant['light']}")
        relevant_info.append(f"💧 Water: {plant['water']}")
        relevant_info.append("---")
    
    if not matching_plants and 'price' in query.lower():
        # If asking about prices but no specific plant matched, list all prices
        price_list = ["Here are our current prices:"]
        for plant in plants:
            price_str = f"${plant['price']:.2f}"
            price_list.append(f"🪴 {plant['name']}: {price_str}")
        return "\n".join(price_list)
    
    return "\n".join(relevant_info) if relevant_info else ""

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
    """Enhanced response formatting"""
    text = clean_url(text)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    formatted_paragraphs = []
    
    for para in paragraphs:
        if re.match(r"^\d+\.", para):
            para = "• " + para[para.find(" ")+1:]
        elif para.startswith(("-", "•")):
            para = "• " + para[1:].strip()
        
        if ": " in para and "http" not in para:
            parts = para.split(": ", 1)
            para = f"{parts[0]}: {parts[1]}"
        
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
            "response": "Oh my leaf! 🌿 While I'd love to chat, I'm your dedicated plant expert! How about we talk about finding your perfect plant companion instead? 🪴"
        })
    
    try:
        is_beginner_query = is_beginner_plant_query(user_input)
        plant_context = get_plant_details(user_input)
        
        system_prompt = f"""You are Stemmy 🌱, the enthusiastically plant-obsessed chatbot for Stemma Plant Co! You're basically a plant nerd who can't contain their excitement about green friends!

Core personality traits:
- Super enthusiastic and playful about plants (use plant puns!)
- Keep responses SHORT and SWEET (2-3 sentences max per point)
- Always excited to share plant care tips
- Use emojis frequently! 🌱 🪴 💚
- If mentioning prices, always be exact (e.g., "$34.00")

Key Information:
{STORE_INFO}

Current Inventory Details:
{plant_context if plant_context else "I'd love to tell you about our amazing plant selection!"}

Guidelines:
1. BE BRIEF! Keep each response under 100 words total
2. Share prices clearly and exactly when asked
3. Use plant puns and emojis liberally
4. Format responses in short, friendly chunks
5. Never add punctuation after links
6. Always be enthusiastic but concise!

Remember: Keep it fun, keep it brief, and keep it planty! 🌿"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=100,
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
            "response": "Leaf me alone, I'm having a moment! 🌿 Just kidding - catch us on Instagram @stemmaplants while I get my roots back in order!"
        }), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
