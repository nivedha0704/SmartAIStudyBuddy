import fitz
def read_pdf(file_path):
    pdf=fitz.open(file_path)
    all_text=""
    for i in range(len(pdf)):
        page=pdf.load_page(i)
        text=page.get_text()
        all_text=all_text+text
    return all_text

text=read_pdf("uploads/Sample.pdf.pdf")
print(text)