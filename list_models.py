import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    
    # List available models
    print("Available models:")
    for model in genai.list_models():
        print(f"  - {model.name}")
        if "gemini" in model.name.lower():
            print(f"    Supported methods: {model.supported_generation_methods}")
else:
    print("API key not found!")