import os
import sys
import traceback
from pathlib import Path

print('CWD:', Path.cwd())
print('PWD file exists:', Path('.env').exists())
print('.env path:', Path('.env').resolve())
print('OPENAI_API_KEY present in os.environ:', 'OPENAI_API_KEY' in os.environ)
print('OPENAI_API_KEY value:', os.environ.get('OPENAI_API_KEY'))
print('GEMINI_API_KEY present in os.environ:', 'GEMINI_API_KEY' in os.environ)
print('GEMINI_API_KEY value:', os.environ.get('GEMINI_API_KEY'))

# Try to load dotenv explicitly
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('Loaded dotenv; OPENAI after load:', os.getenv('OPENAI_API_KEY'))
except Exception as e:
    print('dotenv load failed:', e)

# Attempt to import api handler
try:
    import importlib
    importlib.invalidate_caches()
    import api_handler_simple
    print('api_handler_simple imported successfully')
    # Print a couple of attributes if present
    print('Has chat_with_framework:', hasattr(api_handler_simple, 'chat_with_framework'))
except Exception as e:
    print('Failed to import api_handler_simple:')
    traceback.print_exc()

# Try to import openai and google.genai
try:
    from openai import OpenAI
    print('openai import OK')
except Exception as e:
    print('openai import failed:', e)

try:
    import google.genai as genai
    print('google.genai import OK')
except Exception as e:
    print('google.genai import failed:', e)

print('sys.executable:', sys.executable)
print('Python version:', sys.version)
