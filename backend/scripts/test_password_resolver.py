import asyncio
import io
import os
from PyPDF2 import PdfReader, PdfWriter
from app.services.password_resolver import (
    BatchPasswordResolver,
    EmptyPasswordResolver,
    resolve_and_decrypt
)

def create_dummy_pdf(encrypted=False, password=None):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    if encrypted and password:
        writer.encrypt(password)
        
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

async def test_resolvers():
    print("Testing unencrypted PDF...")
    unencrypted_bytes = create_dummy_pdf()
    resolver = EmptyPasswordResolver()
    b, status = await resolve_and_decrypt(unencrypted_bytes, "test1.pdf", ".pdf", resolver)
    assert status == 'UNENCRYPTED'
    print("Unencrypted PDF passed.")

    print("Testing encrypted PDF with correct password...")
    encrypted_bytes = create_dummy_pdf(encrypted=True, password="secret_password")
    resolver = BatchPasswordResolver("secret_password")
    b, status = await resolve_and_decrypt(encrypted_bytes, "test2.pdf", ".pdf", resolver)
    assert status == 'DECRYPTED'
    print("Encrypted PDF (correct password) passed.")

    print("Testing encrypted PDF with missing password...")
    resolver = EmptyPasswordResolver()
    b, status = await resolve_and_decrypt(encrypted_bytes, "test3.pdf", ".pdf", resolver)
    assert status == 'PASSWORD_NOT_FOUND'
    print("Encrypted PDF (missing password) passed.")

    print("Testing encrypted PDF with wrong password...")
    resolver = BatchPasswordResolver("wrong_password")
    b, status = await resolve_and_decrypt(encrypted_bytes, "test4.pdf", ".pdf", resolver)
    assert status == 'INVALID_PASSWORD'
    print("Encrypted PDF (wrong password) passed.")

if __name__ == "__main__":
    asyncio.run(test_resolvers())
