import json
from groq import Groq
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize spaCy model for NLU
nlp = spacy.load("en_core_web_sm")

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

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
        elif self.is_greeting(user_input):
            response = "Hello! How can I assist you today?"
        elif self.is_conversational(user_input):
            response = "Sure! I'm here to chat. What would you like to know or talk about?"
        elif self.is_about_bot(user_input):  # Detect if the question is about the bot itself
            response = "I am Kavy, your AI assistant for Saveetha Engineering College. Feel free to ask about courses, programs, and more!"
        elif self.is_negative_query(user_input):  # Check for negative queries
            response = "I believe SEC has many strengths to offer, and I'm happy to provide you with more information about its programs and facilities!"
        else:
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

    def is_about_bot(self, user_input):
        # Check if the user is asking about the bot
        bot_related_phrases = ['what are you doing', 'what is your purpose', 'what is your name', 'who are you', 'are you a bot']
        return any(phrase in user_input.lower() for phrase in bot_related_phrases)

    def is_negative_query(self, user_input):
        negative_keywords = ['disadvantage', 'worst', 'bad', 'downside', 'negative', 'disadvantageous']
        return any(keyword in user_input.lower() for keyword in negative_keywords)
    
    def extract_entities(self, text):
        doc = nlp(text)
        entities = {ent.text: ent.label_ for ent in doc.ents}
        return entities

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
            # Generate AI response with context
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

            # Collect and return response from API
            response = ""
            for chunk in completion:
                response += chunk.choices[0].delta.content or ""

            # Avoid repetition
            if response.strip() == self.memory.get(user_input, ""):
                return "I’ve already shared this info. Would you like more details?"

            return self.shorten_response(response, sentiment)
        except Exception as e:
            print("Error:", e)
            return "Sorry, I encountered an issue. Can I assist with something else?"

    def shorten_response(self, response, sentiment):
        response_lines = response.splitlines()
        important_keywords = ['course', 'program', 'list', 'details']

        contains_important_content = any(keyword in response.lower() for keyword in important_keywords)
        shortened = "\n".join(response_lines) if contains_important_content else "\n".join(response_lines[:3])

        follow_up = "Would you like more details?" if sentiment == "positive" else (
            "Is there an issue I should address?" if sentiment == "negative" else "Let me know if you'd like additional details.")
        return f"{shortened}\n{follow_up}"

    def get_chat_history(self):
        # Display complete chat history
        return "\n".join([ 
            f"User: {entry['user']}" if 'user' in entry else f"Bot: {entry['bot']}"
            for entry in self.chat_history
        ])

    def is_greeting(self, user_input):
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good evening']
        return any(greeting in user_input.lower() for greeting in greetings)

    def is_conversational(self, user_input):
        conversational_phrases = ['can we talk', 'let’s chat', 'talk to me', 'let’s talk']
        return any(phrase in user_input.lower() for phrase in conversational_phrases)

    def is_negative_question(self, user_input):
        negative_keywords = ['bad', 'worst', 'dissatisfied','disadvantage', 'downside', 'negative', 'disadvantageous']
        return any(keyword in user_input.lower() for keyword in negative_keywords)


# Initialize the chatbot
chatbot = Chatbot(api_key="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", 
                  json_file=r"C:\Users\SEC\Desktop\sec-backend\chatbot-backend\new.json")

# Run chatbot interaction in terminal
while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Bot: Goodbye! Have a great day!")
        break
    response = chatbot.ask(user_input)
    print(f"Bot: {response}")
    


