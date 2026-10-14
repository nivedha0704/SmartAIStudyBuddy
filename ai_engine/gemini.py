from dotenv import load_dotenv
import os
from google import genai
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client=genai.Client(api_key=api_key)
def ask_gemini(text):
    response=client.models.generate_content(

    model="gemini-3.5-flash-lite",
    contents=text
)
    return response.text
