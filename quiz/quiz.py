from ai_engine.gemini import ask_gemini
def generate_quiz(text):
    prompt=prompt = """Create 5 multiple-choice questions from the following text.

For each question:
- Give 4 options (A, B, C, D)
- Give the correct answer
- Keep the questions simple and based only on the provided text

Text:
""" + text
    return ask_gemini(prompt)
