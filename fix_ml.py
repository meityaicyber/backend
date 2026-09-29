import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'Alert\s+FormControl', 'Alert,\n  FormControl', content)

customize_btn = r'''
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 0 }}>AI Risk Analytics</Typography>
          <FormControl size="small" sx={{ minWidth: 200, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
            <InputLabel sx={{ color: 'text.secondary' }}>Customize Widgets</InputLabel>
            <Select
              multiple
              value={visibleWidgets}
              onChange={(e) => setVisibleWidgets(e.target.value)}
              input={<OutlinedInput label="Customize Widgets" />}
              renderValue={(selected) => ${selected.length} Widgets}
            >
              {allWidgets.map((w) => (
                <MenuItem key={w.id} value={w.id}>
                  <Checkbox checked={visibleWidgets.indexOf(w.id) > -1} />
                  <ListItemText primary={w.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
'''

content = content.replace('<Typography variant="h4" fontWeight={800} sx={{ mb: 4 }}>AI Risk Analytics</Typography>', customize_btn)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
