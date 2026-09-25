import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the buttons using regex to handle formatting differences
old_button_regex = r'<Box>\s*<Button variant="contained" color="primary" size="large" startIcon=\{<PlayArrow />\}[^>]*>\s*\{bulkRunning \? \'Running\.\.\.\' : \'Launch Bulk Processing\'\}\s*</Button>\s*</Box>'

new_buttons = """<Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <Button variant="contained" color="primary" size="large" startIcon={<PlayArrow />} onClick={handleBulkLaunch} disabled={bulkRunning || pdfFiles.length === 0}>
                    {bulkRunning && !bulkPaused ? 'Running...' : 'Launch Bulk Processing'}
                  </Button>
                  
                  {bulkRunning && !bulkFinished && !bulkPaused && (
                    <Button variant="contained" color="warning" size="large" onClick={pauseBulkUpload}>
                      Pause Queue
                    </Button>
                  )}
                  {bulkPaused && !bulkFinished && (
                    <Button variant="contained" color="success" size="large" onClick={() => resumeBulkUpload(passwordMap, selectedAgency, concurrency)}>
                      Resume Queue
                    </Button>
                  )}
                  {(bulkRunning || bulkPaused) && !bulkFinished && (
                    <Button variant="contained" color="error" size="large" onClick={() => { pauseBulkUpload(); setBulkFinished(true); setBulkRunning(false); }}>
                      Stop
                    </Button>
                  )}
                  
                  {etaSeconds !== null && (
                    <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                      ETA: {Math.floor(etaSeconds / 60)}m {etaSeconds % 60}s
                    </Typography>
                  )}
                </Box>"""

content = re.sub(old_button_regex, new_buttons, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('UploadReportPage patched!')
