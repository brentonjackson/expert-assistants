import os
import requests
import sys
import json
import subprocess
import argparse

MAX_TOKENS = 500000 # This overrides the default max token limit (for bigger folders)
FOLDER_PATH = os.getcwd()  # Change this to the desired folder path
os.environ['DATADUDE_DIRECTORY'] = os.path.expanduser("~/code/datadude") # location of server

########## Helper Functions ###########
def get_directory_structure(root_dir=FOLDER_PATH):
    """
    Calls the directory_scanner.py script as a subprocess and returns the directory structure object.
    """
    # Prepare the command to run directory_scanner.py
    command = ['python',  os.path.join(os.environ['DATADUDE_DIRECTORY'],'directory_utils/directory_scanner.py')]
    if root_dir is not None:
        command.append(str(root_dir))
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
        # print(result.stdout)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"client.py: Error: {e.stderr}")
        sys.exit(result.returncode)
    
def run_token_validator(str, max_tokens=MAX_TOKENS):
    """
    Calls token validator script.
    """
    command = ['python', os.path.join(os.environ['DATADUDE_DIRECTORY'],'ai_utils/token_validator.py')]
    if max_tokens is not None:
        command.append(f'{max_tokens}')
    try:
        result = subprocess.run(command, input=str, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
    except subprocess.CalledProcessError as e:
        if e.stdout:
            print(f"\nclient.py: Token Validator Error: {e.stdout}")
        if e.stderr:
            print(f"\nclient.py: Token Validator Error: {e.stderr}")
        sys.exit(result.returncode)
#######################################



########## API Requests ###########
def get_session_and_thread_id(ai_type: str):
    """
    Sends /session POST request to the server.
    Receives the sessionID and threadID to use to start a chat session.
    """
    url = 'http://127.0.0.1:5000/session'
    
    files = get_directory_structure()
    body = {"path": FOLDER_PATH, "files": files}
    if ai_type:
        body["ai_type"] = ai_type

    # Validate token count
    json_str = json.dumps(body)
    run_token_validator(json_str)
    
    response = requests.post(url, json=body)
    if response.status_code != 200:
        print(response.text)
    response.raise_for_status()
    return (response.json().get("sessionID"), response.json().get("threadID"))

def send_chat_message(sessionID, threadID, message, initMessage=False):
    """
    Sends /chat/<sessionID> POST request to the server.
    Request includes chat message to the AI Assistant.
    Receives a response chat message from the AI Assistant.
    """
    url = 'http://127.0.0.1:5000/chat/' + sessionID
    
    body = {"threadID": threadID, "message": message, "initMessage": initMessage}

    # Validate token count
    json_str = json.dumps(body)
    run_token_validator(json_str)
    response = requests.post(url, json=body)
    
    if response.status_code != 200:
        print(response.text)
    response.raise_for_status()
    return (response.json().get("message"))
###################################


if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Client for interacting with DataDude server")
    parser.add_argument('-a','--ai', type=str, default="", required=False, choices=['a', 'c'],
                        help='Type of AI handler to use (a for assistants, c for chat_completions)')
    args = parser.parse_args()

    # Map shorthand options to full AI type names
    ai_type_map = {'a': 'assistants', 'c': 'chat_completions'}
    ai_type = ""
    if args.ai:
        ai_type = ai_type_map[args.ai]
        
    # pass AI type to the session endpoint
    sessionID, threadID = get_session_and_thread_id(ai_type)

    if not sessionID:
        sys.exit(1)

    first_message = True

    # Check if input is from a pipe
    if not sys.stdin.isatty():
        # Input is from a pipe
        for line in sys.stdin:
            message = line.strip()
            if message:
                print("Me:\t\t" + message)
                if first_message:
                    response = send_chat_message(sessionID, threadID, message, initMessage=True)
                    first_message = False
                else:
                    response = send_chat_message(sessionID, threadID, message)
                print("Datadude:\t" + response)
    else:
        # Interactive input
        print("You can start typing your queries. Press ^D (Ctrl+D) to exit.")
        while True:
            try:
                message = input("Me:\t\t")
                if first_message:
                    response = send_chat_message(sessionID, threadID, message, initMessage=True)
                    first_message = False
                else:
                    response = send_chat_message(sessionID, threadID, message)
                print("Datadude:\t" + response)
            except EOFError:
                break