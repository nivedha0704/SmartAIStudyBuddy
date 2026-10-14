from ai_engine.gemini import ask_gemini
def generate_flashcards(text):
    prompt = """Create 5 flashcards from the following text.

For each flashcard:
- Give a question on the front
- Give a short answer on the back
- Keep the flashcards simple and based only on the provided text

Text:
""" + text
    return ask_gemini(prompt)
