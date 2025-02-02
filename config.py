"""
config.py

This module loads environment variables and configures API keys for the application.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from the .env file
load_dotenv()

# Configure Google API key for Gemini Pro model
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Configure PandasAI API key
PANDASAI_API_KEY = os.getenv("PANDASAI_API_KEY")
os.environ["PANDASAI_API_KEY"] = PANDASAI_API_KEY
