from ai_utils.chat_completions_handler import ChatCompletionsHandler
from ai_utils.assistants_handler import AssistantsHandler

def get_ai_handler(ai_type, subject: str, threadID: str):
    if ai_type == "chat_completions":
        return ChatCompletionsHandler()
    elif ai_type == "assistants":
        return AssistantsHandler(subject=subject, threadID=threadID)
    else:
        raise ValueError(f"Unknown AI type: {ai_type}")
