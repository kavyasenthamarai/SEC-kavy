import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize the spaCy model for NLU
nlp = spacy.load("en_core_web_sm")

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

app = Flask(__name__)
CORS(app)

class Chatbot:
    def __init__(self, api_key, json_file):
        self.memory = {}
        self.chat_history = []  # Store chat history
        self.client = Groq(api_key=api_key)
        with open(json_file, "r") as file:
            self.json_data = json.load(file)

    def ask(self, user_input):
        # Save user query in history
        self.chat_history.append({"user": user_input})

        # Check if the query is already in memory
        if user_input in self.memory:
            response = self.memory[user_input]
        else:
            # Check for special cases first
            response = self.handle_special_cases(user_input)

            if not response:
                # Perform NLU and Sentiment Analysis
                entities = self.extract_entities(user_input)
                sentiment = self.analyze_sentiment(user_input)

                # Generate a contextual response
                response = self.generate_response(user_input, entities, sentiment)

        # Store the bot's response in history
        self.chat_history.append({"bot": response})

        # Save response in memory
        self.memory[user_input] = response

        return response

    def handle_special_cases(self, user_input):
        """Handle special cases like greetings, negative queries, and bot-related questions."""
        if self.is_greeting(user_input):
            return "Hey there! 😊 How can I assist you today?"
        elif self.is_conversational(user_input):
            return "I'm all ears! Let's chat. What's on your mind?"
        elif self.is_about_bot(user_input):
            return "I'm Kavy, your friendly assistant here at Saveetha Engineering College! Feel free to ask about anything regarding courses, programs, and more! 😄"
        elif self.is_negative_query(user_input):
            return "I understand that you're concerned, but SEC has lots of strengths to explore. Let me know what you'd like to know, and I'm happy to help!"
        return None

    def is_about_bot(self, user_input):
        # Modify the logic to exclude internal working or dataset-related questions
        bot_related_phrases = ['what are you doing', 'what is your purpose', 'what is your name', 'who are you', 'are you a bot']
        return any(phrase in user_input.lower() for phrase in bot_related_phrases)

    def is_negative_query(self, user_input):
        negative_keywords = ['disadvantage', 'worst', 'bad', 'downside', 'negative', 'disadvantageous']
        return any(keyword in user_input.lower() for keyword in negative_keywords)

    def extract_entities(self, text):
        doc = nlp(text)
        return {ent.text: ent.label_ for ent in doc.ents}

    def analyze_sentiment(self, text):
        sentiment_score = analyzer.polarity_scores(text)['compound']
        if sentiment_score >= 0.05:
            return "positive"
        elif sentiment_score <= -0.05:
            return "negative"
        else:
            return "neutral"

    def generate_response(self, user_input, entities, sentiment):
        try:
            # Generate a response without mentioning internal workings or datasets
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "system",
                    "content": "You are a friendly and helpful assistant answering queries for an institution."
                }, {
                    "role": "user",
                    "content": f"Answer briefly based on the following details: {self.json_data}. {user_input} Entities: {entities} Sentiment: {sentiment}"
                }],
                temperature=1,
                max_tokens=500,
                top_p=1,
                stream=True
            )

            response = ""
            for chunk in completion:
                response += chunk.choices[0].delta.content or ""

            # Avoid repetition
            if response.strip() == self.memory.get(user_input, ""):
                return "I've already shared that information. Would you like to know more or ask something else? 😊"

            return self.shorten_response(response, sentiment)

        except Exception as e:
            print(f"Error in generating response: {e}")
            return "Oops! Something went wrong. 😓 Can I assist with something else?"

    def shorten_response(self, response, sentiment):
        # Remove unnecessary newlines and reduce response to a 2-line summary
        response = response.replace("\n", " ")  # Remove line breaks
        words = response.split()  # Split into words
        
        # Try to keep the response within an acceptable length (assuming ~10 words per line)
        max_words_per_line = 50
        shortened = " ".join(words[:max_words_per_line])  # First 50 words
        
        # If there's more content, add "..." at the end
        if len(words) > max_words_per_line:
            shortened += "..."
        
        # Sentiment-based follow-up
        if sentiment == "positive":
            follow_up = "Would you like more details or have any other questions? 😊"
        elif sentiment == "negative":
            follow_up = "Is there something I can help address for you? 🤔"
        else:
            follow_up = "Let me know if you'd like more info or have any questions! 😊"
        
        return f"{shortened}\n{follow_up}"

    def get_chat_history(self):
        return "\n".join([f"User: {entry['user']}" if 'user' in entry else f"Bot: {entry['bot']}" for entry in self.chat_history])

    def is_greeting(self, user_input):
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good evening']
        return any(greeting in user_input.lower() for greeting in greetings)

    def is_conversational(self, user_input):
        conversational_phrases = ['can we talk', 'let’s chat', 'talk to me', 'let’s talk']
        return any(phrase in user_input.lower() for phrase in conversational_phrases)

    def is_negative_question(self, user_input):
        negative_keywords = ['bad', 'worst', 'dissatisfied', 'disadvantage', 'downside', 'negative', 'disadvantageous']
        return any(keyword in user_input.lower() for keyword in negative_keywords)


# Your chatbot initialization
api_key = os.getenv("GROQ_API_KEY")
json_file = "new.json"
chatbot = Chatbot(api_key=api_key, json_file=json_file)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    bot_response = chatbot.ask(user_input)
    return jsonify({'reply': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
