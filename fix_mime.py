import re

file_path = 'c:/Main Project/Modules/backend/backend/app/services/report_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_mime_block = """    # 2. Validate MIME type
    mime_valid, detected_mime = validate_mime_type(file_bytes, extension)
    if not mime_valid:
        await _create_audit_log(
            db, user_id, None, "FILE_UPLOAD", "FAILED",
            {"reason": f"MIME type mismatch: {detected_mime}", "filename": filename}
        )
        raise ValueError(
            f"File content type '{detected_mime}' does not match extension '{extension}'"
        )"""

new_mime_block = """    # 2. Validate MIME type
    mime_valid, detected_mime = validate_mime_type(file_bytes, extension)
    
    # Auto-correct extension if the user uploaded a valid file type with the wrong extension
    if not mime_valid:
        if detected_mime.startswith("text/"):
            extension = ".txt"
            mime_valid = True
        elif detected_mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or (detected_mime == "application/zip" and b"word/document.xml" in file_bytes[:200000]):
            extension = ".docx"
            mime_valid = True
            
    if not mime_valid:
        await _create_audit_log(
            db, user_id, None, "FILE_UPLOAD", "FAILED",
            {"reason": f"MIME type mismatch: {detected_mime}", "filename": filename}
        )
        raise ValueError(
            f"File content type '{detected_mime}' does not match extension '{extension}'"
        )"""

content = content.replace(old_mime_block, new_mime_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
