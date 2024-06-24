import tiktoken
import sys

if len(sys.argv) > 1:
    model = sys.argv[1]
else: 
    model = "gpt-3.5-turbo"
enc = tiktoken.encoding_for_model(model)
# print(enc.__dir__())
print(enc.__dict__["_mergeable_ranks"])
