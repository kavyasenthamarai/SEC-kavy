// chatbot.js

// Send the user input to the backend and receive the response
function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    
    if (!userInput.trim()) {
        alert("Please type a message!");
        return;
    }

    // Display the user's message
    const chatHistory = document.getElementById('chat-history');
    chatHistory.innerHTML += `<p><strong>You:</strong> ${userInput}</p>`;
    
    // Send message to the backend via POST request
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json())
    .then(data => {
        const botResponse = data.response;
        
        // Display the bot's response
        chatHistory.innerHTML += `<p><strong>Bot:</strong> ${botResponse}</p>`;
        
        // Clear the input field
        document.getElementById('user-input').value = '';
    })
    .catch(error => {
        console.error("Error:", error);
    });
}
