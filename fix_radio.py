import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_radio = r'<FormControlLabel value="batch4" control=\{<Radio />\} label="Batch of 4" />'
new_radio = '<FormControlLabel value="batch4" control={<Radio />} label="Batch of 4" />\n                    <FormControlLabel value="batch8" control={<Radio />} label="Batch of 8" />'

content = re.sub(old_radio, new_radio, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Radio buttons patched!')
