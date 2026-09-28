import os
import json
import random
import csv
import subprocess
import sys

def install_dependencies():
    try:
        import reportlab
        import PyPDF2
    except ImportError:
        print("Installing required packages (reportlab, PyPDF2)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "PyPDF2"])

install_dependencies()

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io

def generate_reports():
    # 1. Load organisations to simulate realistic ML text extraction
    orgs_path = os.path.join(os.path.dirname(__file__), 'organisations.json')
    orgs = []
    if os.path.exists(orgs_path):
        with open(orgs_path, 'r', encoding='utf-8') as f:
            orgs = json.load(f)
    else:
        orgs = [
            {"official_name": "PricewaterhouseCoopers Pvt. Ltd.", "aliases": ["PwC"]},
            {"official_name": "Deloitte Touche Tohmatsu India LLP", "aliases": ["Deloitte"]},
            {"official_name": "Ernst & Young LLP", "aliases": ["EY"]},
            {"official_name": "KPMG India Pvt. Ltd.", "aliases": ["KPMG"]}
        ]

    # 2. Setup output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_reports_v2')
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, 'passwords_manifest.csv')
    
    num_reports = 50
    manifest_data = []
    
    print(f"Generating {num_reports} test audit reports in: {output_dir}")

    for i in range(1, num_reports + 1):
        # Pick an org, sometimes use alias, sometimes introduce a slight typo for fuzzy matching test
        org = random.choice(orgs)
        use_alias = random.choice([True, False])
        
        if use_alias and org.get('aliases'):
            display_name = random.choice(org['aliases'])
        else:
            display_name = org.get('official_name', 'Unknown Agency')
            
        # Introduce a typo 10% of the time to test AGENCY_REVIEW_REQUIRED
        if random.random() < 0.1:
            display_name = display_name.replace('e', 'a', 1).replace('i', 'l', 1) + " Corp"

        # Generate base PDF in memory using ReportLab
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 700, f"Cybersecurity Audit Report #{i:04d}")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, 650, f"Auditing Agency: {display_name}")
        c.drawString(100, 630, "Date: 2026-09-23")
        c.drawString(100, 610, "Status: FINAL")
        c.drawString(100, 550, "Executive Summary:")
        c.drawString(100, 530, "This is a dummy report generated for testing the bulk upload pipeline.")
        c.drawString(100, 510, "It contains findings, vulnerabilities, and risk assessments.")
        c.save()
        
        packet.seek(0)
        new_pdf = PdfReader(packet)
        writer = PdfWriter()
        writer.add_page(new_pdf.pages[0])
        
        # Decide if we want to encrypt it (approx 30% of files)
        is_encrypted = random.random() < 0.3
        password = None
        
        if is_encrypted:
            # Create a subfolder for the encrypted file and its password
            sub_dir = os.path.join(output_dir, f"Agency_{display_name.replace(' ', '_').replace('.', '').replace('&', 'and')}_{i:04d}")
            os.makedirs(sub_dir, exist_ok=True)
            
            # Generate a random 4-digit pin or word
            password = random.choice(["secret123", "audit2026", "pass" + str(random.randint(1000, 9999))])
            writer.encrypt(password)
            
            filename = f"Audit_Report_{i:04d}.pdf"
            filepath = os.path.join(sub_dir, filename)
            
            with open(filepath, "wb") as f:
                writer.write(f)
                
            pwd_path = os.path.join(sub_dir, "password.txt")
            with open(pwd_path, "w", encoding='utf-8') as pf:
                pf.write(password)
        else:
            filename = f"Audit_Report_{i:04d}_{display_name.replace(' ', '_').replace('.', '').replace('&', 'and')}.pdf"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                writer.write(f)
            
    print(f"\nDone! Generated {num_reports} PDFs.")
    print(f"Around 30% are password-protected, placed in subfolders alongside their 'password.txt'.")
    print(f"You can now drag the entire '{output_dir}' folder into the UI.")

if __name__ == "__main__":
    generate_reports()
