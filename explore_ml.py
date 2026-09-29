import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# print the Grid structure
lines = content.splitlines()
for i, line in enumerate(lines):
    if '<Grid ' in line or '</Grid>' in line or '<Card' in line or '</Card>' in line:
        print(f"{i}: {line.strip()}")

