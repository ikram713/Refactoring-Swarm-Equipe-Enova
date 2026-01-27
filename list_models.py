import os
import google.generativeai as genai

# Make sure your API key is set in the environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("⚠️  GOOGLE_API_KEY not found in environment!")
else:
    genai.configure(api_key=api_key)

    # List available models
    models = genai.list_models()
    print("Available Gemini models:")
    for m in models:
        print("-", m["name"], "|", m.get("description", "No description"))
