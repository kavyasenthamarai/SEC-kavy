from flask import Flask, request, jsonify
from chatbot import Chatbot  # Replace with the actual filename of your chatbot module
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Initialize the chatbot
chatbot = Chatbot(api_key="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", 
                  json_file=os.path.join(os.path.dirname(__file__), 'new.json'))  # Update with relative path

@app.route('/chatbot', methods=['POST'])
def chatbot_api():
    try:
        # Get the user input from the request
        user_input = request.json.get('message', '')
        if not user_input:
            return jsonify({'reply': 'Please provide a message.'}), 400

        # Generate a response from the chatbot
        response = chatbot.ask(user_input)
        return jsonify({'reply': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
