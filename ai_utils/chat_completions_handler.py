from openai import OpenAI
from ai_utils.ai_base import AIHandler

def create_context_text(context: object):
    """
    Summarizes the context to keep it concise
    """
    files_summary = "\n".join([f"{file['name']} ({file['path']}, {file['size']} bytes)" for file in context['files']])
    # git_info_summary = "\n".join([f"{key}: {value}" for key, value in context['git_info'].items()])

    return f"Files:\n{files_summary}\n"
    # \nGit Info:\n{git_info_summary}"

class ChatCompletionsHandler(AIHandler):
    """
    This AI handler holds no state between messages.
    They effectively reset to zero.
    However, context is up to date on every message sent.
    The context is sent as a "system" message.
    """
    def __init__(self):
        self.client = OpenAI()
        self.system_messages = []


    def setup(self, sessionContext: object):
        context_text = create_context_text(sessionContext)
        messages = [
            {"role": "system", "content": f"You are DataDude, a filesystem assistant that knows everything about the specified directory. Using only the following context: {context_text}, answer the resulting queries. Answer queries briefly, in a sentence or less."},
            {"role": "system", "name":"example_user", "content": "When was the last updated file?"},
            {"role": "system", "name": "example_assistant", "content": "server.py, which was updated on 6/1/2024 at 6:18 PM."},
            {"role": "system", "name":"example_user", "content": "What is the path to server.py?"},
            {"role": "system", "name": "example_assistant", "content": "/Users/example_user/code/project/server.py"},
        ]
        self.system_messages = messages

    def get_response(self, input: str):
        messages = []
        for message in self.system_messages:
            messages.append(message)  
        messages.append(
            {"role": "user", "content": f"{input}"},
        )
        
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0 # from 0 to 2, where 0 is most deterministic and 2 most random.
        )
        return completion.choices[0].message.content
