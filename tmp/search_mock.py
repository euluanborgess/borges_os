import sys
import os

with open(r'c:\Users\User\Documents\BorgesOS_Atualizado\api\routes\traffic.py', 'r') as f:
    text = f.read()

if "mock_token" in text:
    print("MOCK TOKEN FOUND IN TRAFFIC.PY!")
    for i, line in enumerate(text.split('\n')):
        if "mock_token" in line:
            print(f"Line {i+1}: {line.strip()}")
else:
    print("NO MOCK TOKEN IN TRAFFIC.PY")
