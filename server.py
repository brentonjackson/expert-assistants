from flask import Flask, request, jsonify, render_template
from ai_utils.ai_factory import get_ai_handler
from ai_utils.ai_base import AIHandler  # The base class to define type hints
from ai_utils.assistants_handler import AssistantsHandler


# Create an instance of AIHandler based on the desired type
# For example, use "chat_completions" or "assistants"
DEFAULT_AI_HANDLER = "assistants"
# Default assistant
assistants_thread = None
assistants = {} 
""" 
assistants: {
    <subject>: {
        subject: "general",
        ai_handler: <ai_handler>
    }
}
"""

app = Flask(__name__)


########## API Endpoints ###########
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/startConversation', methods=['POST'])
def start_session():
    global assistants_thread
    """
    Creates a default assistant and returns the thread ID 
    for others to tap into the convo.
    Also returns a message and the subject.
    """
    data = request.get_json()    
    subject = data["subject"]

    # Create a new AI handler
    if not assistants.get(subject) and not assistants_thread:
        ai_handler: AssistantsHandler  = get_ai_handler(DEFAULT_AI_HANDLER, subject=subject, threadID="") 
        assistants_thread = ai_handler.thread_id
        assistants[subject] = {
            "subject": subject,
            "ai_handler" :ai_handler,
        }

    return jsonify({'threadID': assistants_thread, "message": "AI assistant joined the chat.", "subject": subject}), 200


@app.route('/provision', methods=['POST'])
def provision():
    """
    Provision other expert assistants.
    """
    data = request.json
    subject = data['subject']
    threadID = data['threadID']
    if not assistants.get(subject):
        ai_handler: AssistantsHandler  = get_ai_handler(DEFAULT_AI_HANDLER, subject=subject, threadID=threadID) 
        assistants[subject] = {
            "subject": subject, 
            "ai_handler": ai_handler
        }
    return jsonify({"message": "AI assistant joined the chat.", "subject": subject})

@app.route('/chat', methods=['POST'])
def chat():
    """
    User sends a message in the convo.
    """
    data = request.json
    user_message = data['message']
    
    responses = {}
    for subject, assistant_object in assistants.items():
        assistant: AIHandler = assistant_object["ai_handler"]
        response = assistant.get_response(input=user_message)
        if response == "" or response == "0":
            continue
        responses[subject] = response
    return jsonify({"responses": responses}), 200

def get_ai_response(subject, message):
    assistant: AIHandler = assistants.get(subject)["ai_handler"]
    return assistant.get_response(input=message)

#####################################

if __name__ == '__main__':
    app.run()  