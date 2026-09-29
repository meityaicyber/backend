import re
file_path = r'c:\Main Project\Module\backend\frontend\src\pages\AnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('height={300}', 'height="100%"')
content = content.replace('height={280}', 'height="100%"')

# Fix data grid height
content = content.replace('sx={{ height: 350, width: \'100%\' }}', 'sx={{ height: "100%", width: \'100%\', minHeight: 300 }}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
