import os
import openai

# Fetch API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")


def ask_stemmy(prompt):
    try:
        # Corrected API call for openai>=1.0.0
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Stemmy 🌱, a friendly and knowledgeable plant assistant for Stemma Plant Co. Answer questions cheerfully and informatively about plant care and Stemma Plant Co. only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        # Extract and return the assistant's response
        return response['choices'][0]['message']['content']
    except Exception as e:
        # Handle and display errors
        return f"🌱 Oops! Something went wrong: {e}"

if __name__ == "__main__":
    print("Hi, I'm Stemmy 🌱! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("🌱 Bye! Have a great day!")
            break
        response = ask_stemmy(user_input)
        print(f"Stemmy: {response}")
