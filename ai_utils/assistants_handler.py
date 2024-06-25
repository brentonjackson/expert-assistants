from openai import OpenAI
from ai_utils.ai_base import AIHandler
import json
import time
import os
import markdown

def show_json(obj):
    dict = json.loads(obj.model_dump_json())
    print(json.dumps(dict, indent=2, sort_keys=True))

def create_temp_file(data, filename):
    """
    creates temp file w/ data in it
    """
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    path = "tmp/" + filename
    with open(path, 'wb') as file:
        file.write(data)
    return path

def delete_temp_folder(filename):
    """
    removes the tmp folder and all files within
    """
    os.rmdir("tmp")
    os.remove("tmp/" + filename)
    return


class AssistantsHandler(AIHandler):
    """
    This AI handler persists message state in the forms of threads.
    """
    def __init__(self, subject: str, threadID:str=None):
        self.client = OpenAI()
        self.assistant = None
        self.thread_id = None
        self.subject = subject
        self.run = None
        self.setup(threadID)

    def setup(self, threadID: str):
        """
        Loads AI assistant and creates a new thread.
        """
        # The assistant only needs to be created once. It should not be created every time.
        # At most, we should find the assistant, then load it here.
        my_assistants = self.client.beta.assistants.list(
            order="desc",
        )
        # if my_assistants.has_next_page(): 
        #     print("dude you got a lot of assistants.")
        # do some pagination https://platform.openai.com/docs/api-reference/assistants/listAssistants
        
        if len(my_assistants.data) > 0:
            # get data dude directory assistant
            assistants_list = my_assistants.data
            # could've used a for loop for this search, but this oneliner is nice
            expert_assistant = next((assistant for assistant in assistants_list if assistant.name == f"{self.subject} Assistant"), None)
            self.assistant = expert_assistant
        
        if self.assistant == None:
            self.assistant = self.client.beta.assistants.create(
                instructions=f"""This GPT is an expert in {self.subject}.
                    If the user's question is ambiguous, the GPT should always ask for clarification before providing an answer.
                    The GPT communicates in the language of the {self.subject} domain, with the expertise and depth of someone with a PhD in the field.
                    Responses should be as short as possible while satisfying the user's request.
                    The GPT is part of a conversation with multiple experts and weighs in with the GPT's expert opinion related to {self.subject}.
                    The GPT should not respond with anything unrelated to {self.subject}.
                    If the GPT has nothing to say or add to the conversation, just say "0".
                    If the GPT doesn't have unique insight to add related to its specific expertise, it should default to saying nothing.
                    The GPT should only answer when the response is specifically related to {self.subject}.
                    """,
                name=f"{self.subject} Assistant",
                model="gpt-3.5-turbo", # https://platform.openai.com/docs/models,
                temperature=0.0 # makes things more deterministic, up to 2 makes things more random,
            )

        # Create new thread and attach vector store to it
        if threadID:
            self.thread_id = threadID
        else:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            

    def get_response(self, input: str):
        """
        Adds message to the thread and creates a Run.
        Runs indicate to an Assistant it should look at the messages in the Thread and take action: either by adding a single response, or using tools.
        
        We don't care about context or an init message because the Assistant itself holds the context.
        """

        user_message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=f"{input.strip()}",
        )
        
        # Create a Run
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant.id,
        )
        self.run = run
        
        # Runs are async, so we have to wait til it completed processing
        self.wait_on_run()
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread_id,
            run_id=self.run.id
        )
        print("Thread ID:", self.thread_id)
        print("Subject: ", self.subject)
        # print("Run steps:")
        # for step in run_steps.data:
        #     show_json(step.step_details)

        # List the Messages in the Thread to see what got added by the Assistant.
        # Listed from oldest first (asc), and filter only messages after the user message.
        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id, order="asc", after=user_message.id)
        
        message_response = []
        for message in messages:
            # print(message)
            if message.content[0].type == 'text':
                content = message.content[0].text.value
                if content == "" or content == "0":
                    message_response.append(content)
                    continue
                message_response.append(markdown.markdown(content))
            if message.content[0].type == 'image_url':
                message_response.append(message.content[0].image_url.url)
            if message.content[0].type == 'image_file':
                message_response.append("File ID: " + message.content[0].image_file.file_id)
        if not message_response:
            return "Error occurred. Please repeat your message."

        # combine messages
        combined_message = ' '.join(message_response)
        print("Message: ", combined_message)
        return combined_message


    
    def wait_on_run(self):
        while self.run.status == "queued" or self.run.status == "in_progress":
            # print("Run status: ", self.run.status)
            self.run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=self.run.id,
            )
            time.sleep(0.5)

    def delete_vectore_stores(self):
        vector_stores = self.client.beta.vector_stores.list(order="desc", limit=100)
        ctr = 1
        for store in vector_stores:
            # delete it
            self.client.beta.vector_stores.delete(store.id)
            ctr += 1
        print(f"deleted {ctr-1} vector stores")

    def delete_files(self):
        files = self.client.files.list(purpose="assistants")
        ctr = 1
        for file in files:
            # delete it
            self.client.files.delete(file.id)
            ctr += 1
        print(f"deleted {ctr-1} files")

    
    def delete_session_files(self):
        files = self.client.files.list(purpose="assistants")
        ctr = 1
        for file in files:
            # delete it
            file_session = file.filename.split("_")
            if file_session[0] == self.sessionID:
                self.client.files.delete(file.id)
            ctr += 1
        print(f"deleted {ctr-1} old files")

    def get_thread_messages(self, thread_id: str):
        """
        Helper to save thread messages, given you know the thread id
        """
        thread_messages = self.client.beta.threads.messages.list(thread_id, order='asc', limit=100)
        content = []
        for message in thread_messages.data:
            if message.role == 'assistant':
                speaker = "Datadude:\t\t"
            else:
                speaker = "Me:\t\t\t\t\t"
            
            if message.content[0].type == 'text':
                content.append(speaker + message.content[0].text.value)
            if message.content[0].type == 'image_url':
                content.append(speaker + message.content[0].image_url.url)
            if message.content[0].type == 'image_file':
                content.append(speaker + "File ID: " + message.content[0].image_file.file_id)
            
        return content

