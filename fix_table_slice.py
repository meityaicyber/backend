file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_table_body = """                        <TableBody>
                          {bulkFilesData.map((row) => ("""

new_table_body = """                        <TableBody>
                          {bulkFilesData.slice(Math.max(0, bulkProgress - 5), Math.max(100, bulkProgress + 95)).map((row) => ("""

content = content.replace(old_table_body, new_table_body)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
