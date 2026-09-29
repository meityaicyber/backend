import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the mangled renderValue
content = re.sub(
    r'renderValue=\{\(selected\) => Widgets\}',
    r'renderValue={(selected) => `${selected.length} Widgets`}',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
