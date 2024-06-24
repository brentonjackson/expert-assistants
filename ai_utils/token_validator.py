import subprocess
import sys
import os

"""
This module simply accepts incoming text and returns a successful status code
if the token count is within its limits. It fails noisily when the count exceeds the limit.
"""

DEFAULT_MAX_TOKENS = 1000  # Default maximum token limit

class TokenLimitExceededError(Exception):
    """Exception raised when the token limit is exceeded."""
    def __init__(self, token_count, max_tokens):
        self.token_count = token_count
        self.max_tokens = max_tokens
        self.message = f"Token count {token_count} exceeds the maximum allowed {max_tokens} tokens."
        super().__init__(self.message)

def validate_token_count(text, max_tokens=DEFAULT_MAX_TOKENS):
    """
    Validates that the token count of the given text does not exceed the maximum token limit.
    Raises TokenLimitExceededError if the limit is exceeded.
    Returns 0 if the validation is successful.
    """
    result = subprocess.run(['python', os.path.join(os.environ['DATADUDE_DIRECTORY'],'ai_utils/token_counter.py')], input=text, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{result.stderr.strip()}")
        sys.exit(1)
    
    token_count = int(result.stdout.strip())
    if token_count > max_tokens:
        raise TokenLimitExceededError(token_count, max_tokens)
    
    return 0

if __name__ == "__main__":
    input_text = sys.stdin.read()
    max_tokens = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_TOKENS

    try:
        validate_token_count(input_text, max_tokens)
        sys.exit(0) # Success
    except TokenLimitExceededError as e:
        print(f"TokenLimitExceededError: {e}")
        sys.exit(1) # Failure