file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/ReportsPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "<CardContent sx={{ p: 0, flexGrow: 1, height: 600 }}>",
    "<CardContent sx={{ p: 0, flexGrow: 1, height: 600, display: 'flex', flexDirection: 'column' }}>"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
