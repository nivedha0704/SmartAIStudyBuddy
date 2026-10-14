from ai_engine.gemini import ask_gemini
def summarize(text):
    print("Summarizing PDF...")
    prompt = "Summarize the following text in simple words:\n" + text
    return ask_gemini(prompt)
