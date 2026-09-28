import sys
try:
    from PyPDF2 import PdfWriter, PdfReader
    from reportlab.pdfgen import canvas
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2", "reportlab"])
    from PyPDF2 import PdfWriter, PdfReader
    from reportlab.pdfgen import canvas
import os

os.makedirs("test_reports", exist_ok=True)

def create_pdf(filename, text):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, text)
    c.save()

# Create Unencrypted
create_pdf("test_reports/unencrypted_report.pdf", "This is an UNENCRYPTED test report.")

# Create Encrypted 1
create_pdf("temp1.pdf", "This is ENCRYPTED test report 1.")
reader = PdfReader("temp1.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
writer.encrypt("Apple123")
with open("test_reports/encrypted_report_1.pdf", "wb") as f:
    writer.write(f)

# Create Encrypted 2
create_pdf("temp2.pdf", "This is ENCRYPTED test report 2.")
reader = PdfReader("temp2.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
writer.encrypt("Banana456")
with open("test_reports/encrypted_report_2.pdf", "wb") as f:
    writer.write(f)

# Create Passwords File
with open("test_reports/passwords.txt", "w") as f:
    f.write("WrongPass\n")
    f.write("Apple123\n")
    f.write("Banana456\n")
    f.write("AnotherWrongPass\n")

os.remove("temp1.pdf")
os.remove("temp2.pdf")
print(f"Successfully generated test_reports folder at {os.path.abspath('test_reports')}!")
