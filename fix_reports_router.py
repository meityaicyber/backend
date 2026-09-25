import re

file_path = 'c:/Main Project/Modules/backend/backend/app/routers/reports.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the upload_report try-except block
old_block = """    try:
        result = await report_service.upload_report(
            db, file_bytes, file.filename, current_user.user_id, agency_id
        )
        return UploadResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )"""

new_block = """    try:
        result = await report_service.upload_report(
            db, file_bytes, file.filename, current_user.user_id, agency_id
        )
        return UploadResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )"""

content = content.replace(old_block, new_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
