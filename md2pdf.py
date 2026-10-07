import sys
from fpdf import FPDF
import re

def markdown_to_pdf(md_file, pdf_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Remove some markdown syntax for cleaner text
    clean_text = md_text
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
    clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)
    clean_text = re.sub(r'_(.*?)_', r'\1', clean_text)
    clean_text = clean_text.replace('$', '')
    
    # Split into lines
    for line in clean_text.split('\n'):
        if line.startswith('# '):
            pdf.set_font("Helvetica", style='B', size=16)
            pdf.write(10, line[2:] + '\n')
        elif line.startswith('## '):
            pdf.set_font("Helvetica", style='B', size=14)
            pdf.write(10, line[3:] + '\n')
        elif line.startswith('### '):
            pdf.set_font("Helvetica", style='B', size=13)
            pdf.write(10, line[4:] + '\n')
        else:
            pdf.set_font("Helvetica", size=11)
            # handle non-breaking space issues
            line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.write(6, line + '\n')
            
    pdf.output(pdf_file)

if __name__ == "__main__":
    markdown_to_pdf(sys.argv[1], sys.argv[2])
