import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Check API key
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    print(f"✅ API Key found: {api_key[:10]}...")
else:
    print("❌ API Key NOT found!")
    print("\nChecking .env file...")
    
    # List files in current directory
    import os
    print("\nFiles in current directory:")
    for file in os.listdir('.'):
        if file.startswith('.env'):
            print(f"  - {file}")
            try:
                with open(file, 'r') as f:
                    print(f"  Content: {f.read()}")
            except:
                print(f"  Could not read {file}")