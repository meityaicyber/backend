from reportlab.pdfgen import canvas
import PyPDF2
import os

def create_and_encrypt(filename, text, password):
    # 1. Create a simple PDF
    c = canvas.Canvas("temp.pdf")
    c.drawString(100, 700, "Cyber Security Audit Report 2024")
    c.drawString(100, 650, text)
    c.save()
    
    # 2. Encrypt with PyPDF2
    reader = PyPDF2.PdfReader("temp.pdf")
    writer = PyPDF2.PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
        
    writer.encrypt(password)
    
    with open(filename, "wb") as f:
        writer.write(f)
        
    os.remove("temp.pdf")

# Use a directory inside user's home or current working dir
os.makedirs("C:/Users/priya/Desktop/dummy_test_files", exist_ok=True)

# Generate KPMG
create_and_encrypt(
    "C:/Users/priya/Desktop/dummy_test_files/KPMG_Report.pdf", 
    "Empanelled by CERT-In: KPMG Assurance and Consulting Services LLP", 
    "kpmg_secure"
)

# Generate BDO
create_and_encrypt(
    "C:/Users/priya/Desktop/dummy_test_files/BDO_Report.pdf", 
    "Audited by BDO India LLP", 
    "bdo_pass"
)

# Generate Deloitte
create_and_encrypt(
    "C:/Users/priya/Desktop/dummy_test_files/Deloitte_Report.pdf", 
    "Information Security Auditor: Deloitte Touche Tohmatsu India LLP", 
    "deloitte_test"
)

# Create passwords mapping. For bulk upload, it expects CSV or specific format. We'll use CSV.
import csv
with open("C:/Users/priya/Desktop/dummy_test_files/passwords.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Filename", "Password"])
    writer.writerow(["KPMG_Report.pdf", "kpmg_secure"])
    writer.writerow(["BDO_Report.pdf", "bdo_pass"])
    writer.writerow(["Deloitte_Report.pdf", "deloitte_test"])

# And also a raw txt file just in case they want a master password list
with open("C:/Users/priya/Desktop/dummy_test_files/passwords.txt", "w") as f:
    f.write("kpmg_secure\nbdo_pass\ndeloitte_test\n")

print("Generated files in C:/Users/priya/Desktop/dummy_test_files/")
