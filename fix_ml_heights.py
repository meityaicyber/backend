import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace CardContent
content = content.replace("<CardContent sx={{ flex: 1 }}>", "<CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>")

# Replace Box height 300 with flex 1
# Since we only want to replace the chart wrappers, let's use regex
# Look for <Box sx={{ height: 300 }}> followed by <ResponsiveContainer width="100%" height="100%">
pattern = r'<Box sx=\{\{ height: 300 \}\}>\s*<ResponsiveContainer width="100%" height="100%">'
replacement = r'<Box sx={{ flex: 1, minHeight: 0 }}>\n                  <ResponsiveContainer width="100%" height="100%">'
content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Heights fixed")
