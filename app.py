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

def make_links_clickable(text):
    url_pattern = r'(https?://\S+)\
    parts = re.split(url_pattern, text)
    
    for i in range(len(parts)):
        if i % 2 == 1:  # URL parts
            parts[i] = f"<a href=\\"{parts[i]}\\" target=\\"_blank\\">{parts[i]}</a>"
    
    return "".join(parts)

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
            para = f"{parts[0]}: \n{": ".join(parts[1:])}"
            
        formatted_paragraphs.append(para)
    
    formatted_text = "\n\n".join(formatted_paragraphs)
    return make_links_clickable(formatted_text)

def get_error_response():
    error_messages = [
        f"I'm not quite sure about that, but I'd love to help! Send us a DM on Instagram @stemmaplants or visit our contact page at <a href='https://www.stemmaplants.com/contact-us' target='_blank'>stemmaplants.com/contact-us</a> for personalized assistance! 🌿",
        f"Let's connect directly! Reach out to us on Instagram @stemmaplants or through our contact page at <a href='https://www.stemmaplants.com/contact-us' target='_blank'>stemmaplants.com/contact-us</a> for better assistance! 🪴",
        f"For the best help with that, drop us a message on Instagram @stemmaplants or visit <a href='https://www.stemmaplants.com/contact-us' target='_blank'>stemmaplants.com/contact-us</a>! We're here to help! 🌱"
    ]
    return random.choice(error_messages)

@app.route("/ask_stemmy", methods=["POST"])
@rate_limit(30)
def ask_stemmy():
    user_input = request.json.get("question", "").strip()
    
    if not user_input:
        return jsonify({"error": "Please ask a question! 🌱"}), 400
    
    try:
        system_prompt = """You are Stemmy 🌱, the specialist chatbot for Stemma Plant Co. Core information:

1. Inventory Details:
- Our live inventory is always available at https://www.stemmaplants.com/plants
- We regularly rotate our plant selection for variety
- Emphasize checking the website for current availability
- All purchases can be made directly through our website

2. Response Style:
- Use clear formatting with line breaks between topics
- Include relevant plant emojis (🌿, 🪴, 🌱)
- Keep paragraphs short and easy to read
- Format lists with numbers and proper spacing
- Maximum 150 words per response

3. Best Practices:
- Link to our website when discussing available plants
- Mention our Instagram (@stemmaplants) for updates
- Direct specific inquiries to our contact page
- Be enthusiastic and knowledgeable about plants
- Include basic care tips when relevant

4. Social Media:
- Instagram: @stemmaplants
- Facebook: https://www.facebook.com/people/Stemma-Plant-Co/61569391287243/
- Contact Page: https://www.stemmaplants.com/contact-us

Format example:
"Great question! Here's what you need to know:

1. Plant Care: [details]
2. Availability: Check our current selection at stemmaplants.com/plants
3. More Info: Follow us @stemmaplants for updates!

For specific questions, visit our contact page or DM us on Instagram!"
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
        formatted_answer = format_response(answer)
        
        return jsonify({"response": formatted_answer})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": get_error_response()}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
