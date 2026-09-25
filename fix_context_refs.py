import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/contexts/BulkUploadContext.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add new refs
new_refs = """  const currentIndexRef = useRef(0);
  const updateIntervalRef = useRef(null);
  
  // Store settings for resume
  const passwordMapRef = useRef({});
  const selectedAgencyRef = useRef('');
  const concurrencyRef = useRef(1);"""

content = content.replace("  const currentIndexRef = useRef(0);\n  const updateIntervalRef = useRef(null);", new_refs)

# 2. Modify startBulkUpload
old_start = "  const startBulkUpload = (filesData, passwordMap, selectedAgency, concurrency) => {"
new_start = """  const startBulkUpload = (filesData, passwordMap, selectedAgency, concurrency) => {
    passwordMapRef.current = passwordMap || {};
    selectedAgencyRef.current = selectedAgency || '';
    concurrencyRef.current = concurrency || 1;"""
content = content.replace(old_start, new_start)

# 3. Modify startQueue call inside startBulkUpload
content = content.replace("startQueue(filesData, passwordMap, selectedAgency, concurrency);", "startQueue(filesData, passwordMapRef.current, selectedAgencyRef.current, concurrencyRef.current);")

# 4. Modify resumeBulkUpload
old_resume = """  const resumeBulkUpload = (passwordMap, selectedAgency, concurrency) => {
    isPausedRef.current = false;
    setBulkPaused(false);
    setBulkRunning(true);
    startQueue(bulkFilesDataRef.current, passwordMap, selectedAgency, concurrency);
  };"""

new_resume = """  const resumeBulkUpload = () => {
    isPausedRef.current = false;
    setBulkPaused(false);
    setBulkRunning(true);
    startQueue(bulkFilesDataRef.current, passwordMapRef.current, selectedAgencyRef.current, concurrencyRef.current);
  };"""

content = content.replace(old_resume, new_resume)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Context refs patched!')
