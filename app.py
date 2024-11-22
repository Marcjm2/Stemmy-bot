from flask import Flask, request, jsonify
import os
import openai

# Fetch API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY") 

# Initialize the Flask app
app = Flask(__name__)

# Define the /ask_stemmy route
@app.route("/ask_stemmy", methods=["POST"])
def ask_stemmy():
    print("Request received at /ask_stemmy")  # Log when a request is received
    user_input = request.json.get("question")  # Extract the user's question from the request
    print(f"User question: {user_input}")  # Log the input

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are Stemmy 🌱, a friendly plant assistant for Stemma Plant Co. "
                    "Answer questions about plants and plant care cheerfully and informatively."
                )},
                {"role": "user", "content": user_input}
            ],
            max_tokens=200,
            temperature=0.7
        )
        answer = response['choices'][0]['message']['content']  # Extract the assistant's response
        print(f"Stemmy response: {answer}")  # Log the response
        return jsonify({"response": answer})  # Return the response as JSON
    except Exception as e:
        print(f"Error: {e}")  # Log any errors
        return jsonify({"error": str(e)})  # Return the error as JSON

# Add a simple test route
@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Flask is working!"})

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
