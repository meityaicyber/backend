file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "onClick={() => resumeBulkUpload(passwordMap, selectedAgency, concurrency)}",
    "onClick={resumeBulkUpload}"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Resume button patched!')
