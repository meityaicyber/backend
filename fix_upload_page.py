import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update context imports
old_context = """    const {
      bulkFilesData, setBulkFilesData, bulkProgress, bulkTotal, bulkRunning, bulkFinished, setBulkFinished,
      bulkStartTime, bulkEndTime, startBulkUpload, resetBulkState
    } = useBulkUpload();"""

new_context = """    const {
      bulkFilesData, setBulkFilesData, bulkProgress, bulkTotal, bulkRunning, bulkFinished, setBulkFinished,
      bulkStartTime, bulkEndTime, bulkPaused, etaSeconds,
      startBulkUpload, pauseBulkUpload, resumeBulkUpload, resetBulkState
    } = useBulkUpload();"""

content = content.replace(old_context, new_context)

# Update concurrency definition
old_concurrency = "const concurrency = batchMode === 'batch4' ? 4 : (batchMode === 'batch2' ? 2 : 1);"
new_concurrency = "const concurrency = batchMode === 'batch8' ? 8 : (batchMode === 'batch4' ? 4 : (batchMode === 'batch2' ? 2 : 1));"
content = content.replace(old_concurrency, new_concurrency)

# Update radio group
old_radio = """                    <RadioGroup row value={batchMode} onChange={(e) => setBatchMode(e.target.value)}>
                      <FormControlLabel value="sequential" control={<Radio />} label="Sequential (1 by 1)" />
                      <FormControlLabel value="batch2" control={<Radio />} label="Batch of 2" />
                      <FormControlLabel value="batch4" control={<Radio />} label="Batch of 4" />
                    </RadioGroup>"""
new_radio = """                    <RadioGroup row value={batchMode} onChange={(e) => setBatchMode(e.target.value)}>
                      <FormControlLabel value="sequential" control={<Radio />} label="Sequential (1 by 1)" />
                      <FormControlLabel value="batch2" control={<Radio />} label="Batch of 2" />
                      <FormControlLabel value="batch4" control={<Radio />} label="Batch of 4" />
                      <FormControlLabel value="batch8" control={<Radio />} label="Batch of 8" />
                    </RadioGroup>"""
content = content.replace(old_radio, new_radio)

# Update Buttons
old_buttons = """                <Box>
                  <Button variant="contained" color="primary" size="large" startIcon={<PlayArrow />} onClick={handleBulkLaunch} disabled={bulkRunning || pdfFiles.length === 0}>
                    {bulkRunning ? 'Running...' : 'Launch Bulk Processing'}
                  </Button>
                </Box>"""

new_buttons = """                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <Button variant="contained" color="primary" size="large" startIcon={<PlayArrow />} onClick={handleBulkLaunch} disabled={bulkRunning || pdfFiles.length === 0}>
                    {bulkRunning && !bulkPaused ? 'Running...' : 'Launch Bulk Processing'}
                  </Button>
                  
                  {bulkRunning && !bulkFinished && !bulkPaused && (
                    <Button variant="contained" color="warning" size="large" onClick={pauseBulkUpload}>
                      Pause Queue
                    </Button>
                  )}
                  {bulkPaused && !bulkFinished && (
                    <Button variant="contained" color="success" size="large" onClick={() => resumeBulkUpload({}, selectedAgency, concurrency)}>
                      Resume Queue
                    </Button>
                  )}
                  
                  {etaSeconds !== null && (
                    <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                      ETA: {Math.floor(etaSeconds / 60)}m {etaSeconds % 60}s
                    </Typography>
                  )}
                </Box>"""
content = content.replace(old_buttons, new_buttons)


# Also need to make sure startBulkUpload isn't awaited if we removed await.
content = content.replace("await startBulkUpload(bulkFilesData", "startBulkUpload(bulkFilesData")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
