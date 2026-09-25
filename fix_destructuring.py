import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_context_regex = r'const \{\s*bulkFilesData,\s*setBulkFilesData,\s*bulkProgress,\s*bulkTotal,\s*bulkRunning,\s*bulkFinished,\s*setBulkFinished,\s*bulkStartTime,\s*bulkEndTime,\s*startBulkUpload,\s*resetBulkState\s*\}\s*=\s*useBulkUpload\(\);'

new_context = """const {
      bulkFilesData, setBulkFilesData, bulkProgress, bulkTotal, bulkRunning, bulkFinished, setBulkFinished,
      bulkStartTime, bulkEndTime, bulkPaused, etaSeconds,
      startBulkUpload, pauseBulkUpload, resumeBulkUpload, resetBulkState
    } = useBulkUpload();"""

content = re.sub(old_context_regex, new_context, content, flags=re.MULTILINE)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Destructuring fixed!')
