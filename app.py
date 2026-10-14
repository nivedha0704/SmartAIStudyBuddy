from pdf_reader.reader import read_pdf
from summarizer.summary import summarize
from quiz.quiz import generate_quiz
from flashcards.flashcards import generate_flashcards
text=read_pdf("uploads/Sample.pdf.pdf")
while True:
    print("\nWhat would you like to do?")
    print("1. Summarize the PDF")
    print("2. Generate a Quiz")
    print("3. Generate Flashcards")
    print("4. Exit")

    choice = input("Enter your choice: ")
    if choice=="1":
        summary=summarize(text)
        print(summary)
    elif choice=="2":
        quiz=generate_quiz(text)
        print(quiz)
    elif choice == "3":
        flashcards = generate_flashcards(text)
        print(flashcards)
    elif choice=="4":
        print("Goodbye! 👋")
        break
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")