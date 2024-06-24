import sys
import tiktoken

def count_tokens(text):
    """
    Counts the number of tokens in a given text using tiktoken library.
    """
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = enc.encode(text)
    return len(tokens)

if __name__ == "__main__":
    input_text = sys.stdin.read()
    token_count = count_tokens(input_text)
    print(token_count)